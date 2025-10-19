#!/bin/bash

# ============================================================================
# Script de Deploy Automatizado - Sistema de Validação CFOP
# Para uso no Google Colab ou ambiente Linux
# ============================================================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Funções auxiliares
print_header() {
    echo -e "\n${BOLD}${BLUE}========================================${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${BOLD}${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Verificar se está no Colab
check_colab() {
    if [ -d "/content" ]; then
        print_success "Ambiente Google Colab detectado"
        IS_COLAB=true
    else
        print_info "Ambiente local detectado"
        IS_COLAB=false
    fi
}

# Criar estrutura de diretórios
create_directories() {
    print_header "Criando Estrutura de Diretórios"
    
    PROJECT_DIR="validador-cfop"
    
    if [ "$IS_COLAB" = true ]; then
        cd /content
    fi
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    mkdir -p uploads
    mkdir -p temp_csvs
    mkdir -p static
    mkdir -p logs
    
    print_success "Diretórios criados"
    print_info "Diretório do projeto: $(pwd)"
}

# Instalar dependências
install_dependencies() {
    print_header "Instalando Dependências"
    
    if [ -f "requirements.txt" ]; then
        print_info "Instalando pacotes do requirements.txt..."
        pip install -q -r requirements.txt
        print_success "Dependências instaladas"
    else
        print_warning "requirements.txt não encontrado"
        print_info "Instalando dependências básicas..."
        
        pip install -q fastapi uvicorn[standard] python-multipart pyngrok python-dotenv
        pip install -q langchain langchain-openai openai
        pip install -q pandas numpy aiofiles
        
        print_success "Dependências básicas instaladas"
    fi
}

# Verificar arquivos necessários
check_required_files() {
    print_header "Verificando Arquivos Necessários"
    
    FILES=("main.py" "agente_cfop.py" "utils.py")
    MISSING=()
    
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file encontrado"
        else
            print_error "$file NÃO encontrado"
            MISSING+=("$file")
        fi
    done
    
    if [ ${#MISSING[@]} -gt 0 ]; then
        print_warning "Arquivos faltando: ${MISSING[*]}"
        print_warning "Faça upload dos arquivos antes de continuar"
        return 1
    fi
    
    return 0
}

# Configurar variáveis de ambiente
configure_env() {
    print_header "Configurando Variáveis de Ambiente"
    
    if [ "$IS_COLAB" = true ]; then
        print_info "No Google Colab, configure os secrets:"
        print_info "  - OPENAI_API_KEY"
        print_info "  - NGROK_AUTHTOKEN"
        
        # Tentar criar .env a partir dos secrets do Colab
        if python3 -c "from google.colab import userdata; print(userdata.get('OPENAI_API_KEY'))" 2>/dev/null; then
            python3 << EOF
from google.colab import userdata
with open('.env', 'w') as f:
    f.write(f"OPENAI_API_KEY={userdata.get('OPENAI_API_KEY')}\n")
print("✓ Arquivo .env criado")
EOF
            print_success "Variáveis de ambiente configuradas"
        else
            print_error "Secrets não configurados no Colab"
            return 1
        fi
    else
        if [ ! -f ".env" ]; then
            print_warning "Arquivo .env não encontrado"
            read -p "Digite sua OPENAI_API_KEY: " OPENAI_KEY
            echo "OPENAI_API_KEY=$OPENAI_KEY" > .env
            print_success "Arquivo .env criado"
        else
            print_success "Arquivo .env já existe"
        fi
    fi
}

# Limpar processos antigos
cleanup_processes() {
    print_header "Limpando Processos Antigos"
    
    # Matar processos uvicorn e ngrok
    pkill -f uvicorn 2>/dev/null || true
    pkill -f ngrok 2>/dev/null || true
    
    # Liberar porta 8000
    fuser -k 8000/tcp 2>/dev/null || true
    
    # Limpar cache ngrok
    rm -rf ~/.ngrok2 2>/dev/null || true
    
    print_success "Processos antigos encerrados"
}

# Iniciar servidor
start_server() {
    print_header "Iniciando Servidor FastAPI"
    
    # Iniciar em background
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
    SERVER_PID=$!
    
    print_info "Servidor iniciado (PID: $SERVER_PID)"
    print_info "Logs: logs/server.log"
    
    # Salvar PID
    echo $SERVER_PID > .server.pid
    
    # Aguardar e testar
    sleep 10
    if curl -s http://localhost:8000/status | grep -q "online"; then
        print_success "Servidor funcionando corretamente"
        return 0
    else
        print_error "Falha ao iniciar servidor"
        cat logs/server.log
        return 1
    fi
}

# Mostrar instruções
show_instructions() {
    print_header "Sistema Pronto!"
    
    echo -e "${BOLD}Como usar:${NC}"
    echo ""
    echo "1. Acesse a URL exibida acima"
    echo "2. Vá para 'Upload de Arquivos'"
    echo "3. Envie um ZIP com os 3 CSVs"
    echo "4. Vá para 'Análise Inteligente'"
    echo "5. Faça perguntas ao agente IA!"
    echo ""
}

# Função principal
main() {
    echo -e "${BOLD}${BLUE}"
    echo "========================================="
    echo "  Sistema de Validação CFOP - Deploy"
    echo "========================================="
    echo -e "${NC}\n"
    
    check_colab
    create_directories
    
    if ! check_required_files; then
        print_error "Deploy abortado: arquivos faltando"
        exit 1
    fi
    
    install_dependencies
    
    if ! configure_env; then
        print_error "Deploy abortado: falha na configuração"
        exit 1
    fi
    
    cleanup_processes
    
    if ! start_server; then
        print_error "Deploy abortado: falha ao iniciar servidor"
        exit 1
    fi
    
    show_instructions
    
    print_success "Deploy concluído com sucesso!"
}

# Executar
main "$@"