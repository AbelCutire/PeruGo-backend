from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from services.auth_service import (
    hash_password, verify_password, create_jwt, 
    create_password_reset_token, consume_reset_token
)
from services.email_service import send_reset_email
from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    """Registro de nuevo usuario"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not all([email, username, password]):
        return jsonify({"error": "Faltan datos obligatorios"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El correo ya está registrado"}), 409
    
    user = User(
        email=email, 
        username=username, 
        password_hash=hash_password(password)
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": "Usuario creado exitosamente",
        "user_id": user.id
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """Login de usuario"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not all([email, username, password]):
        return jsonify({"error": "Faltan credenciales"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    if user.username != username:
        return jsonify({"error": "Nombre de usuario incorrecto"}), 401
    
    if not verify_password(password, user.password_hash):
        return jsonify({"error": "Contraseña incorrecta"}), 401
    
    token = create_jwt(user.id, user.email)
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }), 200

@auth_bp.route("/recover", methods=["POST"])
def recover():
    """Solicitar recuperación de contraseña"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "Correo requerido"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    # Respuesta neutral para evitar enumeración de cuentas
    if not user:
        return jsonify({
            "message": "Si el correo existe, recibirás un enlace de recuperación"
        }), 200
    
    # Crear token de recuperación
    prt = create_password_reset_token(user, expires_minutes=30)
    reset_link = f"{Config.FRONTEND_BASE}/reset-password?token={prt.token}"
    
    # Enviar correo
    if not send_reset_email(user.email, reset_link):
        return jsonify({
            "error": "Error al enviar correo. Contacta soporte."
        }), 500
    
    return jsonify({
        "message": "Si el correo existe, recibirás un enlace de recuperación"
    }), 200

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Ejecutar reset de contraseña con token"""
    data = request.get_json() or {}
    token = data.get("token", "").strip()
    new_password = data.get("newPassword", "").strip()
    
    if not token or not new_password:
        return jsonify({"error": "Token y nueva contraseña requeridos"}), 400
    
    user, error = consume_reset_token(token)
    if error:
        return jsonify({"error": error}), 400
    
    user.password_hash = hash_password(new_password)
    db.session.commit()
    
    return jsonify({"message": "Contraseña actualizada exitosamente"}), 200
