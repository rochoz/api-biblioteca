# API de la biblioteca

API REST de práctica para crear, consultar, buscar, actualizar, prestar y eliminar libros.
Está desarrollada con Python, FastAPI y Pydantic; Uvicorn ejecuta el servidor y la biblioteca estándar administra el archivo JSON.

## Preparación y ejecución

1. Crear un entorno virtual: `python -m venv .venv`.
2. Activarlo en Windows: `.venv\Scripts\Activate.ps1`.
3. Instalar las dependencias: `pip install -r requirements.txt`.
4. Ejecutar con `uvicorn main:app --reload`.

Los libros se guardan en `datos/libros.json`, una ruta calculada desde `main.py`.
Si el archivo no existe, está vacío o contiene JSON dañado, la API comienza con una lista vacía.

## Endpoints

- `GET /`: mensaje de la API.
- `GET /libros`: listado con filtros por autor y disponibilidad, y paginación.
- `GET /libros/buscar?texto=...`: búsqueda parcial por título o autor.
- `GET /libros/estadisticas`: total, disponibles y prestados.
- `POST /libros`: crea un libro; `GET /libros/{id}` lo consulta.
- `PUT /libros/{id}` reemplaza y `PATCH /libros/{id}` modifica campos enviados.
- `DELETE /libros/{id}` elimina un libro.
- `POST /libros/{id}/prestar` y `POST /libros/{id}/devolver` cambian su disponibilidad.
