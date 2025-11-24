from flask import Blueprint, request, jsonify
from groq import Groq

process_bp = Blueprint("process", __name__)

def call_groq_llm(user_text):
    """Procesa texto con Groq LLM"""
    try:
        client = Groq()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente turístico de PerúGo. "
                        "Responde siempre en español de forma breve, amable y natural."
                    )
                },
                {"role": "user", "content": user_text}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en Groq: {e}")
        return "Error procesando solicitud con Groq."

@process_bp.route("/process", methods=["POST"])
def process_text():
    """Endpoint para procesamiento de texto con LLM"""
    data = request.get_json() or {}
    user_text = data.get("text", "").strip()
    
    if not user_text:
        return jsonify({"error": "No se recibió texto"}), 400
    
    llm_text = call_groq_llm(user_text)
    
    return jsonify({
        "text_response": llm_text
    }), 200