from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, field_validator


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


app = FastAPI(title="API de la biblioteca")
