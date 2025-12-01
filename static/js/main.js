const body = document.getElementById("app-body");
const toggle = document.getElementById("mode-toggle-checkbox");
const modeKey = "pdfFinderMode";

// --- THEME TOGGLE ---
// FIX 1: Wrap toggle logic in an existence check to prevent script errors on pages without the toggle
if (toggle) {
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
}

let currentFavorites = new Set(); // Keep this first declaration

// --- KEY MANAGER FUNCTION ---
function updateUserKey() {
    const input = document.getElementById('user-key-input');
    const newKey = input.value;

    fetch('/api/set-key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key: newKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // Reload the page to fetch the new favorites list for this key
            window.location.reload(); 
        }
    })
    .catch(error => console.error('Error setting key:', error));
}

// --- DROP ZONE & PREVIEW LOGIC ---
function displayImagePreview(file) {
    const preview = document.getElementById("preview");
    if (!preview) return;
    
    const reader = new FileReader();
    reader.onload = () => {
        preview.src = reader.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
}

function initializeDropZoneListeners() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("image-input");

    if (!dropZone || !fileInput) return;

    // Click to upload
    dropZone.onclick = () => fileInput.click();

    // Drag and Drop Handlers
    dropZone.addEventListener("dragover", function handleDragOver(e) {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", function handleDragLeave() {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", function handleDrop(e) {
        e.preventDefault();
        dropZone.classList.remove("dragover");

        const file = e.dataTransfer.files[0];
        if (!file) return;

        fileInput.files = e.dataTransfer.files;
        displayImagePreview(file);
    });

    // File Input Change Handler
    fileInput.addEventListener("change", function handleFileInputChange(e) {
        const file = e.target.files[0];
        if (!file) return;
        displayImagePreview(file);
    });
}

// --- FAVORITES LOGIC ---


// In main.js
function addFavorite(pdfUrl, buttonElement) {
    console.log(`Attempting to add favorite: ${pdfUrl}`); // Console check 1
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
    .then(response => {
        // Console check 2: Log the HTTP Status Code (e.g., 200, 400, 500)
        console.log('API Response Status for Add Favorite:', response.status); 
        if (!response.ok) {
            // Server returned an error status (4xx or 5xx)
            console.error('Server returned an error status:', response); 
            return response.json().catch(() => ({ error: 'Non-JSON error response from server.' }));
        }
        return response.json();
    })
    .then(data => {
        // Console check 3: Log the data payload from the server
        console.log('Server Data Payload:', data); 
        
        if (data.status === 'ok') {
            console.log('SUCCESS: Favorite added successfully.');
            // ... (rest of the success logic)
            currentFavorites.add(pdfUrl);
            
            buttonElement.innerHTML = '❤️';
            buttonElement.classList.add('favorited');
            buttonElement.title = 'Click to unfavorite';
            buttonElement.setAttribute('onclick', `removeFavorite('${pdfUrl}', this)`);
            
            addFavoriteToList(pdfUrl, new Date());
        } else {
            // Server returned {"status": "error", "error": "..."}
            console.error('Favorite failed. Server returned error details:', data.error);
        }
    })
    .catch(error => {
        // Console check 4: Network failure or JSON parse error
        console.error('Network or Parse Error during Add Favorite:', error);
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
            noFavoritesMessage.className = 'no-favorites-message';
            noFavoritesMessage.textContent = 'No favorites yet for this list. Click the "Favorite" button next to PDF links to save them here.';
            favoritesSection.appendChild(noFavoritesMessage);
            favoritesList.remove();
        }
    }
}

function addFavoriteToList(pdfUrl, timestamp) {
    const favoritesSection = document.querySelector('.favorites-section');
    if (!favoritesSection) return;

    let actualFavoritesList = favoritesSection.querySelector('.favorites-list');
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
    const dateObject = (typeof timestamp === 'string' || typeof timestamp === 'number') ? new Date(timestamp) : timestamp;
    if (isNaN(dateObject.getTime())) return 'Recently';
    
    const now = new Date();
    const diffMs = now - dateObject;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    
    return dateObject.toLocaleDateString() + ' ' + dateObject.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
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

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', function() {
    initializeDropZoneListeners(); 
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
                const newFavoritesSection = doc.querySelector('.favorites-section');
                const newForm = doc.querySelector('form');
                
                const currentSearchResults = document.querySelector('.search-results');
                const currentFavoritesSection = document.querySelector('.favorites-section');
                const currentForm = document.querySelector('form');

                // 1. Update Search Results
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
                
                // 2. Update Favorites Section
                if (newFavoritesSection && currentFavoritesSection) {
                    currentFavoritesSection.innerHTML = newFavoritesSection.innerHTML;
                }
                
                // 3. Update Form Content
                if (newForm && currentForm) {
                    const newQuery = newForm.querySelector('input[name="query"]').value;
                    currentForm.querySelector('input[name="query"]').value = newQuery;
                    
                    const dropZoneDiv = currentForm.querySelector('.drop-zone').parentNode;
                    if (dropZoneDiv) {
                        const newDropZoneContent = newForm.innerHTML;
                        currentForm.innerHTML = newDropZoneContent;
                    }
                }
                
                // 4. Re-attach/Re-initialize listeners after DOM update
                setTimeout(() => {
                    initializeDropZoneListeners(); 
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