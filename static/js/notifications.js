// Sistema de notificaciones toast

function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 3000;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    };
    
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    
    const color = colors[type] || colors['info'];
    const icon = icons[type] || '•';
    
    toast.style.cssText = `
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 1rem;
        border-left: 4px solid ${color};
        animation: slideIn 0.3s ease-out;
        font-family: inherit;
    `;
    
    toast.innerHTML = `
        <span style="font-size: 1.5rem; color: ${color}; font-weight: bold;">${icon}</span>
        <span style="font-weight: 600; color: #1f2937; flex: 1;">${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto-remover después del tiempo especificado
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Agregar estilos de animación si no existen
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
    `;
    document.head.appendChild(style);
}

// Alias para compatibilidad
window.showToast = showToast;