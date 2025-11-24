FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

# Puerto
EXPOSE 8080

# Comando de inicio
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120