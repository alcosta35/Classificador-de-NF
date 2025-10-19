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
print("\n" + "="*70)
print("🚀 INICIANDO SISTEMA DE VALIDAÇÃO CFOP")
print("="*70 + "\n")

import subprocess
import sys
import time
from pyngrok import ngrok
from google.colab import userdata
import requests

# Limpar processos e cache antigos
print("🧹 Limpando processos antigos...")
get_ipython().system('killall ngrok 2>/dev/null || true')
get_ipython().system('fuser -k 8000/tcp 2>/dev/null || true')
get_ipython().system('rm -rf ~/.ngrok2')

# Configurar ngrok
try:
    ngrok_token = userdata.get('NGROK_AUTHTOKEN')
    ngrok.set_auth_token(ngrok_token)
    print("✅ ngrok configurado!\n")
except Exception as e:
    print(f"❌ Erro ao configurar ngrok: {e}")
    print("Certifique-se de ter adicionado NGROK_AUTHTOKEN nos secrets!\n")

# Mudar para diretório do projeto
os.chdir('/content/validador-cfop')

print("🚀 Iniciando servidor FastAPI...")

# Iniciar servidor FastAPI em background
processo = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Aguardar inicialização
print("⏳ Aguardando servidor inicializar (15 segundos)...")
time.sleep(15)

# Testar servidor local
print("🔍 Testando servidor local...")
try:
    test_response = requests.get("http://localhost:8000/status", timeout=5)
    print("✅ Servidor local está rodando!")
    print(f"   Status: {test_response.json()}\n")
except Exception as e:
    print(f"❌ Erro ao conectar com servidor local: {e}")
    print("   Verifique se os arquivos foram criados corretamente.\n")

# Criar túnel ngrok
print("🌐 Criando túnel público com ngrok...")
try:
    tunnel = ngrok.connect(8000)
    public_url = tunnel.public_url
    
    print("\n" + "="*70)
    print("✅ SISTEMA DE VALIDAÇÃO CFOP ESTÁ RODANDO!")
    print("="*70)
    print(f"\n🌐 URL Principal:")
    print(f"   {public_url}")
    print(f"\n📚 Documentação API (Swagger):")
    print(f"   {public_url}/docs")
    print(f"\n📤 Página de Upload:")
    print(f"   {public_url}/upload")
    print(f"\n🤖 Página de Análise IA:")
    print(f"   {public_url}/analise")
    print("\n" + "="*70)
    
    # Teste de conectividade pública
    print("\n🔍 Testando conexão pública...")
    try:
        response = requests.get(f"{public_url}/status", timeout=10)
        print(f"✅ Conexão pública OK!")
        print(f"   {response.json()}\n")
    except Exception as e:
        print(f"⚠️ Aviso: {e}\n")
    
    print("="*70)
    print("📋 COMO USAR:")
    print("="*70)
    print("""
1. Acesse a URL principal no seu navegador
2. Clique em "Upload de Arquivos"
3. Envie um ZIP contendo os 3 CSVs:
   - 202401_NFs_Cabecalho.csv
   - 202401_NFs_Itens.csv
   - CFOP.csv
4. Após o upload, vá para "Análise Inteligente"
5. Faça perguntas ao agente IA!

Exemplos de perguntas:
- Validar CFOP de todas as notas fiscais
- Mostrar apenas as notas com CFOP incorreto
- Analisar a nota fiscal número 3510129
- Gerar relatório completo de validação
    """)
    
    print("="*70)
    print("⚠️ IMPORTANTE:")
    print("="*70)
    print("""
- Mantenha esta célula RODANDO enquanto usar o sistema
- A URL do ngrok muda a cada execução
- Para parar: Runtime → Interrupt execution
- Sessão Colab expira após inatividade prolongada
    """)
    
    print("="*70)
    print("🔄 Sistema em execução... Aguardando requisições...")
    print("="*70 + "\n")
    
    # Manter o script rodando
    try:
        while True:
            time.sleep(60)
            # Verificar se servidor ainda está rodando
            if processo.poll() is not None:
                print("\n⚠️ Servidor parou inesperadamente!")
                break
    except KeyboardInterrupt:
        print("\n🛑 Sistema parado pelo usuário!")
        processo.terminate()
        ngrok.disconnect(public_url)
        print("✅ Encerrado com sucesso!")
        
except Exception as e:
    print(f"\n❌ ERRO ao criar túnel ngrok: {e}")
    print("\nPossíveis soluções:")
    print("1. Verifique se NGROK_AUTHTOKEN está correto nos secrets")
    print("2. Acesse https://dashboard.ngrok.com/ para obter um novo token")
    print("3. Tente executar esta célula novamente")
    if processo:
        processo.terminate()

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