\# ⚡ Guia Rápido - Sistema de Validação CFOP



Referência rápida para uso do sistema.



---



\## 🚀 Setup Rápido (Google Colab)

```python

\# 1. Clonar/Upload arquivos

%cd /content

!git clone https://github.com/seu-usuario/validador-cfop.git

%cd validador-cfop



\# 2. Instalar

!pip install -r requirements.txt pyngrok



\# 3. Configurar secrets (UI do Colab)

\# OPENAI\_API\_KEY + NGROK\_AUTHTOKEN



\# 4. Criar .env

from google.colab import userdata

with open('.env', 'w') as f:

&nbsp;   f.write(f"OPENAI\_API\_KEY={userdata.get('OPENAI\_API\_KEY')}\\n")



\# 5. Iniciar

import subprocess, sys, time

from pyngrok import ngrok

from google.colab import userdata



ngrok.set\_auth\_token(userdata.get('NGROK\_AUTHTOKEN'))

processo = subprocess.Popen(\[sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'])

time.sleep(15)

tunnel = ngrok.connect(8000)

print(f"🌐 URL: {tunnel.public\_url}")

```



---



\## 📋 Estrutura de Arquivos

```

validador-cfop/

├── main.py              # API FastAPI

├── agente\_cfop.py       # Agente IA

├── utils.py             # Utilitários

├── requirements.txt     # Dependências

├── .env                 # API keys

├── uploads/             # Arquivos enviados

└── temp\_csvs/           # CSVs processados

```



---



\## 🔗 Endpoints Principais



| Método | Endpoint | Descrição |

|--------|----------|-----------|

| GET | `/` | Página inicial |

| GET | `/upload` | Interface de upload |

| GET | `/analise` | Interface de análise IA |

| POST | `/processar\_upload/` | Upload do ZIP |

| POST | `/analisar/` | Análise com IA |

| GET | `/status` | Status da API |

| GET | `/docs` | Documentação Swagger |



---



\## 🤖 Perguntas Comuns ao Agente



\- `Validar CFOP de todas as notas fiscais`

\- `Mostrar apenas as notas com CFOP incorreto`

\- `Analisar a nota fiscal número 3510129`

\- `Gerar relatório completo de validação`



---



\*\*Pronto para validar! 🚀\*\*

