import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import base64
from io import BytesIO
import numpy as np

class DashboardGenerator:
    def __init__(self, db_path='manutencao.db'):
        self.db_path = db_path
    
    def gerar_dados_dashboard(self):
        """Gera todos os dados necessários para o dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Dados de veículos
        df_veiculos = pd.read_sql_query('SELECT * FROM veiculos', conn)
        
        # Dados de manutenções
        df_manutencoes = pd.read_sql_query('''
            SELECT * FROM manutencoes 
            ORDER BY data_manutencao DESC
        ''', conn)
        
        conn.close()
        
        # Processar dados
        dados = {
            'kpis': self.calcular_kpis(df_veiculos, df_manutencoes),
            'tendencias': self.analisar_tendencias(df_manutencoes),
            'previsoes': self.gerar_previsoes(df_manutencoes),
            'ranking': self.ranking_veiculos(df_veiculos, df_manutencoes),
            'alertas': self.alertas_dashboard(df_veiculos)
        }
        
        return dados
    
    def calcular_kpis(self, df_veiculos, df_manutencoes):
        """Calcula KPIs principais"""
        hoje = datetime.now()
        
        # Total de veículos
        total_veiculos = len(df_veiculos)
        
        # Veículos com manutenção em dia
        veiculos_com_manutencao = df_veiculos[df_veiculos['ultima_manutencao'].notna()]
        dias_atraso = []
        
        for _, row in veiculos_com_manutencao.iterrows():
            try:
                ultima = datetime.strptime(row['ultima_manutencao'], '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    ultima = datetime.strptime(row['ultima_manutencao'], '%Y-%m-%d %H:%M:%S')
                except:
                    continue
            dias = (hoje - ultima).days
            dias_atraso.append(dias)
        
        if len(dias_atraso) > 0:
            df_veiculos.loc[veiculos_com_manutencao.index, 'dias_atraso'] = dias_atraso
            verdes = len([d for d in dias_atraso if d <= 6])
            amarelos = len([d for d in dias_atraso if 6 < d <= 13])
            vermelhos = len([d for d in dias_atraso if d > 13])
            media_dias = sum(dias_atraso) / len(dias_atraso)
        else:
            verdes = amarelos = vermelhos = 0
            media_dias = 0
        
        # Taxa de conformidade
        taxa_conformidade = (verdes / total_veiculos * 100) if total_veiculos > 0 else 0
        
        # Total de manutenções no mês
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        if len(df_manutencoes) > 0:
            df_manutencoes['data'] = pd.to_datetime(df_manutencoes['data_manutencao'], errors='coerce')
            manutencoes_mes = len(df_manutencoes[
                (df_manutencoes['data'].dt.month == mes_atual) & 
                (df_manutencoes['data'].dt.year == ano_atual)
            ])
        else:
            manutencoes_mes = 0
        
        return {
            'total_veiculos': total_veiculos,
            'verdes': verdes,
            'amarelos': amarelos,
            'vermelhos': vermelhos,
            'taxa_conformidade': round(taxa_conformidade, 1),
            'media_dias': round(media_dias, 1),
            'manutencoes_mes': manutencoes_mes,
            'total_manutencoes': len(df_manutencoes)
        }
    
    def analisar_tendencias(self, df_manutencoes):
        """Analisa tendências de manutenção"""
        if len(df_manutencoes) == 0:
            return {}
        
        df = df_manutencoes.copy()
        df['data'] = pd.to_datetime(df['data_manutencao'], errors='coerce')
        df['mes_ano'] = df['data'].dt.strftime('%Y-%m')
        
        # Manutenções por mês
        tendencia_mensal = df.groupby('mes_ano').size().to_dict()
        
        # Tipos mais comuns
        tipos_comuns = df.groupby('tipo').size().sort_values(ascending=False).head(5).to_dict()
        
        return {
            'tendencia_mensal': tendencia_mensal,
            'tipos_comuns': tipos_comuns
        }
    
    def gerar_previsoes(self, df_manutencoes):
        """Gera previsões simples baseadas em histórico"""
        if len(df_manutencoes) < 7:
            return {'mensagem': 'Dados insuficientes para previsões'}
        
        df = df_manutencoes.copy()
        df['data'] = pd.to_datetime(df['data_manutencao'], errors='coerce')
        df['dia'] = df['data'].dt.date
        
        # Média móvel de manutenções por dia
        manutencoes_por_dia = df.groupby('dia').size()
        
        if len(manutencoes_por_dia) > 0:
            media_movel = manutencoes_por_dia.rolling(window=7, min_periods=1).mean()
            tendencia = media_movel.iloc[-1] if len(media_movel) > 0 else 0
            previsao_proxima_semana = round(tendencia * 7)
        else:
            previsao_proxima_semana = 0
        
        return {
            'previsao_proxima_semana': previsao_proxima_semana,
            'media_diaria': round(df.groupby('dia').size().mean(), 1)
        }
    
    def ranking_veiculos(self, df_veiculos, df_manutencoes):
        """Ranking de veículos por manutenção"""
        ranking = []
        
        for _, veiculo in df_veiculos.iterrows():
            manutencoes_veiculo = df_manutencoes[df_manutencoes['placa'] == veiculo['placa']]
            
            ranking.append({
                'placa': veiculo['placa'],
                'total_manutencoes': len(manutencoes_veiculo),
                'ultima_manutencao': veiculo.get('ultima_manutencao', 'Nunca'),
                'modelo': veiculo.get('modelo', 'N/A')
            })
        
        # Ordenar por total de manutenções
        ranking.sort(key=lambda x: x['total_manutencoes'], reverse=True)
        
        return ranking[:10]  # Top 10
    
    def alertas_dashboard(self, df_veiculos):
        """Gera alertas para o dashboard"""
        hoje = datetime.now()
        alertas = []
        
        for _, veiculo in df_veiculos.iterrows():
            if veiculo['ultima_manutencao']:
                try:
                    ultima = datetime.strptime(veiculo['ultima_manutencao'], '%Y-%m-%d %H:%M:%S.%f')
                except:
                    try:
                        ultima = datetime.strptime(veiculo['ultima_manutencao'], '%Y-%m-%d %H:%M:%S')
                    except:
                        continue
                dias = (hoje - ultima).days
                
                if dias > 20:
                    alertas.append({
                        'placa': veiculo['placa'],
                        'dias': dias,
                        'tipo': 'CRÍTICO',
                        'mensagem': f'Veículo {veiculo["placa"]} está há {dias} dias sem manutenção!'
                    })
                elif dias > 13:
                    alertas.append({
                        'placa': veiculo['placa'],
                        'dias': dias,
                        'tipo': 'URGENTE',
                        'mensagem': f'Veículo {veiculo["placa"]} precisa de manutenção URGENTE!'
                    })
        
        return sorted(alertas, key=lambda x: x['dias'], reverse=True)[:5]
    
    def gerar_graficos_base64(self):
        """Gera gráficos em base64 para o dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Gráfico de status
        df_veiculos = pd.read_sql_query('SELECT * FROM veiculos', conn)
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.patch.set_facecolor('#f8f9fa')
        
        # Gráfico 1: Status dos veículos
        ax1 = axes[0, 0]
        status_counts = self._get_status_counts(df_veiculos)
        if sum(status_counts.values()) > 0:
            colors = ['#00C851', '#ffbb33', '#ff4444']
            wedges, texts, autotexts = ax1.pie(
                status_counts.values(), 
                labels=status_counts.keys(), 
                colors=colors, 
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 12, 'fontweight': 'bold'}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        ax1.set_title('Status dos Veículos', fontsize=14, fontweight='bold')
        
        # Gráfico 2: Manutenções por tipo
        ax2 = axes[0, 1]
        df_manutencoes = pd.read_sql_query('''
            SELECT tipo, COUNT(*) as quantidade 
            FROM manutencoes 
            GROUP BY tipo 
            ORDER BY quantidade DESC 
            LIMIT 5
        ''', conn)
        
        if len(df_manutencoes) > 0:
            bars = ax2.barh(df_manutencoes['tipo'], df_manutencoes['quantidade'], 
                          color='#667eea')
            ax2.set_title('Top 5 Tipos de Manutenção', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Quantidade')
            for bar in bars:
                width = bar.get_width()
                ax2.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                        f'{int(width)}', ha='left', va='center', fontweight='bold')
        
        # Gráfico 3: Tendência mensal
        ax3 = axes[1, 0]
        df_manutencoes_mensal = pd.read_sql_query('''
            SELECT strftime('%Y-%m', data_manutencao) as mes,
                   COUNT(*) as total
            FROM manutencoes
            GROUP BY mes
            ORDER BY mes DESC
            LIMIT 6
        ''', conn)
        
        if len(df_manutencoes_mensal) > 0:
            df_manutencoes_mensal = df_manutencoes_mensal.iloc[::-1]
            ax3.plot(range(len(df_manutencoes_mensal)), df_manutencoes_mensal['total'], 
                    marker='o', linewidth=2, markersize=8, color='#764ba2')
            ax3.set_title('Tendência de Manutenções', fontsize=14, fontweight='bold')
            ax3.set_xticks(range(len(df_manutencoes_mensal)))
            ax3.set_xticklabels(df_manutencoes_mensal['mes'], rotation=45)
            ax3.grid(True, alpha=0.3)
            ax3.set_ylabel('Quantidade')
        
        # Gráfico 4: Dias sem manutenção
        ax4 = axes[1, 1]
        dias_sem_manutencao = self._get_dias_sem_manutencao(df_veiculos)
        
        if dias_sem_manutencao:
            ax4.hist(dias_sem_manutencao, bins=15, color='#ff6b6b', edgecolor='white', alpha=0.7)
            ax4.set_title('Distribuição de Dias sem Manutenção', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Dias')
            ax4.set_ylabel('Quantidade de Veículos')
            ax4.axvline(x=7, color='#ffbb33', linestyle='--', linewidth=2, label='Alerta (7 dias)')
            ax4.axvline(x=14, color='#ff4444', linestyle='--', linewidth=2, label='Crítico (14 dias)')
            ax4.legend()
        
        plt.tight_layout()
        
        # Converter para base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='#f8f9fa')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        grafico_base64 = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        conn.close()
        
        return {'dashboard_grafico': grafico_base64}
    
    def _get_status_counts(self, df_veiculos):
        """Conta veículos por status"""
        hoje = datetime.now()
        verde = amarelo = vermelho = 0
        
        for _, row in df_veiculos.iterrows():
            if row['ultima_manutencao']:
                try:
                    ultima = datetime.strptime(row['ultima_manutencao'], '%Y-%m-%d %H:%M:%S.%f')
                except:
                    try:
                        ultima = datetime.strptime(row['ultima_manutencao'], '%Y-%m-%d %H:%M:%S')
                    except:
                        continue
                dias = (hoje - ultima).days
                
                if dias <= 6:
                    verde += 1
                elif dias <= 13:
                    amarelo += 1
                else:
                    vermelho += 1
        
        return {'Em dia': verde, 'Atenção': amarelo, 'Crítico': vermelho}
    
    def _get_dias_sem_manutencao(self, df_veiculos):
        """Retorna lista de dias sem manutenção"""
        hoje = datetime.now()
        dias_lista = []
        
        for _, row in df_veiculos.iterrows():
            if row['ultima_manutencao']:
                try:
                    ultima = datetime.strptime(row['ultima_manutencao'], '%Y-%m-%d %H:%M:%S.%f')
                except:
                    try:
                        ultima = datetime.strptime(row['ultima_manutencao'], '%Y-%m-%d %H:%M:%S')
                    except:
                        continue
                dias = (hoje - ultima).days
                dias_lista.append(dias)
        
        return dias_lista