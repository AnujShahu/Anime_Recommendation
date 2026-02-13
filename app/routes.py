from flask import Blueprint, render_template, request, jsonify
from .recommender import get_recommendations

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/recommend", methods=["POST"])
def recommend():
    anime_title = request.json.get("anime")
    recommendations = get_recommendations(anime_title)
    return jsonify(recommendations)

