// Header functionality
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    let isAnimating = false;
    
    // Toggle mobile menu with animation handling
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            if (isAnimating) return;
            isAnimating = true;
            
            hamburger.classList.toggle('active');
            navLinks.style.display = 'flex';
            
            // Trigger reflow for animation
            navLinks.offsetHeight;
            
            navLinks.classList.toggle('active');
            
            // Reset animation lock after transition
            setTimeout(() => {
                isAnimating = false;
                if (!navLinks.classList.contains('active')) {
                    navLinks.style.display = '';
                }
            }, 300);
        });
    }

    // Improved dropdown handling
    const dropdowns = document.querySelectorAll('.dropdown, .user-menu');
    
    dropdowns.forEach(dropdown => {
        const button = dropdown.querySelector('button');
        const content = dropdown.querySelector('.dropdown-content, .user-dropdown');
        let timeout;

        // Handle mouse interactions
        dropdown.addEventListener('mouseenter', () => {
            clearTimeout(timeout);
            dropdowns.forEach(d => {
                if (d !== dropdown) {
                    const c = d.querySelector('.dropdown-content, .user-dropdown');
                    if (c) {
                        c.style.display = 'none';
                        c.style.opacity = '0';
                        c.style.transform = 'translateY(10px)';
                    }
                }
            });
            
            if (content) {
                content.style.display = 'block';
                // Trigger reflow
                content.offsetHeight;
                content.style.opacity = '1';
                content.style.transform = 'translateY(0)';
            }
        });

        dropdown.addEventListener('mouseleave', () => {
            timeout = setTimeout(() => {
                if (content) {
                    content.style.opacity = '0';
                    content.style.transform = 'translateY(10px)';
                    setTimeout(() => {
                        content.style.display = 'none';
                    }, 300);
                }
            }, 100);
        });

        // Handle click for mobile
        if (button) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (window.innerWidth <= 768) {
                    const isVisible = content.style.display === 'block';
                    
                    // Close all other dropdowns
                    dropdowns.forEach(d => {
                        if (d !== dropdown) {
                            const c = d.querySelector('.dropdown-content, .user-dropdown');
                            if (c) {
                                c.style.display = 'none';
                                c.style.opacity = '0';
                                c.style.transform = 'translateY(10px)';
                            }
                        }
                    });
                    
                    if (!isVisible) {
                        content.style.display = 'block';
                        content.offsetHeight; // Trigger reflow
                        content.style.opacity = '1';
                        content.style.transform = 'translateY(0)';
                    } else {
                        content.style.opacity = '0';
                        content.style.transform = 'translateY(10px)';
                        setTimeout(() => {
                            content.style.display = 'none';
                        }, 300);
                    }
                }
            });
        }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', (event) => {
        if (window.innerWidth <= 768) {
            const isDropdownClick = event.target.closest('.dropdown, .user-menu');
            if (!isDropdownClick) {
                dropdowns.forEach(dropdown => {
                    const content = dropdown.querySelector('.dropdown-content, .user-dropdown');
                    if (content) {
                        content.style.opacity = '0';
                        content.style.transform = 'translateY(10px)';
                        setTimeout(() => {
                            content.style.display = 'none';
                        }, 300);
                    }
                });
            }
        }
    });

    // Close menu when clicking on a link (mobile)
    const navLinksAll = document.querySelectorAll('.nav-links a');
    navLinksAll.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                navLinks.classList.remove('active');
                hamburger.classList.remove('active');
                
                // Close any open dropdowns
                dropdowns.forEach(dropdown => {
                    const content = dropdown.querySelector('.dropdown-content, .user-dropdown');
                    if (content) {
                        content.style.opacity = '0';
                        content.style.transform = 'translateY(10px)';
                        setTimeout(() => {
                            content.style.display = 'none';
                        }, 300);
                    }
                });
            }
        });
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth > 768) {
                navLinks.style.display = '';
                navLinks.classList.remove('active');
                hamburger.classList.remove('active');
                
                dropdowns.forEach(dropdown => {
                    const content = dropdown.querySelector('.dropdown-content, .user-dropdown');
                    if (content) {
                        content.style.display = '';
                        content.style.opacity = '';
                        content.style.transform = '';
                    }
                });
            }
        }, 250);
    });
});
