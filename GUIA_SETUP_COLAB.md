# 🧾 Sistema de Validação CFOP - Guia Google Colab



Guia completo para executar o Sistema de Validação de CFOP para Notas Fiscais no Google Colab.



---



## 📋 Passo 1: Preparar Arquivos do Projeto



Crie os arquivos do projeto em seu ambiente local ou repositório GitHub:



### Estrutura de Arquivos:

```

validador-cfop/

├── main.py

├── agente_cfop.py

├── utils.py

├── requirements.txt

└── .env (será criado no Colab)

```



**Opção A: Upload Manual**

```python

# Upload dos arquivos para o Colab

from google.colab import files

import os



# Criar diretório

!mkdir -p /content/validador-cfop

%cd /content/validador-cfop



# Fazer upload de cada arquivo

print("Faça upload de: main.py")

uploaded = files.upload()



print("Faça upload de: agente_cfop.py")

uploaded = files.upload()



print("Faça upload de: utils.py")

uploaded = files.upload()



print("Faça upload de: requirements.txt")

uploaded = files.upload()

```



**Opção B: Clonar do GitHub** (recomendado)

```python

# Se você hospedou no GitHub

!git clone https://github.com/seu-usuario/validador-cfop.git

%cd validador-cfop

!ls -la

```



---



## 📦 Passo 2: Instalar Dependências

```python

# Instalar todas as dependências

!pip install -q -r requirements.txt



# Instalar ferramentas adicionais para Colab

!pip install -q pyngrok uvicorn python-dotenv



# Verificar instalação

!pip list | grep -E "fastapi|langchain|openai|pyngrok"

```



---



## 🔑 Passo 3: Configurar API Keys



### 3.1 - Configurar OpenAI API Key



1. Clique no ícone de chave (🔑) no painel lateral esquerdo do Colab

2. Clique em "+ Add new secret"

3. **Nome:** `OPENAI_API_KEY`

4. **Valor:** Sua chave da OpenAI (começa com `sk-...`)

5. Ative "Notebook access"



**Obter chave OpenAI:**

- Acesse: https://platform.openai.com/api-keys

- Crie uma nova chave se necessário



### 3.2 - Configurar ngrok Token



1. Acesse: https://dashboard.ngrok.com/get-started/your-authtoken

2. Faça login ou crie conta gratuita

3. Copie seu authtoken

4. No Colab, adicione outro secret:

&nbsp;  - **Nome:** `NGROK_AUTHTOKEN`

&nbsp;  - **Valor:** Cole o token do ngrok

&nbsp;  - Ative "Notebook access"



### 3.3 - Criar arquivo .env

```python

from google.colab import userdata



# Criar arquivo .env

openai_key = userdata.get('OPENAI_API_KEY')



with open('.env', 'w') as f:

&nbsp;   f.write(f"OPENAI_API_KEY={openai_key}n")



print("✅ Arquivo .env criado!")

!cat .env

```



---



## 🚀 Passo 4: Iniciar o Servidor

