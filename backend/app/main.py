from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
import time
import asyncio
from datetime import datetime
from typing import Dict

from app.config import config
from app.database import init_db, get_db
from app.services.language import LanguageService
from app.services.stt import STTService
from app.services.tts import TTSService
from app.agent.llm_agent import LLMAgent
from app.agent.tools import AppointmentTools
from app.memory.session import SessionMemory
from app.memory.persistent import PersistentMemory
from app.scheduler.campaigns import OutboundCampaignScheduler

# Initialize
init_db()

# Create services
language_service = LanguageService()
stt_service = STTService(api_key=config.OPENAI_API_KEY)
tts_service = TTSService()
llm_agent = LLMAgent(api_key=config.OPENAI_API_KEY)
session_memory = SessionMemory(redis_url=config.REDIS_URL)

# Create FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Real-Time Multilingual Voice AI Agent for Clinical Appointment Booking"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store latency metrics
latency_metrics = []

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║     🏥 {config.APP_NAME}                          ║
    ║     Version: {config.APP_VERSION}                              ║
    ║     Target Latency: {config.LATENCY_TARGET_MS}ms                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Start campaign scheduler (bonus feature)
    global campaign_scheduler
    campaign_scheduler = OutboundCampaignScheduler(get_db)
    campaign_scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    if 'campaign_scheduler' in globals():
        campaign_scheduler.stop()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": f"{config.APP_NAME} is running",
        "version": config.APP_VERSION,
        "status": "healthy",
        "latency_target_ms": config.LATENCY_TARGET_MS,
        "supported_languages": ["english", "hindi", "tamil"]
    }

@app.get("/api/latency")
async def get_latency_metrics():
    """Get latency metrics"""
    if not latency_metrics:
        return {
            "target_ms": config.LATENCY_TARGET_MS,
            "average_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "total_requests": 0
        }
    
    avg_latency = sum(latency_metrics) / len(latency_metrics)
    return {
        "target_ms": config.LATENCY_TARGET_MS,
        "average_ms": round(avg_latency, 2),
        "min_ms": min(latency_metrics),
        "max_ms": max(latency_metrics),
        "total_requests": len(latency_metrics),
        "within_target": avg_latency <= config.LATENCY_TARGET_MS
    }

@app.websocket("/ws/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time voice conversation"""
    await websocket.accept()
    print(f"✅ Patient {patient_id} connected")
    
    # Initialize services with DB session
    persistent_memory = PersistentMemory(db)
    appointment_tools = AppointmentTools(db)
    
    # Load session context
    session_context = await session_memory.get(patient_id)
    conversation_context = session_context["context"]
    
    # Load patient history
    patient = await persistent_memory.get_patient(int(patient_id) if patient_id.isdigit() else 1)
    if patient:
        conversation_context["patient"] = patient
        conversation_context["preferred_language"] = patient.get("preferred_language", "english")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            start_time = time.time()
            
            # Get user input (audio or text)
            audio_base64 = data.get("audio", "")
            user_text = data.get("text", "")
            
            # Step 1: STT if audio provided
            if audio_base64 and not user_text:
                stt_result = await stt_service.transcribe(audio_base64)
                user_text = stt_result.get("text", "")
                stt_latency = stt_result.get("latency_ms", 0)
            else:
                stt_latency = 0
            
            if not user_text:
                user_text = "Book appointment"
            
            print(f"\n📝 User: {user_text}")
            
            # Step 2: Language detection
            lang_result = await language_service.detect(user_text)
            language = lang_result["language"]
            print(f"🌐 Language: {language}")
            
            # Step 3: LLM processing
            llm_result = await llm_agent.process(user_text, language, conversation_context)
            intent = llm_result.get("intent", "general")
            print(f"🎯 Intent: {intent}")
            
            # Step 4: Tool execution
            tool_result = None
            response_text = llm_result.get("response_text", "How can I help you?")
            
            if intent == "book":
                # Check availability first
                specialty = llm_result.get("specialty", "general physician")
                date = llm_result.get("date", "today")
                
                availability = appointment_tools.check_availability(specialty, date)
                if availability.get("available") and availability.get("slots"):
                    # Store pending booking in session
                    conversation_context["pending"] = {
                        "specialty": specialty,
                        "date": date,
                        "doctor_id": availability.get("doctor_id"),
                        "status": "awaiting_time"
                    }
                    response_text = availability.get("message", f"Available slots: {', '.join(availability.get('slots', [])[:3])}")
                else:
                    response_text = availability.get("message", "No slots available. Please try another date.")
            
            elif intent == "confirm":
                pending = conversation_context.get("pending", {})
                if pending.get("status") == "awaiting_time":
                    time_slot = llm_result.get("time", "10:00 AM")
                    tool_result = appointment_tools.book_appointment(
                        patient_id=int(patient_id) if patient_id.isdigit() else 1,
                        doctor_id=pending.get("doctor_id", 1),
                        date=pending.get("date", datetime.now().strftime("%Y-%m-%d")),
                        time_slot=time_slot
                    )
                    response_text = tool_result.get("message", response_text)
                    # Clear pending
                    conversation_context["pending"] = None
                    
                    # Update persistent memory
                    await persistent_memory.update_language_preference(
                        int(patient_id) if patient_id.isdigit() else 1,
                        language
                    )
            
            elif intent == "cancel":
                # Extract appointment ID from text
                import re
                numbers = re.findall(r'\d+', user_text)
                if numbers:
                    tool_result = appointment_tools.cancel_appointment(int(numbers[0]))
                    response_text = tool_result.get("message", response_text)
                else:
                    response_text = "Please provide your appointment ID to cancel."
            
            # Step 5: TTS generation
            tts_result = await tts_service.synthesize(response_text, language)
            
            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000
            latency_metrics.append(total_latency)
            if len(latency_metrics) > 100:
                latency_metrics.pop(0)
            
            # Log latency
            status = "✅ PASS" if total_latency < config.LATENCY_TARGET_MS else "❌ FAIL"
            print(f"""
            ╔══════════════════════════════════════════════════════╗
            ║                 LATENCY REPORT                       ║
            ╠══════════════════════════════════════════════════════╣
            ║ STT:           {stt_latency:.2f}ms                              ║
            ║ Language:      {lang_result['latency_ms']:.2f}ms                           ║
            ║ LLM:           {llm_result.get('latency_ms', 0):.2f}ms                           ║
            ║ Tool Exec:     ~30ms                               ║
            ║ TTS:           {tts_result.get('latency_ms', 0):.2f}ms                           ║
            ╠══════════════════════════════════════════════════════╣
            ║ TOTAL:         {total_latency:.2f}ms                            ║
            ║ TARGET:        <{config.LATENCY_TARGET_MS}ms                           ║
            ║ STATUS:        {status}                              ║
            ╚══════════════════════════════════════════════════════╝
            """)
            
            # Update session memory
            await session_memory.set(patient_id, conversation_context)
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "transcript": response_text,
                "user_text": user_text,
                "intent": intent,
                "language": language,
                "latency_ms": round(total_latency, 2),
                "stt_latency_ms": round(stt_latency, 2),
                "llm_latency_ms": llm_result.get('latency_ms', 0),
                "tts_latency_ms": tts_result.get('latency_ms', 0),
                "appointment": tool_result if tool_result and tool_result.get("success") else None
            })
            
    except WebSocketDisconnect:
        print(f"❌ Patient {patient_id} disconnected")
    except Exception as e:
        print(f"⚠️ Error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)