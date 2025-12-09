// Sistema de notificaciones Toast
function showToast(message, type = 'info', duration = 3000) {
    let container = document.getElementById('toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `relative flex items-center w-full max-w-xs p-4 text-gray-500 bg-white rounded-lg shadow`;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-${type}-500 bg-${type}-100 rounded-lg">
            ${icons[type] || icons.info}
        </div>
        <div class="ml-3 text-sm font-normal">${message}</div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

window.showToast = showToast;
