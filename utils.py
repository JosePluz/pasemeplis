import sqlite3
import random
import string
from datetime import datetime
from functools import wraps
from flask import session, request, jsonify, redirect, url_for

def login_required(f):
    """Decorador para requerir login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """Decorador para requerir rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                return jsonify({'error': 'No autorizado'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generar_codigo():
    """Genera un código único de 6 caracteres"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def audit_log(usuario, accion):
    """Registra una acción en el log de auditoría"""
    try:
        db = sqlite3.connect('taqueria.db')
        db.execute(
            'INSERT INTO audit_log (usuario, accion, timestamp) VALUES (?, ?, ?)',
            (usuario, accion, datetime.utcnow().isoformat())
        )
        db.commit()
        db.close()
    except Exception as e:
        print(f"Error en audit_log: {e}")