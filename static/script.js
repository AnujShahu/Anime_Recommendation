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

    let animeTitles = [];
    let selectedGenres = [];
    let currentFocus = -1;
    let debounceTimer;
    let currentPage = 1;

    /* ================= THEME TOGGLE ================= */
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
        .then(data => animeTitles = data.titles || []);

    /* ================= AUTOCOMPLETE ================= */
    searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            showSuggestions(this.value.trim());
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
            .slice(0, 8);

        ranked.forEach(item => {
            const div = document.createElement("div");
            div.classList.add("suggestion-item");
            div.innerHTML = highlightMatch(item.title, query);

            div.addEventListener("click", function () {
                searchInput.value = item.title;
                suggestionsBox.innerHTML = "";
                searchForm.submit();
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

    /* ================= KEYBOARD NAVIGATION ================= */
    searchInput.addEventListener("keydown", function (e) {

        const items = suggestionsBox.getElementsByClassName("suggestion-item");
        if (!items.length) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            currentFocus++;
            addActive(items);
        }

        else if (e.key === "ArrowUp") {
            e.preventDefault();
            currentFocus--;
            addActive(items);
        }

        else if (e.key === "Enter") {
            if (currentFocus > -1 && items[currentFocus]) {
                e.preventDefault();
                items[currentFocus].click();
            }
        }

        else if (e.key === "PageDown") {
            e.preventDefault();
            suggestionsBox.scrollTop += suggestionsBox.clientHeight;
        }

        else if (e.key === "PageUp") {
            e.preventDefault();
            suggestionsBox.scrollTop -= suggestionsBox.clientHeight;
        }

        else if (e.key === "Escape") {
            suggestionsBox.innerHTML = "";
            currentFocus = -1;
        }
    });

    function addActive(items) {
        removeActive(items);

        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;

        items[currentFocus].classList.add("active-suggestion");
        items[currentFocus].scrollIntoView({ block: "nearest", behavior: "smooth" });
    }

    function removeActive(items) {
        for (let item of items) {
            item.classList.remove("active-suggestion");
        }
    }

    /* ================= LOAD GENRES ================= */
fetch("/get_genres")

    /* ================= SEARCH BY GENRE ================= */
   if (genreSearchBtn) {
    genreSearchBtn.addEventListener("click", function () {
        currentPage = 1;
        loadGenreResults();
    });
}

    function loadGenreResults() {

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

            if (!results.length && currentPage === 1) {
                genreResults.innerHTML = "<p>No anime found.</p>";
                return;
            }

            results.forEach(anime => {
                genreResults.innerHTML += `
                <div class="anime-card clickable-card fade-in"
                     data-title="${anime.title}">
                    <img src="${anime.image_url}"
                         class="anime-img"
                         onerror="this.src='/static/placeholder.jpg'">
                    <h3>${anime.title}</h3>
                    <p>${anime.genres}</p>
                    <p>⭐ ${anime.score}</p>
                </div>`;
            });

            if (results.length === 20) {

                const existingBtn = document.getElementById("loadMoreBtn");
                if (existingBtn) existingBtn.remove();

                genreResults.innerHTML += `
                    <button id="loadMoreBtn" class="search-btn">
                        Load More
                    </button>`;

                document.getElementById("loadMoreBtn")
                    .addEventListener("click", function () {
                        currentPage++;
                        loadGenreResults();
                    });
            }
        });
    }

    /* ================= CARD CLICK HANDLER ================= */
    document.addEventListener("click", function (e) {
        const card = e.target.closest(".clickable-card");
        if (card && card.dataset.title) {
            redirectToGoogle(card.dataset.title);
        }
    });

    /* ================= MODAL CONTROLS ================= */

    function openModal(modal) {
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }

    function closeModal(modal) {
        modal.classList.add("hidden");
        document.body.style.overflow = "auto";
    }

    window.openLogin = () => openModal(loginModal);
    window.closeLogin = () => closeModal(loginModal);
    window.openRegister = () => openModal(registerModal);
    window.closeRegister = () => closeModal(registerModal);

    window.addEventListener("click", function(e) {
        if (e.target === loginModal) closeModal(loginModal);
        if (e.target === registerModal) closeModal(registerModal);
    });

    document.addEventListener("keydown", function(e) {
        if (e.key === "Escape") {
            closeModal(loginModal);
            closeModal(registerModal);
        }
    });
/* ================= USER DROPDOWN ================= */

const userMenuBtn = document.getElementById("userMenuBtn");
const userDropdown = document.getElementById("userDropdown");

if (userMenuBtn && userDropdown) {

    userMenuBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        userDropdown.classList.toggle("hidden");
    });

    userDropdown.addEventListener("click", function (e) {
        e.stopPropagation();
    });

    document.addEventListener("click", function (e) {
        if (!userMenuBtn.contains(e.target) &&
            !userDropdown.contains(e.target)) {
            userDropdown.classList.add("hidden");
        }
    });

}
}
});