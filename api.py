from flask import Blueprint, request, jsonify, session
from database_sqlite import DatabaseSQLite
from auth import AuthManager, login_required, admin_required
from relatorios import GeradorRelatorios
from backup_manager import BackupManager
from dashboard import DashboardGenerator
import sqlite3
from datetime import datetime

api_bp = Blueprint('api', __name__)
db = DatabaseSQLite()
auth = AuthManager()
relatorios = GeradorRelatorios()
backup = BackupManager()
dashboard = DashboardGenerator()

# ============== AUTENTICAÇÃO ==============
@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Endpoint de login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = auth.autenticar(username, password)
    
    if user:
        token = auth.gerar_token_jwt(user['id'], user['username'], user['nivel_acesso'])
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['nivel_acesso'] = user['nivel_acesso']
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nome': user['nome'],
                'nivel_acesso': user['nivel_acesso']
            }
        })
    
    return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Endpoint de logout"""
    session.clear()
    return jsonify({'success': True})

@api_bp.route('/auth/register', methods=['POST'])
@admin_required
def register():
    """Endpoint para criar novo usuário (apenas admin)"""
    data = request.json
    
    success = auth.criar_usuario(
        username=data['username'],
        password=data['password'],
        nome=data.get('nome'),
        email=data.get('email'),
        nivel_acesso=data.get('nivel_acesso', 1)
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Usuário criado com sucesso'})
    return jsonify({'success': False, 'error': 'Username já existe'}), 400

# ============== VEÍCULOS ==============
@api_bp.route('/veiculos', methods=['GET'])
@login_required
def listar_veiculos():
    """Lista todos os veículos"""
    veiculos = db.listar_veiculos()
    
    # Adicionar status para cada veículo
    for veiculo in veiculos:
        status = db.verificar_status(veiculo['placa'])
        veiculo['status'] = status
    
    return jsonify(veiculos)

@api_bp.route('/veiculos/<placa>', methods=['GET'])
@login_required
def get_veiculo(placa):
    """Busca um veículo específico"""
    veiculo = db.buscar_veiculo(placa)
    
    if not veiculo:
        return jsonify({'error': 'Veículo não encontrado'}), 404
    
    status = db.verificar_status(placa)
    historico = db.buscar_historico(placa, limit=10)
    
    return jsonify({
        'veiculo': veiculo,
        'status': status,
        'historico': historico
    })

@api_bp.route('/veiculos', methods=['POST'])
@login_required
def criar_veiculo():
    """Cria um novo veículo"""
    data = request.json
    
    success = db.adicionar_veiculo(
        placa=data['placa'],
        modelo=data.get('modelo'),
        ano=data.get('ano'),
        cor=data.get('cor'),
        observacoes=data.get('observacoes')
    )
    
    if success:
        registrar_log(
            usuario=session.get('username'),
            acao='CRIAR_VEICULO',
            detalhes=f"Placa: {data['placa']}"
        )
        return jsonify({'success': True, 'message': 'Veículo cadastrado com sucesso'})
    return jsonify({'success': False, 'error': 'Placa já existe'}), 400

# ============== MANUTENÇÕES ==============
@api_bp.route('/manutencoes', methods=['POST'])
@login_required
def registrar_manutencao():
    """Registra nova manutenção"""
    data = request.json
    
    registro = db.registrar_manutencao(
        placa=data['placa'],
        tipo=data['tipo'],
        tecnico=session.get('username', 'Sistema'),
        observacoes=data.get('observacoes', '')
    )
    
    # Registrar log
    registrar_log(
        usuario=session.get('username'),
        acao='REGISTRAR_MANUTENCAO',
        detalhes=f"Placa: {data['placa']} - Tipo: {data['tipo']}"
    )
    
    return jsonify({
        'success': True,
        'registro': registro
    })

@api_bp.route('/manutencoes', methods=['GET'])
@login_required
def listar_manutencoes():
    """Lista manutenções"""
    placa = request.args.get('placa')
    limit = request.args.get('limit', 100, type=int)
    
    historico = db.buscar_historico(placa, limit)
    return jsonify(historico)

# ============== RELATÓRIOS ==============
@api_bp.route('/relatorios/completo', methods=['GET'])
@login_required
def relatorio_completo():
    """Gera relatório completo"""
    filename = relatorios.gerar_relatorio_completo_sqlite()
    return jsonify({'filename': filename, 'success': True})

@api_bp.route('/relatorios/historico', methods=['GET'])
@login_required
def relatorio_historico():
    """Gera relatório de histórico"""
    filename = relatorios.gerar_relatorio_historico_sqlite()
    if filename:
        return jsonify({'filename': filename, 'success': True})
    return jsonify({'success': False, 'error': 'Sem dados'}), 404

@api_bp.route('/relatorios/alertas', methods=['GET'])
@login_required
def relatorio_alertas():
    """Gera relatório de alertas"""
    filename = relatorios.gerar_relatorio_alertas_sqlite()
    return jsonify({'filename': filename, 'success': True})

@api_bp.route('/relatorios/tipos', methods=['GET'])
@login_required
def relatorio_tipos():
    """Gera relatório por tipo"""
    filename = relatorios.gerar_relatorio_por_tipo_sqlite()
    return jsonify({'filename': filename, 'success': True})

# ============== DASHBOARD ==============
@api_bp.route('/dashboard/dados', methods=['GET'])
@login_required
def dashboard_dados():
    """Retorna dados para o dashboard"""
    dados = dashboard.gerar_dados_dashboard()
    return jsonify(dados)

@api_bp.route('/dashboard/graficos', methods=['GET'])
@login_required
def dashboard_graficos():
    """Gera gráficos para o dashboard"""
    graficos = dashboard.gerar_graficos_base64()
    return jsonify(graficos)

# ============== BACKUP ==============
@api_bp.route('/backup/criar', methods=['POST'])
@admin_required
def criar_backup():
    """Cria um novo backup"""
    filename = backup.criar_backup_completo()
    registrar_log(
        usuario=session.get('username'),
        acao='CRIAR_BACKUP',
        detalhes=f"Arquivo: {os.path.basename(filename)}"
    )
    return jsonify({'success': True, 'filename': filename})

@api_bp.route('/backup/restaurar', methods=['POST'])
@admin_required
def restaurar_backup():
    """Restaura um backup"""
    data = request.json
    success = backup.restaurar_backup(data['filename'])
    if success:
        registrar_log(
            usuario=session.get('username'),
            acao='RESTAURAR_BACKUP',
            detalhes=f"Arquivo: {data['filename']}"
        )
    return jsonify({'success': success})

@api_bp.route('/backup/listar', methods=['GET'])
@admin_required
def listar_backups():
    """Lista todos os backups"""
    backups = backup.listar_backups()
    return jsonify(backups)

# ============== LOGS ==============
@api_bp.route('/logs', methods=['GET'])
@admin_required
def listar_logs():
    """Lista logs do sistema"""
    limit = request.args.get('limit', 100, type=int)
    
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM logs 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(logs)

# ============== UTILITÁRIOS ==============
@api_bp.route('/tipos-manutencao', methods=['GET'])
@login_required
def tipos_manutencao():
    """Retorna lista de tipos de manutenção"""
    from config import Config
    return jsonify(Config.TIPOS_MANUTENCAO)

@api_bp.route('/status', methods=['GET'])
def status():
    """Verifica status da API"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

def registrar_log(usuario: str, acao: str, detalhes: str = None, ip: str = None):
    """Registra um log no sistema"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO logs (usuario, acao, detalhes, ip)
        VALUES (?, ?, ?, ?)
    ''', (usuario, acao, detalhes, ip))
    
    conn.commit()
    conn.close()