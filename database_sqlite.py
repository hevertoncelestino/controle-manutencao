import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json
import os

class DatabaseSQLite:
    def __init__(self, db_path='manutencao.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados e cria as tabelas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de veículos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS veiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placa TEXT UNIQUE NOT NULL,
                modelo TEXT,
                ano INTEGER,
                cor TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_manutencao TIMESTAMP,
                ultimo_tipo TEXT,
                observacoes TEXT
            )
        ''')
        
        # Tabela de manutenções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manutencoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placa TEXT NOT NULL,
                data_manutencao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,
                observacoes TEXT,
                tecnico TEXT,
                FOREIGN KEY (placa) REFERENCES veiculos (placa)
            )
        ''')
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nome TEXT,
                email TEXT,
                nivel_acesso INTEGER DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT,
                acao TEXT,
                detalhes TEXT,
                ip TEXT
            )
        ''')
        
        # Tabela de backup
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_backup TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                arquivo TEXT,
                tamanho INTEGER,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def adicionar_veiculo(self, placa: str, modelo: str = None, ano: int = None, 
                         cor: str = None, observacoes: str = None) -> bool:
        """Adiciona um novo veículo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO veiculos (placa, modelo, ano, cor, observacoes)
                VALUES (?, ?, ?, ?, ?)
            ''', (placa.upper(), modelo, ano, cor, observacoes))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def registrar_manutencao(self, placa: str, tipo: str, tecnico: str = "Sistema", 
                           observacoes: str = "") -> Dict:
        """Registra uma nova manutenção"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data_atual = datetime.now()
        
        # Verificar se veículo existe, se não, criar
        veiculo = self.buscar_veiculo(placa)
        if not veiculo:
            self.adicionar_veiculo(placa)
        
        # Inserir manutenção
        cursor.execute('''
            INSERT INTO manutencoes (placa, tipo, tecnico, observacoes, data_manutencao)
            VALUES (?, ?, ?, ?, ?)
        ''', (placa.upper(), tipo, tecnico, observacoes, data_atual))
        
        # Atualizar última manutenção do veículo
        cursor.execute('''
            UPDATE veiculos 
            SET ultima_manutencao = ?, ultimo_tipo = ?
            WHERE placa = ?
        ''', (data_atual, tipo, placa.upper()))
        
        conn.commit()
        
        # Buscar o registro inserido
        cursor.execute('''
            SELECT * FROM manutencoes WHERE id = last_insert_rowid()
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'placa': row[1],
                'data_manutencao': row[2],
                'tipo': row[3],
                'observacoes': row[4],
                'tecnico': row[5]
            }
        return {}
    
    def buscar_veiculo(self, placa: str) -> Optional[Dict]:
        """Busca um veículo pela placa"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM veiculos WHERE placa = ?', (placa.upper(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def buscar_historico(self, placa: str = None, limit: int = 100) -> List[Dict]:
        """Busca histórico de manutenções"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if placa:
            cursor.execute('''
                SELECT * FROM manutencoes 
                WHERE placa = ? 
                ORDER BY data_manutencao DESC 
                LIMIT ?
            ''', (placa.upper(), limit))
        else:
            cursor.execute('''
                SELECT * FROM manutencoes 
                ORDER BY data_manutencao DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def listar_veiculos(self) -> List[Dict]:
        """Lista todos os veículos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM veiculos ORDER BY placa')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def verificar_status(self, placa: str) -> Dict:
        """Verifica status de manutenção do veículo"""
        veiculo = self.buscar_veiculo(placa)
        
        if not veiculo or not veiculo['ultima_manutencao']:
            return {
                'status': 'nao_encontrado', 
                'dias': None, 
                'cor': 'cinza',
                'mensagem': 'Sem manutenção registrada'
            }
        
        try:
            ultima_manutencao = datetime.strptime(
                veiculo['ultima_manutencao'], '%Y-%m-%d %H:%M:%S.%f'
            )
        except:
            ultima_manutencao = datetime.strptime(
                veiculo['ultima_manutencao'], '%Y-%m-%d %H:%M:%S'
            )
        
        dias_diff = (datetime.now() - ultima_manutencao).days
        
        status_info = {
            'status': '',
            'dias': dias_diff,
            'cor': '',
            'ultima_data': veiculo['ultima_manutencao'],
            'ultimo_tipo': veiculo.get('ultimo_tipo', 'N/A')
        }
        
        if dias_diff <= 6:
            status_info['status'] = 'ok'
            status_info['cor'] = 'verde'
            status_info['mensagem'] = f'Em dia - {dias_diff} dias'
        elif dias_diff <= 13:
            status_info['status'] = 'atencao'
            status_info['cor'] = 'amarelo'
            status_info['mensagem'] = f'Atenção - {dias_diff} dias'
        else:
            status_info['status'] = 'critico'
            status_info['cor'] = 'vermelho'
            status_info['mensagem'] = f'Crítico - {dias_diff} dias'
        
        return status_info
    
    def get_estatisticas(self) -> Dict:
        """Retorna estatísticas completas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de veículos
        cursor.execute('SELECT COUNT(*) FROM veiculos')
        total_veiculos = cursor.fetchone()[0]
        
        # Status dos veículos
        cursor.execute('SELECT placa, ultima_manutencao FROM veiculos WHERE ultima_manutencao IS NOT NULL')
        veiculos = cursor.fetchall()
        
        verde = amarelo = vermelho = 0
        dias_total = 0
        
        for placa, ultima in veiculos:
            try:
                ultima_dt = datetime.strptime(ultima, '%Y-%m-%d %H:%M:%S.%f')
            except:
                ultima_dt = datetime.strptime(ultima, '%Y-%m-%d %H:%M:%S')
            dias = (datetime.now() - ultima_dt).days
            dias_total += dias
            
            if dias <= 6:
                verde += 1
            elif dias <= 13:
                amarelo += 1
            else:
                vermelho += 1
        
        # Total de manutenções
        cursor.execute('SELECT COUNT(*) FROM manutencoes')
        total_manutencoes = cursor.fetchone()[0]
        
        # Manutenções por tipo
        cursor.execute('''
            SELECT tipo, COUNT(*) as quantidade 
            FROM manutencoes 
            GROUP BY tipo 
            ORDER BY quantidade DESC
        ''')
        manutencoes_por_tipo = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_veiculos': total_veiculos,
            'verde': verde,
            'amarelo': amarelo,
            'vermelho': vermelho,
            'total_manutencoes': total_manutencoes,
            'manutencoes_por_tipo': manutencoes_por_tipo,
            'media_dias_manutencao': round(dias_total / max(len(veiculos), 1), 1)
        }
    
    def get_alertas(self) -> Dict:
        """Retorna alertas categorizados"""
        veiculos = self.listar_veiculos()
        alertas = {
            'amarelo': [],
            'vermelho': []
        }
        
        for veiculo in veiculos:
            if veiculo['ultima_manutencao']:
                status = self.verificar_status(veiculo['placa'])
                if status['dias'] > 6:
                    alerta = {
                        'placa': veiculo['placa'],
                        'dias': status['dias'],
                        'ultima_manutencao': veiculo['ultima_manutencao'],
                        'ultimo_tipo': veiculo.get('ultimo_tipo', 'N/A'),
                        'mensagem': status['mensagem']
                    }
                    if status['dias'] <= 13:
                        alertas['amarelo'].append(alerta)
                    else:
                        alertas['vermelho'].append(alerta)
        
        return alertas
    