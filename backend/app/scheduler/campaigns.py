from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio

class OutboundCampaignScheduler:
    """Handle outbound calling campaigns for reminders and follow-ups"""
    
    def __init__(self, db_session_factory):
        self.scheduler = BackgroundScheduler()
        self.db_session_factory = db_session_factory
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        # Daily reminder job at 9 AM
        self.scheduler.add_job(
            func=self.send_appointment_reminders,
            trigger="cron",
            hour=9,
            minute=0,
            id="appointment_reminders",
            replace_existing=True
        )
        
        # Follow-up job at 6 PM
        self.scheduler.add_job(
            func=self.send_follow_up_calls,
            trigger="cron",
            hour=18,
            minute=0,
            id="follow_up_calls",
            replace_existing=True
        )
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        print("✅ Outbound campaign scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("⏹️ Outbound campaign scheduler stopped")
    
    async def send_appointment_reminders(self):
        """Send reminders for tomorrow's appointments"""
        print(f"📞 Running appointment reminder campaign at {datetime.now()}")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        db = self.db_session_factory()
        try:
            from app.models import Appointment, Patient
            
            appointments = db.query(Appointment).filter(
                Appointment.date == tomorrow,
                Appointment.status == "scheduled"
            ).all()
            
            for apt in appointments:
                patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
                if patient:
                    # In production: trigger actual outbound call
                    print(f"📞 Outbound call to {patient.phone_number}: Reminder for appointment tomorrow")
                    
        finally:
            db.close()
    
    async def send_follow_up_calls(self):
        """Send follow-up calls for completed appointments"""
        print(f"📞 Running follow-up campaign at {datetime.now()}")
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        db = self.db_session_factory()
        try:
            from app.models import Appointment, Patient
            
            appointments = db.query(Appointment).filter(
                Appointment.date == yesterday,
                Appointment.status == "completed"
            ).all()
            
            for apt in appointments:
                patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
                if patient:
                    # In production: trigger actual outbound call
                    print(f"📞 Outbound follow-up call to {patient.phone_number}")
                    
        finally:
            db.close()
    
    async def trigger_campaign(self, campaign_type: str, patient_ids: List[int], message: str):
        """Manually trigger a campaign"""
        print(f"📞 Manual campaign '{campaign_type}' triggered for {len(patient_ids)} patients")
        
        db = self.db_session_factory()
        try:
            from app.models import Patient
            
            for patient_id in patient_ids:
                patient = db.query(Patient).filter(Patient.id == patient_id).first()
                if patient:
                    # In production: trigger actual outbound call
                    print(f"📞 Outbound call to {patient.phone_number}: {message}")
        finally:
            db.close()