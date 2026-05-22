import time
import re
from typing import Dict, Any

class LLMAgent:
    """LLM Agent for intent recognition and response generation"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    async def process(self, user_text: str, language: str, context: Dict) -> Dict[str, Any]:
        """
        Process user input and return intent
        """
        start_time = time.time()
        
        # Rule-based intent detection
        result = self._rule_based_detection(user_text, context)
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return result
    
    def _rule_based_detection(self, text: str, context: Dict) -> Dict:
        """Rule-based intent detection"""
        text_lower = text.lower()
        
        # Check for pending context (follow-up from previous message)
        pending = context.get("pending", {})
        if pending.get("status") == "awaiting_time":
            # Check if user is providing a time
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
        
        # Booking intent
        if any(word in text_lower for word in ["book", "appointment", "schedule", "want to see", "need to see"]):
            specialty = "general physician"
            if "cardio" in text_lower:
                specialty = "cardiologist"
            elif "derma" in text_lower or "skin" in text_lower:
                specialty = "dermatologist"
            elif "ortho" in text_lower:
                specialty = "orthopedic"
            elif "pediatric" in text_lower:
                specialty = "pediatrician"
            
            date = "today"
            if "tomorrow" in text_lower:
                date = "tomorrow"
            
            return {
                "intent": "book",
                "specialty": specialty,
                "date": date,
                "time": None,
                "appointment_id": None,
                "response_text": f"Sure! I can help you book an appointment with a {specialty}. Available slots: 09:00 AM, 10:00 AM, 11:00 AM, 02:00 PM. Which time works for you?"
            }
        
        # Cancel intent - FIXED: Extract appointment ID
        elif "cancel" in text_lower:
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
                return {
                    "intent": "cancel",
                    "specialty": None,
                    "date": None,
                    "time": None,
                    "appointment_id": None,
                    "response_text": "Please provide your appointment ID to cancel. Example: 'Cancel appointment 1'"
                }
        
        # Reschedule intent
        elif "reschedule" in text_lower or "change" in text_lower:
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
        
        # Greeting
        elif text_lower in ["hi", "hello", "hey", "good morning", "good afternoon", "namaste"]:
            return {
                "intent": "greeting",
                "specialty": None,
                "date": None,
                "time": None,
                "appointment_id": None,
                "response_text": "Hello! How can I help you today? You can say 'Book appointment with cardiologist' or 'Cancel appointment 1'."
            }
        
        # Default response
        return {
            "intent": "general",
            "specialty": None,
            "date": None,
            "time": None,
            "appointment_id": None,
            "response_text": "How can I help you? You can say 'Book appointment with cardiologist' or 'Cancel appointment 1'."
        }