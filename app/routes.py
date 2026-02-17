from flask import Blueprint, render_template, request, jsonify
from .recommender import get_recommendations
import sqlite3
import pandas as pd
import os

main = Blueprint("main", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "anime.db")


@main.route("/", methods=["GET", "POST"])
def home():
    anime = None
    recommendations = None
    error = None

    if request.method == "POST":
        anime_name = request.form.get("anime_name")
        anime_data, recs = get_recommendations(anime_name)

        if anime_data is None:
            error = "Anime not found!"
        else:
            anime = anime_data.to_dict()
            recommendations = recs.to_dict(orient="records")

    return render_template(
        "index.html",
        anime=anime,
        recommendations=recommendations,
        error=error
    )
