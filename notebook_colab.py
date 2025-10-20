# ============================================================================
# SISTEMA DE VALIDAÇÃO CFOP - GOOGLE COLAB
# Script completo para executar no Google Colab
# ============================================================================

# ----------------------------------------------------------------------------
# CÉLULA 1: Setup Inicial - Criar Arquivos do Projeto
# ----------------------------------------------------------------------------
print("="*70)
print("🧾 SISTEMA DE VALIDAÇÃO CFOP - CONFIGURAÇÃO INICIAL")
print("="*70)
print("\n📦 Criando estrutura de arquivos do projeto...\n")

import os
from pathlib import Path

# Criar diretório do projeto
project_dir = Path("/content/validador-cfop")
project_dir.mkdir(exist_ok=True)
os.chdir(project_dir)

# Criar diretórios necessários
for dir_name in ["uploads", "temp_csvs", "static"]:
    (project_dir / dir_name).mkdir(exist_ok=True)

print("✅ Estrutura de diretórios criada!")
print(f"📁 Diretório do projeto: {project_dir}\n")

# Instruções para próximo passo
print("="*70)
print("📋 PRÓXIMO PASSO:")
print("="*70)
print("""
Você precisa fazer upload dos seguintes arquivos para este diretório:
  1. main.py
  2. agente_cfop.py
  3. utils.py
  4. requirements.txt

Execute este código para fazer upload:
""")

print("""
from google.colab import files
import shutil

print("📤 Faça upload de: main.py")
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, '/content/validador-cfop/')

print("📤 Faça upload de: agente_cfop.py")
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, '/content/validador-cfop/')

print("📤 Faça upload de: utils.py")
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, '/content/validador-cfop/')

print("📤 Faça upload de: requirements.txt")
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, '/content/validador-cfop/')

print("\\n✅ Todos os arquivos foram enviados!")
""")

# ----------------------------------------------------------------------------
# CÉLULA 2: Instalação de Dependências
# ----------------------------------------------------------------------------
print("\n" + "="*70)
print("📦 INSTALANDO DEPENDÊNCIAS")
print("="*70 + "\n")

# Instalar pacotes necessários
get_ipython().system('pip install -q fastapi uvicorn[standard] python-multipart pyngrok python-dotenv')
get_ipython().system('pip install -q langchain langchain-openai openai')
get_ipython().system('pip install -q pandas numpy aiofiles')

print("\n✅ Dependências instaladas com sucesso!")

# Verificar instalação
print("\n📋 Verificando instalação:")
get_ipython().system('pip list | grep -E "fastapi|langchain|openai|pyngrok|pandas"')

# ----------------------------------------------------------------------------
# CÉLULA 3: Configurar Secrets e Criar .env
# ----------------------------------------------------------------------------
print("\n" + "="*70)
print("🔑 CONFIGURAÇÃO DE API KEYS")
print("="*70 + "\n")

print("""
⚠️ IMPORTANTE: Você precisa configurar 2 secrets no Google Colab:

1️⃣ OPENAI_API_KEY
   - Clique no ícone de chave (🔑) no painel lateral esquerdo
   - Clique em "+ Add new secret"
   - Nome: OPENAI_API_KEY
   - Valor: Sua chave OpenAI (começa com sk-...)
   - Ative "Notebook access"
   - Obter em: https://platform.openai.com/api-keys

2️⃣ NGROK_AUTHTOKEN
   - Adicione outro secret
   - Nome: NGROK_AUTHTOKEN
   - Valor: Seu token ngrok
   - Ative "Notebook access"
   - Obter em: https://dashboard.ngrok.com/get-started/your-authtoken

Após configurar os secrets, execute esta célula:
""")

try:
    from google.colab import userdata
    
    # Tentar obter as chaves
    openai_key = userdata.get('OPENAI_API_KEY')
    ngrok_token = userdata.get('NGROK_AUTHTOKEN')
    
    # Criar arquivo .env
    os.chdir('/content/validador-cfop')
    with open('.env', 'w') as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")
    
    print("\n✅ Secrets configurados com sucesso!")
    print("✅ Arquivo .env criado!\n")
    
    # Verificar (sem mostrar a chave completa)
    print(f"OPENAI_API_KEY: {'*' * 20}{openai_key[-8:] if len(openai_key) > 8 else '***'}")
    print(f"NGROK_AUTHTOKEN: {'*' * 20}{ngrok_token[-8:] if len(ngrok_token) > 8 else '***'}")
    
