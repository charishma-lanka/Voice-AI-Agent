from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import config
from app.models import Base, Patient, Doctor, Appointment

# Create engine
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    _seed_sample_data()

def _seed_sample_data():
    """Seed sample doctors if none exist"""
    db = SessionLocal()
    try:
        if db.query(Doctor).count() == 0:
            sample_doctors = [
                Doctor(name="Dr. Sharma", specialty="cardiologist", is_available=True),
                Doctor(name="Dr. Patel", specialty="dermatologist", is_available=True),
                Doctor(name="Dr. Kumar", specialty="general physician", is_available=True),
                Doctor(name="Dr. Reddy", specialty="orthopedic", is_available=True),
                Doctor(name="Dr. Gupta", specialty="pediatrician", is_available=True),
            ]
            for doctor in sample_doctors:
                db.add(doctor)
            db.commit()
            print("✅ Sample doctors added to database")
    finally:
        db.close()

def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()