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
    allow_origins=["*"],      
    allow_credentials=True,
    allow_methods=["*"],      
    allow_headers=["*"],      
)

# ----------------------------------------------------
# 🔥 Inicializar Firebase (Railway usa variable de entorno)
# ----------------------------------------------------

firebase_json = os.getenv("FIREBASE_CREDENTIALS")

if firebase_json:
    print("🔑 Cargando credenciales desde variable de entorno FIREBASE_CREDENTIALS...")  # añadido para debug
    try:
        firebase_dict = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_dict)
    except json.JSONDecodeError as e:
        raise Exception(f"❌ Error al decodificar JSON de FIREBASE_CREDENTIALS: {e}")
else:
    if os.path.exists("serviceAccountKey.json"):
        print("📂 Cargando credenciales desde archivo local serviceAccountKey.json...")  # añadido para debug
        cred = credentials.Certificate("serviceAccountKey.json")
    else:
        raise Exception("❌ No se encontró FIREBASE_CREDENTIALS ni serviceAccountKey.json")

if not firebase_admin._apps:
    initialize_app(cred)
    print("✅ Firebase inicializado correctamente")  # añadido para debug

db = firestore.client()

# ----------------------------------------------------
# 📌 Modelo del request
# ----------------------------------------------------
class RatingPayload(BaseModel):
    uid: str
    ratings: dict


# ----------------------------------------------------
# 📌 Endpoint para enviar calificaciones
# ----------------------------------------------------
@app.post("/ratings/submit")
async def submit_ratings(data: RatingPayload):

    uid = data.uid
    ratings = data.ratings

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return {"error": "User not found"}

    rated_movies = list(map(int, ratings.keys()))

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
