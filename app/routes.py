from flask import Blueprint, render_template, request
from .recommender import get_recommendations

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []

    if request.method == 'POST':
        genre = request.form.get('genre')
        recommendations = get_recommendations(genre)

    return render_template('index.html', recommendations=recommendations)
