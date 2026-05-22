from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List
from app.models import Doctor, Appointment, Patient

class AppointmentTools:
    """Tool orchestration for appointment management"""
    
    # Available time slots
    TIME_SLOTS = ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM"]
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_availability(self, specialty: str, date: str) -> Dict[str, Any]:
        """
        Check doctor availability
        """
        # Find matching doctors
        doctors = self.db.query(Doctor).filter(
            Doctor.specialty.ilike(f"%{specialty}%"),
            Doctor.is_available == True
        ).all()
        
        if not doctors:
            return {
                "available": False,
                "slots": [],
                "doctor": None,
                "message": f"Sorry, no {specialty} doctors available today."
            }
        
        # Get booked slots for these doctors on given date
        booked_appointments = self.db.query(Appointment).filter(
            Appointment.doctor_id.in_([d.id for d in doctors]),
            Appointment.date == date,
            Appointment.status == "scheduled"
        ).all()
        
        booked_times = [apt.time for apt in booked_appointments]
        available_slots = [slot for slot in self.TIME_SLOTS if slot not in booked_times]
        
        if available_slots:
            return {
                "available": True,
                "slots": available_slots,
                "doctor": doctors[0].name,
                "doctor_id": doctors[0].id,
                "message": f"Available slots for {specialty} on {date}: {', '.join(available_slots[:3])}"
            }
        else:
            return {
                "available": False,
                "slots": [],
                "doctor": doctors[0].name,
                "message": f"No slots available for {specialty} on {date}. Please try another date."
            }
    
    def book_appointment(self, patient_id: int, doctor_id: int, date: str, time_slot: str) -> Dict[str, Any]:
        """
        Book an appointment
        """
        # Validate date not in past
        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d")
            if appointment_date.date() < datetime.now().date():
                return {
                    "success": False,
                    "message": "Cannot book appointment in the past."
                }
        except:
            pass
        
        # Check for conflicts
        existing = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == date,
            Appointment.time == time_slot,
            Appointment.status == "scheduled"
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": f"Sorry, {time_slot} is already booked. Please choose another time."
            }
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=date,
            time=time_slot,
            status="scheduled"
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        # Get doctor name
        doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        doctor_name = doctor.name if doctor else "the doctor"
        
        return {
            "success": True,
            "appointment_id": appointment.id,
            "message": f"✅ Appointment confirmed! Your appointment with {doctor_name} is scheduled for {date} at {time_slot}. Appointment ID: {appointment.id}"
        }
    
    def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """
        Cancel an existing appointment
        """
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            return {
                "success": False,
                "message": f"Appointment {appointment_id} not found."
            }
        
        if appointment.status == "cancelled":
            return {
                "success": False,
                "message": f"Appointment {appointment_id} is already cancelled."
            }
        
        appointment.status = "cancelled"
        self.db.commit()
        
        return {
            "success": True,
            "message": f"✅ Appointment {appointment_id} has been cancelled successfully."
        }
    
    def reschedule_appointment(self, appointment_id: int, new_date: str, new_time: str) -> Dict[str, Any]:
        """
        Reschedule an appointment
        """
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            return {
                "success": False,
                "message": f"Appointment {appointment_id} not found."
            }
        
        if appointment.status == "cancelled":
            return {
                "success": False,
                "message": "Cannot reschedule a cancelled appointment."
            }
        
        # Check availability for new slot
        conflict = self.db.query(Appointment).filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.date == new_date,
            Appointment.time == new_time,
            Appointment.status == "scheduled"
        ).first()
        
        if conflict:
            return {
                "success": False,
                "message": f"Slot {new_time} on {new_date} is already booked. Please choose another time."
            }
        
        old_date = appointment.date
        old_time = appointment.time
        
        appointment.date = new_date
        appointment.time = new_time
        self.db.commit()
        
        return {
            "success": True,
            "message": f"✅ Appointment rescheduled from {old_date} at {old_time} to {new_date} at {new_time}."
        }
    
    def get_patient_appointments(self, patient_id: int) -> List[Dict]:
        """Get all appointments for a patient"""
        appointments = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.date.desc()).all()
        
        return [
            {
                "id": apt.id,
                "date": apt.date,
                "time": apt.time,
                "status": apt.status
            }
            for apt in appointments
        ]