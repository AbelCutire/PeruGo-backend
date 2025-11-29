from flask import Blueprint, request, jsonify, render_template_string
from extensions import db
from models import User, EmailVerificationToken
import secrets
from services.auth_service import (
    hash_password,
    verify_password,
    create_jwt,
    create_password_reset_token,
    consume_reset_token,
    decode_jwt,
)
from services.email_service import send_reset_email, send_verification_email
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
        password_hash=hash_password(password),
        is_verified=False,
    )
    db.session.add(user)
    db.session.commit()

    token = secrets.token_urlsafe(48)
    evt = EmailVerificationToken(
        user_id=user.id,
        token=token,
        used=False,
    )
    db.session.add(evt)
    db.session.commit()

    verify_link = f"{Config.FRONTEND_BASE}/verify-email?token={token}"
    send_verification_email(user.email, verify_link)

    return jsonify({
        "message": "Usuario creado exitosamente. Revisa tu correo para verificar la cuenta.",
        "user_id": user.id,
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """Login de usuario - solo requiere email y contraseña"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    
    # Validar que se recibieron los datos mínimos
    if not email or not password:
        return jsonify({"error": "Email y contraseña son requeridos"}), 400
    
    # Buscar usuario por email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Credenciales incorrectas"}), 401
    
    # Verificar contraseña
    if not verify_password(password, user.password_hash):
        return jsonify({"error": "Credenciales incorrectas"}), 401
    
    # Login exitoso - generar token
    token = create_jwt(user.id, user.email)
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }), 200


@auth_bp.route("/profile", methods=["PATCH"])
def update_profile():
    """Actualizar datos básicos del perfil (actualmente solo username)"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_jwt(token)
    if not payload:
        return jsonify({"error": "Token inválido o expirado"}), 401

    user_id = payload.get("sub")
    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify({"error": "El nombre de usuario es requerido"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user.username = username
    db.session.commit()

    return jsonify({
        "message": "Perfil actualizado correctamente",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        },
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


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json() or {}
    token = (data.get("token") or "").strip()

    if not token:
        return jsonify({"error": "Token requerido"}), 400

    evt = EmailVerificationToken.query.filter_by(token=token, used=False).first()
    if not evt:
        return jsonify({"error": "Token inválido o ya usado"}), 400

    user = evt.user
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user.is_verified = True
    evt.used = True
    db.session.commit()

    return jsonify({"message": "Correo verificado correctamente"}), 200


@auth_bp.route("/verify-email", methods=["GET"])
def verify_email_page():
    """Ruta HTML sencilla para verificar correo desde el enlace del email"""
    token = (request.args.get("token") or "").strip()

    if not token:
        message = "Token de verificación no proporcionado."
        success = False
    else:
        evt = EmailVerificationToken.query.filter_by(token=token, used=False).first()
        if not evt:
            message = "El enlace de verificación es inválido o ya fue utilizado."
            success = False
        else:
            user = evt.user
            if not user:
                message = "Usuario asociado al token no encontrado."
                success = False
            else:
                user.is_verified = True
                evt.used = True
                db.session.commit()
                message = "Tu correo ha sido verificado correctamente. Ya puedes iniciar sesión en la app."
                success = True

    html = """
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <title>Verificación de correo - PeruGo</title>
        <style>
          body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e5e7eb; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
          .card { background: #020617; padding: 24px 28px; border-radius: 16px; box-shadow: 0 20px 40px rgba(15, 23, 42, 0.6); max-width: 420px; text-align: center; border: 1px solid #1f2937; }
          h1 { font-size: 22px; margin-bottom: 12px; }
          p { font-size: 15px; line-height: 1.6; }
          .ok { color: #4ade80; }
          .error { color: #f97373; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1 class="{{ 'ok' if success else 'error' }}">{{ 'Correo verificado' if success else 'Verificación fallida' }}</h1>
          <p>{{ message }}</p>
        </div>
      </body>
    </html>
    """

    return render_template_string(html, success=success, message=message)

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
