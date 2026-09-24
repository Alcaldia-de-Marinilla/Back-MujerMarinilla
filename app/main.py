"""
Punto de entrada. Uvicorn importa la variable `app` de este módulo:

    uvicorn app.main:app --reload

FastAPI en sí NO es un servidor: es el framework que define las rutas,
valida datos (Pydantic) y genera la documentación OpenAPI. Uvicorn es
el servidor ASGI que realmente escucha en un puerto y ejecuta ese
código ante cada petición HTTP. Por eso siempre van juntos.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    health, auth, phones, violence_types, equipment_types, equipment_categories,
    referrals, holidays, equipments,
)

settings = get_settings()

app = FastAPI(
    title="Mujer Marinilla API",
    description="API del backend de la plataforma Mujer Marinilla (MVP).",
    version="0.1.0",
    # /docs (Swagger) y /redoc se generan solos a partir de las rutas y schemas (RF08)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # RNF-03: solo los orígenes del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(phones.router)
app.include_router(violence_types.router)
app.include_router(equipment_types.router)
app.include_router(equipment_categories.router)
app.include_router(referrals.router)
app.include_router(holidays.router)
app.include_router(equipments.router)
