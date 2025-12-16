// ========================================
// CVision Main JavaScript
// ========================================

// Auth Helper Functions
const Auth = {
    // Check if user is logged in
    isLoggedIn() {
        return localStorage.getItem('access_token') !== null;
    },
    
    // Get current user info
    getUser() {
        if (!this.isLoggedIn()) return null;
        
        return {
            id: localStorage.getItem('user_id'),
            email: localStorage.getItem('user_email'),
            role: localStorage.getItem('user_role'),
            fullName: localStorage.getItem('user_full_name')
        };
    },
    
    // Get auth token
    getToken() {
        return localStorage.getItem('access_token');
    },
    
    // Login user
    login(token, user) {
        localStorage.setItem('access_token', token);
        localStorage.setItem('user_id', user.id);
        localStorage.setItem('user_email', user.email);
        localStorage.setItem('user_role', user.role);
        if (user.full_name) {
            localStorage.setItem('user_full_name', user.full_name);
        }
    },
    
    // Logout user
    logout() {
        // Clear all CV drafts before clearing user data
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('cv_builder_draft_')) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));
        localStorage.removeItem('cv_builder_draft'); // Xóa dữ liệu cũ nếu có
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_email');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_full_name');
        window.location.href = '/login';
    },
    
    // Make authenticated API request
    async fetchAuth(url, options = {}) {
        const token = this.getToken();
        
        if (!token) {
            throw new Error('Not authenticated');
        }
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        // If unauthorized, logout
        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }
        
        return response;
    }
};

// Toast Notification System - Professional UI
const Toast = {
    show(message, type = 'info', duration = 4000) {
        const toastContainer = document.getElementById('toastContainer') || this.createContainer();
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.setAttribute('role', 'alert');
        
        // Get icon and color
        const iconData = this.getIconData(type);
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <i class="bi bi-${iconData.icon}"></i>
                </div>
                <div class="toast-message">${this.escapeHtml(message)}</div>
                <button type="button" class="toast-close" aria-label="Close">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <div class="toast-progress"></div>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.remove(toast));
        
        // Auto remove after duration
        const progressBar = toast.querySelector('.toast-progress');
        progressBar.style.animation = `toastProgress ${duration}ms linear`;
        
        setTimeout(() => {
            this.remove(toast);
        }, duration);
    },
    
    remove(toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    },
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    },
    
    getIconData(type) {
        const icons = {
            success: { icon: 'check-circle-fill', color: '#10b981' },
            danger: { icon: 'exclamation-triangle-fill', color: '#ef4444' },
            warning: { icon: 'exclamation-circle-fill', color: '#f59e0b' },
            info: { icon: 'info-circle-fill', color: '#3b82f6' }
        };
        return icons[type] || icons.info;
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    success(message) {
        this.show(message, 'success');
    },
    
    error(message) {
        this.show(message, 'danger');
    },
    
    warning(message) {
        this.show(message, 'warning');
    },
    
    info(message) {
        this.show(message, 'info');
    }
};

// Loading Overlay
const Loading = {
    show(message = 'Đang xử lý...') {
        if (document.getElementById('loadingOverlay')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 99999;
        `;
        overlay.innerHTML = `
            <div class="spinner-custom"></div>
            <p style="color: white; margin-top: 1rem; font-weight: 500;">${message}</p>
        `;
        
        document.body.appendChild(overlay);
    },
    
    hide() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    }
};

// Form Validation Helper
const FormValidator = {
    email(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    password(password) {
        return password.length >= 6;
    },
    
    required(value) {
        return value && value.trim() !== '';
    }
};

// Smooth Scroll to Element
function smoothScroll(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Format Date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('vi-VN', options);
}

// Format File Size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Copy to Clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.success('Đã sao chép vào clipboard!');
    } catch (err) {
        Toast.error('Không thể sao chép!');
    }
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Check auth status and update UI
    if (Auth.isLoggedIn()) {
        const user = Auth.getUser();
        console.log('User logged in:', user.email);
        
        // Update UI to show logged in state
        // TODO: Show user menu, hide login buttons
    }
    
    // Add smooth scroll to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});


// Export for use in other files
window.Auth = Auth;
window.Toast = Toast;
window.Loading = Loading;
window.FormValidator = FormValidator;

