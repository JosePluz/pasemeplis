import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

DB_PATH = 'taqueria.db'

def init_database():
    """Inicializa la base de datos con estructura mejorada"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla usuarios con campos adicionales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'mesero', 'cocina', 'caja')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP NOT NULL,
            last_login TIMESTAMP,
            UNIQUE(username)
        )
    ''')

    # Tabla cocinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cocinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Tabla enlace mesero-cocina
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mesero_cocina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesero_id INTEGER UNIQUE NOT NULL,
            codigo_cocina TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mesero_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (codigo_cocina) REFERENCES cocinas(codigo) ON DELETE CASCADE
        )
    ''')

    # Tabla mesas con estado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            capacity INTEGER DEFAULT 4,
            status TEXT DEFAULT 'disponible' CHECK(status IN ('disponible', 'ocupada', 'reservada')),
            branch_id INTEGER DEFAULT 1
        )
    ''')

    # Tabla productos mejorada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT CHECK(category IN ('tacos', 'bebidas', 'extras', 'postres')) NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            stock INTEGER,
            is_active INTEGER DEFAULT 1,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla órdenes mejorada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesero_id INTEGER NOT NULL,
            codigo_cocina TEXT,
            status TEXT CHECK(status IN ('borrador', 'pendiente', 'en_preparacion', 'servida', 'cerrada', 'cancelada')) DEFAULT 'borrador',
            total REAL DEFAULT 0,
            notas_generales TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP,
            closed_at TIMESTAMP,
            FOREIGN KEY (mesero_id) REFERENCES users(id)
        )
    ''')

    # Tabla items de orden
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty INTEGER NOT NULL CHECK(qty > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            subtotal REAL GENERATED ALWAYS AS (qty * unit_price) STORED,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Tabla relación mesa-orden
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS table_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            status TEXT CHECK(status IN ('abierta', 'pendiente', 'servida', 'cerrada')) DEFAULT 'abierta',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES tables(id),
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    ''')

    # Tabla de auditoría mejorada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            accion TEXT NOT NULL,
            detalle TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP NOT NULL,
            entity_type TEXT,
            entity_id INTEGER
        )
    ''')

    # Índices para mejor rendimiento
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_mesero ON orders(mesero_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_cocina ON orders(codigo_cocina)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_log(usuario)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')

    # Usuario admin por defecto
    admin_exists = cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        cursor.execute('''
            INSERT INTO users (username, password, role, created_at) 
            VALUES (?, ?, ?, ?)
        ''', ('admin', hashed_password, 'admin', datetime.now().isoformat()))
        print('✅ Usuario admin creado: admin / admin123')

    # Insertar mesas predeterminadas
    for i in range(1, 16):
        cursor.execute('''
            INSERT OR IGNORE INTO tables (id, name, capacity, status) 
            VALUES (?, ?, ?, ?)
        ''', (i, f'Mesa {i}', 4, 'disponible'))

    # Productos predeterminados
    productos = [
        # Tacos
        ("Taco al Pastor", "tacos", 15.00, 100, "Carne de cerdo marinada con especias"),
        ("Taco de Asada", "tacos", 18.00, 100, "Carne de res asada"),
        ("Taco de Chorizo", "tacos", 15.00, 100, "Chorizo artesanal"),
        ("Taco de Suadero", "tacos", 16.00, 100, "Suadero de res"),
        ("Taco de Carnitas", "tacos", 17.00, 100, "Carnitas estilo Michoacán"),
        ("Taco de Pollo", "tacos", 14.00, 100, "Pollo marinado"),
        
        # Bebidas
        ("Refresco 600ml", "bebidas", 20.00, 50, "Coca-Cola, Sprite, Fanta"),
        ("Agua de Horchata", "bebidas", 15.00, 50, "Agua fresca de horchata"),
        ("Agua de Jamaica", "bebidas", 15.00, 50, "Agua fresca de jamaica"),
        ("Agua de Limón", "bebidas", 15.00, 50, "Agua fresca de limón"),
        ("Cerveza", "bebidas", 35.00, 50, "Cerveza nacional"),
        ("Agua Natural", "bebidas", 12.00, 50, "Agua embotellada"),
        
        # Extras
        ("Orden de Guacamole", "extras", 40.00, None, "Guacamole preparado al momento"),
        ("Orden de Frijoles", "extras", 25.00, None, "Frijoles refritos"),
        ("Orden de Nopales", "extras", 30.00, None, "Nopales asados"),
        ("Limones Extra", "extras", 5.00, None, "Porción de limones"),
        ("Salsas Extra", "extras", 10.00, None, "Variedad de salsas"),
        
        # Postres
        ("Flan Napolitano", "postres", 35.00, 20, "Flan casero"),
        ("Churros (3 pzas)", "postres", 30.00, 30, "Churros con azúcar"),
    ]
    
    for nombre, categoria, precio, stock, descripcion in productos:
        cursor.execute('''
            INSERT OR IGNORE INTO products (name, category, price, stock, description) 
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, categoria, precio, stock, descripcion))

    conn.commit()
    conn.close()
    print('✅ Base de datos inicializada correctamente')
    print('✅ 15 mesas creadas')
    print('✅ 19 productos agregados')
if __name__ == '__main__':
    if os.getenv('FLASK_ENV') != 'production' and os.path.exists(DB_PATH):
        print('⚠️  La base de datos ya existe. ¿Desea recrearla? (s/n)')
        respuesta = input().lower()
        if respuesta == 's':
            os.remove(DB_PATH)
            print('🗑️  Base de datos anterior eliminada')

    init_database()