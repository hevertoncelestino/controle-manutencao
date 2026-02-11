import hashlib
import secrets
from datetime import datetime, timedelta
import sqlite3
import jwt
import os
from functools import wraps
from flask import request, jsonify, session

class AuthManager:
    def __init__(self, db_path='manutencao.db', secret_key=None):
        self.db_path = db_path
        self.secret_key = secret_key or secrets.token_hex(32)
    
    def hash_password(self, password: str) -> str:
        """Gera hash da senha"""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
        pwdhash = pwdhash.hex()
        return salt.decode('ascii') + pwdhash
    
    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verifica se a senha está correta"""
        salt = stored_password[:64]
        stored_pwdhash = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), 
                                      salt.encode('ascii'), 100000)
        pwdhash = pwdhash.hex()
        return pwdhash == stored_pwdhash
    
    def criar_usuario(self, username: str, password: str, nome: str = None, 
                     email: str = None, nivel_acesso: int = 1) -> bool:
        """Cria um novo usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO usuarios (username, password_hash, nome, email, nivel_acesso)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, nome, email, nivel_acesso))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def autenticar(self, username: str, password: str):
        """Autentica um usuário"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and self.verify_password(user['password_hash'], password):
            return dict(user)
        return None
    
    def gerar_token_jwt(self, user_id: int, username: str, nivel_acesso: int) -> str:
        """Gera token JWT para autenticação"""
        payload = {
            'user_id': user_id,
            'username': username,
            'nivel_acesso': nivel_acesso,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verificar_token(self, token: str):
        """Verifica token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# Decorator para rotas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Autenticação necessária'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Autenticação necessária'}), 401
        if session.get('nivel_acesso', 0) < 2:
            return jsonify({'error': 'Acesso negado - Nível de administrador necessário'}), 403
        return f(*args, **kwargs)
    return decorated_function

def criar_admin_padrao(db_path='manutencao.db'):
    """Cria usuário admin padrão se não existir"""
    auth = AuthManager(db_path)
    if not auth.autenticar('admin', 'admin123'):
        auth.criar_usuario('admin', 'admin123', 'Administrador', 
                          'admin@sistema.com', nivel_acesso=2)
        print("✅ Usuário admin criado (admin/admin123)")
        