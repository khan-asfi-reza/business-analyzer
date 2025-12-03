// Main JavaScript file for Business Analyzer

// Toggle mobile menu
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    const menuIcon = document.getElementById('menuIcon');
    const closeIcon = document.getElementById('closeIcon');

    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }

    if (menuIcon && closeIcon) {
        menuIcon.classList.toggle('hidden');
        closeIcon.classList.toggle('hidden');
    }
}

// Handle search form submission
function handleSearch(event) {
    event.preventDefault();
    const searchInput = document.getElementById('searchInput');
    if (searchInput && searchInput.value.trim()) {
        window.location.href = `search.html?q=${encodeURIComponent(searchInput.value)}`;
    }
}

// Initialize icons when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});
