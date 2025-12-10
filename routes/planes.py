from flask import Blueprint, request, jsonify
from extensions import db
from models import Plan, Review
from datetime import datetime
# Asegúrate de importar tu decorador de autenticación. 
# Si no tienes uno aún, revisa services/auth_service.py o routes/auth.py
# Por ahora asumiremos que existe 'token_required'
from services.auth_service import token_required 

planes_bp = Blueprint('planes', __name__)

# ---------------------------------------------------------
# RUTAS PARA GESTIÓN DE PLANES
# ---------------------------------------------------------

@planes_bp.route('/api/planes', methods=['GET'])
@token_required
def get_planes(current_user):
    """
    Obtiene todos los planes del usuario logueado.
    Web/App: GET /api/planes
    """
    try:
        # Buscar planes del usuario ordenados por fecha de creación (más recientes primero)
        planes = Plan.query.filter_by(user_id=current_user.id).order_by(Plan.created_at.desc()).all()
        
        output = []
        for p in planes:
            output.append({
                "id": p.id,
                "destino_id": p.destination_id,
                "tour": p.tour_name,
                "precio": p.price,
                "estado": p.status,
                # Formatear fechas a String ISO para que JS las entienda
                "fecha_inicio": p.start_date.isoformat() if p.start_date else None,
                "fecha_fin": p.end_date.isoformat() if p.end_date else None,
                "duracion": "Consultar detalles", # Opcional si guardas string
                "gastos": p.expenses,  # SQLAlchemy manejará el JSON si la BD lo soporta
                "resena_completada": p.review_completed
            })
        
        return jsonify(output), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@planes_bp.route('/api/planes', methods=['POST'])
@token_required
def create_plan(current_user):
    """
    Crea un nuevo plan.
    Web/App: POST /api/planes
    Body: { destino_id, tour, precio, gastos, ... }
    """
    try:
        data = request.get_json()
        
        # Mapeo de datos Frontend (español) -> Backend Model (inglés)
        new_plan = Plan(
            user_id=current_user.id,
            destination_id=data.get('destino_id'),
            tour_name=data.get('tour'), # En frontend se llama 'tour'
            price=data.get('precio'),
            status=data.get('estado', 'borrador'),
            expenses=data.get('gastos')
        )
        
        # Guardar fechas si vienen en la creación (opcional)
        if data.get('fecha_inicio'):
            new_plan.start_date = datetime.fromisoformat(data['fecha_inicio'])
        if data.get('fecha_fin'):
            new_plan.end_date = datetime.fromisoformat(data['fecha_fin'])

        db.session.add(new_plan)
        db.session.commit()
        
        return jsonify({
            "message": "Plan creado exitosamente", 
            "id": new_plan.id,
            "plan": { # Devolvemos el objeto creado para actualizar el estado local sin recargar
                "id": new_plan.id,
                "destino_id": new_plan.destination_id,
                "tour": new_plan.tour_name,
                "estado": new_plan.status
            }
        }), 201
    except Exception as e:
        print(f"Error creando plan: {e}")
        return jsonify({"error": "No se pudo guardar el plan"}), 500

@planes_bp.route('/api/planes/<plan_id>', methods=['PUT'])
@token_required
def update_plan(current_user, plan_id):
    """
    Actualiza un plan existente (confirmar fechas, pagar, cancelar).
    Web/App: PUT /api/planes/<id>
    """
    try:
        # Verificar que el plan pertenezca al usuario
        plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first()
        
        if not plan:
            return jsonify({"error": "Plan no encontrado o acceso denegado"}), 404
            
        data = request.get_json()
        
        # Actualizar solo los campos que vienen en la petición
        if 'estado' in data:
            plan.status = data['estado']
        
        if 'fecha_inicio' in data and data['fecha_inicio']:
            # Cortar la fecha 'YYYY-MM-DD' si viene así, o parsear ISO completo
            fecha_str = data['fecha_inicio'].split('T')[0] 
            plan.start_date = datetime.strptime(fecha_str, "%Y-%m-%d")
            
        if 'fecha_fin' in data and data['fecha_fin']:
            fecha_str = data['fecha_fin'].split('T')[0]
            plan.end_date = datetime.strptime(fecha_str, "%Y-%m-%d")
            
        if 'resena_completada' in data:
            plan.review_completed = data['resena_completada']
            
        db.session.commit()
        return jsonify({"message": "Plan actualizado correctamente"}), 200
        
    except Exception as e:
        print(f"Error actualizando plan: {e}")
        return jsonify({"error": str(e)}), 500

@planes_bp.route('/api/planes/<plan_id>', methods=['DELETE'])
@token_required
def delete_plan(current_user, plan_id):
    """
    Elimina un plan.
    Web/App: DELETE /api/planes/<id>
    """
    try:
        plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first()
        
        if not plan:
            return jsonify({"error": "Plan no encontrado"}), 404
            
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"message": "Plan eliminado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# RUTAS PARA RESEÑAS
# ---------------------------------------------------------

@planes_bp.route('/api/reviews', methods=['POST'])
@token_required
def create_review(current_user):
    """
    Guarda una reseña.
    Web/App: POST /api/reviews
    """
    try:
        data = request.get_json()
        
        # Validar datos mínimos
        if not data.get('comentario') or not data.get('estrellas'):
            return jsonify({"error": "Faltan datos de la reseña"}), 400

        new_review = Review(
            user_id=current_user.id,
            plan_id=data.get('plan_id'),
            destination_id=data.get('destino_id'),
            rating=data.get('estrellas'),
            comment=data.get('comentario')
        )
        
        # Opcional: Marcar el plan como reseñado si se envía el plan_id
        if data.get('plan_id'):
            plan = Plan.query.filter_by(id=data.get('plan_id'), user_id=current_user.id).first()
            if plan:
                plan.review_completed = True
        
        db.session.add(new_review)
        db.session.commit()
        
        return jsonify({"message": "Reseña guardada exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
