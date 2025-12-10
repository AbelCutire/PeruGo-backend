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
    
    @app.route("/")
    def home():
        return jsonify({
            "message": "✅ Backend PeruGo operativo",
            "version": "2.0",
            "endpoints": {
                "auth": "/auth/register, /auth/login, /auth/recover, /auth/reset-password",
                "llm": "/process",
                "rdf": "/rdf"
            }
        })
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
