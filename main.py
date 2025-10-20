from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import os
import zipfile
import shutil
import traceback
from agente_cfop import AgenteValidadorCFOP

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================================

app = FastAPI(title="Sistema de Validação CFOP")

# Variável global para o agente
agente_validador = None

# ============================================================================
# MODELO DE DADOS
# ============================================================================

class PerguntaRequest(BaseModel):
    pergunta: str

# ============================================================================
# FUNÇÃO PARA INICIALIZAR AGENTE
# ============================================================================

def inicializar_agente_se_possivel():
    """Verifica se os CSVs existem e inicializa o agente"""
    global agente_validador
    
    print("\n" + "="*70)
    print("🔍 VERIFICANDO SE PODE INICIALIZAR AGENTE")
    print("="*70)
    
    temp_dir = "temp_csvs"
    
    if not os.path.exists(temp_dir):
        print("❌ Diretório temp_csvs não existe")
        print("="*70 + "\n")
        return False
    
    # Procurar os 3 CSVs necessários
    csvs_encontrados = {
        'cabecalho': None,
        'itens': None,
        'cfop': None
    }
    
    arquivos_no_dir = os.listdir(temp_dir)
    print(f"📂 Arquivos no diretório: {arquivos_no_dir}")
    
    for filename in arquivos_no_dir:
        filepath = os.path.join(temp_dir, filename)
        filename_lower = filename.lower()
        
        if 'cabecalho' in filename_lower or 'cabeçalho' in filename_lower:
            csvs_encontrados['cabecalho'] = filepath
            print(f"   ✅ Cabeçalho: {filename}")
        elif 'itens' in filename_lower or 'item' in filename_lower:
            csvs_encontrados['itens'] = filepath
            print(f"   ✅ Itens: {filename}")
        elif 'cfop' in filename_lower:
            csvs_encontrados['cfop'] = filepath
            print(f"   ✅ CFOP: {filename}")
    
    # Verificar se encontrou todos
    missing = [k for k, v in csvs_encontrados.items() if v is None]
    
    if missing:
        print(f"❌ CSVs faltando: {', '.join(missing)}")
        print("="*70 + "\n")
        return False
    
    print("\n✅ Todos os CSVs encontrados:")
    for tipo, path in csvs_encontrados.items():
        tamanho = os.path.getsize(path)
        print(f"   - {tipo}: {os.path.basename(path)} ({tamanho:,} bytes)")
    
    # Tentar criar o agente
    try:
        print("\n🤖 Criando AgenteValidadorCFOP...")
        agente_validador = AgenteValidadorCFOP(
            cabecalho_path=csvs_encontrados['cabecalho'],
            itens_path=csvs_encontrados['itens'],
            cfop_path=csvs_encontrados['cfop']
        )
        print("✅ AGENTE INICIALIZADO COM SUCESSO!")
        print("="*70 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar agente: {e}")
        traceback.print_exc()
        print("="*70 + "\n")
        agente_validador = None
        return False

# ============================================================================
# EVENTO DE STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Executado quando a aplicação inicia"""
    print("\n" + "="*70)
    print("🚀 INICIANDO APLICAÇÃO FASTAPI")
    print("="*70)
    print(f"⏰ Timestamp: {datetime.now()}")
    print("="*70 + "\n")
    
    # Criar diretórios se não existirem
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("temp_csvs", exist_ok=True)
    print("✅ Diretórios criados/verificados")
    
    # Tentar inicializar agente automaticamente
    print("\n🔄 Tentando inicializar agente automaticamente...")
    inicializar_agente_se_possivel()

# ============================================================================
# COMPONENTE DE NAVEGAÇÃO (para reusar em todas as páginas)
# ============================================================================

NAV_BUTTONS = """
<div style="text-align: center; margin: 20px 0; padding: 15px; background: #f0f0f0; border-radius: 5px;">
    <a href="/" style="margin: 0 10px; color: #667eea; text-decoration: none; font-weight: bold;">🏠 Início</a>
    <a href="/upload" style="margin: 0 10px; color: #667eea; text-decoration: none; font-weight: bold;">📤 Upload</a>
    <a href="/analise" style="margin: 0 10px; color: #667eea; text-decoration: none; font-weight: bold;">🔍 Análise</a>
    <a href="/status" style="margin: 0 10px; color: #667eea; text-decoration: none; font-weight: bold;">📊 Status</a>
</div>
"""

# ============================================================================
# ENDPOINTS DE STATUS E DEBUG
# ============================================================================

@app.get("/")
def home():
    """Página inicial"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema de Validação CFOP</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
            h1 { text-align: center; margin-bottom: 30px; }
            .btn {
                display: block;
                width: 100%;
                padding: 15px;
                margin: 10px 0;
                background: white;
                color: #667eea;
                text-decoration: none;
                text-align: center;
                border-radius: 5px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            .btn:hover { transform: scale(1.05); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Sistema de Validação CFOP</h1>
            <a href="/upload" class="btn">📤 Upload de Arquivos CSV</a>
            <a href="/analise" class="btn">🔍 Análise Inteligente</a>
            <a href="/status" class="btn">📊 Status do Sistema</a>
            <a href="/docs" class="btn">📚 Documentação API</a>
        </div>
    </body>
    </html>
    """)

