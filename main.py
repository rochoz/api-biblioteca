import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response, status
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


def buscar_libro(id_libro: int) -> Libro:
    """Obtiene un libro o genera el error HTTP 404."""
    for libro in libros:
        if libro.id == id_libro:
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")


def hay_duplicado(titulo: str, autor: str, id_ignorado: int | None = None) -> bool:
    """Comprueba si ya existe el mismo título y autor, ignorando mayúsculas."""
    return any(
        libro.id != id_ignorado
        and libro.titulo.lower() == titulo.lower()
        and libro.autor.lower() == autor.lower()
        for libro in libros
    )


@app.get("/libros", response_model=list[Libro], summary="Listar libros")
def listar_libros(
    autor: str | None = None,
    disponible: bool | None = None,
    desde: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=0),
) -> list[Libro]:
    """Lista libros con filtros opcionales y paginación."""
    resultado = sorted(libros, key=lambda libro: libro.id)
    if autor is not None:
        resultado = [
            libro for libro in resultado if libro.autor.lower() == autor.lower()
        ]
    if disponible is not None:
        resultado = [libro for libro in resultado if libro.disponible is disponible]
    return resultado[desde : desde + limite]


@app.get(
    "/libros/buscar", response_model=list[Libro], summary="Buscar libros por texto"
)
def buscar_libros(texto: str = Query(...)) -> list[Libro]:
    """Busca el texto en títulos y autores sin distinguir mayúsculas."""
    texto_normalizado = texto.lower()
    return [
        libro
        for libro in sorted(libros, key=lambda item: item.id)
        if texto_normalizado in libro.titulo.lower()
        or texto_normalizado in libro.autor.lower()
    ]


@app.post(
    "/libros",
    response_model=Libro,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un libro",
)
def crear_libro(entrada: LibroEntrada) -> Libro:
    """Crea un libro nuevo y asigna el siguiente ID disponible."""
    global siguiente_id
    if hay_duplicado(entrada.titulo, entrada.autor):
        raise HTTPException(
            status_code=409, detail="Ya existe un libro con el mismo título y autor"
        )
    libro = Libro(id=siguiente_id, **entrada.model_dump())
    siguiente_id += 1
    libros.append(libro)
    guardar_libros()
    return libro


@app.get("/libros/{id}", response_model=Libro, summary="Obtener un libro")
def obtener_libro(id: int) -> Libro:
    """Devuelve un libro identificado por su ID."""
    return buscar_libro(id)


@app.put("/libros/{id}", response_model=Libro, summary="Reemplazar un libro")
def reemplazar_libro(id: int, entrada: LibroEntrada) -> Libro:
    """Reemplaza los datos de un libro y conserva su ID."""
    anterior = buscar_libro(id)
    if hay_duplicado(entrada.titulo, entrada.autor, id_ignorado=id):
        raise HTTPException(
            status_code=409, detail="Ya existe un libro con el mismo título y autor"
        )
    actualizado = Libro(id=id, **entrada.model_dump())
    libros[libros.index(anterior)] = actualizado
    guardar_libros()
    return actualizado


@app.patch("/libros/{id}", response_model=Libro, summary="Modificar un libro")
def modificar_libro(id: int, cambios: LibroCambios) -> Libro:
    """Modifica solo los campos enviados y conserva el resto."""
    anterior = buscar_libro(id)
    datos = anterior.model_dump()
    datos.update(cambios.model_dump(exclude_unset=True))
    actualizado = Libro.model_validate(datos)
    if hay_duplicado(actualizado.titulo, actualizado.autor, id_ignorado=id):
        raise HTTPException(
            status_code=409, detail="Ya existe un libro con el mismo título y autor"
        )
    if cambios.model_fields_set:
        libros[libros.index(anterior)] = actualizado
        guardar_libros()
    return actualizado


@app.delete(
    "/libros/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un libro"
)
def eliminar_libro(id: int) -> Response:
    """Elimina un libro y responde sin contenido."""
    libro = buscar_libro(id)
    libros.remove(libro)
    guardar_libros()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
