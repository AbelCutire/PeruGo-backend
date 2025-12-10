from datetime import datetime, timedelta
import bcrypt
import jwt
import secrets
from config import Config
from extensions import db
from models import User, PasswordResetToken
from functools import wraps
from flask import request, jsonify

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

def token_required(f):
    """
    Decorador para proteger rutas. 
    Verifica que el header 'Authorization' contenga un JWT válido.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Buscar el token en el header Authorization: Bearer <token>
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token de autenticación faltante'}), 401
        
        try:
            # 2. Decodificar y validar el token
            data = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
            
            # 3. Buscar el usuario en la BD (data['sub'] suele ser el user_id)
            current_user = User.query.filter_by(id=data['sub']).first()
            
            if not current_user:
                return jsonify({'message': 'Usuario no encontrado o token inválido'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'El token ha expirado, por favor inicia sesión nuevamente'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        except Exception as e:
            print(f"Error auth: {e}")
            return jsonify({'message': 'Error de autenticación'}), 401
            
        # 4. Pasar el usuario actual a la función de la ruta
        return f(current_user, *args, **kwargs)
    
    return decorated
