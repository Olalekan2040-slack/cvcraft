// CVCraft — Global JS

// Re-initialize Lucide icons after HTMX swaps
document.addEventListener('htmx:afterSwap', () => {
    if (window.lucide) lucide.createIcons();
});

// Auto-dismiss flash messages after 5 seconds
setTimeout(() => {
    const flashBox = document.getElementById('flash-messages');
    if (flashBox) {
        flashBox.querySelectorAll('[x-data]').forEach(el => {
            if (window.Alpine) {
                // trigger hide via Alpine
            } else {
                el.style.opacity = '0';
                el.style.transition = 'opacity 0.3s';
                setTimeout(() => el.remove(), 300);
            }
        });
    }
}, 5000);
