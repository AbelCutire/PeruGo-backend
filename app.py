from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Importar configuración y extensiones
from config import Config
from extensions import db, migrate

# Importar blueprints
from routes.auth import auth_bp
from routes.process import process_bp
from generate_rdf import rdf_bp
from routes.planes import planes_bp

# Importar modelos para que SQLAlchemy los reconozca al crear tablas
import models  # <--- IMPORTANTE: Asegura que los modelos estén cargados

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # CORS
    CORS(app)
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(rdf_bp)
    app.register_blueprint(planes_bp)
    
    # --- CREACIÓN AUTOMÁTICA DE TABLAS ---
    # Esto revisa si las tablas existen; si no, las crea.
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas de base de datos verificadas/creadas correctamente.")
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")
    # -------------------------------------
    
    @app.route("/")
    def home():
        return jsonify({
            "message": "✅ Backend PeruGo operativo",
            "version": "2.0",
            "endpoints": {
                "auth": "/auth/register, /auth/login, /auth/recover, /auth/reset-password",
                "llm": "/process",
                "rdf": "/rdf",
                "planes": "/api/planes"
            }
        })
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
