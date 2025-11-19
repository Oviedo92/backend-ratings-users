from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from firebase_admin import firestore, credentials, initialize_app
import firebase_admin
import os
import json

app = FastAPI()

# ----------------------------------------------------
# 🔥 CORS — Permitir peticiones desde cualquier cliente
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Permite todos los dominios (Android, iOS, Web, etc.)
    allow_credentials=True,
    allow_methods=["*"],      # Permite todos los métodos HTTP
    allow_headers=["*"],      # Permite cualquier header
)

# ----------------------------------------------------
# 🔥 Inicializar Firebase (Railway usa variable de entorno)
# ----------------------------------------------------
firebase_json = os.getenv("FIREBASE_CREDENTIALS")

if firebase_json:
    firebase_dict = json.loads(firebase_json)
    cred = credentials.Certificate(firebase_dict)
else:
    # Si estás en local y sí tienes el archivo JSON
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    initialize_app(cred)

db = firestore.client()

# ----------------------------------------------------
# 📌 Modelo del request
# ----------------------------------------------------
class RatingPayload(BaseModel):
    uid: str
    ratings: dict  # Ejemplo {"1": 4, "2": 5}


# ----------------------------------------------------
# 📌 Endpoint para enviar calificaciones
# ----------------------------------------------------
@app.post("/ratings/submit")
async def submit_ratings(data: RatingPayload):

    uid = data.uid
    ratings = data.ratings  # ejemplo {"1": 5, "2": 3}

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return {"error": "User not found"}

    # IDs de las películas calificadas
    rated_movies = list(map(int, ratings.keys()))

    # Catálogo ejemplo
    MOVIES = {
        1: {"title": "Avengers: Endgame", "genre": "Acción"},
        2: {"title": "Scary Movie", "genre": "Comedia"},
        3: {"title": "Inception", "genre": "Ciencia Ficción"},
        4: {"title": "The Dark Knight", "genre": "Acción"},
        5: {"title": "Forrest Gump", "genre": "Drama"},
        6: {"title": "The Matrix", "genre": "Ciencia Ficción"},
        7: {"title": "Titanic", "genre": "Romance"},
    }

    rated_details = []

    for movie_id, rating_value in ratings.items():
        movie_id_int = int(movie_id)
        if movie_id_int in MOVIES:
            movie_info = MOVIES[movie_id_int]
            rated_details.append({
                "movieId": movie_id_int,
                "title": movie_info["title"],
                "genre": movie_info["genre"],
                "rating": rating_value
            })

    # Guardar en Firestore
    user_ref.update({
        "hasRated": True,
        "ratedMovies": rated_movies,
        "ratings": ratings,
        "ratedMoviesDetails": rated_details
    })

    return {
        "message": "Ratings saved successfully",
        "details": rated_details
    }
