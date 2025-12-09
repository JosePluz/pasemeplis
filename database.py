import sqlite3
from datetime import datetime

DB_NAME = 'taqueria.db'

def get_db():
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row
    return db

def close_db():
    db = sqlite3.connect(DB_NAME)
    db.close()

class User:
    @staticmethod
    def get_by_username(username):
        db = get_db()
        return db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    @staticmethod
    def get_cocina_code(user_id):
        db = get_db()
        row = db.execute('SELECT codigo FROM cocinas WHERE user_id = ?', (user_id,)).fetchone()
        return row['codigo'] if row else None

    @staticmethod
    def save_cocina_code(user_id, codigo):
        db = get_db()
        db.execute('INSERT OR REPLACE INTO cocinas (user_id, codigo, created_at) VALUES (?, ?, ?)',
                   (user_id, codigo, datetime.utcnow().isoformat()))
        db.commit()

class Order:
    @staticmethod
    def get_by_mesero(user_id):
        db = get_db()
        return db.execute('''
            SELECT o.*, COUNT(oi.id) as items_count
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.mesero_id = ? AND o.status != 'cerrada'
            GROUP BY o.id
            ORDER BY o.created_at DESC
        ''', (user_id,)).fetchall()

    @staticmethod
    def get_pendientes_by_cocina(codigo):
        db = get_db()
        return db.execute('''
            SELECT o.id, t.name as mesa, o.created_at, u.username as mesero
            FROM orders o
            LEFT JOIN table_orders tbl ON tbl.order_id = o.id
            LEFT JOIN tables t ON t.id = tbl.table_id
            LEFT JOIN users u ON u.id = o.mesero_id
            WHERE o.codigo_cocina = ? AND o.status = 'pendiente'
            ORDER BY o.created_at ASC
        ''', (codigo,)).fetchall()

    @staticmethod
    def get_items(order_id):
        db = get_db()
        return db.execute('''
            SELECT oi.qty, p.name as producto, oi.notes
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        ''', (order_id,)).fetchall()

    @staticmethod
    def marcar_servida(order_id):
        db = get_db()
        db.execute('UPDATE orders SET status = ? WHERE id = ?', ('servida', order_id))
        db.commit()

class Product:
    @staticmethod
    def all():
        db = get_db()
        return db.execute('SELECT * FROM products ORDER BY category, name').fetchall()

class Table:
    @staticmethod
    def all():
        db = get_db()
        return db.execute('SELECT * FROM tables ORDER BY id').fetchall()