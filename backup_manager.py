import sqlite3
import shutil
import os
from datetime import datetime
import json
import zipfile
import schedule
import time
import threading

class BackupManager:
    def __init__(self, db_path='manutencao.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def criar_backup_completo(self) -> str:
        """Cria backup completo do banco de dados e arquivos"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_completo_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Criar pasta do backup
        os.makedirs(backup_path, exist_ok=True)
        
        # Backup do banco SQLite
        if os.path.exists(self.db_path):
            db_backup = os.path.join(backup_path, 'manutencao.db')
            shutil.copy2(self.db_path, db_backup)
        
        # Backup dos arquivos JSON (se existirem)
        json_files = ['manutencoes.json', 'historico.json']
        for json_file in json_files:
            if os.path.exists(json_file):
                shutil.copy2(json_file, os.path.join(backup_path, json_file))
        
        # Backup dos relatórios
        if os.path.exists('exports'):
            exports_backup = os.path.join(backup_path, 'exports')
            shutil.copytree('exports', exports_backup, dirs_exist_ok=True)
        
        # Compactar backup
        zip_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        # Remover pasta temporária
        shutil.rmtree(backup_path)
        
        # Registrar backup no banco
        self._registrar_backup(zip_path)
        
        return zip_path
    
    def _registrar_backup(self, arquivo: str):
        """Registra backup no banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tamanho = os.path.getsize(arquivo)
        
        cursor.execute('''
            INSERT INTO backups (arquivo, tamanho, status)
            VALUES (?, ?, ?)
        ''', (os.path.basename(arquivo), tamanho, 'SUCESSO'))
        
        conn.commit()
        conn.close()
    
    def restaurar_backup(self, backup_filename: str) -> bool:
        """Restaura um backup específico"""
        try:
            zip_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(zip_path):
                print(f"❌ Arquivo de backup não encontrado: {backup_filename}")
                return False
            
            # Criar pasta temporária
            temp_dir = os.path.join(self.backup_dir, 'temp_restore')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extrair backup
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restaurar banco de dados
            db_backup = os.path.join(temp_dir, 'manutencao.db')
            if os.path.exists(db_backup):
                # Fazer backup do banco atual antes de restaurar
                self.criar_backup_completo()
                # Restaurar
                shutil.copy2(db_backup, self.db_path)
            
            # Restaurar arquivos JSON
            json_files = ['manutencoes.json', 'historico.json']
            for json_file in json_files:
                json_backup = os.path.join(temp_dir, json_file)
                if os.path.exists(json_backup):
                    shutil.copy2(json_backup, json_file)
            
            # Restaurar exports
            exports_backup = os.path.join(temp_dir, 'exports')
            if os.path.exists(exports_backup):
                shutil.copytree(exports_backup, 'exports', dirs_exist_ok=True)
            
            # Limpar
            shutil.rmtree(temp_dir)
            
            print(f"✅ Backup restaurado com sucesso: {backup_filename}")
            return True
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def listar_backups(self) -> list:
        """Lista todos os backups disponíveis"""
        backups = []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM backups 
            ORDER BY data_backup DESC
        ''')
        
        for row in cursor.fetchall():
            backup = dict(row)
            backup['tamanho_mb'] = round(backup['tamanho'] / (1024 * 1024), 2)
            backup['data_formatada'] = datetime.strptime(
                backup['data_backup'], '%Y-%m-%d %H:%M:%S'
            ).strftime('%d/%m/%Y %H:%M')
            backups.append(backup)
        
        conn.close()
        
        return backups
    
    def limpar_backups_antigos(self, dias=30):
        """Remove backups com mais de X dias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM backups 
            WHERE julianday('now') - julianday(data_backup) > ?
        ''', (dias,))
        
        conn.commit()
        conn.close()
        
        # Remover arquivos físicos
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_dir, file)
                # Verificar data do arquivo
                file_time = os.path.getmtime(file_path)
                if time.time() - file_time > dias * 86400:
                    os.remove(file_path)
                    print(f"🗑️ Removido backup antigo: {file}")
    
    def iniciar_backup_automatico(self, intervalo_horas=24):
        """Inicia backup automático em intervalo regular"""
        schedule.every(intervalo_horas).hours.do(self.criar_backup_completo)
        schedule.every().day.at("03:00").do(lambda: self.limpar_backups_antigos(30))
        
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        
        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()
        
        print(f"✅ Backup automático configurado - A cada {intervalo_horas} horas")