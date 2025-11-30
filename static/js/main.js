const body = document.getElementById("app-body");
const toggle = document.getElementById("mode-toggle-checkbox");
const modeKey = "pdfFinderMode";

if (localStorage.getItem(modeKey) === "dark") {
    body.classList.add("dark-mode");
    toggle.checked = true;
}
toggle.addEventListener("change", () => {
    if (toggle.checked) {
        body.classList.add("dark-mode");
        localStorage.setItem(modeKey, "dark");
    } else {
        body.classList.remove("dark-mode");
        localStorage.setItem(modeKey, "light");
    }
});

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("image-input");
const preview = document.getElementById("preview");

dropZone.onclick = () => fileInput.click();

dropZone.addEventListener("dragover", e => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", e => {
    e.preventDefault();
    dropZone.classList.remove("dragover");

    const file = e.dataTransfer.files[0];
    if (!file) return;

    fileInput.files = e.dataTransfer.files;

    const reader = new FileReader();
    reader.onload = () => {
        preview.src = reader.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
});

fileInput.addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        preview.src = reader.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
});

let currentFavorites = new Set();

function addFavorite(pdfUrl, buttonElement) {
    fetch('/api/favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            link_url: pdfUrl,
            action: 'add'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            currentFavorites.add(pdfUrl);
            
            buttonElement.innerHTML = '❤️';
            buttonElement.classList.add('favorited');
            buttonElement.title = 'Click to unfavorite';
            buttonElement.setAttribute('onclick', `removeFavorite('${pdfUrl}', this)`);
            
            addFavoriteToList(pdfUrl, new Date());
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function removeFavorite(pdfUrl, buttonElement) {
    fetch('/api/favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            link_url: pdfUrl,
            action: 'remove'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            currentFavorites.delete(pdfUrl);
            updateAllHeartButtons(pdfUrl, false);
            removeFavoriteFromList(pdfUrl);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateAllHeartButtons(pdfUrl, isFavorited) {
    const allFavoriteButtons = document.querySelectorAll('.favorite-btn');
    allFavoriteButtons.forEach(button => {
        const pdfLink = button.closest('.pdf-link');
        if (pdfLink) {
            const linkElement = pdfLink.querySelector('a');
            if (linkElement && linkElement.href === pdfUrl) {
                if (isFavorited) {
                    button.innerHTML = '❤️';
                    button.classList.add('favorited');
                    button.title = 'Click to unfavorite';
                    button.setAttribute('onclick', `removeFavorite('${pdfUrl}', this)`);
                } else {
                    button.innerHTML = '♡';
                    button.classList.remove('favorited');
                    button.title = 'Click to favorite';
                    button.setAttribute('onclick', `addFavorite('${pdfUrl}', this)`);
                }
            }
        }
    });
}

function removeFavoriteFromList(pdfUrl) {
    const favoritesList = document.querySelector('.favorites-list');
    if (!favoritesList) return;
    
    const favoriteItems = favoritesList.querySelectorAll('.favorite-item');
    favoriteItems.forEach(item => {
        const link = item.querySelector('a');
        if (link && link.href === pdfUrl) {
            item.remove();
        }
    });
    
    if (favoritesList.children.length === 0) {
        const favoritesSection = document.querySelector('.favorites-section');
        if (favoritesSection) {
            const noFavoritesMessage = document.createElement('p');
            // Use the new class defined in styles.css
            noFavoritesMessage.className = 'no-favorites-message'; 
            noFavoritesMessage.textContent = 'No favorites yet. Click the "Favorite" button next to PDF links to save them here.';
            favoritesSection.appendChild(noFavoritesMessage);
            favoritesList.remove();
        }
    }
}

function addFavoriteToList(pdfUrl, timestamp) {
    const favoritesSection = document.querySelector('.favorites-section');
    if (!favoritesSection) return;

    let actualFavoritesList = favoritesSection.querySelector('.favorites-list');
    
    // Select using the new class name
    const noFavoritesMessage = favoritesSection.querySelector('.no-favorites-message');
    
    if (noFavoritesMessage) {
        noFavoritesMessage.remove();
    }
    
    if (!actualFavoritesList) {
        actualFavoritesList = document.createElement('div');
        actualFavoritesList.className = 'favorites-list';
        const h3 = favoritesSection.querySelector('h3');
        if (h3) {
            h3.insertAdjacentElement('afterend', actualFavoritesList);
        } else {
            favoritesSection.appendChild(actualFavoritesList);
        }
    }
    
    const existingItems = actualFavoritesList.querySelectorAll('.favorite-item');
    let existingItem = null;
    for (let item of existingItems) {
        const link = item.querySelector('a');
        if (link && link.href === pdfUrl) {
            existingItem = item;
            break;
        }
    }
    
    const timeText = formatTimestamp(timestamp);
    
    // Use the new CSS class 'remove-btn'
    const removeButtonHTML = `<button class="remove-btn" onclick="removeFavoriteFromFavoritesSection('${pdfUrl}')">Remove</button>`;

    if (existingItem) {
        const timeElement = existingItem.querySelector('small');
        if (timeElement) {
            timeElement.innerHTML = `Saved: ${timeText} ${removeButtonHTML}`;
        }
        actualFavoritesList.insertBefore(existingItem, actualFavoritesList.firstChild);
    } else {
        const favoriteItem = document.createElement('div');
        favoriteItem.className = 'favorite-item';
        favoriteItem.innerHTML = `
            <a href="${pdfUrl}" target="_blank">${pdfUrl}</a>
            <small>
                Saved: ${timeText}
                ${removeButtonHTML}
            </small>
        `;
        actualFavoritesList.insertBefore(favoriteItem, actualFavoritesList.firstChild);
    }
}

function formatTimestamp(timestamp) {
    const now = new Date();
    const diffMs = now - new Date(timestamp);
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    
    return timestamp.toLocaleDateString() + ' ' + timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function removeFavoriteFromFavoritesSection(pdfUrl) {
    fetch('/api/favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            link_url: pdfUrl,
            action: 'remove'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            currentFavorites.delete(pdfUrl);
            updateAllHeartButtons(pdfUrl, false);
            removeFavoriteFromList(pdfUrl);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function initializeFavorites() {
    fetch('/api/get-favorites')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok' && data.favorites) {
                currentFavorites.clear();
                data.favorites.forEach(fav => {
                    currentFavorites.add(fav.link_url);
                });
                updateHeartButtonsFromFavorites();
            }
        })
        .catch(error => {
            console.error('Error initializing favorites:', error);
        });
}

function updateHeartButtonsFromFavorites() {
    const allFavoriteButtons = document.querySelectorAll('.favorite-btn');
    allFavoriteButtons.forEach(button => {
        const pdfLink = button.closest('.pdf-link');
        if (pdfLink) {
            const linkElement = pdfLink.querySelector('a');
            if (linkElement) {
                const pdfUrl = linkElement.href;
                if (currentFavorites.has(pdfUrl)) {
                    button.innerHTML = '❤️';
                    button.classList.add('favorited');
                    button.title = 'Click to unfavorite';
                    button.setAttribute('onclick', `removeFavorite('${pdfUrl}', this)`);
                } else {
                    button.innerHTML = '♡';
                    button.classList.remove('favorited');
                    button.title = 'Click to favorite';
                    button.setAttribute('onclick', `addFavorite('${pdfUrl}', this)`);
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initializeFavorites();
    
    const form = document.getElementById('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newSearchResults = doc.querySelector('.search-results');
                const newForm = doc.querySelector('form');
                
                const currentSearchResults = document.querySelector('.search-results');
                const currentForm = document.querySelector('form');
                
                if (newSearchResults) {
                    if (currentSearchResults) {
                        currentSearchResults.innerHTML = newSearchResults.innerHTML;
                    } else {
                        currentForm.insertAdjacentElement('afterend', newSearchResults);
                    }
                } else {
                    if (currentSearchResults) {
                        currentSearchResults.remove();
                    }
                }
                
                if (newForm) {
                    currentForm.innerHTML = newForm.innerHTML;
                }
                
                setTimeout(() => {
                    updateHeartButtonsFromFavorites();
                    attachEventListeners();
                }, 100);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
    
    attachEventListeners();
});

function attachEventListeners() {
    document.querySelectorAll(".pdf-link a").forEach(link => {
        link.addEventListener("click", () => {
            fetch("/api/click", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ link_url: link.href })
            });
        });
    });
}