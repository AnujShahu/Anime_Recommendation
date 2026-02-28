document.addEventListener("DOMContentLoaded", function () {

    /* ================= GOOGLE REDIRECT ================= */
    function redirectToGoogle(title) {
        const query = encodeURIComponent(title + " anime");
        window.open(`https://www.google.com/search?q=${query}`, "_blank");
    }

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

    const themeToggle = document.getElementById("themeToggle");

    const loginModal = document.getElementById("loginModal");
    const registerModal = document.getElementById("registerModal");

    const userMenuBtn = document.getElementById("userMenuBtn");
    const userDropdown = document.getElementById("userDropdown");

    let animeTitles = [];
    let selectedGenres = [];
    let currentFocus = -1;
    let debounceTimer;
    let currentPage = 1;

    /* ================= THEME TOGGLE ================= */
    if (themeToggle) {

        if (localStorage.getItem("theme") === "light") {
            document.body.classList.add("light-mode");
            themeToggle.textContent = "☀ Light Mode";
        }

        themeToggle.addEventListener("click", function () {
            document.body.classList.toggle("light-mode");

            if (document.body.classList.contains("light-mode")) {
                localStorage.setItem("theme", "light");
                themeToggle.textContent = "☀ Light Mode";
            } else {
                localStorage.setItem("theme", "dark");
                themeToggle.textContent = "🌙 Dark Mode";
            }
        });
    }

    /* ================= TAB SWITCH ================= */
    if (searchTab && genreTab && searchSection && genreSection) {

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
    }

    /* ================= LOAD TITLES ================= */
    if (searchInput && suggestionsBox) {
        fetch("/get_anime_titles")
            .then(res => res.json())
            .then(data => animeTitles = data.titles || []);

        searchInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                showSuggestions(this.value.trim());
            }, 150);
        });
    }

    function showSuggestions(query) {
        if (!suggestionsBox) return;

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
            .slice(0, 8);

        ranked.forEach(item => {
            const div = document.createElement("div");
            div.classList.add("suggestion-item");
            div.innerHTML = highlightMatch(item.title, query);

            div.addEventListener("click", function () {
                searchInput.value = item.title;
                suggestionsBox.innerHTML = "";
                if (searchForm) searchForm.submit();
            });

            suggestionsBox.appendChild(div);
        });
    }

    function calculateScore(title, input) {
        if (title.startsWith(input)) return 100;
        if (title.includes(input)) return 60;

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

    /* ================= GENRE SYSTEM (SAFE) ================= */
    if (genreContainer && genreSearchBtn && genreResults) {

        fetch("/get_genres")
            .then(res => res.json())
            .then(genres => {
                genres.forEach(genre => {
                    const btn = document.createElement("button");
                    btn.classList.add("genre-btn");
                    btn.textContent = genre;

                    btn.addEventListener("click", function () {
                        btn.classList.toggle("selected");

                        if (selectedGenres.includes(genre)) {
                            selectedGenres = selectedGenres.filter(g => g !== genre);
                        } else {
                            selectedGenres.push(genre);
                        }
                    });

                    genreContainer.appendChild(btn);
                });
            });

        genreSearchBtn.addEventListener("click", function () {
            currentPage = 1;
            loadGenreResults();
        });
    }

    function loadGenreResults() {
        if (!genreResults) return;

        genreResults.innerHTML = `<div class="loader"></div>`;

        fetch("/search_by_genres", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                genres: selectedGenres,
                page: currentPage
            })
        })
        .then(res => res.json())
        .then(results => {

            if (currentPage === 1) genreResults.innerHTML = "";

            results.forEach(anime => {
                genreResults.innerHTML += `
                <div class="anime-card clickable-card"
                     data-title="${anime.title}">
                    <img src="${anime.image_url}" class="anime-img">
                    <h3>${anime.title}</h3>
                    <p>${anime.genres}</p>
                    <p>⭐ ${anime.score}</p>
                </div>`;
            });
        });
    }

    /* ================= CARD REDIRECT ================= */
    document.addEventListener("click", function (e) {
        const card = e.target.closest(".clickable-card");
        if (card && card.dataset.title) {
            redirectToGoogle(card.dataset.title);
        }
    });

    /* ================= MODALS ================= */
    function openModal(modal) {
        if (!modal) return;
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.add("hidden");
        document.body.style.overflow = "auto";
    }

    window.openLogin = () => openModal(loginModal);
    window.closeLogin = () => closeModal(loginModal);
    window.openRegister = () => openModal(registerModal);
    window.closeRegister = () => closeModal(registerModal);

    /* ================= USER DROPDOWN ================= */
    if (userMenuBtn && userDropdown) {

        userMenuBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle("hidden");
        });

        userDropdown.addEventListener("click", function (e) {
            e.stopPropagation();
        });

        document.addEventListener("click", function () {
            userDropdown.classList.add("hidden");
        });
    }

});