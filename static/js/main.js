// ==========================
// NOTIFICATIONS (TOAST)
// ==========================
function showToast(message, type = 'info', duration = 3000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `relative flex items-center w-full max-w-xs p-4 text-gray-500 bg-white rounded-lg shadow dark:text-gray-400 dark:bg-gray-800`;

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    const icon = icons[type] || icons.info;

    toast.innerHTML = `
        <div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-${type}-500 bg-${type}-100 rounded-lg">
            ${icon}
        </div>
        <div class="ml-3 text-sm font-normal">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==========================
// ADMIN FUNCTIONS
// ==========================
function deleteEntity(entityType, entityId) {
    if (!confirm(`¿Estás seguro de que quieres eliminar este ${entityType.slice(0, -1)}?`)) return;

    fetch(`/admin/${entityType}/delete/${entityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Eliminado correctamente.', 'success');
            location.reload();
        } else {
            showToast(data.error || 'No se pudo eliminar.', 'error');
        }
    })
    .catch(err => {
        showToast('Error de red al intentar eliminar.', 'error');
    });
}

function openEditModal(entityType, entityId) {
    const modal = document.getElementById('editModal');
    const formFields = document.getElementById('edit-form-fields');
    const entityTypeInput = document.getElementById('edit-entity-type');
    const entityIdInput = document.getElementById('edit-entity-id');

    entityTypeInput.value = entityType;
    entityIdInput.value = entityId;

    fetch(`/admin/api/${entityType}/${entityId}`)
        .then(response => response.json())
        .then(data => {
            formFields.innerHTML = '';

            const fields = {
                users: [
                    { name: 'username', label: 'Nombre de usuario', type: 'text' },
                    { name: 'role', label: 'Rol', type: 'select', options: ['admin', 'mesero', 'cocina', 'caja'] }
                ],
                products: [
                    { name: 'name', label: 'Nombre', type: 'text' },
                    { name: 'category', label: 'Categoría', type: 'select', options: ['tacos', 'bebidas', 'extras'] },
                    { name: 'price', label: 'Precio', type: 'number' },
                    { name: 'stock', label: 'Stock', type: 'number' },
                ],
                tables: [
                    { name: 'name', label: 'Nombre de Mesa', type: 'text' }
                ]
            };

            fields[entityType].forEach(field => {
                const value = data[field.name] || '';
                let inputHtml = '';

                if (field.type === 'select') {
                    inputHtml = `<label class="block">${field.label}</label><select name="${field.name}" class="w-full p-2 border rounded">`;
                    field.options.forEach(opt => {
                        inputHtml += `<option value="${opt}" ${opt === value ? 'selected' : ''}>${opt}</option>`;
                    });
                    inputHtml += '</select>';
                } else {
                    inputHtml = `<label class="block">${field.label}</label><input type="${field.type}" name="${field.name}" value="${value}" class="w-full p-2 border rounded">`;
                }

                formFields.innerHTML += `<div class="mb-2">${inputHtml}</div>`;
            });

            modal.classList.remove('hidden');
        });
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
}

function submitEditForm() {
    const entityType = document.getElementById('edit-entity-type').value;
    const entityId = document.getElementById('edit-entity-id').value;
    const form = document.getElementById('editForm');
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => { data[key] = value; });

    fetch(`/admin/api/${entityType}/${entityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            showToast(result.message, 'success');
            closeEditModal();
            location.reload();
        } else {
            showToast(result.error, 'error');
        }
    });
}

// ==========================
// UTILS
// ==========================
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-MX', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function validateCodigoCocina(codigo) {
    return /^[A-Z0-9]{6}$/.test(codigo);
}

function confirmAction(message) {
    return confirm(message);
}

async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en la solicitud');
        }

        return { success: true, data };
    } catch (error) {
        console.error('Fetch error:', error);
        showToast(error.message || 'Error de red', 'error');
        return { success: false, error: error.message };
    }
}

// ==========================
// GLOBAL ACCESS
// ==========================
window.showToast = showToast;
window.deleteEntity = deleteEntity;
window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.submitEditForm = submitEditForm;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.validateCodigoCocina = validateCodigoCocina;
window.confirmAction = confirmAction;
window.fetchWithErrorHandling = fetchWithErrorHandling;