```python

import subprocess

import sys

import time

from pyngrok import ngrok

from google.colab import userdata

import requests



# Limpar processos antigos

!killall ngrok 2>/dev/null || true

!fuser -k 8000/tcp 2>/dev/null || true

!rm -rf ~/.ngrok2



# Configurar ngrok

ngrok.set_auth_token(userdata.get('NGROK_AUTHTOKEN'))



print("🚀 Iniciando Sistema de Validação CFOP...")



# Iniciar servidor FastAPI

processo = subprocess.Popen(

&nbsp;   [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'],

&nbsp;   stdout=subprocess.PIPE,

&nbsp;   stderr=subprocess.PIPE

)



print("⏳ Aguardando inicialização (15 segundos)...")

time.sleep(15)



# Testar servidor local

try:

&nbsp;   test_response = requests.get("http://localhost:8000/", timeout=5)

&nbsp;   print("✅ Servidor local OK!")

except Exception as e:

&nbsp;   print(f"❌ Erro no servidor: {e}")

&nbsp;   raise



# Criar túnel ngrok

try:

&nbsp;   tunnel = ngrok.connect(8000)

&nbsp;   public_url = tunnel.public_url

&nbsp;   

&nbsp;   print("n" + "="*70)

&nbsp;   print("✅ SISTEMA DE VALIDAÇÃO CFOP RODANDO!")

&nbsp;   print("="*70)

&nbsp;   print(f"🔗 URL Principal: {public_url}")

&nbsp;   print(f"📚 Documentação API: {public_url}/docs")

&nbsp;   print(f"📤 Página de Upload: {public_url}/upload")

&nbsp;   print(f"🤖 Página de Análise: {public_url}/analise")

&nbsp;   print("="*70)

&nbsp;   

&nbsp;   # Teste público

&nbsp;   response = requests.get(f"{public_url}/", timeout=10)

&nbsp;   print(f"✅ Teste de conexão: OK")

&nbsp;   

&nbsp;   print("n⚠️ Mantenha esta célula rodando enquanto usar o sistema!")

&nbsp;   print("Para parar: Runtime → Interrupt executionn")

&nbsp;   

&nbsp;   # Manter rodando

&nbsp;   while True:

&nbsp;       time.sleep(60)

&nbsp;       

except KeyboardInterrupt:

&nbsp;   print("n🛑 Sistema parado pelo usuário!")

&nbsp;   processo.terminate()

except Exception as e:

&nbsp;   print(f"n❌ ERRO: {e}")

&nbsp;   processo.terminate()

&nbsp;   raise

```



---



## 📊 Passo 5: Preparar Dados CSV



Prepare um arquivo ZIP contendo os 3 arquivos CSV necessários:



### Arquivos obrigatórios:

1. **202401_NFs_Cabecalho.csv** - Dados de cabeçalho das Notas Fiscais

2. **202401_NFs_Itens.csv** - Itens detalhados das Notas Fiscais  

3. **CFOP.csv** - Tabela de códigos CFOP com descrição e aplicação



### Formato do ZIP:

```

dados_nf.zip

├── 202401_NFs_Cabecalho.csv

├── 202401_NFs_Itens.csv

└── CFOP.csv

```



**Criar ZIP localmente:**

```bash

# No Windows (PowerShell)

Compress-Archive -Path *.csv -DestinationPath dados_nf.zip



# No Linux/Mac

zip dados_nf.zip *.csv

```



---



## 🎯 Passo 6: Usar o Sistema



### Opção 1: Interface Web (Recomendado) 🌐



1. **Página Inicial**

&nbsp;  - Acesse a URL gerada no Passo 4

&nbsp;  - Escolha entre "Upload de Arquivos" ou "Análise Inteligente"



2. **Upload de Arquivos** 📤

&nbsp;  - Clique em "Upload de Arquivos"

&nbsp;  - Arraste o ZIP ou clique para selecionar

&nbsp;  - Aguarde o processamento

&nbsp;  - Veja confirmação dos arquivos carregados



3. **Análise Inteligente** 🤖

&nbsp;  - Após upload, vá para "Análise Inteligente"

&nbsp;  - Digite perguntas ou comandos no chat

&nbsp;  - Veja respostas em tempo real com validação de CFOP



### Opção 2: API Swagger 📚



1. Acesse: `{URL}/docs`

2. Teste os endpoints:

