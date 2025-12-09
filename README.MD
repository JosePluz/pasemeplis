# 🌮 Sistema de Gestión para Taquería - Versión Profesional

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema completo de gestión de órdenes para taquerías con roles diferenciados, auditoría completa y diseño profesional.

## 🚀 Demo en Vivo

**URL:** [https://taqueria-pro.onrender.com](https://taqueria-pro.onrender.com)

**Credenciales de prueba:**
- Usuario: `admin`
- Contraseña: `admin123`

## ✨ Características Principales

### 🔐 Sistema de Autenticación
- Registro abierto para meseros, cocina y caja
- Contraseñas hasheadas con PBKDF2-SHA256
- Sesiones seguras con cookies HttpOnly
- Control de roles con decoradores
- Registro de último acceso

### 👨‍🍳 Panel de Cocina
- Código único de 6 caracteres
- Vista de órdenes pendientes en tiempo real
- Auto-actualización cada 5 segundos
- Marcado de órdenes servidas
- Contador de órdenes activas
- Vista detallada de items por orden

### 🍽️ Panel de Mesero
- Sistema de enlace con cocina por código
- Creación de órdenes en borrador
- Agregado de items con notas especiales
- Envío de órdenes a cocina
- Vista de órdenes activas
- Límites automáticos (30 tacos, 15 bebidas por mesa)

### 💰 Panel de Caja
- Vista de órdenes servidas
- Cierre de órdenes con confirmación
- Generación de tickets en formato TXT
- Cálculo automático de totales
- Vista detallada de consumo

### 👑 Panel de Administración
- CRUD completo de usuarios
- CRUD de productos con categorías
- CRUD de mesas
- Log de auditoría detallado
- Estadísticas globales
- Vista de todas las órdenes

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** Flask 3.0
- **Base de Datos:** SQLite con índices optimizados
- **Autenticación:** Werkzeug Security
- **Servidor:** Gunicorn con workers multi-thread

### Frontend
- **HTML5** con templates Jinja2
- **CSS3** con variables CSS y animaciones
- **JavaScript** vanilla (sin frameworks)
- **Diseño:** Responsive mobile-first

### Deployment
- **Plataforma:** Render.com
- **Plan:** Free tier
- **Persistencia:** Disco integrado de Render

## 📦 Instalación Local

### Requisitos Previos
- Python 3.11+
- pip
- git

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/taqueria-pro.git
cd taqueria-pro

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Inicializar base de datos
python init_db.py

# 6. Ejecutar servidor de desarrollo
python app.py

# 7. Abrir en navegador
# http://localhost:5000
```

## 🚀 Despliegue en Render

### Opción 1: Deploy Automático

1. Fork este repositorio
2. Crear cuenta en [Render.com](https://render.com)
3. Click en "New +" → "Web Service"
4. Conectar tu repositorio
5. Render detectará automáticamente `render.yaml`
6. Click en "Create Web Service"
7. Esperar 3-5 minutos

### Opción 2: Deploy Manual

1. Ir a [Render Dashboard](https://dashboard.render.com)
2. New + → Web Service
3. Configurar:
   - **Name:** `taqueria-pro`
   - **Region:** Seleccionar la más cercana
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt && python init_db.py
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT
     ```
   - **Instance Type:** Free

4. Variables de entorno (opcional):
   - `SECRET_KEY`: Se genera automáticamente
   - `FLASK_ENV`: `production`

5. Click en "Create Web Service"

## 📚 Estructura del Proyecto

```
taqueria-pro/
├── app.py                 # Backend Flask principal
├── init_db.py            # Script de inicialización de BD
├── requirements.txt      # Dependencias Python
├── render.yaml          # Configuración Render
├── .gitignore           # Archivos ignorados por git
├── README.md            # Documentación
├── static/
│   ├── css/
│   │   └── style.css    # Estilos profesionales
│   └── js/
│       ├── utils.js     # Utilidades JavaScript
│       └── app.js       # JavaScript principal
└── templates/
    ├── base.html        # Template base
    ├── login.html       # Página de login
    ├── register.html    # Página de registro
    ├── mesero.html      # Panel mesero
    ├── cocina.html      # Panel cocina
    ├── caja.html        # Panel caja
    └── admin.html       # Panel admin
```

## 🗄️ Modelo de Datos

### Tablas Principales

#### users
```sql
- id (PK)
- username (UNIQUE)
- password (HASH)
- role (admin|mesero|cocina|caja)
- is_active (BOOLEAN)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

#### orders
```sql
- id (PK)
- mesero_id (FK → users)
- codigo_cocina (FK → cocinas)
- status (borrador|pendiente|servida|cerrada|cancelada)
- total (DECIMAL)
- created_at (TIMESTAMP)
```

#### order_items
```sql
- id (PK)
- order_id (FK → orders)
- product_id (FK → products)
- qty (INTEGER)
- unit_price (DECIMAL)
- subtotal (GENERATED COLUMN)
- notes (TEXT)
```

#### audit_log
```sql
- id (PK)
- usuario (TEXT)
- accion (TEXT)
- detalle (TEXT)
- ip_address (TEXT)
- timestamp (TIMESTAMP)
```

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con PBKDF2-SHA256
- ✅ Sesiones seguras con cookies HttpOnly
- ✅ Protección CSRF con tokens
- ✅ Validación de inputs server-side
- ✅ Control de acceso basado en roles
- ✅ Auditoría completa de acciones
- ✅ Rate limiting implícito en Render
- ✅ HTTPS obligatorio en producción

## 📊 Características Avanzadas

### Auto-actualización Inteligente
```javascript
// Actualiza solo cuando la página está visible
const autoRefresh = new AutoRefresh(fetchOrders, 5000);
autoRefresh.start();
```

### Sistema de Notificaciones
```javascript
showToast('Orden creada correctamente', 'success');
showToast('Error al procesar', 'error', 5000);
```

### Validaciones Automáticas
- Límites por mesa (30 tacos, 15 bebidas)
- Validación de códigos de cocina
- Verificación de permisos por rol
- Validación de formularios

## 🎨 Personalización

### Colores del Sistema
Editar en `static/css/style.css`:
```css
:root {
    --primary: #2563eb;        /* Azul principal */
    --secondary: #10b981;      /* Verde secundario */
    --danger: #ef4444;         /* Rojo peligro */
    --warning: #f59e0b;        /* Amarillo advertencia */
}
```

### Límites de Productos
Editar en `app.py`:
```python
MAX_TACOS_POR_MESA = 30
MAX_BEBIDAS_POR_MESA = 15
```

## 🐛 Solución de Problemas

### Error: Base de datos bloqueada
```bash
rm taqueria.db
python init_db.py
```

### Error: Módulo no encontrado
```bash
pip install -r requirements.txt --upgrade
```

### Error en Render: Build failed
1. Verificar que `requirements.txt` esté correcto
2. Revisar logs en Render Dashboard
3. Asegurar que Build Command incluya `python init_db.py`

### No se ven cambios en producción
```bash
git add .
git commit -m "Update"
git push origin main
# Render auto-desplegará en 2-3 minutos
```

## 📈 Próximas Mejoras

- [ ] Reportes en PDF
- [ ] Dashboard con gráficas
- [ ] Notificaciones push
- [ ] App móvil React Native
- [ ] Multi-sucursal
- [ ] Integración con impresoras térmicas
- [ ] Sistema de reservaciones
- [ ] Programa de lealtad

## 🤝 Contribuir

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ para modernizar la gestión de taquerías.

## 📞 Soporte

¿Necesitas ayuda?
- 📧 Email: soporte@taqueria-pro.com
- 💬 GitHub Issues: [Abrir issue](https://github.com/tu-usuario/taqueria-pro/issues)
- 📖 Documentación: [Wiki](https://github.com/tu-usuario/taqueria-pro/wiki)

---

⭐ Si te gusta este proyecto, dale una estrella en GitHub!