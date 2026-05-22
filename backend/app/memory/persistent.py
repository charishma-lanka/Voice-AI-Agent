from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.models import Patient, PatientPreference, Appointment

class PersistentMemory:
    """Persistent memory using SQLite/PostgreSQL"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_patient(self, patient_id: int) -> Optional[Dict]:
        """Get patient by ID"""
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None
        
        preferences = self.db.query(PatientPreference).filter(
            PatientPreference.patient_id == patient_id
        ).first()
        
        return {
            "id": patient.id,
            "name": patient.name,
            "phone": patient.phone_number,
            "preferred_language": patient.preferred_language,
            "preferred_doctor_id": patient.preferred_doctor_id,
            "preferences": {
                "notification_enabled": preferences.notification_enabled if preferences else True,
                "preferred_time_slots": preferences.preferred_time_slots if preferences else "[]"
            } if preferences else {}
        }
    
    async def get_or_create_patient(self, phone: str, name: str = None) -> Dict:
        """Get existing patient or create new one"""
        patient = self.db.query(Patient).filter(Patient.phone_number == phone).first()
        
        if not patient:
            patient = Patient(
                phone_number=phone,
                name=name or "Patient",
                preferred_language="english"
            )
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
            
            # Create preferences
            preferences = PatientPreference(patient_id=patient.id)
            self.db.add(preferences)
            self.db.commit()
        
        return await self.get_patient(patient.id)
    
    async def update_language_preference(self, patient_id: int, language: str) -> None:
        """Update patient's preferred language"""
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            patient.preferred_language = language
            self.db.commit()
    
    async def get_appointment_history(self, patient_id: int, limit: int = 10) -> List[Dict]:
        """Get patient's appointment history"""
        appointments = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.date.desc()).limit(limit).all()
        
        return [
            {
                "id": apt.id,
                "doctor_id": apt.doctor_id,
                "date": apt.date,
                "time": apt.time,
                "status": apt.status
            }
            for apt in appointments
        ]
    
    async def save_conversation_summary(self, patient_id: int, summary: str) -> None:
        """Save conversation summary for future context"""
        preferences = self.db.query(PatientPreference).filter(
            PatientPreference.patient_id == patient_id
        ).first()
        
        if preferences:
            preferences.last_conversation_summary = summary[:500]  # Limit length
            self.db.commit()