import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, field_validator

RUTA_DATOS = Path(__file__).parent / "datos"
RUTA_LIBROS = RUTA_DATOS / "libros.json"


class Libro(BaseModel):
    """Representa un libro completo almacenado por la API."""

    id: int
    titulo: str = Field(min_length=3, max_length=100)
    autor: str = Field(min_length=3, max_length=60)
    anio: int = Field(ge=1000, le=2100)
    disponible: bool = True


class LibroEntrada(BaseModel):
    """Datos necesarios para crear o reemplazar un libro."""

    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(min_length=3, max_length=100)
    autor: str = Field(min_length=3, max_length=60)
    anio: int = Field(ge=1000, le=2100)
    disponible: bool = True


class LibroCambios(BaseModel):
    """Campos opcionales que se pueden modificar con PATCH."""

    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=3, max_length=100)
    autor: str | None = Field(default=None, min_length=3, max_length=60)
    anio: int | None = Field(default=None, ge=1000, le=2100)
    disponible: bool | None = None

    @field_validator("titulo", "autor", "anio", "disponible", mode="before")
    @classmethod
    def rechazar_nulos(cls, valor: object) -> object:
        """PATCH acepta campos omitidos, pero no valores null."""
        if valor is None:
            raise ValueError("El valor no puede ser null")
        return valor


def cargar_libros() -> list[Libro]:
    """Carga la lista guardada, o comienza vacía si falta o está dañada."""
    RUTA_DATOS.mkdir(parents=True, exist_ok=True)
    if not RUTA_LIBROS.exists():
        return []

    try:
        contenido = RUTA_LIBROS.read_text(encoding="utf-8")
        if not contenido.strip():
            return []
        datos = json.loads(contenido)
        if not isinstance(datos, list):
            raise TypeError("El archivo debe contener una lista")
        return [Libro.model_validate(elemento) for elemento in datos]
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return []


def guardar_libros() -> None:
    """Guarda los libros usando siempre la ubicación del proyecto."""
    RUTA_DATOS.mkdir(parents=True, exist_ok=True)
    contenido = [libro.model_dump() for libro in libros]
    RUTA_LIBROS.write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8"
    )


libros = cargar_libros()
siguiente_id = max((libro.id for libro in libros), default=0) + 1
app = FastAPI(title="API de la biblioteca")
