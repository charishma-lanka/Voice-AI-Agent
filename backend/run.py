import uvicorn

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     🏥  VOICE AI HEALTHCARE AGENT                            ║
    ║     Real-Time Multilingual Clinical Appointment Booking      ║
    ║                                                               ║
    ║     Target Latency: <450ms                                   ║
    ║     Languages: English | हिन्दी | தமிழ்                      ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Starting server...
    📡 Backend API: http://localhost:8000
    🔌 WebSocket: ws://localhost:8000/ws/{patient_id}
    
    Press Ctrl+C to stop
    """)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )