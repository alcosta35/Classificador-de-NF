"""
Testes automatizados para a API de Validação CFOP
Execute: python test_api.py
"""

import requests
import json
import time
from pathlib import Path

# Configuração
API_URL = "http://localhost:8000"  # Altere para sua URL ngrok se necessário
TIMEOUT = 30

class Colors:
    """Cores para output no terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

class TestAPI:
    """Classe para testes da API"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
    
    def test_status(self):
        """Testa endpoint de status"""
        print_header("Teste 1: Endpoint de Status")
        try:
            response = requests.get(f"{self.base_url}/status", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Status Code: {response.status_code}")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "online":
                    print_success("API está online")
                    self.passed += 1
                    return True
                else:
                    print_error("API retornou status inválido")
                    self.failed += 1
                    return False
            else:
                print_error(f"Status Code inesperado: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def test_home_page(self):
        """Testa página inicial"""
        print_header("Teste 2: Página Inicial")
        try:
            response = requests.get(f"{self.base_url}/", timeout=TIMEOUT)
            
            if response.status_code == 200:
                print_success(f"Status Code: {response.status_code}")
                
                # Verificar se é HTML
                if "text/html" in response.headers.get("content-type", ""):
                    print_success("Página HTML retornada")
                    
                    # Verificar conteúdo
                    if "Sistema de Validação CFOP" in response.text:
                        print_success("Conteúdo da página OK")
                        self.passed += 1
                        return True
                    else:
                        print_warning("Título da página não encontrado")
                        self.failed += 1
                        return False
                else:
                    print_error("Resposta não é HTML")
                    self.failed += 1
                    return False
            else:
                print_error(f"Status Code inesperado: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def test_upload_page(self):
        """Testa página de upload"""
        print_header("Teste 3: Página de Upload")
        try:
            response = requests.get(f"{self.base_url}/upload", timeout=TIMEOUT)
            
            if response.status_code == 200:
                print_success(f"Status Code: {response.status_code}")
                
                if "Upload de Arquivos" in response.text:
                    print_success("Página de upload OK")
                    self.passed += 1
                    return True
                else:
                    print_error("Conteúdo esperado não encontrado")
                    self.failed += 1
                    return False
            else:
                print_error(f"Status Code inesperado: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def test_analise_page(self):
        """Testa página de análise"""
        print_header("Teste 4: Página de Análise")
        try:
            response = requests.get(f"{self.base_url}/analise", timeout=TIMEOUT)
            
            if response.status_code == 200:
                print_success(f"Status Code: {response.status_code}")
                
                if "Análise Inteligente" in response.text:
                    print_success("Página de análise OK")
                    self.passed += 1
                    return True
                else:
                    print_error("Conteúdo esperado não encontrado")
                    self.failed += 1
                    return False
            else:
                print_error(f"Status Code inesperado: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def test_swagger_docs(self):
        """Testa documentação Swagger"""
        print_header("Teste 5: Documentação Swagger")
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=TIMEOUT)
            
            if response.status_code == 200:
                print_success(f"Status Code: {response.status_code}")
                print_success("Documentação Swagger acessível")
                self.passed += 1
                return True
            else:
                print_error(f"Status Code inesperado: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def test_upload_without_file(self):
        """Testa upload sem arquivo (deve falhar)"""
        print_header("Teste 6: Upload sem Arquivo (deve falhar)")
        try:
            response = requests.post(
                f"{self.base_url}/processar_upload/",
                timeout=TIMEOUT
            )
            
            # Esperamos um erro 422 (validação)
            if response.status_code == 422:
                print_success("Validação funcionando corretamente")
                print_info(f"Status Code: {response.status_code}")
                self.passed += 1
                return True
            else:
                print_warning(f"Status Code inesperado: {response.status_code}")
                print_warning("Era esperado status 422 (validação)")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def test_analise_without_data(self):
        """Testa análise sem dados carregados"""
        print_header("Teste 7: Análise sem Dados Carregados")
        try:
            response = requests.post(
                f"{self.base_url}/analisar/",
                data={"pergunta": "Teste"},
                timeout=TIMEOUT
            )
            
            # Pode retornar 400 (bad request) se não houver dados
            if response.status_code in [400, 422]:
                print_success("Validação de pré-requisitos funcionando")
                print_info(f"Status Code: {response.status_code}")
                
                data = response.json()
                print_info(f"Mensagem: {data.get('detail', 'N/A')}")
                self.passed += 1
                return True
            else:
                print_warning(f"Status Code inesperado: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"Erro de conexão: {e}")
            self.failed += 1
            return False
    
    def print_summary(self):
        """Imprime resumo dos testes"""
        print_header("Resumo dos Testes")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total de testes: {total}")
        print(f"{Colors.GREEN}Passou: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Falhou: {self.failed}{Colors.END}")
        print(f"Taxa de sucesso: {success_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Todos os testes passaram!{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Alguns testes falharam{Colors.END}")

def main():
    """Função principal"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print(" "*15 + "TESTE DA API CFOP")
    print("="*60)
    print(f"{Colors.END}")
    
    print_info(f"URL da API: {API_URL}")
    print_info(f"Timeout: {TIMEOUT}s\n")
    
    # Criar instância de teste
    tester = TestAPI(API_URL)
    
    # Executar testes
    tester.test_status()
    time.sleep(1)
    
    tester.test_home_page()
    time.sleep(1)
    
    tester.test_upload_page()
    time.sleep(1)
    
    tester.test_analise_page()
    time.sleep(1)
    
    tester.test_swagger_docs()
    time.sleep(1)
    
    tester.test_upload_without_file()
    time.sleep(1)
    
    tester.test_analise_without_data()
    time.sleep(1)
    
    # Resumo
    tester.print_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testes interrompidos pelo usuário{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Erro inesperado: {e}{Colors.END}")