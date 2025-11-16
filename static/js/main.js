// MODE TOGGLE
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

// DROP ZONE LOGIC
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