except Exception as e:
    print(f"\n❌ Erro ao obter secrets: {e}")
    print("\nCertifique-se de ter configurado os secrets corretamente no Colab!")

# ----------------------------------------------------------------------------
# CÉLULA 4: Iniciar Servidor FastAPI + ngrok
# ----------------------------------------------------------------------------
import subprocess
import sys
import time
from pyngrok import ngrok
from google.colab import userdata
import requests

# ============================================================================
# CONFIGURAÇÕES DE DEBUG
# ============================================================================
print("\n" + "="*70)
print("🔍 MODO DEBUG ATIVADO")
print("="*70)
print("Todos os logs serão exibidos no console")
print("="*70 + "\n")

# ============================================================================
# PASSO 1: Limpar processos antigos
# ============================================================================
print("🧹 Limpando processos antigos...")
!killall ngrok 2>/dev/null || true
!fuser -k 8000/tcp 2>/dev/null || true
!rm -rf ~/.ngrok2

# ============================================================================
# PASSO 2: Verificar arquivos necessários
# ============================================================================
print("\n📂 Verificando arquivos necessários...")
import os

arquivos_necessarios = ['main.py', 'agente_cfop.py', 'utils.py', '.env']
faltando = [f for f in arquivos_necessarios if not os.path.exists(f)]

if faltando:
    print(f"❌ Arquivos faltando: {', '.join(faltando)}")
    print("\n💡 Certifique-se de ter criado todos os arquivos com %%writefile")
    raise Exception("Arquivos necessários não encontrados")
else:
    print("✅ Todos os arquivos encontrados!")
    for arquivo in arquivos_necessarios:
        tamanho = os.path.getsize(arquivo)
        print(f"   - {arquivo}: {tamanho} bytes")

# ============================================================================
# PASSO 3: Verificar API Keys
# ============================================================================
print("\n🔑 Verificando API Keys...")

try:
    openai_key = userdata.get('OPENAI_API_KEY')
    print(f"   ✅ OPENAI_API_KEY: {openai_key[:8]}...{openai_key[-4:]}")
except Exception as e:
    print(f"   ❌ OPENAI_API_KEY não encontrada!")
    print(f"   Erro: {e}")
    raise

try:
    ngrok_token = userdata.get('NGROK_AUTHTOKEN')
    print(f"   ✅ NGROK_AUTHTOKEN: {ngrok_token[:8]}...{ngrok_token[-4:]}")
except Exception as e:
    print(f"   ❌ NGROK_AUTHTOKEN não encontrado!")
    print(f"   Erro: {e}")
    raise

# ============================================================================
# PASSO 4: Configurar ngrok
# ============================================================================
print("\n🔑 Configurando ngrok...")
try:
    ngrok.set_auth_token(ngrok_token)
    print("✅ ngrok configurado!")
except Exception as e:
    print(f"❌ Erro ao configurar ngrok: {e}")
    raise

# ============================================================================
# PASSO 5: Iniciar servidor FastAPI
# ============================================================================
print("\n🚀 Iniciando Sistema de Validação CFOP...")
print("   Logs do servidor aparecerão abaixo:")
print("="*70 + "\n")

# Iniciar com logs visíveis
processo = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--log-level', 'info'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,  # Redirecionar stderr para stdout
    universal_newlines=True,
    bufsize=1
)

# Aguardar inicialização e mostrar logs
print("⏳ Aguardando inicialização (10 segundos)...")
time.sleep(10)

# ============================================================================
# PASSO 6: Testar servidor local
# ============================================================================
print("\n🔍 Testando servidor local...")
try:
    test_response = requests.get("http://localhost:8000/status", timeout=5)
    print("✅ Servidor local OK!")
    print(f"   Resposta: {test_response.json()}")
