\# 🚀 Exemplos de Uso da API - Sistema de Validação CFOP



Este documento contém exemplos práticos de como usar a API de Validação CFOP.



---



\## Exemplos com Python



\### 1. Verificar Status da API

```python

import requests



API\_URL = "http://localhost:8000"



def verificar\_status():

&nbsp;   """Verifica se a API está online"""

&nbsp;   response = requests.get(f"{API\_URL}/status")

&nbsp;   

&nbsp;   if response.status\_code == 200:

&nbsp;       data = response.json()

&nbsp;       print(f"✅ API Status: {data\['status']}")

&nbsp;       print(f"Agente inicializado: {data\['agente\_inicializado']}")

&nbsp;       return True

&nbsp;   else:

&nbsp;       print(f"❌ Erro: {response.status\_code}")

&nbsp;       return False



verificar\_status()

```



---



\### 2. Upload de Arquivo ZIP

```python

import requests



def fazer\_upload(zip\_path):

&nbsp;   """Faz upload do arquivo ZIP com os CSVs"""

&nbsp;   

&nbsp;   with open(zip\_path, 'rb') as f:

&nbsp;       files = {'zip\_file': f}

&nbsp;       

&nbsp;       response = requests.post(

&nbsp;           f"{API\_URL}/processar\_upload/",

&nbsp;           files=files,

&nbsp;           timeout=60

&nbsp;       )

&nbsp;   

&nbsp;   if response.status\_code == 200:

&nbsp;       data = response.json()

&nbsp;       print(f"✅ Upload bem-sucedido!")

&nbsp;       print(f"Mensagem: {data\['mensagem']}")

&nbsp;       print(f"Arquivos processados:")

&nbsp;       for arquivo in data\['arquivos']:

&nbsp;           print(f"  - {arquivo}")

&nbsp;       return True

&nbsp;   else:

&nbsp;       print(f"❌ Erro no upload: {response.status\_code}")

&nbsp;       print(response.json())

&nbsp;       return False



fazer\_upload('dados\_nf.zip')

```



---



\### 3. Análise com Agente IA

```python

import requests



def fazer\_analise(pergunta):

&nbsp;   """Faz uma pergunta ao agente IA"""

&nbsp;   

&nbsp;   data = {'pergunta': pergunta}

&nbsp;   

&nbsp;   response = requests.post(

&nbsp;       f"{API\_URL}/analisar/",

&nbsp;       data=data,

&nbsp;       timeout=120

&nbsp;   )

&nbsp;   

&nbsp;   if response.status\_code == 200:

&nbsp;       resultado = response.json()

&nbsp;       print(f"\\n🤖 Resposta do Agente:\\n")

&nbsp;       print(resultado\['resposta'])

&nbsp;       return resultado\['resposta']

&nbsp;   else:

&nbsp;       print(f"❌ Erro: {response.status\_code}")

&nbsp;       print(response.json())

&nbsp;       return None



\# Exemplos de perguntas

fazer\_analise("Validar CFOP de todas as notas fiscais")

fazer\_analise("Mostrar apenas as notas com CFOP incorreto")

fazer\_analise("Analisar a nota fiscal número 3510129")

```



---



\### 4. Workflow Completo

```python

import requests

import time



class ValidadorCFOP:

&nbsp;   """Cliente Python para API de Validação CFOP"""

&nbsp;   

&nbsp;   def \_\_init\_\_(self, api\_url):

&nbsp;       self.api\_url = api\_url

&nbsp;       self.session = requests.Session()

&nbsp;   

&nbsp;   def status(self):

&nbsp;       """Verifica status da API"""

&nbsp;       response = self.session.get(f"{self.api\_url}/status")

&nbsp;       return response.json()

&nbsp;   

&nbsp;   def upload(self, zip\_path):

&nbsp;       """Faz upload do ZIP"""

&nbsp;       with open(zip\_path, 'rb') as f:

&nbsp;           files = {'zip\_file': f}

&nbsp;           response = self.session.post(

&nbsp;               f"{self.api\_url}/processar\_upload/",

&nbsp;               files=files,

&nbsp;               timeout=60

&nbsp;           )

&nbsp;       return response.json()

&nbsp;   

&nbsp;   def analisar(self, pergunta):

&nbsp;       """Faz análise com IA"""

&nbsp;       data = {'pergunta': pergunta}

&nbsp;       response = self.session.post(

&nbsp;           f"{self.api\_url}/analisar/",

&nbsp;           data=data,

&nbsp;           timeout=120

&nbsp;       )

&nbsp;       return response.json()\['resposta']

&nbsp;   

&nbsp;   def workflow\_completo(self, zip\_path):

&nbsp;       """Executa workflow completo"""

&nbsp;       print("="\*60)

&nbsp;       print("WORKFLOW DE VALIDAÇÃO CFOP")

&nbsp;       print("="\*60)

&nbsp;       

&nbsp;       # 1. Verificar status

&nbsp;       print("\\n1. Verificando status...")

&nbsp;       status = self.status()

&nbsp;       print(f"   ✓ API: {status\['status']}")

&nbsp;       

&nbsp;       # 2. Upload

&nbsp;       print("\\n2. Fazendo upload dos dados...")

&nbsp;       resultado\_upload = self.upload(zip\_path)

&nbsp;       print(f"   ✓ {resultado\_upload\['mensagem']}")

&nbsp;       

&nbsp;       # 3. Aguardar processamento

&nbsp;       print("\\n3. Aguardando processamento...")

&nbsp;       time.sleep(2)

&nbsp;       

&nbsp;       # 4. Validação completa

&nbsp;       print("\\n4. Executando validação completa...")

&nbsp;       validacao = self.analisar("Validar CFOP de todas as notas fiscais")

&nbsp;       print(validacao)

&nbsp;       

&nbsp;       print("\\n" + "="\*60)

&nbsp;       print("WORKFLOW CONCLUÍDO")

&nbsp;       print("="\*60)



\# Usar

validador = ValidadorCFOP("http://localhost:8000")

validador.workflow\_completo('dados\_nf.zip')

```



---



\## Exemplos com cURL



\### 1. Verificar Status

```bash

curl -X GET "http://localhost:8000/status"

```



---



\### 2. Upload de Arquivo

```bash

curl -X POST "http://localhost:8000/processar\_upload/" \\

&nbsp; -F "zip\_file=@dados\_nf.zip"

```



---



\### 3. Fazer Análise

```bash

curl -X POST "http://localhost:8000/analisar/" \\

&nbsp; -F "pergunta=Validar CFOP de todas as notas fiscais"

```



---



\## 💡 Perguntas Frequentes ao Agente



\### Validação Geral

\- "Validar CFOP de todas as notas fiscais"

\- "Mostrar apenas as notas com CFOP incorreto"

\- "Gerar relatório completo de validação"

\- "Quantas notas têm divergência de CFOP?"



\### Análise Específica

\- "Analisar a nota fiscal número 3510129"

\- "Verificar CFOP da nota com chave 41240106267630001509550010035101291224888487"

\- "Explicar por que o CFOP 2949 foi usado na nota 3510129"



\### Consultas

\- "Listar todas as notas do estado PR"

\- "Mostrar notas de devolução"

\- "Quantas notas são de operação interna?"

\- "Buscar CFOP 6403 na tabela"



---



\*\*Desenvolvido com ❤️ para análise inteligente de CFOP\*\*



\*Última atualização: Outubro 2025\*

