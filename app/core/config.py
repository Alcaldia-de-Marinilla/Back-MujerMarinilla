"""
Configuracion de la aplicacion.

Todo lo que puede cambiar entre entornos (dev/prod) vive aqui y se lee
de variables de entorno (o del archivo .env). Nunca se hardcodean
secretos en el codigo (RNF-02).
"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Texto de ejemplo que trae .env.example. Si alguien copia el archivo
# sin cambiar el valor, NO debe poder arrancar la aplicacion con eso
# (fue exactamente la falla C1 de la revision: con este valor conocido
# cualquiera puede firmar un JWT valido sin pasar por /auth/login).
_EXAMPLE_SECRET = "cambia-esto-por-una-clave-larga-y-aleatoria"
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos: SQLite en dev, PostgreSQL en prod. Mismo codigo, distinta URL.
    database_url: str = "sqlite:///./mujer_marinilla.db"

    # JWT: SIN valor por defecto a proposito (C1). Si falta en el entorno,
    # pydantic-settings falla al construir Settings() y la app no arranca.
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    # CORS: lista separada por comas en la variable de entorno
    cors_origins: str = "http://localhost:3000"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """
        C1 de la revision del 16 de sept: nunca debe ser posible arrancar
        con un secreto adivinable. Se valida longitud minima y que no sea
        el texto de ejemplo de .env.example.
        """
        if value == _EXAMPLE_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY sigue siendo el valor de ejemplo de .env.example. "
                "Genera uno real, por ejemplo con: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if len(value) < _MIN_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY debe tener al menos {_MIN_SECRET_LENGTH} caracteres "
                f"(tiene {len(value)}). Un secreto corto se puede adivinar por fuerza bruta."
            )
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # lru_cache evita releer el .env en cada request.
    # Si JWT_SECRET_KEY falta o es invalido, esto lanza pydantic.ValidationError
    # y el proceso de Uvicorn no llega a levantar el servidor (falla rapido,
    # con un mensaje claro, en vez de exponer una API insegura).
    return Settings()
