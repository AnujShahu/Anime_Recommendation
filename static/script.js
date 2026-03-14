document.addEventListener("DOMContentLoaded", function () {
    function redirectToGoogle(title) {
        const query = encodeURIComponent(title + " anime");
        window.open(`https://www.google.com/search?q=${query}`, "_blank");
    }

    function showFlashMessage(message) {
        let flashContainer = document.getElementById("flashContainer");

        if (!flashContainer) {
            flashContainer = document.createElement("div");
            flashContainer.id = "flashContainer";
            flashContainer.className = "flash-container";
            const container = document.querySelector(".container");
            if (container) container.prepend(flashContainer);
        }

        const msg = document.createElement("div");
        msg.className = "flash-message";
        msg.textContent = message;
        flashContainer.appendChild(msg);

        setTimeout(() => {
            msg.classList.add("fade-out");
            setTimeout(() => msg.remove(), 300);
        }, 2500);
    }

    function maybeShowEmptyState(sectionSelector, text) {
        const section = document.querySelector(sectionSelector);
        if (!section) return;

        const cards = section.querySelectorAll(".anime-card");
        const existingEmpty = section.querySelector(".empty-note");

        if (cards.length === 0 && !existingEmpty) {
            const p = document.createElement("p");
            p.className = "empty-note";
            p.textContent = text;
            section.appendChild(p);
        }
    }

    function activateCards(scope = document) {
        const cards = scope.querySelectorAll(".anime-card");
        cards.forEach((card, idx) => {
            card.style.setProperty("--stagger", `${Math.min(idx, 10) * 55}ms`);
        });

        if ("IntersectionObserver" in window) {
            if (!window.__animeCardObserver) {
                window.__animeCardObserver = new IntersectionObserver((entries) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add("in-view");
                            window.__animeCardObserver.unobserve(entry.target);
                        }
                    });
                }, { threshold: 0.12 });
            }
            cards.forEach((card) => window.__animeCardObserver.observe(card));
        } else {
            cards.forEach((card) => card.classList.add("in-view"));
        }
    }

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
    const forgotModal = document.getElementById("forgotModal");

    const userMenuBtn = document.getElementById("userMenuBtn");
    const userDropdown = document.getElementById("userDropdown");

    const isAuthenticated = document.body.dataset.auth === "1";

    let animeTitles = [];
    let selectedGenres = [];
    let currentFocus = -1;
    let debounceTimer;
    let currentPage = 1;

    if (themeToggle) {
        if (localStorage.getItem("theme") === "light") {
            document.body.classList.add("light-mode");
            themeToggle.textContent = "Light Mode";
        }

        themeToggle.addEventListener("click", function () {
            document.body.classList.toggle("light-mode");

            if (document.body.classList.contains("light-mode")) {
                localStorage.setItem("theme", "light");
                themeToggle.textContent = "Light Mode";
            } else {
                localStorage.setItem("theme", "dark");
                themeToggle.textContent = "Dark Mode";
            }
        });
    }

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

    if (searchInput && suggestionsBox) {
        fetch("/get_anime_titles")
            .then((res) => res.json())
            .then((data) => {
                animeTitles = data.titles || [];
            })
            .catch(() => {
                animeTitles = [];
            });

        searchInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                showSuggestions(this.value.trim());
            }, 150);
        });

        searchInput.addEventListener("keydown", function (e) {
            const items = suggestionsBox.getElementsByClassName("suggestion-item");
            if (!items.length) return;

            if (e.key === "ArrowDown") {
                e.preventDefault();
                currentFocus++;
                addActive(items);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                currentFocus--;
                addActive(items);
            } else if (e.key === "Enter") {
                if (currentFocus > -1 && items[currentFocus]) {
                    e.preventDefault();
                    items[currentFocus].click();
                }
            } else if (e.key === "PageDown") {
                e.preventDefault();
                suggestionsBox.scrollTop += suggestionsBox.clientHeight;
            } else if (e.key === "PageUp") {
                e.preventDefault();
                suggestionsBox.scrollTop -= suggestionsBox.clientHeight;
            } else if (e.key === "Escape") {
                suggestionsBox.innerHTML = "";
                currentFocus = -1;
            }
        });
    }

    function showSuggestions(query) {
        if (!suggestionsBox) return;

        suggestionsBox.innerHTML = "";
        currentFocus = -1;
        if (!query) return;

        const input = query.toLowerCase();
        const ranked = animeTitles
            .map((title) => ({
                title: title,
                score: calculateScore(title.toLowerCase(), input),
            }))
            .filter((item) => item.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 8);

        ranked.forEach((item) => {
            const div = document.createElement("div");
            div.classList.add("suggestion-item");
            div.innerHTML = highlightMatch(item.title, query);

            div.addEventListener("click", function () {
                if (searchInput) searchInput.value = item.title;
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
        for (const char of input) {
            if (title.includes(char)) matches++;
        }
        return matches;
    }

    function highlightMatch(title, query) {
        const regex = new RegExp(`(${query})`, "gi");
        return title.replace(regex, "<strong>$1</strong>");
    }

    if (genreContainer && genreSearchBtn && genreResults) {
        fetch("/get_genres")
            .then((res) => res.json())
            .then((genres) => {
                genres.forEach((genre) => {
                    const btn = document.createElement("button");
                    btn.classList.add("genre-btn");
                    btn.textContent = genre;

                    btn.addEventListener("click", function () {
                        btn.classList.toggle("selected");

                        if (selectedGenres.includes(genre)) {
                            selectedGenres = selectedGenres.filter((g) => g !== genre);
                        } else {
                            selectedGenres.push(genre);
                        }
                    });

                    genreContainer.appendChild(btn);
                });
            })
            .catch(() => {
                genreContainer.innerHTML = "<p>Could not load genres.</p>";
            });

        genreSearchBtn.addEventListener("click", function () {
            if (!selectedGenres.length) {
                genreResults.innerHTML = "<p>Please select at least one genre.</p>";
                return;
            }
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
                page: currentPage,
            }),
        })
            .then((res) => res.json())
            .then((results) => {
                genreResults.innerHTML = "";

                if (!results.length) {
                    genreResults.innerHTML = "<p>No anime found for selected genres.</p>";
                    return;
                }

                results.forEach((anime) => {
                    const actions = isAuthenticated
                        ? `<div class="card-actions">
                                <a href="/add_favorite/${anime.anime_id}" class="heart-btn action-link" data-action="favorite">Favorite</a>
                                <a href="/add_watchlist/${anime.anime_id}" class="watch-btn action-link" data-action="watchlist">Watchlist</a>
                           </div>`
                        : "";

                    genreResults.innerHTML += `
                    <div class="anime-card clickable-card genre-result-card" data-title="${anime.title}" data-anime-id="${anime.anime_id}">
                        <img src="${anime.image_url}" class="anime-img" alt="${anime.title}">
                        <h3>${anime.title}</h3>
                        <p>${anime.genres}</p>
                        <p>Score: ${anime.score ?? "N/A"}</p>
                        ${actions}
                    </div>`;
                });

                activateCards(genreResults);
            })
            .catch(() => {
                genreResults.innerHTML = "<p>Something went wrong. Please try again.</p>";
            });
    }

    function addActive(items) {
        removeActive(items);

        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;

        items[currentFocus].classList.add("active-suggestion");
        items[currentFocus].scrollIntoView({ block: "nearest", behavior: "smooth" });
    }

    function removeActive(items) {
        for (const item of items) {
            item.classList.remove("active-suggestion");
        }
    }

    document.addEventListener("click", function (e) {
        const actionLink = e.target.closest(".action-link");
        if (actionLink) {
            e.preventDefault();
            fetch(actionLink.href, {
                method: "GET",
                headers: { "X-Requested-With": "XMLHttpRequest" },
            })
                .then((res) => res.json())
                .then((data) => {
                    showFlashMessage(data.message || "Updated");

                    if ((actionLink.dataset.action === "remove-favorite" || actionLink.dataset.action === "remove-watchlist") && data.ok) {
                        const card = actionLink.closest(".anime-card");
                        if (card) card.remove();

                        maybeShowEmptyState("#favoritesSection", "No favorites yet. Add anime from search or rankings.");
                        maybeShowEmptyState("#watchlistSection", "No watchlist items yet. Add anime from search or rankings.");
                    }
                })
                .catch(() => showFlashMessage("Something went wrong. Try again."));
            return;
        }

        const interactive = e.target.closest("a, button, input, textarea, form");
        if (interactive) return;

        const card = e.target.closest(".clickable-card");
        if (card && card.dataset.title) {
            redirectToGoogle(card.dataset.title);
        }
    });

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
    window.openForgot = () => openModal(forgotModal);
    window.closeForgot = () => closeModal(forgotModal);

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

    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
        backBtn.addEventListener("click", function () {
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = "/";
            }
        });
    }

    const heroShell = document.querySelector(".hero-shell");
    if (heroShell && window.matchMedia("(pointer: fine)").matches) {
        heroShell.classList.add("tilt");
        heroShell.addEventListener("mousemove", (e) => {
            const rect = heroShell.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            heroShell.style.transform = `perspective(900px) rotateX(${(-y * 3).toFixed(2)}deg) rotateY(${(x * 4).toFixed(2)}deg)`;
        });
        heroShell.addEventListener("mouseleave", () => {
            heroShell.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)";
        });
    }

    activateCards(document);

    document.querySelectorAll(".flash-message").forEach((message) => {
        setTimeout(() => {
            message.classList.add("fade-out");
            setTimeout(() => message.remove(), 300);
        }, 2500);
    });
});
