from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db, User, Order, Product, Table
from utils import audit_log, generar_codigo, login_required, role_required
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

@app.before_request
def before_request():
    get_db()

@app.teardown_appcontext
def close(error):
    close_db()

# ---------- AUTH ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and check_password_hash(user['password'], password):
            session.update({'user_id': user['id'], 'username': user['username'], 'role': user['role']})
            audit_log(username, 'Login')
            role = user['role']
            if role == 'mesero':
                return redirect(url_for('mesero_dashboard'))
            elif role == 'cocina':
                return redirect(url_for('cocina_dashboard'))
            elif role == 'caja':
                return redirect(url_for('caja_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
        return render_template('login.html', error='Credenciales inválidas')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()
        
        if not username or not password or not role:
            return render_template('register.html', error='Todos los campos son requeridos')
        
        if role not in ['mesero', 'cocina', 'caja']:
            return render_template('register.html', error='Rol inválido')
        
        existing_user = User.get_by_username(username)
        if existing_user:
            return render_template('register.html', error='El usuario ya existe')
        
        db = get_db()
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            db.execute(
                'INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)',
                (username, hashed_password, role, __import__('datetime').datetime.now().isoformat())
            )
            db.commit()
            audit_log(username, 'Registro')
            return render_template('register.html', success='Cuenta creada exitosamente. Inicia sesión ahora.')
        except Exception as e:
            return render_template('register.html', error=f'Error al registrar: {str(e)}')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    audit_log(session.get('username'), 'Logout')
    session.clear()
    return redirect(url_for('login'))

# ---------- MESERO ----------
@app.route('/mesero')
@login_required
@role_required('mesero')
def mesero_dashboard():
    codigo = session.get('codigo_cocina')
    db = get_db()
    orders = Order.get_by_mesero(session['user_id'])
    mesas = Table.all()
    return render_template('mesero_mesas.html', codigo_actual=codigo, mesas=mesas, orders=orders)

@app.route('/mesero/enlazar-cocina', methods=['POST'])
@login_required
@role_required('mesero')
def enlazar_cocina():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()
    
    db = get_db()
    cocina = db.execute('SELECT * FROM cocinas WHERE codigo = ?', (codigo,)).fetchone()
    
    if not cocina:
        return jsonify({'error': 'Código de cocina inválido'}), 400
    
    db.execute('INSERT OR REPLACE INTO mesero_cocina (mesero_id, codigo_cocina) VALUES (?, ?)',
               (session['user_id'], codigo))
    db.commit()
    
    session['codigo_cocina'] = codigo
    audit_log(session['username'], f'Enlazado a cocina {codigo}')
    return jsonify({'codigo': codigo})

@app.route('/mesero/desenlazar-cocina', methods=['POST'])
@login_required
@role_required('mesero')
def desenlazar_cocina():
    db = get_db()
    db.execute('DELETE FROM mesero_cocina WHERE mesero_id = ?', (session['user_id'],))
    db.commit()
    session.pop('codigo_cocina', None)
    audit_log(session['username'], 'Desenlazado de cocina')
    return jsonify({'success': True})

@app.route('/mesero/crear-orden', methods=['POST'])
@login_required
@role_required('mesero')
def crear_orden():
    codigo = session.get('codigo_cocina')
    if not codigo:
        return jsonify({'error': 'No estás enlazado a una cocina'}), 400
    
    db = get_db()
    from datetime import datetime
    db.execute(
        'INSERT INTO orders (mesero_id, codigo_cocina, status, created_at) VALUES (?, ?, ?, ?)',
        (session['user_id'], codigo, 'borrador', datetime.now().isoformat())
    )
    db.commit()
    order_id = db.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    
    audit_log(session['username'], f'Orden {order_id} creada')
    return jsonify({'order_id': order_id})

@app.route('/mesero/agregar-item', methods=['POST'])
@login_required
@role_required('mesero')
def agregar_item():
    data = request.get_json()
    
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (data['product_id'],)).fetchone()
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    try:
        db.execute(
            'INSERT INTO order_items (order_id, product_id, qty, unit_price, notes) VALUES (?, ?, ?, ?, ?)',
            (data['order_id'], data['product_id'], data['qty'], product['price'], data.get('notes', ''))
        )
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mesero/enviar-orden/<int:order_id>', methods=['POST'])
@login_required
@role_required('mesero')
def enviar_orden(order_id):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', ('pendiente', order_id))
    db.commit()
    audit_log(session['username'], f'Orden {order_id} enviada a cocina')
    return jsonify({'success': True})

@app.route('/mesero/cancelar-orden/<int:order_id>', methods=['POST'])
@login_required
@role_required('mesero')
def cancelar_orden(order_id):
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order or order['mesero_id'] != session['user_id']:
        return jsonify({'error': 'No autorizado'}), 403
    
    db.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
    db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    db.commit()
    
    audit_log(session['username'], f'Orden {order_id} cancelada')
    return jsonify({'success': True})

# ---------- COCINA ----------
@app.route('/cocina')
@login_required
@role_required('cocina')
def cocina_dashboard():
    codigo = User.get_cocina_code(session['user_id'])
    if not codigo:
        codigo = generar_codigo()
        User.save_cocina_code(session['user_id'], codigo)
    ordenes = Order.get_pendientes_by_cocina(codigo)
    return render_template('cocina_mesas.html', mi_codigo=codigo, ordenes=ordenes)

@app.route('/cocina/marcar_servido/<int:order_id>', methods=['POST'])
@login_required
@role_required('cocina')
def marcar_servido(order_id):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', ('servida', order_id))
    db.commit()
    audit_log(session['username'], f'Orden {order_id} servida')
    return jsonify({'success': True})

# ---------- CAJA ----------
@app.route('/caja')
@login_required
@role_required('caja')
def caja_dashboard():
    codigo = session.get('codigo_cocina')
    db = get_db()
    if codigo:
        ordenes = db.execute(
            'SELECT * FROM orders WHERE codigo_cocina = ? AND status = ? ORDER BY created_at DESC',
            (codigo, 'servida')
        ).fetchall()
    else:
        ordenes = []
    return render_template('caja.html', orders=ordenes, codigo_actual=codigo)

@app.route('/caja/enlazar-cocina', methods=['POST'])
@login_required
@role_required('caja')
def caja_enlazar_cocina():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()
    
    db = get_db()
    cocina = db.execute('SELECT * FROM cocinas WHERE codigo = ?', (codigo,)).fetchone()
    
    if not cocina:
        return jsonify({'error': 'Código de cocina inválido'}), 400
    
    session['codigo_cocina'] = codigo
    audit_log(session['username'], f'Caja enlazada a cocina {codigo}')
    return jsonify({'codigo': codigo})

@app.route('/caja/desenlazar-cocina', methods=['POST'])
@login_required
@role_required('caja')
def caja_desenlazar_cocina():
    session.pop('codigo_cocina', None)
    audit_log(session['username'], 'Caja desenlazada de cocina')
    return jsonify({'success': True})

@app.route('/caja/orden/<int:order_id>')
@login_required
@role_required('caja')
def caja_orden_items(order_id):
    items = Order.get_items(order_id)
    return jsonify([dict(item) for item in items])

@app.route('/caja/cerrar/<int:order_id>', methods=['POST'])
@login_required
@role_required('caja')
def caja_cerrar(order_id):
    db = get_db()
    from datetime import datetime
    db.execute('UPDATE orders SET status = ?, closed_at = ? WHERE id = ?',
               ('cerrada', datetime.now().isoformat(), order_id))
    db.commit()
    audit_log(session['username'], f'Orden {order_id} cerrada')
    return jsonify({'success': True})

# ---------- ADMIN ----------
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY id').fetchall()
    products = db.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    mesas = db.execute('SELECT * FROM tables ORDER BY id').fetchall()
    return render_template('admin.html', users=users, products=products, mesas=mesas)

@app.route('/admin/api/<entity_type>/<int:entity_id>')
@login_required
@role_required('admin')
def admin_get_entity(entity_type, entity_id):
    db = get_db()
    
    if entity_type == 'users':
        row = db.execute('SELECT * FROM users WHERE id = ?', (entity_id,)).fetchone()
    elif entity_type == 'products':
        row = db.execute('SELECT * FROM products WHERE id = ?', (entity_id,)).fetchone()
    elif entity_type == 'tables':
        row = db.execute('SELECT * FROM tables WHERE id = ?', (entity_id,)).fetchone()
    else:
        return jsonify({'error': 'Tipo no válido'}), 400
    
    if not row:
        return jsonify({'error': 'No encontrado'}), 404
    
    return jsonify(dict(row))

@app.route('/admin/api/<entity_type>/<int:entity_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_entity(entity_type, entity_id):
    db = get_db()
    data = request.get_json()
    
    try:
        if entity_type == 'users':
            db.execute('UPDATE users SET username = ?, role = ? WHERE id = ?',
                      (data['username'], data['role'], entity_id))
        elif entity_type == 'products':
            db.execute('UPDATE products SET name = ?, category = ?, price = ?, stock = ? WHERE id = ?',
                      (data['name'], data['category'], data['price'], data['stock'], entity_id))
        elif entity_type == 'tables':
            db.execute('UPDATE tables SET name = ? WHERE id = ?',
                      (data['name'], entity_id))
        else:
            return jsonify({'error': 'Tipo no válido'}), 400
        
        db.commit()
        return jsonify({'success': True, 'message': 'Actualizado correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/<entity_type>/delete/<int:entity_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_entity(entity_type, entity_id):
    db = get_db()
    
    try:
        if entity_type == 'users':
            if entity_id == 1:
                return jsonify({'error': 'No se puede eliminar al administrador principal'}), 400
            db.execute('DELETE FROM users WHERE id = ?', (entity_id,))
        elif entity_type == 'products':
            db.execute('DELETE FROM products WHERE id = ?', (entity_id,))
        elif entity_type == 'tables':
            db.execute('DELETE FROM tables WHERE id = ?', (entity_id,))
        else:
            return jsonify({'error': 'Tipo no válido'}), 400
        
        db.commit()
        return jsonify({'success': True, 'message': 'Eliminado correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- API ----------
@app.route('/api/orden/<int:order_id>/items')
@login_required
def api_order_items(order_id):
    items = Order.get_items(order_id)
    return jsonify([dict(item) for item in items])

@app.route('/api/orden/<int:order_id>/servir', methods=['POST'])
@login_required
@role_required('cocina')
def api_servir(order_id):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', ('servida', order_id))
    db.commit()
    audit_log(session['username'], f'Orden {order_id} servida')
    return jsonify({'success': True})

@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)