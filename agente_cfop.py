import pandas as pd
import os
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from dotenv import load_dotenv
import traceback
import re
from typing import Optional

load_dotenv()

class AgenteValidadorCFOP:
    """Agente inteligente para validação de CFOP em Notas Fiscais"""
    
    def __init__(self, cabecalho_path: str, itens_path: str, cfop_path: str):
        """Inicializa o agente com os dados dos CSVs"""
        print("\n" + "="*70)
        print("🔧 INICIALIZANDO AGENTE VALIDADOR CFOP")
        print("="*70)
        
        # Carregar CSVs
        print(f"📂 Carregando: {cabecalho_path}")
        self.df_cabecalho = pd.read_csv(cabecalho_path)
        print(f"   ✅ {len(self.df_cabecalho)} registros de cabeçalho")
        
        print(f"📂 Carregando: {itens_path}")
        self.df_itens = pd.read_csv(itens_path)
        print(f"   ✅ {len(self.df_itens)} itens")
        
        print(f"📂 Carregando: {cfop_path}")
        self.df_cfop = pd.read_csv(cfop_path)
        print(f"   ✅ {len(self.df_cfop)} códigos CFOP")
        
        # Mostrar exemplos de CFOPs para debug
        print(f"   📋 Exemplos de CFOPs no arquivo:")
        for i, cfop in enumerate(self.df_cfop['CFOP'].head(5)):
            print(f"      {i+1}. '{cfop}'")
        
        # Mostrar colunas disponíveis
        print(f"   📋 Colunas do cabeçalho: {', '.join(self.df_cabecalho.columns.tolist()[:5])}...")
        
        # Verificar API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY não encontrada no .env!")
        print(f"🔑 API Key encontrada: {api_key[:8]}...{api_key[-4:]}")
        
        # Configurar LLM
        print("🤖 Configurando ChatOpenAI...")
        try:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0,
                openai_api_key=api_key,
                verbose=True
            )
            print("   ✅ LLM configurado com sucesso")
        except Exception as e:
            print(f"   ❌ Erro ao configurar LLM: {e}")
            raise
        
        # Criar ferramentas
        print("🛠️ Criando ferramentas...")
        self.tools = self._criar_ferramentas()
        print(f"   ✅ {len(self.tools)} ferramentas criadas")
        
        # Criar prompt
        print("📝 Criando prompt do agente...")
        self.prompt = self._criar_prompt()
        print("   ✅ Prompt criado")
        
        # Criar agente
        print("🤖 Criando agente executor...")
        try:
            self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                max_iterations=10,
                return_intermediate_steps=True,
                handle_parsing_errors=True
            )
            print("   ✅ Agente criado com sucesso!")
        except Exception as e:
            print(f"   ❌ Erro ao criar agente: {e}")
            traceback.print_exc()
            raise
        
        print("="*70)
        print("✅ AGENTE INICIALIZADO E PRONTO PARA USO!")
        print("="*70 + "\n")
    
    def _formatar_cfop_para_busca(self, cfop: str) -> str:
        """
        Formata o CFOP para o padrão usado no CSV.
        Se tiver 4 dígitos: X.YYY (exemplo: 5102 -> 5.102)
        Se tiver menos: sem ponto (exemplo: 1 -> 1, 51 -> 51)
        """
        # Remove espaços e pontos existentes
        cfop_limpo = str(cfop).strip().replace('.', '').replace(',', '')
        
        # Se tiver exatamente 4 dígitos, adiciona o ponto
        if len(cfop_limpo) == 4 and cfop_limpo.isdigit():
            cfop_formatado = f"{cfop_limpo[0]}.{cfop_limpo[1:]}"
            print(f"      🔧 Formatando CFOP: '{cfop}' -> '{cfop_formatado}'")
            return cfop_formatado
        
        # Caso contrário, retorna como está
        print(f"      🔧 CFOP sem formatação: '{cfop_limpo}'")
        return cfop_limpo
    
    def _explicar_primeiro_digito(self, digito: str) -> str:
        """Explica o significado do primeiro dígito do CFOP"""
        explicacoes = {
            '1': 'Entrada - Operação Interna',
            '2': 'Entrada - Operação Interestadual',
            '3': 'Entrada - Operação com Exterior',
            '5': 'Saída - Operação Interna',
            '6': 'Saída - Operação Interestadual',
            '7': 'Saída - Operação com Exterior'
        }
        return explicacoes.get(digito, 'Indefinido')
    
    def _criar_prompt(self):
        """Cria o prompt para o agente"""
        system_message = """Você é um especialista em análise e validação de CFOP (Código Fiscal de Operações e Prestações) de Notas Fiscais brasileiras.

Sua missão é:
1. Analisar notas fiscais e seus itens
2. Inferir o CFOP correto baseado nas regras fiscais
3. Validar se o CFOP informado está correto
4. Gerar relatórios de divergências
5. Explicar as regras aplicadas

FORMATO DE CFOP:
- CFOPs no sistema podem ser informados como "5102", "5.102", "5 102", etc
- O sistema automaticamente formata para busca (4 dígitos = X.YYY)
- Você pode usar qualquer formato, o sistema converte automaticamente

PROCEDIMENTO PARA INFERIR CFOP:

PASSO 1 - IDENTIFICAR TIPO DE OPERAÇÃO:
- Palavras como "VENDA", "REMESSA", "RETORNO" (sem "Dev") → SAÍDA (CFOP inicia com 5, 6 ou 7)
- Palavras como "ENTRADA", "COMPRA", "DEVOLUÇÃO", "Dev" → ENTRADA (CFOP inicia com 1, 2 ou 3)

PASSO 2 - DETERMINAR ÂMBITO:
- "1 - OPERAÇÃO INTERNA" ou UF Emitente = UF Destinatário:
  * Entrada: CFOP 1xxx
  * Saída: CFOP 5xxx
- "2 - OPERAÇÃO INTERESTADUAL" ou UF Emitente ≠ UF Destinatário:
  * Entrada: CFOP 2xxx
  * Saída: CFOP 6xxx
- "3 - OPERAÇÃO COM EXTERIOR":
  * Entrada: CFOP 3xxx
  * Saída: CFOP 7xxx

IMPORTANTE - ÍNDICES:
- Os índices no pandas começam em 0
- "Primeiro registro" = índice 0
- "Quinto registro" = índice 4
- "Décimo-quinto item" = índice 14
- Para converter: posição - 1 = índice

FERRAMENTAS DISPONÍVEIS:
- Use validar_cfop_item_especifico para validar CFOP de um item específico de uma nota
  * IMPORTANTE: Esta ferramenta aceita 2 parâmetros separados por vírgula
  * Formato: chave_acesso, numero_item
  * Exemplo: "35240134028316923228550010003680821895807710", "4"
- Use buscar_nota_por_chave para buscar nota pela CHAVE DE ACESSO (44 dígitos)
- Use buscar_nota_cabecalho para buscar nota pelo NÚMERO da nota
- Use buscar_item_por_indice para encontrar itens por posição
- Use buscar_nota_por_indice para encontrar notas por posição
- Use listar_notas_cabecalho para ver várias notas de uma vez
- Use buscar_cfop quando souber o código CFOP específico (qualquer formato)
- Use validar_todas_notas para análise geral de conformidade

IMPORTANTE - CHAVE DE ACESSO:
- Quando o usuário fornecer uma sequência longa de números (geralmente 44 dígitos), é uma CHAVE DE ACESSO
- Use SEMPRE buscar_nota_por_chave para chaves de acesso
- Use buscar_nota_cabecalho apenas para números de nota (números menores)

IMPORTANTE - VALIDAÇÃO DE ITEM ESPECÍFICO:
- Quando o usuário pedir para validar um item específico, você DEVE fornecer a chave de acesso E o número do item
- Os parâmetros devem ser passados separadamente (não em formato JSON)
- A ferramenta aceita: chave de 44 dígitos e número do item (1, 2, 3, 4, etc)

Seja objetivo, claro e mostre os dados de forma organizada."""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def _criar_ferramentas(self):
        """Cria as ferramentas para o agente"""
        
        def contar_notas() -> str:
            """Retorna estatísticas sobre os arquivos carregados"""
            print(f"   🔍 Tool: contar_notas()")
            
            total_cabecalho = len(self.df_cabecalho)
            total_itens = len(self.df_itens)
            total_cfop = len(self.df_cfop)
            
            resultado = f"""📊 ESTATÍSTICAS DOS ARQUIVOS

📋 Cabeçalho de Notas: {total_cabecalho} registros
🛒 Itens de Notas: {total_itens} registros
📖 Tabela CFOP: {total_cfop} códigos

Colunas do Cabeçalho ({len(self.df_cabecalho.columns)}):
{', '.join(self.df_cabecalho.columns.tolist())}

Colunas dos Itens ({len(self.df_itens.columns)}):
{', '.join(self.df_itens.columns.tolist())}

Colunas do CFOP ({len(self.df_cfop.columns)}):
{', '.join(self.df_cfop.columns.tolist())}
"""
            
            print(f"   ✅ Total: {total_cabecalho} notas, {total_itens} itens")
            return resultado
        
        def listar_notas_cabecalho(limit: str = "10") -> str:
            """Lista as primeiras N notas do cabeçalho"""
            print(f"   🔍 Tool: listar_notas_cabecalho(limit={limit})")
            try:
                n = int(limit)
                notas = self.df_cabecalho.head(n)
                
                resultado = f"📊 PRIMEIRAS {n} NOTAS DO CABEÇALHO\n"
                resultado += f"Total de notas disponíveis: {len(self.df_cabecalho)}\n\n"
                
                for idx, row in notas.iterrows():
                    resultado += f"\n{'='*60}\n"
                    resultado += f"REGISTRO {idx + 1} (Índice {idx})\n"
                    resultado += f"{'='*60}\n"
                    resultado += f"Número: {row.get('NÚMERO', 'N/A')}\n"
                    resultado += f"Natureza: {row.get('NATUREZA DA OPERAÇÃO', 'N/A')}\n"
                    resultado += f"Emitente: {row.get('NOME EMITENTE', 'N/A')} ({row.get('UF EMITENTE', 'N/A')})\n"
                    resultado += f"Destinatário: {row.get('NOME DESTINATÁRIO', 'N/A')} ({row.get('UF DESTINATÁRIO', 'N/A')})\n"
                    resultado += f"Valor: R$ {row.get('VALOR TOTAL DA NF', 'N/A')}\n"
                    resultado += f"Destino: {row.get('DESTINO DA OPERAÇÃO', 'N/A')}\n"
                
                print(f"   ✅ Listadas {len(notas)} notas")
                return resultado
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao listar notas: {str(e)}"
        
        def buscar_nota_por_indice(indice: str) -> str:
            """Busca uma nota específica por índice no arquivo de cabeçalho"""
            print(f"   🔍 Tool: buscar_nota_por_indice(indice={indice})")
            try:
                idx = int(indice)
                
                if idx < 0 or idx >= len(self.df_cabecalho):
                    return f"❌ Índice {idx} fora do intervalo. O arquivo de cabeçalho tem {len(self.df_cabecalho)} registros (índices 0 a {len(self.df_cabecalho)-1})."
                
                nota = self.df_cabecalho.iloc[idx]
                
                resultado = f"📋 NOTA REGISTRO {idx + 1} (ÍNDICE {idx})\n\n"
                for col, valor in nota.items():
                    resultado += f"{col}: {valor}\n"
                
                print(f"   ✅ Nota no índice {idx} encontrada")
                return resultado
                
            except ValueError:
                return f"❌ Índice inválido: '{indice}'. Use um número inteiro."
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao buscar nota: {str(e)}"
        
        def buscar_item_por_indice(indice: str) -> str:
            """Busca um item específico por índice no arquivo de itens"""
            print(f"   🔍 Tool: buscar_item_por_indice(indice={indice})")
            try:
                idx = int(indice)
                
                if idx < 0 or idx >= len(self.df_itens):
                    return f"❌ Índice {idx} fora do intervalo. O arquivo de itens tem {len(self.df_itens)} registros (índices 0 a {len(self.df_itens)-1})."
                
                item = self.df_itens.iloc[idx]
                
                resultado = f"📦 ITEM REGISTRO {idx + 1} (ÍNDICE {idx})\n\n"
                for col, valor in item.items():
                    resultado += f"{col}: {valor}\n"
                
                # Destacar o CFOP
                if 'CFOP' in item.index:
                    resultado += f"\n🎯 CFOP DESTE ITEM: {item['CFOP']}\n"
                
                print(f"   ✅ Item no índice {idx} encontrado")
                return resultado
                
            except ValueError:
                return f"❌ Índice inválido: '{indice}'. Use um número inteiro."
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao buscar item: {str(e)}"
        
        def buscar_cfop_por_indice(indice: str) -> str:
            """Busca um CFOP específico por índice na tabela de CFOPs"""
            print(f"   🔍 Tool: buscar_cfop_por_indice(indice={indice})")
            try:
                idx = int(indice)
                
                if idx < 0 or idx >= len(self.df_cfop):
                    return f"❌ Índice {idx} fora do intervalo. A tabela CFOP tem {len(self.df_cfop)} registros (índices 0 a {len(self.df_cfop)-1})."
                
                cfop = self.df_cfop.iloc[idx]
                
                resultado = f"📖 CFOP REGISTRO {idx + 1} (ÍNDICE {idx})\n\n"
                for col, valor in cfop.items():
                    resultado += f"{col}: {valor}\n"
                
                print(f"   ✅ CFOP no índice {idx} encontrado")
                return resultado
                
            except ValueError:
                return f"❌ Índice inválido: '{indice}'. Use um número inteiro."
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao buscar CFOP: {str(e)}"
        
        def buscar_nota_por_chave(chave_acesso: str) -> str:
            """Busca uma nota fiscal pela chave de acesso (44 dígitos)"""
            print(f"   🔍 Tool: buscar_nota_por_chave(chave_acesso={chave_acesso})")
            try:
                # Limpar a chave de acesso (remover espaços, hífens, etc)
                chave_limpa = str(chave_acesso).strip().replace(' ', '').replace('-', '').replace('.', '').replace("'", "")
                
                print(f"      🔧 Chave de acesso limpa: {chave_limpa}")
                print(f"      📏 Tamanho: {len(chave_limpa)} caracteres")
                
                # Tentar várias possíveis colunas onde a chave pode estar
                possiveis_colunas = [
                    'CHAVE DE ACESSO', 'CHAVE', 'CHAVE NF-E', 'CHAVE NFE',
                    'CHAVE_ACESSO', 'NF-E CHAVE DE ACESSO', 'NFE_CHAVE', 'CHAVE_NFE'
                ]
                
                # Verificar quais colunas existem no dataframe
                colunas_disponiveis = self.df_cabecalho.columns.tolist()
                print(f"      📋 Colunas disponíveis: {colunas_disponiveis}")
                
                nota_encontrada = None
                coluna_encontrada = None
                
                # Tentar cada possível coluna
                for coluna in possiveis_colunas:
                    if coluna in colunas_disponiveis:
                        print(f"      🔍 Tentando buscar na coluna: {coluna}")
                        
                        # Buscar com a chave limpa
                        nota = self.df_cabecalho[
                            self.df_cabecalho[coluna].astype(str).str.replace(' ', '').str.replace('-', '').str.replace('.', '').str.replace("'", "") == chave_limpa
                        ]
                        
                        if not nota.empty:
                            nota_encontrada = nota
                            coluna_encontrada = coluna
                            print(f"      ✅ Encontrada na coluna: {coluna}")
                            break
                
                # Se não encontrou em colunas específicas, tentar em todas as colunas
                if nota_encontrada is None:
                    print(f"      🔍 Buscando em todas as colunas...")
                    for coluna in colunas_disponiveis:
                        try:
                            nota = self.df_cabecalho[
                                self.df_cabecalho[coluna].astype(str).str.replace(' ', '').str.replace('-', '').str.replace('.', '').str.replace("'", "").str.contains(chave_limpa, na=False, regex=False)
                            ]
                            
                            if not nota.empty:
                                nota_encontrada = nota
                                coluna_encontrada = coluna
                                print(f"      ✅ Encontrada na coluna: {coluna}")
                                break
                        except:
                            continue
                
                if nota_encontrada is None or nota_encontrada.empty:
                    # Mostrar as primeiras chaves disponíveis para debug
                    resultado = f"❌ Nota com chave de acesso não encontrada.\n\n"
                    resultado += f"🔍 Chave procurada (limpa): {chave_limpa}\n"
                    resultado += f"📏 Tamanho da chave: {len(chave_limpa)} caracteres\n"
                    resultado += f"📋 Colunas disponíveis no arquivo:\n"
                    for col in colunas_disponiveis:
                        resultado += f"   - {col}\n"
                    
                    # Tentar mostrar alguns exemplos de chaves que existem
                    resultado += f"\n💡 Exemplos de valores nas colunas (primeiras 3 notas):\n"
                    for coluna in possiveis_colunas:
                        if coluna in colunas_disponiveis:
                            exemplos = self.df_cabecalho[coluna].dropna().head(3)
                            if not exemplos.empty:
                                resultado += f"\n📌 Coluna '{coluna}':\n"
                                for i, ex in enumerate(exemplos, 1):
                                    resultado += f"   {i}. {ex}\n"
                                break
                    
                    return resultado
                
                resultado = f"✅ NOTA FISCAL ENCONTRADA\n"
                resultado += f"   (Chave encontrada na coluna: '{coluna_encontrada}')\n\n"
                
                for col in nota_encontrada.columns:
                    valor = nota_encontrada.iloc[0][col]
                    resultado += f"{col}: {valor}\n"
                
                print(f"   ✅ Nota encontrada pela chave de acesso")
                return resultado
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao buscar nota por chave de acesso: {str(e)}"
        
        def buscar_nota_cabecalho(numero_nota: str) -> str:
            """Busca informações de cabeçalho de uma nota fiscal pelo número"""
            print(f"   🔍 Tool: buscar_nota_cabecalho(numero_nota={numero_nota})")
            try:
                nota = self.df_cabecalho[self.df_cabecalho['NÚMERO'].astype(str) == str(numero_nota)]
                if nota.empty:
                    return f"❌ Nota {numero_nota} não encontrada no cabeçalho."
                
                resultado = f"📋 NOTA FISCAL Nº {numero_nota}\n\n"
                for col in nota.columns:
                    valor = nota.iloc[0][col]
                    resultado += f"{col}: {valor}\n"
                
                print(f"   ✅ Encontrada nota {numero_nota}")
                return resultado
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                return f"Erro ao buscar nota: {str(e)}"
        
        def buscar_itens_nota(numero_nota: str) -> str:
            """Busca todos os itens de uma nota fiscal pelo número"""
            print(f"   🔍 Tool: buscar_itens_nota(numero_nota={numero_nota})")
            try:
                itens = self.df_itens[self.df_itens['NÚMERO'].astype(str) == str(numero_nota)]
                if itens.empty:
                    return f"❌ Nenhum item encontrado para nota {numero_nota}."
                
                resultado = f"🛒 ITENS DA NOTA {numero_nota}\n"
                resultado += f"Total de itens: {len(itens)}\n\n"
                
                for idx, item in itens.iterrows():
                    resultado += f"\n{'='*60}\n"
                    resultado += f"ITEM {idx + 1}\n"
                    resultado += f"{'='*60}\n"
                    for col, valor in item.items():
                        resultado += f"{col}: {valor}\n"
                
                print(f"   ✅ Encontrados {len(itens)} itens")
                return resultado
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                return f"Erro ao buscar itens: {str(e)}"
        
        def buscar_cfop(codigo_cfop: str) -> str:
            """Busca informações sobre um código CFOP específico. 
            Aceita CFOP em qualquer formato: 5102, 5.102, 5 102, etc.
            O sistema formata automaticamente."""
            print(f"   🔍 Tool: buscar_cfop(codigo_cfop={codigo_cfop})")
            try:
                # Formatar o CFOP para o padrão do CSV
                cfop_formatado = self._formatar_cfop_para_busca(codigo_cfop)
                
                # Buscar o CFOP formatado
                cfop = self.df_cfop[self.df_cfop['CFOP'].astype(str) == cfop_formatado]
                
                if cfop.empty:
                    # Tentar busca alternativa sem formatação
                    cfop_limpo = str(codigo_cfop).strip().replace('.', '').replace(',', '').replace(' ', '')
                    cfop = self.df_cfop[self.df_cfop['CFOP'].astype(str).str.replace('.', '').str.replace(',', '').str.replace(' ', '') == cfop_limpo]
                    
                    if cfop.empty:
                        # Mostrar CFOPs disponíveis próximos
                        primeiro_digito = cfop_limpo[0] if cfop_limpo else ''
                        sugestoes = self.df_cfop[self.df_cfop['CFOP'].astype(str).str.startswith(primeiro_digito)].head(5)
                        
                        resultado = f"❌ CFOP {codigo_cfop} (formatado: {cfop_formatado}) não encontrado na tabela.\n\n"
                        
                        if not sugestoes.empty:
                            resultado += f"💡 CFOPs que começam com '{primeiro_digito}':\n"
                            for _, row in sugestoes.iterrows():
                                resultado += f"   - {row['CFOP']}\n"
                        
                        return resultado
                
                resultado = f"📖 CFOP {codigo_cfop}\n"
                resultado += f"   (Formato no sistema: {cfop.iloc[0]['CFOP']})\n\n"
                
                for col, valor in cfop.iloc[0].items():
                    resultado += f"{col}: {valor}\n"
                
                print(f"   ✅ CFOP encontrado: {cfop.iloc[0]['CFOP']}")
                return resultado
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao buscar CFOP: {str(e)}"
        
        def validar_todas_notas() -> str:
            """Valida CFOP de todas as notas e retorna um resumo"""
            print(f"   🔍 Tool: validar_todas_notas()")
            try:
                divergencias = []
                total_itens = 0
                
                # Limitar a 100 para performance
                itens_para_validar = self.df_itens.head(100)
                
                for _, item in itens_para_validar.iterrows():
                    total_itens += 1
                    numero_nota = str(item.get('NÚMERO', ''))
                    cfop_item = str(item.get('CFOP', ''))
                    
                    cabecalho = self.df_cabecalho[
                        self.df_cabecalho['NÚMERO'].astype(str) == numero_nota
                    ]
                    
                    if not cabecalho.empty:
                        natureza = str(cabecalho.iloc[0].get('NATUREZA DA OPERAÇÃO', ''))
                        uf_emit = str(cabecalho.iloc[0].get('UF EMITENTE', ''))
                        uf_dest = str(cabecalho.iloc[0].get('UF DESTINATÁRIO', ''))
                        destino_op = str(cabecalho.iloc[0].get('DESTINO DA OPERAÇÃO', ''))
                        
                        primeiro_digito_esperado = self._inferir_primeiro_digito(
                            natureza, uf_emit, uf_dest, destino_op
                        )
                        
                        # Extrair primeiro dígito do CFOP (pode estar no formato X.YYY)
                        cfop_limpo = cfop_item.replace('.', '').replace(',', '').replace(' ', '')
                        primeiro_digito_atual = cfop_limpo[0] if cfop_limpo and len(cfop_limpo) > 0 else "?"
                        
                        if primeiro_digito_esperado != primeiro_digito_atual:
                            divergencias.append({
                                'nota': numero_nota,
                                'cfop_atual': cfop_item,
                                'esperado': f"{primeiro_digito_esperado}xxx",
                                'natureza': natureza,
                                'uf_emit': uf_emit,
                                'uf_dest': uf_dest
                            })
                
                resultado = f"✅ VALIDAÇÃO COMPLETA\n\n"
                resultado += f"Total de itens analisados: {total_itens}\n"
                resultado += f"Divergências encontradas: {len(divergencias)}\n"
                
                if total_itens > 0:
                    taxa_conformidade = ((total_itens - len(divergencias)) / total_itens * 100)
                    resultado += f"Taxa de conformidade: {taxa_conformidade:.1f}%\n\n"
                
                if divergencias:
                    resultado += "❌ DIVERGÊNCIAS ENCONTRADAS:\n\n"
                    for i, d in enumerate(divergencias[:10], 1):
                        resultado += f"{i}. Nota {d['nota']}:\n"
                        resultado += f"   CFOP atual: {d['cfop_atual']}\n"
                        resultado += f"   CFOP esperado: {d['esperado']}\n"
                        resultado += f"   Natureza: {d['natureza']}\n"
                        resultado += f"   Rota: {d['uf_emit']} → {d['uf_dest']}\n\n"
                    
                    if len(divergencias) > 10:
                        resultado += f"\n... e mais {len(divergencias) - 10} divergências.\n"
                else:
                    resultado += "✅ Todos os CFOPs verificados estão corretos!\n"
                
                print(f"   ✅ Validação concluída: {len(divergencias)} divergências")
                return resultado
                
            except Exception as e:
                print(f"   ❌ Erro na validação: {e}")
                traceback.print_exc()
                return f"Erro na validação: {str(e)}"
        
        # FUNÇÃO PRINCIPAL: Validar CFOP de item específico
        # MUDANÇA CHAVE: Usar StructuredTool ao invés de Tool com args_schema
        def validar_cfop_item_especifico(chave_acesso: str, numero_item: str) -> str:
            """Valida o CFOP de um item específico de uma nota usando a chave de acesso.
            
            Args:
                chave_acesso: Chave de acesso da nota fiscal (44 dígitos)
                numero_item: Número do item (1, 2, 3, etc ou 'primeiro', 'segundo', etc)
            
            Returns:
                Relatório detalhado de validação do CFOP
            """
            print(f"   🔍 Tool: validar_cfop_item_especifico(chave={chave_acesso[:20] if len(chave_acesso) > 20 else chave_acesso}..., item={numero_item})")
            
            try:
                # Limpar chave de acesso
                chave_limpa = str(chave_acesso).strip().replace(' ', '').replace('-', '').replace('.', '').replace("'", "")
                
                # Converter número do item (pode vir como "1", "primeiro", "item 1", etc)
                numero_item_str = str(numero_item).lower().strip()
                
                # Extrair número
                numeros = re.findall(r'\d+', numero_item_str)
                if numeros:
                    item_numero = int(numeros[0])
                else:
                    # Tentar palavras por extenso
                    palavras_numericas = {
                        'primeiro': 1, 'primeira': 1,
                        'segundo': 2, 'segunda': 2,
                        'terceiro': 3, 'terceira': 3,
                        'quarto': 4, 'quarta': 4,
                        'quinto': 5, 'quinta': 5,
                        'sexto': 6, 'sexta': 6,
                        'sétimo': 7, 'sétima': 7,
                        'oitavo': 8, 'oitava': 8,
                        'nono': 9, 'nona': 9,
                        'décimo': 10, 'décima': 10
                    }
                    item_numero = palavras_numericas.get(numero_item_str, 1)
                
                print(f"      🔢 Número do item: {item_numero}")
                
                # ==================================================================
                # BUSCAR NOTA PELO CHAVE DE ACESSO
                # ==================================================================
                possiveis_colunas_chave = [
                    'CHAVE DE ACESSO', 'CHAVE', 'CHAVE NF-E', 'CHAVE NFE',
                    'CHAVE_ACESSO', 'NF-E CHAVE DE ACESSO', 'NFE_CHAVE', 'CHAVE_NFE'
                ]
                
                nota_encontrada = None
                for coluna in possiveis_colunas_chave:
                    if coluna in self.df_cabecalho.columns:
                        nota = self.df_cabecalho[
                            self.df_cabecalho[coluna].astype(str).str.replace(' ', '').str.replace('-', '').str.replace('.', '').str.replace("'", "") == chave_limpa
                        ]
                        if not nota.empty:
                            nota_encontrada = nota.iloc[0]
                            break
                
                if nota_encontrada is None:
                    return f"❌ Nota com chave {chave_acesso} não encontrada no arquivo de cabeçalho."
                
                numero_nota = str(nota_encontrada.get('NÚMERO', ''))
                print(f"      ✅ Nota encontrada: {numero_nota}")
                
                # ==================================================================
                # BUSCAR ITENS DA NOTA
                # ==================================================================
                itens_nota = self.df_itens[self.df_itens['NÚMERO'].astype(str) == numero_nota]
                
                if itens_nota.empty:
                    return f"❌ Nenhum item encontrado para a nota {numero_nota}."
                
                if item_numero < 1 or item_numero > len(itens_nota):
                    return f"❌ Item {item_numero} não existe. A nota tem {len(itens_nota)} itens."
                
                # Pegar o item específico (item_numero - 1 porque índice começa em 0)
                item = itens_nota.iloc[item_numero - 1]
                cfop_registrado = str(item.get('CFOP', '')).strip()
                
                print(f"      📦 Item {item_numero} encontrado")
                print(f"      🏷️ CFOP registrado: {cfop_registrado}")
                
                # ==================================================================
                # PASSO 1: IDENTIFICAR TIPO DE OPERAÇÃO (ENTRADA OU SAÍDA)
                # ==================================================================
                natureza = str(nota_encontrada.get('NATUREZA DA OPERAÇÃO', '')).upper()
                
                is_entrada = any(palavra in natureza for palavra in 
                                ['ENTRADA', 'COMPRA', 'DEVOLUÇÃO', 'DEV', 'AQUISIÇÃO'])
                is_saida = any(palavra in natureza for palavra in 
                              ['VENDA', 'REMESSA', 'RETORNO']) and 'DEV' not in natureza and 'DEVOLUÇÃO' not in natureza
                
                tipo_operacao = "ENTRADA" if is_entrada else "SAÍDA"
                
                # ==================================================================
                # PASSO 2: DETERMINAR ÂMBITO DA OPERAÇÃO
                # ==================================================================
                uf_emitente = str(nota_encontrada.get('UF EMITENTE', '')).strip()
                uf_destinatario = str(nota_encontrada.get('UF DESTINATÁRIO', '')).strip()
                destino_operacao = str(nota_encontrada.get('DESTINO DA OPERAÇÃO', '')).strip()
                
                # Determinar primeiro dígito
                if '1 - OPERAÇÃO INTERNA' in destino_operacao or uf_emitente == uf_destinatario:
                    ambito = "INTERNA"
                    primeiro_digito = '1' if is_entrada else '5'
                elif '2 - OPERAÇÃO INTERESTADUAL' in destino_operacao or (uf_emitente != uf_destinatario and uf_destinatario):
                    ambito = "INTERESTADUAL"
                    primeiro_digito = '2' if is_entrada else '6'
                elif '3 - OPERAÇÃO COM EXTERIOR' in destino_operacao:
                    ambito = "EXTERIOR"
                    primeiro_digito = '3' if is_entrada else '7'
                else:
                    ambito = "INDEFINIDO"
                    primeiro_digito = '?'
                
                # ==================================================================
                # PASSO 3 e 4: IDENTIFICAR NATUREZA ESPECÍFICA E CAMPOS COMPLEMENTARES
                # ==================================================================
                consumidor_final = str(nota_encontrada.get('CONSUMIDOR FINAL', '')).strip()
                indicador_ie = str(nota_encontrada.get('INDICADOR IE DESTINATÁRIO', '')).strip()
                
                # Determinar os últimos 3 dígitos baseado na natureza
                ultimos_digitos = None
                justificativa = ""
                
                # DEVOLUÇÕES
                if any(palavra in natureza for palavra in ['DEV', 'DEVOLUÇÃO']):
                    if 'REMESSA' in natureza:
                        ultimos_digitos = '949'
                        justificativa = "Devolução de remessa"
                    else:
                        ultimos_digitos = '202'
                        justificativa = "Devolução de compra/venda"
                
                # VENDAS/COMPRAS
                elif 'VENDA' in natureza or 'COMPRA' in natureza or 'AQUISIÇÃO' in natureza:
                    if 'NÃO CONTRIBUINTE' in indicador_ie or 'CONSUMIDOR FINAL' in consumidor_final:
                        ultimos_digitos = '102'
                        justificativa = "Venda/Compra para não contribuinte ou consumidor final"
                    else:
                        ultimos_digitos = '102'
                        justificativa = "Venda/Compra de mercadoria"
                
                # REMESSAS
                elif 'REMESSA' in natureza:
                    if 'DEMONSTRAÇÃO' in natureza:
                        ultimos_digitos = '912'
                        justificativa = "Remessa para demonstração"
                    elif 'CONSERTO' in natureza or 'REPARO' in natureza:
                        ultimos_digitos = '915'
                        justificativa = "Remessa para conserto/reparo"
                    elif 'COMODATO' in natureza:
                        ultimos_digitos = '908'
                        justificativa = "Remessa em comodato"
                    else:
                        ultimos_digitos = '949'
                        justificativa = "Outra remessa"
                
                # OUTRAS OPERAÇÕES
                else:
                    ultimos_digitos = '949'
                    justificativa = "Outra operação não especificada"
                
                # ==================================================================
                # PASSO 5: MONTAR CFOP INFERIDO
                # ==================================================================
                if primeiro_digito != '?':
                    cfop_inferido = f"{primeiro_digito}.{ultimos_digitos}"
                else:
                    cfop_inferido = "INDETERMINADO"
                
                print(f"      🎯 CFOP inferido: {cfop_inferido}")
                
                # ==================================================================
                # PASSO 6: COMPARAR E GERAR RELATÓRIO
                # ==================================================================
                # Normalizar CFOPs para comparação
                cfop_registrado_limpo = cfop_registrado.replace('.', '').replace(',', '').replace(' ', '')
                cfop_inferido_limpo = cfop_inferido.replace('.', '').replace(',', '').replace(' ', '')
                
                # Comparar primeiro dígito (mais importante)
                primeiro_digito_registrado = cfop_registrado_limpo[0] if cfop_registrado_limpo else '?'
                diverge_primeiro = primeiro_digito != primeiro_digito_registrado
                
                # Comparar CFOP completo
                diverge_completo = cfop_registrado_limpo != cfop_inferido_limpo
                
                # ==================================================================
                # GERAR RELATÓRIO
                # ==================================================================
                resultado = f"""{'='*70}
🔍 VALIDAÇÃO DE CFOP - ITEM ESPECÍFICO
{'='*70}

📋 IDENTIFICAÇÃO DA NOTA:
   Chave de Acesso: {chave_acesso}
   Número da Nota: {numero_nota}
   Item Analisado: {item_numero}º item

📦 DADOS DO ITEM:
   Descrição: {item.get('DESCRIÇÃO DO PRODUTO', 'N/A')}
   Valor: R$ {item.get('VALOR TOTAL', 'N/A')}
   CFOP Registrado: {cfop_registrado}

📊 ANÁLISE DO CABEÇALHO DA NOTA:
   Natureza da Operação: {natureza}
   Tipo de Operação: {tipo_operacao}
   Âmbito: {ambito} ({uf_emitente} → {uf_destinatario})
   Consumidor Final: {consumidor_final}
   Indicador IE Destinatário: {indicador_ie}

🎯 INFERÊNCIA DO CFOP:
   CFOP Inferido: {cfop_inferido}
   Primeiro Dígito: {primeiro_digito} ({ambito})
   Últimos Dígitos: {ultimos_digitos}
   Justificativa: {justificativa}

{'='*70}
"""
                
                if diverge_primeiro:
                    resultado += f"""
⚠️ ALERTA CRÍTICO - DIVERGÊNCIA NO PRIMEIRO DÍGITO!
   CFOP Registrado: {cfop_registrado} (primeiro dígito: {primeiro_digito_registrado})
   CFOP Inferido: {cfop_inferido} (primeiro dígito: {primeiro_digito})
   
   ❌ O primeiro dígito está INCORRETO!
   
   Impacto: O primeiro dígito define o âmbito da operação:
   - {primeiro_digito_registrado} indica: {self._explicar_primeiro_digito(primeiro_digito_registrado)}
   - {primeiro_digito} (correto) indica: {self._explicar_primeiro_digito(primeiro_digito)}
   
   🚨 AÇÃO REQUERIDA: Correção obrigatória do CFOP!
"""
                elif diverge_completo:
                    resultado += f"""
⚠️ ALERTA - DIVERGÊNCIA NOS ÚLTIMOS DÍGITOS
   CFOP Registrado: {cfop_registrado}
   CFOP Inferido: {cfop_inferido}
   
   ℹ️ O primeiro dígito está correto, mas os últimos 3 dígitos diferem.
   
   Possíveis causas:
   - Natureza específica da operação não capturada pela análise
   - CFOP mais específico aplicável ao produto
   - Regime tributário especial (ex: substituição tributária)
   
   💡 RECOMENDAÇÃO: Revisar a natureza específica da operação
"""
                else:
                    resultado += f"""
✅ VALIDAÇÃO APROVADA
   O CFOP registrado ({cfop_registrado}) está correto!
   Corresponde ao CFOP inferido ({cfop_inferido})
   
   ✓ Primeiro dígito correto: {primeiro_digito}
   ✓ Natureza da operação adequada: {ultimos_digitos}
"""
                
                resultado += f"\n{'='*70}\n"
                
                print(f"      {'❌ DIVERGÊNCIA' if (diverge_primeiro or diverge_completo) else '✅ CORRETO'}")
                
                return resultado
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                traceback.print_exc()
                return f"Erro ao validar CFOP do item: {str(e)}"
        
        # LISTA DE FERRAMENTAS
        # MUDANÇA CHAVE: Usar StructuredTool para a função com 2 parâmetros
        tools = [
            Tool(
                name="contar_notas",
                func=contar_notas,
                description="Retorna estatísticas completas sobre os arquivos carregados (quantidade de notas, itens, CFOPs e todas as colunas disponíveis)."
            ),
            Tool(
                name="listar_notas_cabecalho",
                func=listar_notas_cabecalho,
                description="Lista as primeiras N notas do arquivo de cabeçalho com resumo de cada uma. Use o parâmetro limit para especificar quantas notas mostrar (padrão: 10)."
            ),
            Tool(
                name="buscar_nota_por_chave",
                func=buscar_nota_por_chave,
                description="Busca uma nota fiscal pela CHAVE DE ACESSO (44 dígitos). Use SEMPRE quando o usuário fornecer uma sequência longa de números. Aceita a chave com ou sem formatação. Exemplo: 23240114124286000121550010000214351719667666"
            ),
            Tool(
                name="buscar_nota_por_indice",
                func=buscar_nota_por_indice,
                description="Busca uma nota específica por ÍNDICE (posição) no arquivo de cabeçalho. Índice começa em 0: primeira nota = 0, quinta nota = 4, décima nota = 9. Use quando perguntarem sobre 'quinta nota', 'décima nota', etc."
            ),
            Tool(
                name="buscar_item_por_indice",
                func=buscar_item_por_indice,
                description="Busca um item específico por ÍNDICE (posição) no arquivo de itens. Índice começa em 0: primeiro item = 0, décimo-quinto item = 14, vigésimo item = 19. Use quando perguntarem sobre 'décimo item', 'décimo-quinto item', etc. Retorna também o CFOP do item."
            ),
            Tool(
                name="buscar_cfop_por_indice",
                func=buscar_cfop_por_indice,
                description="Busca um CFOP específico por ÍNDICE (posição) na tabela de CFOPs. Índice começa em 0."
            ),
            Tool(
                name="buscar_nota_cabecalho",
                func=buscar_nota_cabecalho,
                description="Busca informações completas de cabeçalho de uma nota fiscal específica pelo NÚMERO da nota (não o índice, não a chave de acesso). Use quando souber o número curto da nota."
            ),
            Tool(
                name="buscar_itens_nota",
                func=buscar_itens_nota,
                description="Busca todos os itens de uma nota fiscal específica pelo NÚMERO da nota. Use quando quiser ver todos os produtos/serviços de uma nota específica."
            ),
            Tool(
                name="buscar_cfop",
                func=buscar_cfop,
                description="Busca informações detalhadas sobre um código CFOP específico. Aceita qualquer formato: 5102, 5.102, 5 102, etc. O sistema formata automaticamente para o padrão do CSV (X.YYY para 4 dígitos)."
            ),
            Tool(
                name="validar_todas_notas",
                func=validar_todas_notas,
                description="Valida o CFOP de todas as notas carregadas (até 100 primeiras) e retorna um resumo completo com divergências encontradas. Use para análise geral de conformidade."
            ),
            # MUDANÇA CHAVE: Usar StructuredTool ao invés de Tool com args_schema
            StructuredTool.from_function(
                func=validar_cfop_item_especifico,
                name="validar_cfop_item_especifico",
                description="Valida o CFOP de um item específico de uma nota fiscal. REQUER DOIS PARÂMETROS SEPARADOS: chave_acesso (string de 44 dígitos) e numero_item (string com número '1', '2', '3' ou palavra 'primeiro', 'segundo', 'terceiro', etc). Infere o CFOP correto baseado na natureza da operação e compara com o CFOP registrado. Gera alertas detalhados se houver divergência."
            )
        ]
        
        return tools
    
    def _inferir_primeiro_digito(self, natureza: str, uf_emit: str, 
                                  uf_dest: str, destino_op: str) -> str:
        """Infere o primeiro dígito do CFOP baseado nas regras"""
        natureza = natureza.upper()
        
        is_entrada = any(palavra in natureza for palavra in 
                        ['ENTRADA', 'COMPRA', 'DEVOLUÇÃO', 'DEV'])
        is_saida = any(palavra in natureza for palavra in 
                      ['VENDA', 'REMESSA']) and 'DEV' not in natureza
        
        if '1 - OPERAÇÃO INTERNA' in destino_op or uf_emit == uf_dest:
            return '1' if is_entrada else '5'
        elif '2 - OPERAÇÃO INTERESTADUAL' in destino_op or uf_emit != uf_dest:
            return '2' if is_entrada else '6'
        elif '3 - OPERAÇÃO COM EXTERIOR' in destino_op:
            return '3' if is_entrada else '7'
        
        return '?'
    
    def processar_pergunta(self, pergunta: str) -> str:
        """Processa uma pergunta usando o agente"""
        print("\n" + "="*70)
        print("📥 NOVA PERGUNTA RECEBIDA")
        print("="*70)
        print(f"Pergunta: {pergunta}")
        print("="*70 + "\n")
        
        try:
            print("🤖 Enviando para o agente executor...")
            resultado = self.agent_executor.invoke({"input": pergunta})
            
            print("\n" + "="*70)
            print("✅ RESPOSTA GERADA")
            print("="*70)
            print(f"Output: {resultado['output'][:200]}...")
            print("="*70 + "\n")
            
            return resultado["output"]
            
        except Exception as e:
            print("\n" + "="*70)
            print("❌ ERRO AO PROCESSAR PERGUNTA")
            print("="*70)
            print(f"Tipo do erro: {type(e).__name__}")
            print(f"Mensagem: {str(e)}")
            print("\nStack trace completo:")
            traceback.print_exc()
            print("="*70 + "\n")
            
            return f"❌ Erro ao processar pergunta: {str(e)}\n\nPor favor, tente novamente ou reformule sua pergunta."