@app.get("/status")
def status():
    """Status do sistema"""
    temp_dir = "temp_csvs"
    csvs_disponiveis = []
    
    if os.path.exists(temp_dir):
        csvs_disponiveis = os.listdir(temp_dir)
    
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "agente_inicializado": agente_validador is not None,
        "csvs_disponiveis": csvs_disponiveis,
        "diretorios": {
            "uploads": os.path.exists("uploads"),
            "temp_csvs": os.path.exists("temp_csvs")
        }
    }

@app.get("/debug")
def debug():
    """Informações detalhadas para debug"""
    return {
        "agente": {
            "inicializado": agente_validador is not None,
            "tipo": str(type(agente_validador)) if agente_validador else None
        },
        "arquivos": {
            "uploads": os.listdir("uploads") if os.path.exists("uploads") else [],
            "temp_csvs": os.listdir("temp_csvs") if os.path.exists("temp_csvs") else []
        },
        "ambiente": {
            "openai_key_configurada": bool(os.getenv("OPENAI_API_KEY")),
            "cwd": os.getcwd()
        }
    }

# ============================================================================
# ENDPOINT PARA FORÇAR REINICIALIZAÇÃO
# ============================================================================

@app.post("/inicializar_agente/")
def inicializar_agente():
    """Força a reinicialização do agente"""
    print("\n📍 Requisição para inicializar/reinicializar agente")
    
    sucesso = inicializar_agente_se_possivel()
    
    if sucesso:
        return {
            "status": "success",
            "message": "Agente inicializado com sucesso!",
            "agente_pronto": True
        }
    else:
        return {
            "status": "error",
            "message": "Não foi possível inicializar o agente. Verifique se os 3 CSVs foram carregados.",
            "agente_pronto": False
        }

# ============================================================================
# PÁGINA DE UPLOAD
# ============================================================================

