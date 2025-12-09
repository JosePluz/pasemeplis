// Variables globales
let editModal = null;
let currentEntityType = null;
let currentEntityId = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    editModal = document.getElementById('editModal');
    setupTabListener();
});

// Setup de tabs
function setupTabListener() {
    const buttons = document.querySelectorAll('[data-tabs-target]');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.getAttribute('data-tabs-target');
            const tabId = this.getAttribute('id');
            
            // Desactivar todos los tabs
            document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
                panel.classList.add('hidden');
            });
            document.querySelectorAll('[role="tab"]').forEach(tab => {
                tab.classList.remove('border-b-2');
            });
            
            // Activar el tab seleccionado
            document.querySelector(target).classList.remove('hidden');
            this.classList.add('border-b-2', 'border-blue-600', 'text-blue-600');
        });
    });
    
    // Activar el primer tab
    const firstBtn = document.querySelector('[data-tabs-target]');
    if (firstBtn) firstBtn.click();
}

// Abrir modal de edición
function openEditModal(entityType, entityId) {
    currentEntityType = entityType;
    currentEntityId = entityId;
    
    // Obtener datos de la entidad
    fetch(`/admin/api/${entityType}/${entityId}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('edit-entity-type').value = entityType;
            document.getElementById('edit-entity-id').value = entityId;
            
            const formFields = document.getElementById('edit-form-fields');
            formFields.innerHTML = '';
            
            if (entityType === 'users') {
                formFields.innerHTML = `
                    <div class="form-group">
                        <label for="username">Usuario</label>
                        <input type="text" id="username" value="${data.username}" required>
                    </div>
                    <div class="form-group">
                        <label for="role">Rol</label>
                        <select id="role" required>
                            <option value="mesero" ${data.role === 'mesero' ? 'selected' : ''}>Mesero</option>
                            <option value="cocina" ${data.role === 'cocina' ? 'selected' : ''}>Cocina</option>
                            <option value="caja" ${data.role === 'caja' ? 'selected' : ''}>Caja</option>
                            <option value="admin" ${data.role === 'admin' ? 'selected' : ''}>Admin</option>
                        </select>
                    </div>
                `;
            } else if (entityType === 'products') {
                formFields.innerHTML = `
                    <div class="form-group">
                        <label for="name">Nombre</label>
                        <input type="text" id="name" value="${data.name}" required>
                    </div>
                    <div class="form-group">
                        <label for="category">Categoría</label>
                        <select id="category" required>
                            <option value="tacos" ${data.category === 'tacos' ? 'selected' : ''}>Tacos</option>
                            <option value="bebidas" ${data.category === 'bebidas' ? 'selected' : ''}>Bebidas</option>
                            <option value="extras" ${data.category === 'extras' ? 'selected' : ''}>Extras</option>
                            <option value="postres" ${data.category === 'postres' ? 'selected' : ''}>Postres</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="price">Precio</label>
                        <input type="number" id="price" value="${data.price}" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="stock">Stock</label>
                        <input type="number" id="stock" value="${data.stock || ''}" step="1">
                    </div>
                `;
            } else if (entityType === 'tables') {
                formFields.innerHTML = `
                    <div class="form-group">
                        <label for="name">Nombre</label>
                        <input type="text" id="name" value="${data.name}" required>
                    </div>
                `;
            }
            
            editModal.classList.remove('hidden');
        })
        .catch(err => {
            alert('Error al cargar datos: ' + err);
        });
}

// Cerrar modal
function closeEditModal() {
    editModal.classList.add('hidden');
    document.getElementById('editForm').reset();
}

// Enviar cambios
function submitEditForm() {
    const entityType = document.getElementById('edit-entity-type').value;
    const entityId = document.getElementById('edit-entity-id').value;
    
    let data = {
        id: entityId
    };
    
    if (entityType === 'users') {
        data.username = document.getElementById('username').value;
        data.role = document.getElementById('role').value;
    } else if (entityType === 'products') {
        data.name = document.getElementById('name').value;
        data.category = document.getElementById('category').value;
        data.price = parseFloat(document.getElementById('price').value);
        data.stock = document.getElementById('stock').value ? parseInt(document.getElementById('stock').value) : null;
    } else if (entityType === 'tables') {
        data.name = document.getElementById('name').value;
    }
    
    fetch(`/admin/api/${entityType}/${entityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showToast('Actualizado correctamente', 'success');
            closeEditModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(result.error || 'Error al actualizar', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

// Eliminar entidad
function deleteEntity(entityType, entityId) {
    if (!confirm('¿Estás seguro de que deseas eliminar esto?')) return;
    
    fetch(`/admin/${entityType}/delete/${entityId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showToast('Eliminado correctamente', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(result.error || 'Error al eliminar', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err, 'error'));
}

// Función showToast (si no existe en utils.js)
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    return icons[type] || '•';
}