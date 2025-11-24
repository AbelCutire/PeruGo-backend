import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cambiar_en_produccion")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "cambiar_jwt_secret")
    JWT_ALGORITHM = "HS256"
    JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", 604800))  # 7 días
    
    # Email
    MAIL_HOST = os.getenv("MAIL_HOST")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USER = os.getenv("MAIL_USER")
    MAIL_PASS = os.getenv("MAIL_PASS")
    MAIL_FROM = os.getenv("MAIL_FROM", os.getenv("MAIL_USER"))
    FRONTEND_BASE = os.getenv("FRONTEND_BASE", "https://perugo.vercel.app")