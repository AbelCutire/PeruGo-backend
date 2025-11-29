import smtplib
from email.message import EmailMessage
from config import Config

def send_reset_email(to_email: str, reset_link: str):
    """Envía correo de recuperación de contraseña"""
    msg = EmailMessage()
    msg["Subject"] = "Recuperación de contraseña - PeruGo"
    msg["From"] = Config.MAIL_FROM
    msg["To"] = to_email
    
    msg.set_content(f"""
Hola,

Has solicitado recuperar tu contraseña en PeruGo.

Haz clic en el siguiente enlace para establecer una nueva contraseña:
{reset_link}

Este enlace expira en 30 minutos y solo puede usarse una vez.

Si no solicitaste este cambio, ignora este correo.

Saludos,
Equipo PeruGo
""")
    
    try:
        with smtplib.SMTP(Config.MAIL_HOST, Config.MAIL_PORT) as server:
            server.starttls()
            server.login(Config.MAIL_USER, Config.MAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False


def send_verification_email(to_email: str, verify_link: str):
    msg = EmailMessage()
    msg["Subject"] = "Verifica tu correo - PeruGo"
    msg["From"] = Config.MAIL_FROM
    msg["To"] = to_email

    msg.set_content(f"""
Hola,

Gracias por registrarte en PeruGo.

Por favor, verifica tu correo haciendo clic en el siguiente enlace:
{verify_link}

Si no creaste esta cuenta, puedes ignorar este mensaje.

Saludos,
Equipo PeruGo
""")

    try:
        with smtplib.SMTP(Config.MAIL_HOST, Config.MAIL_PORT) as server:
            server.starttls()
            server.login(Config.MAIL_USER, Config.MAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Error enviando email de verificación: {e}")
        return False
