from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from database_sqlite import DatabaseSQLite
from auth import AuthManager, login_required, admin_required, criar_admin_padrao
from api import api_bp, registrar_log
from backup_manager import BackupManager
from dashboard import DashboardGenerator
from relatorios import GeradorRelatorios
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Registrar blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Inicializar componentes
db = DatabaseSQLite()
auth = AuthManager()
backup = BackupManager()
dashboard = DashboardGenerator()
relatorios = GeradorRelatorios()

# Criar usuário admin padrão
criar_admin_padrao()

# ============== ROTAS DA INTERFACE ==============
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return redirect(url_for('dashboard_page'))

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard_completo.html', 
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

@app.route('/veiculos')
@login_required
def veiculos_page():
    return render_template('veiculos.html', 
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

@app.route('/manutencoes')
@login_required
def manutencoes_page():
    return render_template('manutencoes.html',
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

@app.route('/relatorios')
@login_required
def relatorios_page():
    return render_template('relatorios.html',
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

@app.route('/configuracoes')
@admin_required
def configuracoes_page():
    return render_template('configuracoes.html',
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

@app.route('/backups')
@admin_required
def backups_page():
    return render_template('backups.html',
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

@app.route('/logs')
@admin_required
def logs_page():
    return render_template('logs.html',
                         usuario=session.get('username'),
                         nivel_acesso=session.get('nivel_acesso'))

# ============== DOWNLOAD DE ARQUIVOS ==============
@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    # Iniciar backup automático
    backup.iniciar_backup_automatico(24)
    
    print("=" * 60)
    print("🚗 SISTEMA DE CONTROLE DE MANUTENÇÃO - WEB")
    print("=" * 60)
    print(f"\n📱 Acesse: http://localhost:5000")
    print(f"👤 Usuário: admin")
    print(f"🔑 Senha: admin123")
    print("\n⚠️  Pressione CTRL+C para encerrar")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)