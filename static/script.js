document.addEventListener("DOMContentLoaded", function () {

    /* ================= ELEMENTS ================= */
    const searchTab = document.getElementById("searchTab");
    const genreTab = document.getElementById("genreTab");
    const searchSection = document.getElementById("searchSection");
    const genreSection = document.getElementById("genreSection");

    const searchInput = document.getElementById("searchInput");
    const suggestionsBox = document.getElementById("suggestions");
    const searchForm = document.getElementById("searchForm");

    const genreContainer = document.getElementById("genreContainer");
    const genreResults = document.getElementById("genreResults");
    const genreSearchBtn = document.getElementById("genreSearchBtn");

    let animeTitles = [];
    let selectedGenres = [];
    let currentFocus = -1;
    let debounceTimer;

    /* ================= TAB SWITCH ================= */
    searchTab.addEventListener("click", function () {
        searchTab.classList.add("active");
        genreTab.classList.remove("active");
        searchSection.classList.remove("hidden");
        genreSection.classList.add("hidden");
    });

    genreTab.addEventListener("click", function () {
        genreTab.classList.add("active");
        searchTab.classList.remove("active");
        genreSection.classList.remove("hidden");
        searchSection.classList.add("hidden");
    });

    /* ================= LOAD TITLES ================= */
    fetch("/get_anime_titles")
        .then(res => res.json())
        .then(data => {
            animeTitles = data.titles || [];
        });

    /* ================= GOOGLE-LIKE AUTOCOMPLETE ================= */
    searchInput.addEventListener("input", function () {

        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(() => {
            showSuggestions(this.value);
        }, 150);
    });

    function showSuggestions(query) {

        suggestionsBox.innerHTML = "";
        currentFocus = -1;

        if (!query) return;

        const input = query.toLowerCase();

        const ranked = animeTitles
            .map(title => ({
                title: title,
                score: calculateScore(title.toLowerCase(), input)
            }))
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 7);

        ranked.forEach(item => {

            const div = document.createElement("div");
            div.classList.add("suggestion-item");
            div.innerHTML = highlightMatch(item.title, query);

            div.onclick = function () {
                searchInput.value = item.title;
                suggestionsBox.innerHTML = "";
                searchForm.submit();
            };

            suggestionsBox.appendChild(div);
        });
    }

    function calculateScore(title, input) {

        if (title.startsWith(input)) return 100;
        if (title.includes(input)) return 50;

        let matches = 0;
        for (let char of input) {
            if (title.includes(char)) matches++;
        }

        return matches;
    }

    function highlightMatch(title, query) {
        const regex = new RegExp(`(${query})`, "gi");
        return title.replace(regex, "<strong>$1</strong>");
    }

    /* ================= KEYBOARD CONTROL ================= */
    searchInput.addEventListener("keydown", function (e) {

        let items = suggestionsBox.getElementsByClassName("suggestion-item");

        if (e.key === "ArrowDown" && items.length > 0) {
            e.preventDefault();
            currentFocus++;
            addActive(items);
        }

        else if (e.key === "ArrowUp" && items.length > 0) {
            e.preventDefault();
            currentFocus--;
            addActive(items);
        }

        else if (e.key === "Enter") {
            if (currentFocus > -1 && items.length > 0) {
                e.preventDefault();
                items[currentFocus].click();
            }
        }

        else if (e.key === "Escape") {
            suggestionsBox.innerHTML = "";
        }
    });

    function addActive(items) {
        removeActive(items);

        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;

        items[currentFocus].classList.add("active-suggestion");
        items[currentFocus].scrollIntoView({ block: "nearest" });
    }

    function removeActive(items) {
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove("active-suggestion");
        }
    }

    document.addEventListener("click", function(e) {
        if (!e.target.closest(".search-wrapper")) {
            suggestionsBox.innerHTML = "";
        }
    });

    /* ================= LOAD GENRES ================= */
    fetch("/get_genres")
        .then(res => res.json())
        .then(genres => {

            genres.forEach(genre => {

                const div = document.createElement("div");
                div.classList.add("genre-item");
                div.textContent = genre;

                div.onclick = function () {
                    div.classList.toggle("selected");

                    if (selectedGenres.includes(genre)) {
                        selectedGenres =
                            selectedGenres.filter(g => g !== genre);
                    } else {
                        selectedGenres.push(genre);
                    }
                };

                genreContainer.appendChild(div);
            });
        });

    /* ================= SEARCH BY GENRE ================= */
    genreSearchBtn.addEventListener("click", function () {

        fetch("/search_by_genres", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ genres: selectedGenres })
        })
        .then(res => res.json())
        .then(results => {

            genreResults.innerHTML = "";

            if (results.length === 0) {
                genreResults.innerHTML = "<p>No anime found.</p>";
                return;
            }

            results.forEach(anime => {
                genreResults.innerHTML += `
                    <div class="anime-card">
                        <img src="${anime.image_url}" class="anime-img">
                        <h3>${anime.title}</h3>
                        <p>${anime.genres}</p>
                        <p>⭐ ${anime.score}</p>
                    </div>
                `;
            });
        });
    });

});