except Exception as e:
    print(f"❌ Erro no servidor: {e}")
    print("\n💡 Verifique os logs acima para identificar o problema")
    processo.terminate()
    raise

# ============================================================================
# PASSO 7: Testar endpoint de debug
# ============================================================================
print("\n🔍 Testando endpoint de debug...")
try:
    debug_response = requests.get("http://localhost:8000/debug", timeout=5)
    print("✅ Debug endpoint OK!")
    print(f"   Info: {debug_response.json()}")
except Exception as e:
    print(f"⚠️ Debug endpoint não disponível: {e}")

# ============================================================================
# PASSO 8: Criar túnel ngrok público
# ============================================================================
print("\n🌐 Criando túnel público com ngrok...")
try:
    tunnel = ngrok.connect(8000)
    public_url = tunnel.public_url
    
    # Exibir informações
    print("\n" + "="*70)
    print("✅ SISTEMA DE VALIDAÇÃO CFOP ESTÁ RODANDO!")
    print("="*70)
    print(f"\n🌐 URL Principal:")
    print(f"   {public_url}")
    print(f"\n📚 Endpoints disponíveis:")
    print(f"   {public_url}/docs          - Documentação API (Swagger)")
    print(f"   {public_url}/upload        - Página de Upload")
    print(f"   {public_url}/analise       - Página de Análise IA")
    print(f"   {public_url}/status        - Status do sistema")
    print(f"   {public_url}/debug         - Informações de debug")
    print("\n" + "="*70)
    
    # Teste de conexão pública
    print("\n🔍 Testando conexão pública...")
    response = requests.get(f"{public_url}/status", timeout=10)
    print("✅ Teste de conexão pública: OK")
    print(f"   Status: {response.json()}")
    
    # Instruções
    print("\n" + "="*70)
    print("📋 INSTRUÇÕES DE USO:")
    print("="*70)
    print("""
1. Acesse a URL principal no seu navegador
2. Clique em "Upload de Arquivos"
3. Envie um ZIP contendo os 3 CSVs
4. Após o upload, vá para "Análise Inteligente"
5. Faça perguntas ao agente IA!

⚠️ PARA DEBUGAR:
- Todos os logs aparecem NESTA CÉLULA do Colab
- Ao fazer perguntas, você verá:
  * Pergunta recebida
  * Chamadas de ferramentas do agente
  * Respostas da OpenAI
  * Tempo de processamento
- Se algo der errado, o erro completo será exibido aqui
    """)
    
    print("="*70)
    print("🔄 Sistema em execução...")
    print("📊 Aguardando requisições (logs aparecerão abaixo)...")
    print("="*70 + "\n")
    
    # Função para ler logs do processo em tempo real
    def print_process_output():
        while True:
            output = processo.stdout.readline()
            if output:
                print(output.strip())
            else:
                break
    
    # Manter rodando e mostrar logs
    import threading
    log_thread = threading.Thread(target=print_process_output, daemon=True)
    log_thread.start()
    
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n🛑 Sistema parado pelo usuário!")
    processo.terminate()
    ngrok.disconnect(public_url)
    print("✅ Encerrado com sucesso!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    processo.terminate()
    raise

# ----------------------------------------------------------------------------
# CÉLULA 5: Verificar Status e Logs
# ----------------------------------------------------------------------------
print("\n" + "="*70)
print("📊 STATUS DO SISTEMA")
print("="*70 + "\n")

# Verificar processos
print("🔍 Processos em execução:")
get_ipython().system('ps aux | grep -E "uvicorn|ngrok" | grep -v grep')

print("\n📁 Arquivos no diretório:")
get_ipython().system('ls -lah /content/validador-cfop/')

print("\n🌐 Túneis ngrok ativos:")
try:
    from pyngrok import ngrok
    tunnels = ngrok.get_tunnels()
    if tunnels:
        for tunnel in tunnels:
            print(f"   {tunnel.public_url} → {tunnel.config['addr']}")
    else:
        print("   Nenhum túnel ativo")
except Exception as e:
    print(f"   Erro ao verificar túneis: {e}")

print("\n✅ Setup completo! Sistema pronto para uso.\n")