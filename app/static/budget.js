document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const comparisonSection = document.getElementById('comparison-section');
    const interestBars = document.querySelectorAll('.bar-fill');

    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            // Hide generate button and show loading spinner
            generateBtn.classList.add('d-none');
            loadingSpinner.classList.remove('d-none');

            // After 1.5 seconds, show comparison section
            setTimeout(() => {
                loadingSpinner.classList.add('d-none');
                comparisonSection.classList.remove('d-none');
                
                // Animate interest bars
                interestBars.forEach(bar => {
                    const width = bar.getAttribute('data-width');
                    bar.style.width = width;
                });
            }, 1500);
        });
    }

    // Handle product actions
    document.querySelectorAll('.btn-like').forEach(btn => {
        btn.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });

    document.querySelectorAll('.btn-dislike').forEach(btn => {
        btn.addEventListener('click', function() {
            const productCard = this.closest('.product-card');
            productCard.style.opacity = '0.5';
            productCard.style.pointerEvents = 'none';
        });
    });

    // Handle clickable price difference
    document.querySelectorAll('.clickable-diff').forEach(diff => {
        diff.addEventListener('click', function() {
            alert(`Price difference: ${this.textContent}`);
        });
    });
});
