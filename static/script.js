function getRecommendations() {
    const anime = document.getElementById("animeInput").value;

    fetch("/recommend", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ anime: anime })
    })
    .then(response => response.json())
    .then(data => {
        let resultDiv = document.getElementById("results");
        resultDiv.innerHTML = "";

        if (data.length === 0) {
            resultDiv.innerHTML = "<p>No recommendations found.</p>";
            return;
        }

        data.forEach(anime => {
            resultDiv.innerHTML += `
                <div class="card">
                    <img src="${anime.image_url}" alt="${anime.title}">
                    <h3>${anime.title}</h3>
                    <p><strong>Type:</strong> ${anime.type}</p>
                    <p><strong>Episodes:</strong> ${anime.episodes}</p>
                    <p><strong>Genre:</strong> ${anime.genre}</p>
                    <p><strong>Score:</strong> ⭐ ${anime.score}</p>
                    <p><strong>Popularity Rank:</strong> ${anime.popularity}</p>
                </div>
            `;
        });
    });
}

