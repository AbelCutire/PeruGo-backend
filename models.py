from datetime import datetime
import uuid
from extensions import db

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref=db.backref("reset_tokens", lazy="dynamic"))


class EmailVerificationToken(db.Model):
    __tablename__ = "email_verification_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("email_verification_tokens", lazy="dynamic"))

class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    
    # Datos del plan
    destination_id = db.Column(db.String(100), nullable=False)  # Ej: "cusco"
    tour_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="borrador", nullable=False) # borrador, pendiente, confirmado, etc.
    
    # Fechas del viaje
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # Gastos (Almacenado como JSON)
    # Nota: Si usas MySQL 5.7+ o PostgreSQL, esto funciona nativo. 
    # Si usas SQLite antiguo, podría requerir ajustes.
    expenses = db.Column(db.JSON, nullable=True)
    
    review_completed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación para acceder desde User: user.plans
    user = db.relationship("User", backref=db.backref("plans", lazy="dynamic"))


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    
    # Opcional: Vincular reseña a un plan específico
    plan_id = db.Column(db.String(36), db.ForeignKey("plans.id"), nullable=True)
    
    destination_id = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 a 5
    comment = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("reviews", lazy="dynamic"))


# Historial de Chat para sincronizar conversaciones
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref=db.backref("chat_sessions", lazy="dynamic"))

class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("chat_sessions.id"), nullable=False)
    
    role = db.Column(db.String(20), nullable=False) # "user" o "assistant"
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("ChatSession", backref=db.backref("messages", lazy="dynamic"))