@app.get("/upload")
def upload_page():
    """Página de upload"""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload de Arquivos CSV</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #667eea; text-align: center; }}
            .upload-area {{
                border: 3px dashed #667eea;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .upload-area:hover {{
                background: #f0f0f0;
                border-color: #764ba2;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                margin-top: 20px;
            }}
            .btn:hover {{ opacity: 0.9; }}
            #resultado {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .file-selected {{
                background: #e7f3ff;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {NAV_BUTTONS}
            
            <h1>📦 Upload de Arquivos CSV</h1>
            
            <p style="text-align: center; color: #666;">
                Arraste e solte o arquivo ZIP aqui<br>
                ou clique para selecionar
            </p>
            
            <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                <div style="font-size: 48px;">📁</div>
                <p>Arraste e solte o arquivo ZIP aqui<br>ou clique para selecionar</p>
                <p style="font-size: 12px; color: #999;">
                    Arquivo selecionado: <span id="fileName">Nenhum</span>
                </p>
            </div>
            
            <input type="file" id="fileInput" accept=".zip" style="display: none;" onchange="handleFileSelect(event)">
            
            <div id="fileSelected" class="file-selected" style="display: none;">
                ✅ Arquivo selecionado: <strong id="selectedFileName"></strong>
            </div>
            
            <button class="btn" onclick="enviarArquivo()">Enviar Arquivos</button>
            
            <div id="resultado"></div>
        </div>

        <script>
            let arquivoSelecionado = null;

            const uploadArea = document.getElementById('uploadArea');
            
            uploadArea.addEventListener('dragover', (e) => {{
                e.preventDefault();
                uploadArea.style.background = '#f0f0f0';
            }});
            
            uploadArea.addEventListener('dragleave', () => {{
                uploadArea.style.background = 'white';
            }});
            
            uploadArea.addEventListener('drop', (e) => {{
                e.preventDefault();
                uploadArea.style.background = 'white';
                const files = e.dataTransfer.files;
                if (files.length > 0) {{
                    arquivoSelecionado = files[0];
                    document.getElementById('fileName').textContent = files[0].name;
                    document.getElementById('selectedFileName').textContent = files[0].name;
                    document.getElementById('fileSelected').style.display = 'block';
                }}
            }});

            function handleFileSelect(event) {{
                arquivoSelecionado = event.target.files[0];
                if (arquivoSelecionado) {{
                    document.getElementById('fileName').textContent = arquivoSelecionado.name;
                    document.getElementById('selectedFileName').textContent = arquivoSelecionado.name;
                    document.getElementById('fileSelected').style.display = 'block';
                }}
            }}

            async function enviarArquivo() {{
                if (!arquivoSelecionado) {{
                    alert('Por favor, selecione um arquivo ZIP primeiro!');
                    return;
                }}

                const resultado = document.getElementById('resultado');
                resultado.innerHTML = '⏳ Enviando arquivo...';
                resultado.className = '';
                resultado.style.display = 'block';

                const formData = new FormData();
                formData.append('file', arquivoSelecionado);

                try {{
                    const response = await fetch('/processar_upload/', {{
                        method: 'POST',
                        body: formData
                    }});

                    const data = await response.json();

                    if (response.ok) {{
                        resultado.innerHTML = `
                            ✅ ${{data.message}}<br>
                            <strong>Agente inicializado:</strong> ${{data.agente_inicializado ? 'Sim' : 'Não'}}<br>
                            <strong>Arquivos extraídos:</strong> ${{data.arquivos_extraidos.join(', ')}}<br><br>
                            ${{data.agente_inicializado ? 
                                '<a href="/analise" style="color: #667eea; font-weight: bold;">→ Ir para Análise Inteligente</a>' : 
                                '⚠️ Agente não foi inicializado. Verifique se os 3 CSVs estão no ZIP.'}}
                        `;
                        resultado.className = 'success';
                    }} else {{
                        resultado.innerHTML = `❌ Erro: ${{data.detail}}`;
                        resultado.className = 'error';
                    }}
                }} catch (error) {{
                    resultado.innerHTML = `❌ Erro ao enviar arquivo: ${{error.message}}`;
                    resultado.className = 'error';
                }}
            }}
        </script>
    </body>
    </html>
    """)

# ============================================================================
# ENDPOINT DE UPLOAD
# ============================================================================

@app.post("/processar_upload/")
async def processar_upload(file: UploadFile = File(...)):
    """Processa o upload do arquivo ZIP com os CSVs"""
    print(f"\n{'='*70}")
    print(f"📦 RECEBENDO UPLOAD: {file.filename}")
    print(f"{'='*70}\n")
    
    try:
        # Validar tipo de arquivo
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Apenas arquivos ZIP são aceitos")
        
        # Salvar ZIP
        zip_path = os.path.join("uploads", file.filename)
        print(f"💾 Salvando ZIP em: {zip_path}")
        
        with open(zip_path, "wb") as f:
            conteudo = await file.read()
            f.write(conteudo)
        
        print(f"✅ ZIP salvo: {len(conteudo):,} bytes")
        
        # Preparar diretório de destino
        temp_dir = "temp_csvs"
        
        # Limpar diretório anterior
        if os.path.exists(temp_dir):
            print(f"🧹 Limpando diretório anterior: {temp_dir}")
            shutil.rmtree(temp_dir)
        
        os.makedirs(temp_dir)
        print(f"📁 Diretório criado: {temp_dir}")
        
        # Extrair ZIP
        print(f"📦 Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        arquivos_extraidos = os.listdir(temp_dir)
        print(f"✅ {len(arquivos_extraidos)} arquivos extraídos:")
        for arquivo in arquivos_extraidos:
            tamanho = os.path.getsize(os.path.join(temp_dir, arquivo))
            print(f"   - {arquivo} ({tamanho:,} bytes)")
        
        # Tentar inicializar agente
        print("\n🤖 Tentando inicializar agente...")
        agente_ok = inicializar_agente_se_possivel()
        
        return {
            "status": "success",
            "message": "Upload concluído e arquivos extraídos!",
            "agente_inicializado": agente_ok,
            "arquivos_extraidos": arquivos_extraidos
        }
        
    except zipfile.BadZipFile:
        print(f"❌ Arquivo ZIP inválido")
        raise HTTPException(status_code=400, detail="Arquivo ZIP inválido ou corrompido")
    except Exception as e:
        print(f"\n❌ ERRO no upload: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PÁGINA DE ANÁLISE
# ============================================================================

@app.get("/analise")
def analise_page():
    """Página de análise inteligente"""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Análise Inteligente CFOP</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #667eea; text-align: center; }}
            .chat-container {{
                height: 500px;
                border: 2px solid #667eea;
                border-radius: 10px;
                padding: 20px;
                overflow-y: auto;
                margin: 20px 0;
                background: #f9f9f9;
            }}
            .message {{
                margin: 10px 0;
                padding: 15px;
                border-radius: 10px;
                max-width: 80%;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            .user-message {{
                background: #667eea;
                color: white;
                margin-left: auto;
                text-align: right;
            }}
            .agent-message {{
                background: white;
                border: 1px solid #ddd;
            }}
            .input-area {{
                display: flex;
                gap: 10px;
            }}
            input[type="text"] {{
                flex: 1;
                padding: 15px;
                border: 2px solid #667eea;
                border-radius: 5px;
                font-size: 16px;
            }}
            button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{ opacity: 0.9; }}
            button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            .loading {{
                text-align: center;
                color: #999;
                font-style: italic;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                margin-bottom: 20px;
            }}
            .status-online {{
                background: #d4edda;
                color: #155724;
            }}
            .status-offline {{
                background: #f8d7da;
                color: #721c24;
            }}
            .examples {{
                background: #e7f3ff;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .examples h3 {{
                margin-top: 0;
                color: #667eea;
            }}
            .example-btn {{
                display: inline-block;
                margin: 5px;
                padding: 8px 15px;
                background: white;
                border: 1px solid #667eea;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                color: #667eea;
            }}
            .example-btn:hover {{
                background: #667eea;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {NAV_BUTTONS}
            
            <h1>🤖 Análise Inteligente de CFOP</h1>
            
            <div id="statusBadge"></div>
            
            <div class="examples">
                <h3>💡 Exemplos de perguntas:</h3>
                <div class="example-btn" onclick="usarExemplo('Quantas notas fiscais foram carregadas?')">
                    Quantas notas?
                </div>
                <div class="example-btn" onclick="usarExemplo('Mostre o quinto registro do cabeçalho de notas')">
                    Ver 5º registro
                </div>
                <div class="example-btn" onclick="usarExemplo('Liste as primeiras 3 notas do cabeçalho')">
                    Primeiras 3 notas
                </div>
                <div class="example-btn" onclick="usarExemplo('Valide todas as notas e me dê um resumo')">
                    Validar tudo
                </div>
                <div class="example-btn" onclick="usarExemplo('Explique o CFOP 5102')">
                    Explicar CFOP
                </div>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="loading">Carregando status do sistema...</div>
            </div>
            
            <div class="input-area">
                <input 
                    type="text" 
                    id="perguntaInput" 
                    placeholder="Digite sua pergunta sobre as notas fiscais..."
                    onkeypress="if(event.key==='Enter') enviarPergunta()"
                >
                <button onclick="enviarPergunta()" id="enviarBtn">Enviar</button>
            </div>
        </div>

        <script>
            let agenteInicializado = false;

            verificarStatus();

            async function verificarStatus() {{
                try {{
                    const response = await fetch('/status');
                    const data = await response.json();
                    
                    agenteInicializado = data.agente_inicializado;
                    
                    const badge = document.getElementById('statusBadge');
                    if (agenteInicializado) {{
                        badge.innerHTML = '<span class="status-badge status-online">✅ Agente pronto</span>';
                        document.getElementById('chatContainer').innerHTML = 
                            '<div class="agent-message message">👋 Olá! Estou pronto para analisar suas notas fiscais. Faça uma pergunta!</div>';
                    }} else {{
                        badge.innerHTML = '<span class="status-badge status-offline">❌ Agente não inicializado</span>';
                        document.getElementById('chatContainer').innerHTML = 
                            '<div class="agent-message message">⚠️ Agente não inicializado. Por favor, faça upload dos arquivos CSV primeiro.<br><a href="/upload">→ Ir para Upload</a></div>';
                        document.getElementById('enviarBtn').disabled = true;
                        document.getElementById('perguntaInput').disabled = true;
                    }}
                }} catch (error) {{
                    console.error('Erro ao verificar status:', error);
                }}
            }}

            function usarExemplo(texto) {{
                document.getElementById('perguntaInput').value = texto;
                enviarPergunta();
            }}

            async function enviarPergunta() {{
                const input = document.getElementById('perguntaInput');
                const pergunta = input.value.trim();
                
                if (!pergunta) {{
                    alert('Por favor, digite uma pergunta!');
                    return;
                }}

                if (!agenteInicializado) {{
                    alert('Agente não inicializado. Faça upload dos arquivos primeiro!');
                    return;
                }}

                adicionarMensagem(pergunta, 'user');
                input.value = '';
                
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading';
                loadingDiv.innerHTML = '🤔 Analisando...';
                loadingDiv.id = 'loading';
                document.getElementById('chatContainer').appendChild(loadingDiv);
                scrollToBottom();

                try {{
                    const response = await fetch('/analisar/', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ pergunta: pergunta }})
                    }});

                    document.getElementById('loading')?.remove();

                    if (response.ok) {{
                        const data = await response.json();
                        adicionarMensagem(data.resposta, 'agent');
                    }} else {{
                        const error = await response.json();
                        adicionarMensagem(`❌ Erro: ${{error.detail}}`, 'agent');
                    }}
                }} catch (error) {{
                    document.getElementById('loading')?.remove();
                    adicionarMensagem(`❌ Erro de conexão: ${{error.message}}`, 'agent');
                }}
            }}

            function adicionarMensagem(texto, tipo) {{
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{tipo}}-message`;
                messageDiv.textContent = texto;
                chatContainer.appendChild(messageDiv);
                scrollToBottom();
            }}

            function scrollToBottom() {{
                const container = document.getElementById('chatContainer');
                container.scrollTop = container.scrollHeight;
            }}
        </script>
    </body>
    </html>
    """)

# ============================================================================
# ENDPOINT DE ANÁLISE
# ============================================================================

@app.post("/analisar/")
async def analisar(request: PerguntaRequest):
    """Processa perguntas através do agente IA"""
    global agente_validador
    
    print(f"\n{'='*70}")
    print(f"📥 REQUEST: POST /analisar/")
    print(f"Detalhes: Pergunta: {request.pergunta}")
    print(f"{'='*70}\n")
    
    print(f"📨 Pergunta recebida: {request.pergunta}")
    print(f"🤖 Agente inicializado: {agente_validador is not None}")
    
    if agente_validador is None:
        print("❌ Agente não inicializado!")
        raise HTTPException(
            status_code=400,
            detail="Agente não inicializado. Faça upload dos arquivos primeiro!"
        )
    
    try:
        print("🔄 Processando pergunta com o agente...")
        resposta = agente_validador.processar_pergunta(request.pergunta)
        print(f"✅ Resposta gerada ({len(resposta)} caracteres)")
        print(f"Prévia: {resposta[:200]}...")
        
        return {"resposta": resposta}
        
    except Exception as e:
        print(f"❌ Erro ao processar: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
