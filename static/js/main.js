// HR Portal JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeUserMenu();
    initializeMessages();
    initializeFormValidation();
    initializeAnimations();
});

// User Menu Functionality
function initializeUserMenu() {
    const userToggle = document.querySelector('.user-toggle');
    const userDropdown = document.querySelector('.user-dropdown');

    if (userToggle && userDropdown) {
        userToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleUserMenu();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (!userToggle.contains(event.target) && !userDropdown.contains(event.target)) {
                userDropdown.style.display = 'none';
            }
        });

        // Prevent dropdown from closing when clicking inside
        userDropdown.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }
}

function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

// Auto-hide Messages
function initializeMessages() {
    const messages = document.querySelectorAll('.alert');
    messages.forEach(function(message) {
        // Auto-hide success messages after 5 seconds
        if (message.classList.contains('alert-success')) {
            setTimeout(function() {
                fadeOut(message);
            }, 5000);
        }

        // Add close button to messages
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.className = 'close-btn';
        closeBtn.style.cssText = `
            float: right;
            background: none;
            border: none;
            font-size: 1.2rem;
            cursor: pointer;
            color: inherit;
            opacity: 0.7;
            margin-left: 10px;
        `;
        closeBtn.onclick = function() {
            fadeOut(message);
        };
        message.appendChild(closeBtn);
    });
}

function fadeOut(element) {
    element.style.transition = 'opacity 0.5s ease';
    element.style.opacity = '0';
    setTimeout(function() {
        element.remove();
    }, 500);
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });

        // Real-time validation for form fields
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(input);
            });

            input.addEventListener('input', function() {
                // Clear error state on input
                input.classList.remove('is-invalid');
                const errorMsg = input.parentNode.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.remove();
                }
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

    inputs.forEach(function(input) {
        if (!validateField(input)) {
            isValid = false;
        }
    });

    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';

    // Clear previous error state
    field.classList.remove('is-invalid');
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }

    // Required field validation
    if (field.hasAttribute('required') && !value) {
        errorMessage = 'This field is required.';
        isValid = false;
    }

    // Email validation
    if (field.type === 'email' && value && !isValidEmail(value)) {
        errorMessage = 'Please enter a valid email address.';
        isValid = false;
    }

    // Password matching validation
    if (field.name === 'password2') {
        const password1 = document.querySelector('input[name="password1"]');
        if (password1 && value !== password1.value) {
            errorMessage = 'Passwords do not match.';
            isValid = false;
        }
    }

    // Show error if validation failed
    if (!isValid) {
        field.classList.add('is-invalid');
        showFieldError(field, errorMessage);
    }

    return isValid;
}

function showFieldError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        color: #dc3545;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: block;
    `;
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Animations and UI Enhancements
function initializeAnimations() {
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading state to buttons on form submission
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        const form = button.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                button.innerHTML = 'Loading...';
                button.disabled = true;
            });
        }
    });

    // Animate cards on scroll
    observeElementsOnScroll();
}

function observeElementsOnScroll() {
    const cards = document.querySelectorAll('.card, .stat-card, .action-card');

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });

    cards.forEach(function(card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.className = 'close-btn';
    closeBtn.style.cssText = `
        float: right;
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        color: inherit;
        opacity: 0.7;
        margin-left: 10px;
    `;
    closeBtn.onclick = function() {
        fadeOut(notification);
    };
    notification.appendChild(closeBtn);

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(function() {
        fadeOut(notification);
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(300px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .is-invalid {
        border-color: #dc3545 !important;
        box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.25) !important;
    }

    .close-btn:hover {
        opacity: 1;
    }

    .btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);

// Export functions for global use
window.toggleUserMenu = toggleUserMenu;
window.showNotification = showNotification;
window.confirmAction = confirmAction;