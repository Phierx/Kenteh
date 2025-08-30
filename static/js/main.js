document.addEventListener('DOMContentLoaded', function() {
    function showSection(id) {
        document.querySelectorAll('.section').forEach(el => el.style.display = 'none');
        const target = document.getElementById(id);
        if (target) {
            target.style.display = 'block';
        } else {
            console.warn("No section found with id:", id);
        }
    }

    // Expose the function to the global scope
    window.showSection = showSection;
});
