FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# En produccion NO usar --reload. Antes de arrancar, correr:
#   alembic upgrade head
#
# --no-access-log (C3): Uvicorn registra por defecto la IP de cada
# peticion en su log de acceso. Eso viola la restriccion de privacidad
# del brief: ningun dato que permita identificar a una victima puede
# quedar almacenado, ni siquiera en logs de servidor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
