#!/usr/bin/env python3
"""
Script de instalação automática do Sistema de Controle de Manutenção
"""

import os
import sys
import subprocess
import platform

def print_step(step):
    """Imprime passo da instalação"""
    print("\n" + "=" * 60)
    print(f"📦 {step}")
    print("=" * 60)

def install_dependencies():
    """Instala dependências Python"""
    print_step("Instalando dependências")
    
    dependencies = [
        'flask',
        'pandas',
        'openpyxl',
        'matplotlib',
        'seaborn',
        'numpy',
        'pyjwt',
        'schedule'
    ]
    
    for dep in dependencies:
        print(f"Instalando {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} instalado")
        except:
            print(f"❌ Erro ao instalar {dep}")
    
    print("✅ Dependências instaladas com sucesso!")

def create_project_structure():
    """Cria estrutura de pastas do projeto"""
    print_step("Criando estrutura de pastas")
    
    folders = [
        'templates',
        'exports',
        'backups',
        'logs'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 Criada pasta: {folder}")
    
    print("✅ Estrutura de pastas criada!")

def create_template_files():
    """Cria arquivos de template HTML básicos"""
    print_step("Criando templates HTML básicos")
    
    # Template login.html
    login_html = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Sistema de Manutenção</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 40px;
            width: 100%;
            max-width: 400px;
        }
        .login-header { text-align: center; margin-bottom: 30px; }
        .login-header h1 { color: #333; font-size: 2em; margin-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s;
        }
        button:hover { transform: scale(1.02); }
        .alert { padding: 12px; border-radius: 8px; margin-bottom: 20px; display: none; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info-text { margin-top: 20px; text-align: center; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🚗 Sistema de Manutenção</h1>
            <p>Faça login para acessar o sistema</p>
        </div>
        <div id="alert" class="alert"></div>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Usuário</label>
                <input type="text" id="username" name="username" placeholder="Digite seu usuário" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Senha</label>
                <input type="password" id="password" name="password" placeholder="Digite sua senha" required>
            </div>
            <button type="submit">Entrar</button>
        </form>
        <div class="info-text">
            <p>Usuário padrão: admin / admin123</p>
        </div>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const alert = document.getElementById('alert');
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                
                if (data.success) {
                    alert.className = 'alert alert-success';
                    alert.style.display = 'block';
                    alert.innerHTML = '✅ Login realizado! Redirecionando...';
                    setTimeout(() => window.location.href = '/dashboard', 1500);
                } else {
                    alert.className = 'alert alert-danger';
                    alert.style.display = 'block';
                    alert.innerHTML = '❌ Usuário ou senha inválidos!';
                }
            } catch (error) {
                alert.className = 'alert alert-danger';
                alert.style.display = 'block';
                alert.innerHTML = '❌ Erro ao conectar ao servidor!';
            }
        });
    </script>
</body>
</html>
"""
    
    with open('templates/login.html', 'w', encoding='utf-8') as f:
        f.write(login_html)
    
    # Template dashboard básico
    dashboard_html = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Sistema de Manutenção</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .navbar {
            background: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-links a {
            margin-left: 20px;
            text-decoration: none;
            color: #333;
            font-weight: 500;
            padding: 8px 15px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .nav-links a:hover { background: #667eea; color: white; }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .welcome-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .kpi-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .kpi-value { font-size: 2.5em; font-weight: bold; margin: 10px 0; }
        .kpi-label { color: #666; font-size: 0.9em; text-transform: uppercase; }
        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            color: white;
        }
        .status-verde { background: #00C851; }
        .status-amarelo { background: #ffbb33; color: black; }
        .status-vermelho { background: #ff4444; }
    </style>
</head>
<body>
    <div class="navbar">
        <h2>🚗 Sistema de Controle de Manutenção</h2>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/veiculos">Veículos</a>
            <a href="/manutencoes">Manutenções</a>
            <a href="/relatorios">Relatórios</a>
            <a href="/api/auth/logout" style="background: #ff4444; color: white;">Sair</a>
        </div>
    </div>
    
    <div class="container">
        <div class="welcome-card">
            <h1>📊 Dashboard</h1>
            <p>Bem-vindo, {{ usuario }}! Sistema instalado com sucesso!</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total de Veículos</div>
                <div class="kpi-value" id="total-veiculos">-</div>
            </div>
            <div class="kpi-card" style="background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);">
                <div class="kpi-label">Em Dia</div>
                <div class="kpi-value" id="total-verde">-</div>
            </div>
            <div class="kpi-card" style="background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);">
                <div class="kpi-label">Atenção</div>
                <div class="kpi-value" id="total-amarelo">-</div>
            </div>
            <div class="kpi-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white;">
                <div class="kpi-label">Crítico</div>
                <div class="kpi-value" id="total-vermelho">-</div>
            </div>
        </div>
        
        <div style="text-align: center; padding: 50px; background: white; border-radius: 15px;">
            <h2>✅ Sistema instalado com sucesso!</h2>
            <p style="margin-top: 20px; color: #666;">O dashboard completo com gráficos será carregado aqui.</p>
            <p style="margin-top: 10px;">Use o menu acima para navegar pelo sistema.</p>
        </div>
    </div>
    
    <script>
        function carregarDados() {
            $.get('/api/dashboard/dados', function(dados) {
                $('#total-veiculos').text(dados.kpis.total_veiculos || 0);
                $('#total-verde').text(dados.kpis.verdes || 0);
                $('#total-amarelo').text(dados.kpis.amarelos || 0);
                $('#total-vermelho').text(dados.kpis.vermelhos || 0);
            });
        }
        $(document).ready(carregarDados);
    </script>
</body>
</html>
"""
    
    with open('templates/dashboard_completo.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print("✅ Templates básicos criados!")

def main():
    """Função principal de instalação"""
    print("\n" + "=" * 60)
    print("🚗 SISTEMA DE CONTROLE DE MANUTENÇÃO")
    print("INSTALADOR AUTOMÁTICO")
    print("=" * 60)
    
    # Criar estrutura
    create_project_structure()
    
    # Instalar dependências
    install_dependencies()
    
    # Criar templates
    create_template_files()
    
    print("\n" + "=" * 60)
    print("✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Execute o sistema: python web_app_completo.py")
    print("2. Acesse: http://localhost:5000")
    print("3. Login: admin / admin123")
    print("\n📁 Estrutura criada:")
    print("   - templates/     (arquivos HTML)")
    print("   - exports/       (relatórios Excel)")
    print("   - backups/       (backups do sistema)")
    print("   - logs/          (logs do sistema)")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()