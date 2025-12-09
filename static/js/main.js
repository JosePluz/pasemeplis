// Toast Notifications
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Admin functions
function openEditModal(entityType, entityId) {
    fetch(`/admin/api/${entityType}/${entityId}`)
        .then(r => r.json())
        .then(data => {
            console.log(data);
            // Implementar modal según necesidad
            alert(`Editar ${entityType} #${entityId}`);
        })
        .catch(err => showToast('Error: ' + err, 'error'));
}

function deleteEntity(entityType, entityId) {
    if (!confirm(`¿Eliminar este ${entityType.slice(0, -1)}?`)) return;
    
    fetch(`/admin/${entityType}/delete/${entityId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('Eliminado correctamente', 'success');
            location.reload();
        } else {
            showToast(data.error || 'Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

// Mesero functions
function enlazarCocina() {
    const codigo = document.getElementById('codigoCocina')?.value?.toUpperCase();
    
    if (!codigo || codigo.length !== 6) {
        showToast('Ingresa un código de 6 caracteres', 'warning');
        return;
    }
    
    fetch('/mesero/enlazar-cocina', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Enlazado a cocina: ${data.codigo}`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

function desenlazarCocina() {
    if (!confirm('¿Desenlazarse de la cocina?')) return;
    
    fetch('/mesero/desenlazar-cocina', {
        method: 'POST'
    })
    .then(r => r.json())
    .then(() => {
        showToast('Desenlazado', 'success');
        setTimeout(() => location.reload(), 1000);
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

function crearNuevaOrden() {
    fetch('/mesero/crear-orden', {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Orden #${data.order_id} creada`, 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

function enviarOrden(orderId) {
    if (!confirm('¿Enviar orden a cocina?')) return;
    
    fetch(`/mesero/enviar-orden/${orderId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Orden #${orderId} enviada`, 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast('Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

function cancelarOrden(orderId) {
    if (!confirm('¿CANCELAR la orden? No se puede deshacer.')) return;
    
    fetch(`/mesero/cancelar-orden/${orderId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Orden #${orderId} cancelada`, 'warning');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

// Cocina functions
function cargarItems(orderId) {
    fetch(`/api/orden/${orderId}/items`)
        .then(r => r.json())
        .then(items => {
            const container = document.getElementById(`items-${orderId}`);
            if (!container) return;
            
            if (items.length === 0) {
                container.innerHTML = '<p>Sin items</p>';
                return;
            }
            
            let html = '<ul style="list-style: none; padding: 0;">';
            let total = 0;
            items.forEach(item => {
                const subtotal = item.qty * item.unit_price;
                html += `
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                        <strong>${item.qty}x ${item.producto}</strong>
                        ${item.notes ? `<br><em style="color: #999;">${item.notes}</em>` : ''}
                        <br><span style="color: #27ae60; font-weight: 600;">$${subtotal.toFixed(2)}</span>
                    </li>
                `;
                total += subtotal;
            });
            html += `<li style="padding: 0.75rem 0; border-top: 2px solid #333; margin-top: 0.5rem; font-weight: 700;">Total: $${total.toFixed(2)}</li>`;
            html += '</ul>';
            container.innerHTML = html;
        });
}

function marcarServido(orderId) {
    if (!confirm('¿Marcar como servida?')) return;
    
    fetch(`/api/orden/${orderId}/servir`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Orden #${orderId} servida`, 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast('Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

// Caja functions
function enlazarCajaCocina() {
    const codigo = document.getElementById('codigoCocina')?.value?.toUpperCase();
    
    if (!codigo || codigo.length !== 6) {
        showToast('Ingresa un código de 6 caracteres', 'warning');
        return;
    }
    
    fetch('/caja/enlazar-cocina', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Enlazado: ${data.codigo}`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

function desenlazarCajaCocina() {
    if (!confirm('¿Desenlazarse?')) return;
    
    fetch('/caja/desenlazar-cocina', {
        method: 'POST'
    })
    .then(r => r.json())
    .then(() => {
        showToast('Desenlazado', 'success');
        setTimeout(() => location.reload(), 1000);
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

function cerrarOrden(orderId) {
    if (!confirm('¿Cerrar orden y confirmar pago?')) return;
    
    fetch(`/caja/cerrar/${orderId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ Orden #${orderId} cerrada`, 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast('Error', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

// Auto-load items on page load
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[id^="items-"]').forEach(el => {
        const orderId = el.id.split('-')[1];
        if (orderId) {
            cargarItems(orderId);
        }
    });
});

// Allow Enter key in code input
document.getElementById('codigoCocina')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        if (this.closest('.mesero-section')) {
            enlazarCocina();
        } else {
            enlazarCajaCocina();
        }
    }
});
