// Password strength indicator
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password');
    const strengthBar = document.querySelector('.strength-bar');
    const strengthText = document.querySelector('.strength-text');

    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = passwordInput.value;
            const strength = calculatePasswordStrength(password);
            updateStrengthIndicator(strength);
        });
    }

    function calculatePasswordStrength(password) {
        let strength = 0;
        
        // Length check
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        
        // Character type checks
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        
        return Math.min(strength, 4);
    }

    function updateStrengthIndicator(strength) {
        const colors = ['#ff4444', '#ffbb33', '#00C851', '#007E33'];
        const texts = ['Very Weak', 'Weak', 'Good', 'Strong'];
        
        strengthBar.style.width = `${(strength + 1) * 25}%`;
        strengthBar.style.backgroundColor = colors[strength];
        strengthText.textContent = texts[strength];
    }
});

// Form validation feedback
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('error');
                } else {
                    input.classList.remove('error');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});
