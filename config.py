import os
from datetime import timedelta

class Config:
    # Chave secreta para sessões
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-super-secreta-123'
    
    # Banco de dados
    DATABASE_PATH = 'manutencao.db'
    
    # Diretórios
    BACKUP_DIR = 'backups'
    EXPORTS_DIR = 'exports'
    LOGS_DIR = 'logs'
    TEMPLATES_DIR = 'templates'
    
    # Configurações de backup automático
    BACKUP_INTERVAL_HOURS = 24
    BACKUP_RETENTION_DAYS = 30
    
    # Configurações de alerta
    ALERTA_AMARELO_DIAS = 7
    ALERTA_VERMELHO_DIAS = 14
    
    # Configurações de email (opcional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # Configurações da API
    API_TOKEN_EXPIRATION = timedelta(days=1)
    
    # Configurações do dashboard
    DASHBOARD_REFRESH_SECONDS = 30
    MAX_HISTORICO_EXIBIR = 100
    
    # Tipos de manutenção disponíveis
    TIPOS_MANUTENCAO = [
        "RESET DA CÂMERA",
        "AJUSTE DATA/HORA",
        "TROCA DO CABO ELÉTRICO",
        "RECOLHER IMAGEM",
        "LIMPEZA DA LENTE",
        "ATUALIZAÇÃO FIRMWARE",
        "REPOSICIONAMENTO",
        "TESTE DE FUNCIONAMENTO",
        "OUTROS"
    ]