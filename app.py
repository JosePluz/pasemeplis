from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from functools import wraps
from datetime import datetime
import random
import string

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "taqueria-pro-secret-key-2024")

DB_PATH = 'taqueria.db'

# ============ DATABASE HELPERS ============
def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db_if_needed():
    """Inicializa BD si no existe"""
    if not os.path.exists(DB_PATH):
        from init_db import init_database
        init_database()

# ============ DECORATORS ============
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============ UTILITY FUNCTIONS ============
def generar_codigo():
    """Genera código único de 6 caracteres"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def audit_log(usuario, accion, detalle=""):
    """Registra acciones en auditoría"""
    try:
        db = get_db()
        db.execute(
            'INSERT INTO audit_log (usuario, accion, detalle, timestamp) VALUES (?, ?, ?, ?)',
            (usuario, accion, detalle, datetime.now().isoformat())
        )
        db.commit()
        db.close()
    except Exception as e:
        print(f"Error audit_log: {e}")

# ============ BEFORE/AFTER REQUEST ============
@app.before_request
def before_request():
    init_db_if_needed()

# ============ AUTH ROUTES ============
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'mesero':
            return redirect(url_for('mesero_dashboard'))
        elif role == 'cocina':
            return redirect(url_for('cocina_dashboard'))
        elif role == 'caja':
            return redirect(url_for('caja_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('login.html', error='Usuario y contraseña requeridos')
        
        try:
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            db.close()
            
            if user and check_password_hash(user['password'], password):
                session.update({
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                })
                
                # Update last login
                db = get_db()
                db.execute('UPDATE users SET last_login = ? WHERE id = ?',
                          (datetime.now().isoformat(), user['id']))
                db.commit()
                db.close()
                
                audit_log(username, 'Login', 'Ingreso exitoso')
                
                if user['role'] == 'mesero':
                    return redirect(url_for('mesero_dashboard'))
                elif user['role'] == 'cocina':
                    return redirect(url_for('cocina_dashboard'))
                elif user['role'] == 'caja':
                    return redirect(url_for('caja_dashboard'))
                elif user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
            
            return render_template('login.html', error='Credenciales inválidas')
        except Exception as e:
            return render_template('login.html', error=f'Error: {str(e)}')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()
        
        if not username or not password or not role:
            return render_template('register.html', error='Todos los campos requeridos')
        
        if role not in ['mesero', 'cocina', 'caja']:
            return render_template('register.html', error='Rol inválido')
        
        try:
            db = get_db()
            existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            
            if existing:
                db.close()
                return render_template('register.html', error='Usuario ya existe')
            
            hashed = generate_password_hash(password, method='pbkdf2:sha256')
            db.execute(
                'INSERT INTO users (username, password, role, is_active, created_at) VALUES (?, ?, ?, ?, ?)',
                (username, hashed, role, 1, datetime.now().isoformat())
            )
            db.commit()
            db.close()
            
            audit_log(username, 'Registro', f'Registro como {role}')
            return render_template('register.html', success='✅ Cuenta creada! Inicia sesión.')
        except Exception as e:
            return render_template('register.html', error=f'Error: {str(e)}')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    audit_log(session.get('username', 'unknown'), 'Logout', 'Cierre sesión')
    session.clear()
    return redirect(url_for('login'))

# ============ MESERO ROUTES ============
@app.route('/mesero')
@login_required
@role_required('mesero')
def mesero_dashboard():
    db = get_db()
    
    codigo = session.get('codigo_cocina')
    
    orders = db.execute('''
        SELECT o.id, o.status, o.created_at, o.total,
               COUNT(oi.id) as items_count
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE o.mesero_id = ? AND o.status != 'cerrada'
        GROUP BY o.id
        ORDER BY o.created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    db.close()
    return render_template('mesero.html', codigo_actual=codigo, orders=orders)

@app.route('/mesero/enlazar-cocina', methods=['POST'])
@login_required
@role_required('mesero')
def enlazar_cocina():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()
    
    if len(codigo) != 6:
        return jsonify({'error': 'Código debe tener 6 caracteres'}), 400
    
    db = get_db()
    cocina = db.execute('SELECT * FROM cocinas WHERE codigo = ?', (codigo,)).fetchone()
    db.close()
    
    if not cocina:
        return jsonify({'error': 'Código inválido'}), 400
    
    session['codigo_cocina'] = codigo
    audit_log(session['username'], 'Enlazado cocina', codigo)
    return jsonify({'success': True, 'codigo': codigo})

@app.route('/mesero/desenlazar-cocina', methods=['POST'])
@login_required
@role_required('mesero')
def desenlazar_cocina():
    session.pop('codigo_cocina', None)
    audit_log(session['username'], 'Desenlazado cocina')
    return jsonify({'success': True})

@app.route('/mesero/crear-orden', methods=['POST'])
@login_required
@role_required('mesero')
def crear_orden():
    codigo = session.get('codigo_cocina')
    if not codigo:
        return jsonify({'error': 'No enlazado a cocina'}), 400
    
    db = get_db()
    db.execute(
        'INSERT INTO orders (mesero_id, codigo_cocina, status, total, created_at) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], codigo, 'borrador', 0, datetime.now().isoformat())
    )
    db.commit()
    
    order_id = db.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    db.close()
    
    audit_log(session['username'], 'Orden creada', f'#{order_id}')
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/mesero/agregar-item', methods=['POST'])
@login_required
@role_required('mesero')
def agregar_item():
    data = request.get_json()
    
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (data['product_id'],)).fetchone()
    
    if not product:
        db.close()
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    try:
        db.execute(
            'INSERT INTO order_items (order_id, product_id, qty, unit_price, notes) VALUES (?, ?, ?, ?, ?)',
            (data['order_id'], data['product_id'], data['qty'], product['price'], data.get('notes', ''))
        )
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500

@app.route('/mesero/enviar-orden/<int:order_id>', methods=['POST'])
@login_required
@role_required('mesero')
def enviar_orden(order_id):
    db = get_db()
    
    # Calcular total
    total = db.execute('''
        SELECT COALESCE(SUM(qty * unit_price), 0) as total
        FROM order_items WHERE order_id = ?
    ''', (order_id,)).fetchone()['total']
    
    db.execute(
        'UPDATE orders SET status = ?, total = ?, updated_at = ? WHERE id = ?',
        ('pendiente', total, datetime.now().isoformat(), order_id)
    )
    db.commit()
    db.close()
    
    audit_log(session['username'], 'Orden enviada', f'#{order_id} a cocina')
    return jsonify({'success': True})

@app.route('/mesero/cancelar-orden/<int:order_id>', methods=['POST'])
@login_required
@role_required('mesero')
def cancelar_orden(order_id):
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    
    if not order or order['mesero_id'] != session['user_id']:
        db.close()
        return jsonify({'error': 'No autorizado'}), 403
    
    db.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
    db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    db.commit()
    db.close()
    
    audit_log(session['username'], 'Orden cancelada', f'#{order_id}')
    return jsonify({'success': True})

# ============ COCINA ROUTES ============
@app.route('/cocina')
@login_required
@role_required('cocina')
def cocina_dashboard():
    db = get_db()
    
    # Get or create cocina code
    cocina = db.execute('SELECT codigo FROM cocinas WHERE user_id = ?', (session['user_id'],)).fetchone()
    codigo = cocina['codigo'] if cocina else generar_codigo()
    
    if not cocina:
        db.execute(
            'INSERT INTO cocinas (user_id, codigo, created_at) VALUES (?, ?, ?)',
            (session['user_id'], codigo, datetime.now().isoformat())
        )
        db.commit()
    
    # Get pending orders
    ordenes = db.execute('''
        SELECT o.id, o.created_at, u.username as mesero
        FROM orders o
        LEFT JOIN users u ON u.id = o.mesero_id
        WHERE o.codigo_cocina = ? AND o.status = 'pendiente'
        ORDER BY o.created_at ASC
    ''', (codigo,)).fetchall()
    
    db.close()
    return render_template('cocina_mesas.html', mi_codigo=codigo, ordenes=ordenes)

@app.route('/api/orden/<int:order_id>/items')
@login_required
def api_order_items(order_id):
    db = get_db()
    items = db.execute('''
        SELECT oi.qty, p.name as producto, oi.unit_price, oi.notes,
               (oi.qty * oi.unit_price) as subtotal
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    db.close()
    
    return jsonify([dict(item) for item in items])

@app.route('/api/orden/<int:order_id>/servir', methods=['POST'])
@login_required
@role_required('cocina')
def api_servir(order_id):
    db = get_db()
    db.execute('UPDATE orders SET status = ?, updated_at = ? WHERE id = ?',
               ('servida', datetime.now().isoformat(), order_id))
    db.commit()
    db.close()
    
    audit_log(session['username'], 'Orden servida', f'#{order_id}')
    return jsonify({'success': True})

# ============ CAJA ROUTES ============
@app.route('/caja')
@login_required
@role_required('caja')
def caja_dashboard():
    db = get_db()
    codigo = session.get('codigo_cocina')
    ordenes = []
    
    if codigo:
        ordenes = db.execute('''
            SELECT o.id, o.created_at, o.total, u.username as mesero
            FROM orders o
            LEFT JOIN users u ON u.id = o.mesero_id
            WHERE o.codigo_cocina = ? AND o.status = 'servida'
            ORDER BY o.created_at DESC
        ''', (codigo,)).fetchall()
    
    db.close()
    return render_template('caja.html', ordenes=ordenes, codigo_actual=codigo)

@app.route('/caja/enlazar-cocina', methods=['POST'])
@login_required
@role_required('caja')
def caja_enlazar_cocina():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()
    
    db = get_db()
    cocina = db.execute('SELECT * FROM cocinas WHERE codigo = ?', (codigo,)).fetchone()
    db.close()
    
    if not cocina:
        return jsonify({'error': 'Código inválido'}), 400
    
    session['codigo_cocina'] = codigo
    return jsonify({'success': True, 'codigo': codigo})

@app.route('/caja/desenlazar-cocina', methods=['POST'])
@login_required
@role_required('caja')
def caja_desenlazar_cocina():
    session.pop('codigo_cocina', None)
    return jsonify({'success': True})

@app.route('/caja/cerrar/<int:order_id>', methods=['POST'])
@login_required
@role_required('caja')
def caja_cerrar(order_id):
    db = get_db()
    db.execute('UPDATE orders SET status = ?, closed_at = ? WHERE id = ?',
               ('cerrada', datetime.now().isoformat(), order_id))
    db.commit()
    db.close()
    
    audit_log(session['username'], 'Orden cerrada', f'#{order_id}')
    return jsonify({'success': True})

# ============ ADMIN ROUTES ============
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY id').fetchall()
    products = db.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    tables = db.execute('SELECT * FROM tables ORDER BY id').fetchall()
    db.close()
    
    return render_template('admin.html', users=users, products=products, mesas=tables)

@app.route('/admin/api/<entity_type>/<int:entity_id>')
@login_required
@role_required('admin')
def admin_get_entity(entity_type, entity_id):
    db = get_db()
    
    if entity_type == 'users':
        row = db.execute('SELECT id, username, role FROM users WHERE id = ?', (entity_id,)).fetchone()
    elif entity_type == 'products':
        row = db.execute('SELECT id, name, category, price, stock FROM products WHERE id = ?', (entity_id,)).fetchone()
    elif entity_type == 'tables':
        row = db.execute('SELECT id, name FROM tables WHERE id = ?', (entity_id,)).fetchone()
    else:
        db.close()
        return jsonify({'error': 'Invalid type'}), 400
    
    db.close()
    
    if not row:
        return jsonify({'error': 'Not found'}), 404
    
    return jsonify(dict(row))

@app.route('/admin/api/<entity_type>/<int:entity_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_entity(entity_type, entity_id):
    data = request.get_json()
    db = get_db()
    
    try:
        if entity_type == 'users':
            db.execute('UPDATE users SET username = ?, role = ? WHERE id = ?',
                      (data['username'], data['role'], entity_id))
        elif entity_type == 'products':
            db.execute('UPDATE products SET name = ?, category = ?, price = ?, stock = ? WHERE id = ?',
                      (data['name'], data['category'], data['price'], data.get('stock'), entity_id))
        elif entity_type == 'tables':
            db.execute('UPDATE tables SET name = ? WHERE id = ?', (data['name'], entity_id))
        else:
            db.close()
            return jsonify({'error': 'Invalid type'}), 400
        
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/<entity_type>/delete/<int:entity_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_entity(entity_type, entity_id):
    db = get_db()
    
    try:
        if entity_type == 'users':
            if entity_id == 1:
                db.close()
                return jsonify({'error': 'Cannot delete main admin'}), 400
            db.execute('DELETE FROM users WHERE id = ?', (entity_id,))
        elif entity_type == 'products':
            db.execute('DELETE FROM products WHERE id = ?', (entity_id,))
        elif entity_type == 'tables':
            db.execute('DELETE FROM tables WHERE id = ?', (entity_id,))
        else:
            db.close()
            return jsonify({'error': 'Invalid type'}), 400
        
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500

# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('login'))

@app.errorhandler(500)
def server_error(e):
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
