from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
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
    url = Column(Text, nullable=False)
    domain = Column(String(255))
    final_verdict = Column(String(50))        # was: verdict
    threat_score = Column(Float)
    ml_prediction = Column(String(50))
    vt_malicious = Column(Integer)            # was: virustotal_malicious
    vt_suspicious = Column(Integer)           # was: virustotal_suspicious
    vt_harmless = Column(Integer)             # new
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Removed: ml_confidence, has_ssl, has_forms, suspicious_keywords, scan_type, ip_address, user_agent
    
    user = relationship('User', back_populates='scans')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'url': self.url,
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


def init_db():
    """Initialize database - create all tables"""
    print("🔧 Creating database tables...")
    Base.metadata.create_all(engine)
    print(" Database tables created successfully!")

def create_sample_data():
    """Create sample data for testing"""
    session = Session()
    
    try:
        admin = session.query(User).filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@cybersentinel.com',
                role='admin'
            )
            admin.set_password('admin123')
            session.add(admin)
            print("Admin user created (username: admin, password: admin123)")
        else:
            if admin.role != 'admin':
                admin.role = 'admin'
                print("Existing admin user updated with admin role")
        
        session.commit()
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print(" CyberSentinel Database Setup")
    print("=" * 60)
    
    init_db()
    create_sample_data()
    
    print("\n Database setup complete!")
    print("\nYou can now:")
    print("  1. Login with: admin / admin123")
    print("  2. Start the Flask server")
    print("  3. Test the API endpoints")
    print("=" * 60)