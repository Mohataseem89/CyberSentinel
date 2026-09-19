from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from config import Config
import bcrypt

Base = declarative_base()

# Database engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    scans = relationship('Scan', back_populates='user', cascade='all, delete-orphan')
    bulk_jobs = relationship('BulkScanJob', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
        }
   
        
        

class Scan(Base):
    __tablename__ = 'scans'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    # Raw URLs are never retained in scan history.
    url_hash = Column(String(64), nullable=False, index=True)
    url_redacted = Column(String(255), nullable=False)
    domain = Column(String(255))
    final_verdict = Column(String(50))        # was: verdict
    threat_score = Column(Float)
    ml_prediction = Column(String(50))
    vt_malicious = Column(Integer)            # was: virustotal_malicious
    vt_suspicious = Column(Integer)           # was: virustotal_suspicious
    vt_harmless = Column(Integer)             # new
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Removed: ml_confidence, has_ssl, has_forms, suspicious_keywords, scan_type, ip_address, user_agent
    
    user = relationship('User', back_populates='scans')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'url': self.url_redacted,
            'domain': self.domain,
            'final_verdict': self.final_verdict,
            'threat_score': self.threat_score,
            'ml_prediction': self.ml_prediction,
            'vt_malicious': self.vt_malicious,
            'vt_suspicious': self.vt_suspicious,
            'vt_harmless': self.vt_harmless,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    url = Column(Text, nullable=False)
    category = Column(String(50))
    actual_threat = Column(String(50))
    our_prediction = Column(String(50))
    description = Column(Text)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'url': self.url,
            'category': self.category,
            'actual_threat': self.actual_threat,
            'our_prediction': self.our_prediction,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BulkScanJob(Base):
    __tablename__ = 'bulk_scan_jobs'
    id = Column(Integer, primary_key=True)
    public_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(32), nullable=False, default='QUEUED')
    total_urls = Column(Integer, nullable=False, default=0)
    processed = Column(Integer, nullable=False, default=0)
    successful = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    user = relationship('User', back_populates='bulk_jobs')
    items = relationship('BulkScanItem', back_populates='job', cascade='all, delete-orphan')
    __table_args__ = (Index('ix_bulk_scan_jobs_owner_status', 'user_id', 'status'),)

class BulkScanItem(Base):
    __tablename__ = 'bulk_scan_items'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('bulk_scan_jobs.id', ondelete='CASCADE'), nullable=False)
    row_number = Column(Integer, nullable=False)
    normalized_url = Column(Text)
    url_redacted = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, default='QUEUED')
    attempts = Column(Integer, nullable=False, default=0)
    final_verdict = Column(String(50))
    threat_score = Column(Float)
    error_code = Column(String(64))
    job = relationship('BulkScanJob', back_populates='items')
    __table_args__ = (Index('ix_bulk_scan_items_job_status', 'job_id', 'status'),)

    def to_dict(self):
        return {
            'row': self.row_number,
            'url': self.url_redacted,
            'status': self.status,
            'verdict': self.final_verdict,
            'threat_score': self.threat_score,
            'error': self.error_code,
        }


def init_db():
    """Initialize database - create all tables"""
    print("🔧 Creating database tables...")
    Base.metadata.create_all(engine)
    print(" Database tables created successfully!")

if __name__ == "__main__":
    print("=" * 60)
    print(" CyberSentinel Database Setup")
    print("=" * 60)
    
    init_db()
    
    print("\n Database setup complete!")
    print("\nCreate the first administrator through a separate, audited bootstrap process.")
    print("=" * 60)
