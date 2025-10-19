from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
from pathlib import Path
from agente_cfop import AgenteValidadorCFOP
from utils import extrair_zip, limpar_diretorio_temp

app = FastAPI(
    title="Sistema de Validação de CFOP - Notas Fiscais",
    description="API para análise e validação de CFOP em Notas Fiscais utilizando IA",
    version="1.0.0"
)

# Diretórios
UPLOAD_DIR = Path("uploads")
TEMP_DIR = Path("temp_csvs")
UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Inicializar agente
agente = None

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página inicial com menu de navegação"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de Validação CFOP - Notas Fiscais</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 50px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
            }
            h1 {
                color: #667eea;
                text-align: center;
                margin-bottom: 15px;
                font-size: 2.5em;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
            }
            .button-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-top: 30px;
            }
            .nav-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 40px 30px;
                border-radius: 15px;
                font-size: 1.2em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 15px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .nav-button:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }
            .icon {
                font-size: 3em;
            }
            .info-box {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-top: 30px;
                border-left: 4px solid #667eea;
            }
            .info-box h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .info-box ul {
                margin-left: 20px;
                color: #666;
            }
            .info-box li {
                margin: 8px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧾 Sistema de Validação CFOP</h1>
            <p class="subtitle">Análise Inteligente de Notas Fiscais</p>
            
            <div class="button-container">
                <a href="/upload" class="nav-button">
                    <span class="icon">📤</span>
                    <span>Upload de Arquivos</span>
                    <span style="font-size: 0.8em; font-weight: normal;">Enviar CSV de Notas Fiscais</span>
                </a>
                
                <a href="/analise" class="nav-button">
                    <span class="icon">🤖</span>
                    <span>Análise Inteligente</span>
                    <span style="font-size: 0.8em; font-weight: normal;">Validar CFOP com IA</span>
                </a>
            </div>
            
            <div class="info-box">
                <h3>📋 Arquivos Necessários:</h3>
                <ul>
                    <li><strong>202401_NFs_Cabecalho.csv</strong> - Dados de cabeçalho das NFs</li>
                    <li><strong>202401_NFs_Itens.csv</strong> - Itens detalhados das NFs</li>
                    <li><strong>CFOP.csv</strong> - Tabela de códigos CFOP</li>
                </ul>
                <p style="margin-top: 15px; color: #666;">
                    💡 <strong>Dica:</strong> Faça upload dos 3 arquivos em formato ZIP na primeira página.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Página de upload de arquivos"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload de Arquivos - CFOP</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                margin-bottom: 30px;
                text-align: center;
            }
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 15px;
                padding: 60px 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #f8f9fa;
            }
            .upload-area:hover {
                background: #e9ecef;
                border-color: #764ba2;
            }
            .upload-area.dragover {
                background: #dee2e6;
                border-color: #764ba2;
            }
            .upload-icon {
                font-size: 4em;
                margin-bottom: 20px;
            }
            input[type="file"] {
                display: none;
            }
            .file-info {
                margin-top: 20px;
                padding: 15px;
                background: #e7f3ff;
                border-radius: 10px;
                display: none;
            }
            .file-info.show {
                display: block;
            }
            .submit-btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1.2em;
                font-weight: bold;
                cursor: pointer;
                margin-top: 20px;
                transition: all 0.3s ease;
            }
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }
            .submit-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .back-btn {
                display: inline-block;
                padding: 10px 20px;
                background: #6c757d;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .back-btn:hover {
                background: #5a6268;
            }
            .response-area {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                display: none;
            }
            .response-area.show {
                display: block;
            }
            .success {
                color: #28a745;
            }
            .error {
                color: #dc3545;
            }
            .loading {
                display: none;
                text-align: center;
                margin-top: 20px;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">⬅️ Voltar</a>
            <h1>📤 Upload de Arquivos CSV</h1>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📦</div>
                    <h3>Arraste e solte o arquivo ZIP aqui</h3>
                    <p style="margin-top: 10px; color: #666;">ou clique para selecionar</p>
                    <input type="file" id="fileInput" name="zip_file" accept=".zip" required>
                </div>
                
                <div class="file-info" id="fileInfo">
                    <strong>Arquivo selecionado:</strong> <span id="fileName"></span>
                </div>
                
                <button type="submit" class="submit-btn" id="submitBtn" disabled>
                    Enviar Arquivos
                </button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px; color: #667eea;">Processando arquivos...</p>
            </div>
            
            <div class="response-area" id="responseArea"></div>
        </div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const fileInfo = document.getElementById('fileInfo');
            const fileName = document.getElementById('fileName');
            const submitBtn = document.getElementById('submitBtn');
            const uploadForm = document.getElementById('uploadForm');
            const loading = document.getElementById('loading');
            const responseArea = document.getElementById('responseArea');
            
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                fileInput.files = e.dataTransfer.files;
                updateFileInfo();
            });
            
            fileInput.addEventListener('change', updateFileInfo);
            
            function updateFileInfo() {
                if (fileInput.files.length > 0) {
                    fileName.textContent = fileInput.files[0].name;
                    fileInfo.classList.add('show');
                    submitBtn.disabled = false;
                }
            }
            
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                formData.append('zip_file', fileInput.files[0]);
                
                loading.classList.add('show');
                submitBtn.disabled = true;
                responseArea.classList.remove('show');
                
                try {
                    const response = await fetch('/processar_upload/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        responseArea.innerHTML = `
                            <h3 class="success">✅ Upload realizado com sucesso!</h3>
                            <p style="margin-top: 15px;"><strong>Mensagem:</strong> ${result.mensagem}</p>
                            <p style="margin-top: 10px;"><strong>Arquivos processados:</strong></p>
                            <ul style="margin-left: 20px; margin-top: 5px;">
                                ${result.arquivos.map(f => `<li>${f}</li>`).join('')}
                            </ul>
                            <p style="margin-top: 15px; padding: 15px; background: #d1ecf1; border-radius: 8px; color: #0c5460;">
                                💡 Agora você pode ir para a página de <a href="/analise" style="color: #004085; font-weight: bold;">Análise Inteligente</a> para validar os CFOP!
                            </p>
                        `;
                        responseArea.classList.add('show');
                    } else {
                        throw new Error(result.detail || 'Erro no upload');
                    }
                } catch (error) {
                    responseArea.innerHTML = `
                        <h3 class="error">❌ Erro no upload</h3>
                        <p style="margin-top: 15px;">${error.message}</p>
                    `;
                    responseArea.classList.add('show');
                    submitBtn.disabled = false;
                } finally {
                    loading.classList.remove('show');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/analise", response_class=HTMLResponse)
async def analise_page():
    """Página de análise com agente IA"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Análise Inteligente CFOP</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 50px auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                margin-bottom: 30px;
                text-align: center;
            }
            .back-btn {
                display: inline-block;
                padding: 10px 20px;
                background: #6c757d;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .back-btn:hover {
                background: #5a6268;
            }
            .chat-container {
                background: #f8f9fa;
                border-radius: 15px;
                padding: 20px;
                min-height: 400px;
                max-height: 500px;
                overflow-y: auto;
                margin-bottom: 20px;
            }
            .message {
                margin-bottom: 15px;
                padding: 15px;
                border-radius: 10px;
                max-width: 80%;
            }
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: auto;
                text-align: right;
            }
            .ai-message {
                background: white;
                color: #333;
                border: 1px solid #dee2e6;
            }
            .input-area {
                display: flex;
                gap: 10px;
            }
            #promptInput {
                flex: 1;
                padding: 15px;
                border: 2px solid #667eea;
                border-radius: 10px;
                font-size: 1em;
                font-family: inherit;
            }
            .send-btn {
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .send-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }
            .send-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .examples {
                background: #e7f3ff;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            .examples h3 {
                color: #667eea;
                margin-bottom: 15px;
            }
            .example-item {
                padding: 10px;
                margin: 8px 0;
                background: white;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                border-left: 3px solid #667eea;
            }
            .example-item:hover {
                background: #f8f9fa;
                transform: translateX(5px);
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">⬅️ Voltar</a>
            <h1>🤖 Análise Inteligente de CFOP</h1>
            
            <div class="chat-container" id="chatContainer">
                <div class="message ai-message">
                    <strong>🤖 Assistente CFOP:</strong><br><br>
                    Olá! Estou pronto para analisar as Notas Fiscais e validar os códigos CFOP. 
                    Você pode me fazer perguntas como:<br>
                    • Validar CFOP de todas as notas<br>
                    • Analisar nota específica<br>
                    • Gerar relatório de divergências<br>
                    • Explicar o CFOP inferido
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 10px; color: #667eea;">Processando...</p>
            </div>
            
            <div class="input-area">
                <input type="text" id="promptInput" placeholder="Digite sua pergunta ou comando..." />
                <button class="send-btn" id="sendBtn">Enviar</button>
            </div>
            
            <div class="examples">
                <h3>💡 Exemplos de comandos:</h3>
                <div class="example-item" onclick="setPrompt(this.textContent)">
                    Validar CFOP de todas as notas fiscais
                </div>
                <div class="example-item" onclick="setPrompt(this.textContent)">
                    Mostrar apenas as notas com CFOP incorreto
                </div>
                <div class="example-item" onclick="setPrompt(this.textContent)">
                    Analisar a nota fiscal número 3510129
                </div>
                <div class="example-item" onclick="setPrompt(this.textContent)">
                    Gerar relatório completo de validação
                </div>
                <div class="example-item" onclick="setPrompt(this.textContent)">
                    Quantas notas têm divergência de CFOP?
                </div>
            </div>
        </div>
        
        <script>
            const chatContainer = document.getElementById('chatContainer');
            const promptInput = document.getElementById('promptInput');
            const sendBtn = document.getElementById('sendBtn');
            const loading = document.getElementById('loading');
            
            function setPrompt(text) {
                promptInput.value = text.trim();
                promptInput.focus();
            }
            
            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
                messageDiv.innerHTML = isUser ? text : `<strong>🤖 Assistente:</strong><br><br>${text}`;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            async function sendMessage() {
                const prompt = promptInput.value.trim();
                if (!prompt) return;
                
                addMessage(prompt, true);
                promptInput.value = '';
                sendBtn.disabled = true;
                loading.classList.add('show');
                
                try {
                    const response = await fetch('/analisar/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ pergunta: prompt })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        addMessage(result.resposta.replace(/\n/g, '<br>'), false);
                    } else {
                        throw new Error(result.detail || 'Erro na análise');
                    }
                } catch (error) {
                    addMessage(`❌ Erro: ${error.message}`, false);
                } finally {
                    loading.classList.remove('show');
                    sendBtn.disabled = false;
                    promptInput.focus();
                }
            }
            
            sendBtn.addEventListener('click', sendMessage);
            promptInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/processar_upload/")
async def processar_upload(zip_file: UploadFile = File(...)):
    """Processa o upload do arquivo ZIP com os CSVs"""
    global agente
    
    try:
        # Limpar diretórios temporários
        limpar_diretorio_temp(TEMP_DIR)
        
        # Salvar arquivo ZIP
        zip_path = UPLOAD_DIR / zip_file.filename
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(zip_file.file, buffer)
        
        # Extrair arquivos
        arquivos_extraidos = extrair_zip(zip_path, TEMP_DIR)
        
        # Verificar arquivos necessários
        arquivos_necessarios = [
            "202401_NFs_Cabecalho.csv",
            "202401_NFs_Itens.csv",
            "CFOP.csv"
        ]
        
        arquivos_encontrados = [f.name for f in TEMP_DIR.glob("*.csv")]
        faltando = [f for f in arquivos_necessarios if f not in arquivos_encontrados]
        
        if faltando:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivos faltando no ZIP: {', '.join(faltando)}"
            )
        
        # Inicializar agente com os arquivos
        agente = AgenteValidadorCFOP(
            cabecalho_path=str(TEMP_DIR / "202401_NFs_Cabecalho.csv"),
            itens_path=str(TEMP_DIR / "202401_NFs_Itens.csv"),
            cfop_path=str(TEMP_DIR / "CFOP.csv")
        )
        
        return JSONResponse(content={
            "mensagem": "Arquivos processados com sucesso!",
            "arquivos": arquivos_encontrados,
            "status": "pronto_para_analise"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analisar/")
async def analisar(pergunta: str = Form(...)):
    """Endpoint para análise com agente IA"""
    global agente
    
    if agente is None:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo foi carregado. Faça upload dos arquivos primeiro."
        )
    
    try:
        resposta = agente.processar_pergunta(pergunta)
        return JSONResponse(content={"resposta": resposta})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status():
    """Verifica o status da aplicação"""
    return {
        "status": "online",
        "agente_inicializado": agente is not None,
        "mensagem": "API de Validação CFOP funcionando!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)