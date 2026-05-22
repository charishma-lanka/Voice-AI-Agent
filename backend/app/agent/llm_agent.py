# FORCE DEPLOY - v2026.05.22.15.30
import time
import re
from typing import Dict, Any

class LLMAgent:
    """LLM Agent for intent recognition and response generation"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    async def process(self, user_text: str, language: str, context: Dict) -> Dict[str, Any]:
        start_time = time.time()
        result = self._rule_based_detection(user_text, context)
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        return result
    
    def _rule_based_detection(self, text: str, context: Dict) -> Dict:
        text_lower = text.lower()
        
        # Check for pending context (follow-up from previous message)
        pending = context.get("pending", {})
        if pending.get("status") == "awaiting_time":
            time_slots = ["09:00", "10:00", "11:00", "02:00", "14:00", "03:00", "15:00", "04:00", "16:00"]
            time_slots_am_pm = ["09:00 am", "10:00 am", "11:00 am", "02:00 pm", "03:00 pm", "04:00 pm"]
            
            selected_time = None
            for slot in time_slots_am_pm:
                if slot in text_lower:
                    selected_time = slot
                    break
            for slot in time_slots:
                if slot in text_lower:
                    selected_time = f"{slot} AM" if int(slot.split(':')[0]) < 12 else f"{slot} PM"
                    break
            
            if selected_time:
                return {
                    "intent": "confirm",
                    "specialty": pending.get("specialty", "doctor"),
                    "date": pending.get("date", "today"),
                    "time": selected_time,
                    "appointment_id": None,
                    "response_text": f"Great! I'll book your appointment at {selected_time}."
                }
        
        # HINDI LANGUAGE DETECTION
        hindi_words = ["मुझे", "डॉक्टर", "मिलना", "अपॉइंटमेंट", "बुक", "करना", "है", "कल"]
        is_hindi = any(word in text for word in hindi_words)
        
        # TAMIL LANGUAGE DETECTION  
        tamil_words = ["நாளை", "மருத்துவரை", "பார்க்க", "சந்திப்பு", "முன்பதிவு"]
        is_tamil = any(word in text for word in tamil_words)
        
        # BOOKING INTENT (English + Hindi + Tamil)
        booking_keywords = ["book", "appointment", "schedule", "want to see", "need to see"]
        if is_hindi or is_tamil or any(word in text_lower for word in booking_keywords):
            specialty = "general physician"
            if "cardio" in text_lower or "हृदय" in text:
                specialty = "cardiologist"
            elif "derma" in text_lower or "त्वचा" in text or "skin" in text_lower:
                specialty = "dermatologist"
            
            date = "today"
            if "tomorrow" in text_lower or "कल" in text or "நாளை" in text:
                date = "tomorrow"
            
            # Hindi response
            if is_hindi:
                response = f"जी हाँ! मैं आपके लिए {specialty} के साथ अपॉइंटमेंट बुक कर सकता हूँ। उपलब्ध समय: 09:00 AM, 10:00 AM, 11:00 AM, 02:00 PM। कौन सा समय आपके लिए सही रहेगा?"
            # Tamil response
            elif is_tamil:
                response = f"ஆம்! {specialty} மருத்துவருடன் சந்திப்பை முன்பதிவு செய்ய உதவுகிறேன். கிடைக்கும் நேரங்கள்: 09:00 AM, 10:00 AM, 11:00 AM, 02:00 PM. எந்த நேரம் உங்களுக்கு வசதியானது?"
            # English response
            else:
                response = f"Sure! I can help you book an appointment with a {specialty}. Available slots: 09:00 AM, 10:00 AM, 11:00 AM, 02:00 PM. Which time works for you?"
            
            return {
                "intent": "book",
                "specialty": specialty,
                "date": date,
                "time": None,
                "appointment_id": None,
                "response_text": response
            }
        
        # CANCEL INTENT (English + Hindi + Tamil)
        cancel_keywords = ["cancel", "रद्द", "ரத்து"]
        if any(word in text_lower for word in cancel_keywords) or "रद्द" in text or "ரத்து" in text:
            numbers = re.findall(r'\d+', text)
            if numbers:
                appointment_id = int(numbers[0])
                return {
                    "intent": "cancel",
                    "specialty": None,
                    "date": None,
                    "time": None,
                    "appointment_id": appointment_id,
                    "response_text": f"Cancelling appointment {appointment_id}."
                }
            else:
                # Hindi cancel response
                if "रद्द" in text:
                    response = "कृपया अपनी अपॉइंटमेंट ID प्रदान करें। उदाहरण: 'अपॉइंटमेंट 1 रद्द करें'"
                # Tamil cancel response
                elif "ரத்து" in text:
                    response = "உங்கள் சந்திப்பு ID ஐ வழங்கவும். எடுத்துக்காட்டு: 'சந்திப்பு 1 ரத்து செய்யவும்'"
                else:
                    response = "Please provide your appointment ID to cancel. Example: 'Cancel appointment 1'"
                
                return {
                    "intent": "cancel",
                    "specialty": None,
                    "date": None,
                    "time": None,
                    "appointment_id": None,
                    "response_text": response
                }
        
        # RESCHEDULE INTENT
        if "reschedule" in text_lower or "change" in text_lower or "बदलें" in text or "மாற்ற" in text:
            numbers = re.findall(r'\d+', text)
            if numbers:
                return {
                    "intent": "reschedule",
                    "specialty": None,
                    "date": None,
                    "time": None,
                    "appointment_id": int(numbers[0]),
                    "response_text": f"I can help you reschedule appointment {numbers[0]}. What date and time would you prefer?"
                }
            else:
                return {
                    "intent": "reschedule",
                    "specialty": None,
                    "date": None,
                    "time": None,
                    "appointment_id": None,
                    "response_text": "Please provide your appointment ID to reschedule."
                }
        
        # GREETING
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "namaste", "नमस्ते", "வணக்கம்"]
        if text_lower in greetings:
            return {
                "intent": "greeting",
                "specialty": None,
                "date": None,
                "time": None,
                "appointment_id": None,
                "response_text": "Hello! How can I help you today? You can say 'Book appointment with cardiologist' or 'Cancel appointment 1'."
            }
        
        # DEFAULT
        return {
            "intent": "general",
            "specialty": None,
            "date": None,
            "time": None,
            "appointment_id": None,
            "response_text": "How can I help you? You can say 'Book appointment with cardiologist' or 'Cancel appointment 1'."
        }