&nbsp;  - **POST /processar_upload/** - Upload do ZIP

&nbsp;  - **POST /analisar/** - Análise com IA

&nbsp;  - **GET /status** - Status do sistema



### Opção 3: Programaticamente 💻

```python

import requests



# URL gerada no Passo 4

API_URL = "https://seu-url-ngrok.ngrok-free.dev"



# Upload de arquivos

with open('dados_nf.zip', 'rb') as f:

&nbsp;   files = {'zip_file': f}

&nbsp;   response = requests.post(f"{API_URL}/processar_upload/", files=files)

&nbsp;   print(response.json())



# Fazer análise

data = {'pergunta': 'Validar CFOP de todas as notas fiscais'}

response = requests.post(f"{API_URL}/analisar/", data=data)

print(response.json()['resposta'])

```



---



## 💡 Exemplos de Perguntas/Comandos



### Validação Geral:

- "Validar CFOP de todas as notas fiscais"

- "Mostrar apenas as notas com CFOP incorreto"

- "Gerar relatório completo de validação"

- "Quantas notas têm divergência de CFOP?"



### Análise Específica:

- "Analisar a nota fiscal número 3510129"

- "Verificar CFOP da nota com chave 41240106267630001509550010035101291224888487"

- "Explicar por que o CFOP 2949 foi usado na nota 3510129"

- "Quais CFOPs são usados para operação interestadual de venda?"



### Consultas:

- "Listar todas as notas do estado PR"

- "Mostrar notas de devolução"

- "Quantas notas são de operação interna?"

- "Buscar CFOP 6403 na tabela"



---



## 🔧 Troubleshooting



### ❌ Erro: "OPENAI_API_KEY not found"

**Solução:**

1. Verifique se adicionou o secret no Colab

2. Execute novamente o Passo 3.3 para criar o .env

3. Reinicie o servidor (Passo 4)



### ❌ Erro: "ngrok authentication failed"

**Solução:**

1. Verifique o token em https://dashboard.ngrok.com/

2. Atualize o secret `NGROK_AUTHTOKEN`

3. Execute novamente o Passo 4



### ❌ Erro: "Arquivos faltando no ZIP"

**Solução:**

- Certifique-se que o ZIP contém EXATAMENTE:

&nbsp; - `202401_NFs_Cabecalho.csv`

&nbsp; - `202401_NFs_Itens.csv`

&nbsp; - `CFOP.csv`

- Nomes devem estar EXATOS (case-sensitive)



### ❌ Erro: "Nenhum arquivo foi carregado"

**Solução:**

1. Faça upload do ZIP primeiro (página Upload)

2. Depois acesse a página de Análise

3. Verifique em `/status` se o agente foi inicializado



### ❌ Servidor parou de responder

**Solução:**

- Execute novamente a célula do Passo 4

- Anote a nova URL gerada (muda a cada execução)



---



## 📊 Estrutura dos Dados



### Campos Críticos para Inferência de CFOP



#### Do Cabeçalho:

1. **NATUREZA DA OPERAÇÃO** - Determina se é entrada/saída

2. **UF EMITENTE** - Estado de origem

3. **UF DESTINATÁRIO** - Estado de destino

4. **DESTINO DA OPERAÇÃO** - Interno/Interestadual/Exterior

5. **CONSUMIDOR FINAL** - Sim ou Não

6. **INDICADOR IE DESTINATÁRIO** - Contribuinte/Não Contribuinte/Isento



---



## 🎓 Regras de Inferência CFOP



O sistema usa estas regras para validar:



### Primeiro Dígito:

- **1xxx** - Entrada dentro do estado

- **2xxx** - Entrada de outro estado

- **3xxx** - Entrada do exterior

- **5xxx** - Saída dentro do estado

- **6xxx** - Saída para outro estado

- **7xxx** - Saída para exterior



---



## ✅ Checklist de Sucesso



- [ ] Arquivos do projeto criados/clonados

- [ ] Dependências instaladas

- [ ] Secret `OPENAI_API_KEY` configurado

- [ ] Secret `NGROK_AUTHTOKEN` configurado

- [ ] Arquivo `.env` criado

- [ ] Servidor iniciado sem erros

- [ ] URL ngrok gerada e funcionando

- [ ] Interface web acessível

- [ ] ZIP com CSVs preparado

- [ ] Upload realizado com sucesso

- [ ] Análise funcionando



---



## 📝 Notas Importantes



- ⏰ **Sessão Colab expira após inatividade** - mantenha aba aberta

- 🔗 **URL ngrok muda a cada execução** - anote sempre

- 💾 **Dados são temporários** - não ficam salvos permanentemente

- 🔑 **API Keys são sensíveis** - nunca compartilhe

- 📊 **GPT-4 é pago** - monitore uso em platform.openai.com



---



**Desenvolvido com FastAPI + LangChain + OpenAI GPT-4**



*Sistema de Validação Inteligente de CFOP para Notas Fiscais*



Última atualização: Outubro 2025

