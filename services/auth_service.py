from datetime import datetime, timedelta
import bcrypt
import jwt
import secrets
from config import Config
from extensions import db
from models import User, PasswordResetToken

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_jwt(user_id: str, email: str):
    """Crea un token JWT para el usuario"""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow().timestamp() + Config.JWT_EXP_SECONDS
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

def decode_jwt(token: str):
    """Decodifica y valida un JWT"""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
    except:
        return None

def create_password_reset_token(user: User, expires_minutes: int = 30):
    """Crea un token de recuperación de contraseña"""
    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    prt = PasswordResetToken(
        user_id=user.id, 
        token=token, 
        expires_at=expires_at, 
        used=False
    )
    db.session.add(prt)
    db.session.commit()
    return prt

def consume_reset_token(token_str: str):
    """Consume un token de reset (solo se puede usar una vez)"""
    prt = PasswordResetToken.query.filter_by(token=token_str, used=False).first()
    if not prt:
        return None, "Token inválido o ya usado"
    
    if prt.expires_at < datetime.utcnow():
        return None, "Token expirado"
    
    prt.used = True
    db.session.commit()
    return prt.user, None