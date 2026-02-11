import pandas as pd
from datetime import datetime
from database_sqlite import DatabaseSQLite
import os

class GeradorRelatorios:
    def __init__(self):
        self.db = DatabaseSQLite()
    
    def gerar_relatorio_completo_sqlite(self):
        """Gera relatório completo em Excel com todas as informações"""
        dados = []
        
        for veiculo in self.db.listar_veiculos():
            status = self.db.verificar_status(veiculo['placa'])
            historico = self.db.buscar_historico(veiculo['placa'])
            
            dados.append({
                'Placa': veiculo['placa'],
                'Modelo': veiculo.get('modelo', 'N/A'),
                'Ano': veiculo.get('ano', 'N/A'),
                'Cor': veiculo.get('cor', 'N/A'),
                'Última Manutenção': veiculo.get('ultima_manutencao', 'Nunca'),
                'Dias sem Manutenção': status.get('dias', 'N/A'),
                'Status': status.get('cor', 'N/A').upper(),
                'Último Tipo': veiculo.get('ultimo_tipo', 'N/A'),
                'Total Manutenções': len(historico),
                'Data Cadastro': veiculo.get('data_cadastro', 'N/A'),
                'Observações': veiculo.get('observacoes', '')
            })
        
        df = pd.DataFrame(dados)
        
        # Criar pasta exports se não existir
        if not os.path.exists('exports'):
            os.makedirs('exports')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"exports/relatorio_completo_{timestamp}.xlsx"
        
        # Criar writer do Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Veículos', index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Veículos']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Adicionar sheet de estatísticas
            stats = self.db.get_estatisticas()
            df_stats = pd.DataFrame([
                ['Total de Veículos', stats['total_veiculos']],
                ['Veículos em Dia', stats['verde']],
                ['Veículos em Atenção', stats['amarelo']],
                ['Veículos Críticos', stats['vermelho']],
                ['Total de Manutenções', stats['total_manutencoes']],
                ['Média de Dias sem Manutenção', stats['media_dias_manutencao']]
            ], columns=['Indicador', 'Valor'])
            df_stats.to_excel(writer, sheet_name='Estatísticas', index=False)
        
        print(f"✅ Relatório completo gerado: {filename}")
        return filename
    
    def gerar_relatorio_historico_sqlite(self):
        """Gera relatório de histórico completo de manutenções"""
        historico = self.db.buscar_historico(limit=10000)
        
        if not historico:
            print("❌ Nenhum histórico encontrado!")
            return None
        
        dados = []
        for reg in historico:
            dados.append({
                'ID': reg['id'],
                'Placa': reg['placa'],
                'Data': reg['data_manutencao'],
                'Tipo': reg['tipo'],
                'Técnico': reg.get('tecnico', 'Sistema'),
                'Observações': reg.get('observacoes', '')
            })
        
        df = pd.DataFrame(dados)
        
        if not os.path.exists('exports'):
            os.makedirs('exports')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"exports/historico_manutencoes_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Histórico', index=False)
            
            worksheet = writer.sheets['Histórico']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        print(f"✅ Histórico gerado: {filename}")
        return filename
    
    def gerar_relatorio_alertas_sqlite(self):
        """Gera relatório apenas de veículos em alerta"""
        alertas = self.db.get_alertas()
        dados = []
        
        for alerta in alertas['amarelo']:
            dados.append({
                'Placa': alerta['placa'],
                'Dias sem Manutenção': alerta['dias'],
                'Nível': 'ATENÇÃO',
                'Último Tipo': alerta['ultimo_tipo'],
                'Última Data': alerta['ultima_manutencao'],
                'Prioridade': 'Média'
            })
        
        for alerta in alertas['vermelho']:
            dados.append({
                'Placa': alerta['placa'],
                'Dias sem Manutenção': alerta['dias'],
                'Nível': 'CRÍTICO',
                'Último Tipo': alerta['ultimo_tipo'],
                'Última Data': alerta['ultima_manutencao'],
                'Prioridade': 'Alta'
            })
        
        df = pd.DataFrame(dados)
        
        if not os.path.exists('exports'):
            os.makedirs('exports')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"exports/alertas_{timestamp}.xlsx"
        
        df.to_excel(filename, index=False)
        print(f"✅ Relatório de alertas gerado: {filename}")
        
        return filename
    
    def gerar_relatorio_por_tipo_sqlite(self):
        """Gera relatório agrupado por tipo de manutenção"""
        stats = self.db.get_estatisticas()
        
        dados = []
        for tipo, quantidade in stats['manutencoes_por_tipo'].items():
            percentual = (quantidade / stats['total_manutencoes'] * 100) if stats['total_manutencoes'] > 0 else 0
            dados.append({
                'Tipo de Manutenção': tipo,
                'Quantidade': quantidade,
                'Percentual': f"{percentual:.1f}%"
            })
        
        df = pd.DataFrame(dados)
        df = df.sort_values('Quantidade', ascending=False)
        
        if not os.path.exists('exports'):
            os.makedirs('exports')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"exports/por_tipo_{timestamp}.xlsx"
        
        df.to_excel(filename, index=False)
        print(f"✅ Relatório por tipo gerado: {filename}")
        
        return filename