import pandas as pd
import os
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from dotenv import load_dotenv

load_dotenv()

class AgenteValidadorCFOP:
    """Agente inteligente para validação de CFOP em Notas Fiscais"""
    
    def __init__(self, cabecalho_path: str, itens_path: str, cfop_path: str):
        """Inicializa o agente com os dados dos CSVs"""
        self.df_cabecalho = pd.read_csv(cabecalho_path)
        self.df_itens = pd.read_csv(itens_path)
        self.df_cfop = pd.read_csv(cfop_path)
        
        # Configurar LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Criar ferramentas
        self.tools = self._criar_ferramentas()
        
        # Criar prompt do agente
        self.prompt = self._criar_prompt()
        
        # Criar agente
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            return_intermediate_steps=True
        )
    
    def _criar_prompt(self):
        """Cria o prompt para o agente"""
        system_message = """Você é um especialista em análise e validação de CFOP (Código Fiscal de Operações e Prestações) de Notas Fiscais brasileiras.

Sua missão é:
1. Analisar notas fiscais e seus itens
2. Inferir o CFOP correto baseado nas regras fiscais
3. Validar se o CFOP informado está correto
4. Gerar relatórios de divergências
5. Explicar as regras aplicadas

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

PASSO 3 - IDENTIFICAR NATUREZA ESPECÍFICA:
- DEVOLUÇÕES: x.201, x.202, x.410, x.411, x.949
- VENDAS/COMPRAS: x.102, x.403
- REMESSAS: Verificar subcategorias

PASSO 4 - ANALISAR CAMPOS COMPLEMENTARES:
- CONSUMIDOR FINAL: "1 - CONSUMIDOR FINAL"
- INDICADOR IE DESTINATÁRIO: CONTRIBUINTE, NÃO CONTRIBUINTE, ISENTO
- PRESENÇA DO COMPRADOR

PASSO 5 - CONSULTAR TABELA CFOP
Use as ferramentas disponíveis para buscar na tabela CFOP.

PASSO 6 - VALIDAR
Compare o CFOP inferido com o CFOP presente nos itens.

Sempre forneça:
- CFOP inferido
- CFOP informado
- Status: CORRETO ou DIVERGENTE
- Justificativa detalhada
- Regras aplicadas"""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def _criar_ferramentas(self):
        """Cria as ferramentas para o agente"""
        
        def buscar_nota_cabecalho(numero_nota: str) -> str:
            """Busca informações de cabeçalho de uma nota fiscal pelo número"""
            try:
                nota = self.df_cabecalho[self.df_cabecalho['NÚMERO'].astype(str) == str(numero_nota)]
                if nota.empty:
                    return f"Nota {numero_nota} não encontrada no cabeçalho."
                return nota.to_string()
            except Exception as e:
                return f"Erro ao buscar nota: {str(e)}"
        
        def buscar_itens_nota(numero_nota: str) -> str:
            """Busca todos os itens de uma nota fiscal pelo número"""
            try:
                itens = self.df_itens[self.df_itens['NÚMERO'].astype(str) == str(numero_nota)]
                if itens.empty:
                    return f"Nenhum item encontrado para nota {numero_nota}."
                return itens.to_string()
            except Exception as e:
                return f"Erro ao buscar itens: {str(e)}"
        
        def buscar_cfop(codigo_cfop: str) -> str:
            """Busca informações sobre um código CFOP específico"""
            try:
                cfop = self.df_cfop[self.df_cfop['CFOP'].astype(str) == str(codigo_cfop)]
                if cfop.empty:
                    return f"CFOP {codigo_cfop} não encontrado na tabela."
                return cfop.to_string()
            except Exception as e:
                return f"Erro ao buscar CFOP: {str(e)}"
        
        def listar_cfops_por_tipo(tipo: str) -> str:
            """Lista CFOPs que começam com um dígito específico (1-7)"""
            try:
                cfops = self.df_cfop[self.df_cfop['CFOP'].astype(str).str.startswith(tipo)]
                if cfops.empty:
                    return f"Nenhum CFOP encontrado começando com {tipo}."
                return cfops[['CFOP', 'DESCRIÇÃO']].head(20).to_string()
            except Exception as e:
                return f"Erro ao listar CFOPs: {str(e)}"
        
        def contar_notas() -> str:
            """Retorna o total de notas fiscais no cabeçalho"""
            return f"Total de notas no cabeçalho: {len(self.df_cabecalho)}"
        
        def contar_itens() -> str:
            """Retorna o total de itens nas notas fiscais"""
            return f"Total de itens: {len(self.df_itens)}"
        
        def validar_todas_notas() -> str:
            """Valida CFOP de todas as notas e retorna um resumo"""
            try:
                divergencias = []
                total_itens = 0
                
                for _, item in self.df_itens.iterrows():
                    total_itens += 1
                    numero_nota = str(item['NÚMERO'])
                    cfop_item = str(item['CFOP'])
                    
                    # Buscar cabeçalho
                    cabecalho = self.df_cabecalho[
                        self.df_cabecalho['NÚMERO'].astype(str) == numero_nota
                    ]
                    
                    if not cabecalho.empty:
                        natureza = str(cabecalho.iloc[0]['NATUREZA DA OPERAÇÃO'])
                        uf_emit = str(cabecalho.iloc[0]['UF EMITENTE'])
                        uf_dest = str(cabecalho.iloc[0]['UF DESTINATÁRIO'])
                        destino_op = str(cabecalho.iloc[0]['DESTINO DA OPERAÇÃO'])
                        
                        # Inferir primeiro dígito esperado
                        primeiro_digito_esperado = self._inferir_primeiro_digito(
                            natureza, uf_emit, uf_dest, destino_op
                        )
                        
                        primeiro_digito_atual = cfop_item[0] if cfop_item else "?"
                        
                        if primeiro_digito_esperado != primeiro_digito_atual:
                            divergencias.append({
                                'nota': numero_nota,
                                'cfop_atual': cfop_item,
                                'esperado': f"{primeiro_digito_esperado}xxx",
                                'natureza': natureza
                            })
                
                resultado = f"VALIDAÇÃO COMPLETA\n"
                resultado += f"Total de itens analisados: {total_itens}\n"
                resultado += f"Divergências encontradas: {len(divergencias)}\n\n"
                
                if divergencias:
                    resultado += "ITENS COM DIVERGÊNCIA:\n"
                    for d in divergencias[:10]:  # Limitar a 10
                        resultado += f"- Nota {d['nota']}: CFOP {d['cfop_atual']} "
                        resultado += f"(esperado {d['esperado']}) - {d['natureza']}\n"
                    
                    if len(divergencias) > 10:
                        resultado += f"... e mais {len(divergencias) - 10} divergências.\n"
                else:
                    resultado += "✅ Todos os CFOPs estão corretos!\n"
                
                return resultado
                
            except Exception as e:
                return f"Erro na validação: {str(e)}"
        
        def buscar_por_chave_acesso(chave: str) -> str:
            """Busca nota pela chave de acesso completa ou parcial"""
            try:
                # Buscar no cabeçalho
                cab = self.df_cabecalho[
                    self.df_cabecalho['CHAVE DE ACESSO'].astype(str).str.contains(chave)
                ]
                
                if cab.empty:
                    return f"Nenhuma nota encontrada com chave contendo: {chave}"
                
                resultado = "CABEÇALHO:\n" + cab.to_string() + "\n\n"
                
                # Buscar itens
                numero = str(cab.iloc[0]['NÚMERO'])
                itens = self.df_itens[self.df_itens['NÚMERO'].astype(str) == numero]
                
                if not itens.empty:
                    resultado += "ITENS:\n" + itens.to_string()
                
                return resultado
                
            except Exception as e:
                return f"Erro ao buscar por chave: {str(e)}"
        
        # Criar lista de ferramentas
        tools = [
            Tool(
                name="buscar_nota_cabecalho",
                func=buscar_nota_cabecalho,
                description="Busca informações de cabeçalho de uma nota fiscal. Use o número da nota como parâmetro."
            ),
            Tool(
                name="buscar_itens_nota",
                func=buscar_itens_nota,
                description="Busca todos os itens de uma nota fiscal. Use o número da nota como parâmetro."
            ),
            Tool(
                name="buscar_cfop",
                func=buscar_cfop,
                description="Busca informações sobre um código CFOP específico na tabela. Use o código CFOP de 4 dígitos."
            ),
            Tool(
                name="listar_cfops_por_tipo",
                func=listar_cfops_por_tipo,
                description="Lista CFOPs que começam com um dígito específico (1-7). Útil para explorar CFOPs de entrada/saída e âmbito."
            ),
            Tool(
                name="contar_notas",
                func=contar_notas,
                description="Retorna o número total de notas fiscais no arquivo de cabeçalho."
            ),
            Tool(
                name="contar_itens",
                func=contar_itens,
                description="Retorna o número total de itens nas notas fiscais."
            ),
            Tool(
                name="validar_todas_notas",
                func=validar_todas_notas,
                description="Valida CFOP de todas as notas e retorna um resumo com divergências encontradas."
            ),
            Tool(
                name="buscar_por_chave_acesso",
                func=buscar_por_chave_acesso,
                description="Busca nota pela chave de acesso completa ou parcial de 44 dígitos."
            )
        ]
        
        return tools
    
    def _inferir_primeiro_digito(self, natureza: str, uf_emit: str, 
                                  uf_dest: str, destino_op: str) -> str:
        """Infere o primeiro dígito do CFOP baseado nas regras"""
        natureza = natureza.upper()
        
        # Determinar se é entrada ou saída
        is_entrada = any(palavra in natureza for palavra in 
                        ['ENTRADA', 'COMPRA', 'DEVOLUÇÃO', 'DEV'])
        is_saida = any(palavra in natureza for palavra in 
                      ['VENDA', 'REMESSA']) and 'DEV' not in natureza
        
        # Determinar âmbito
        if '1 - OPERAÇÃO INTERNA' in destino_op or uf_emit == uf_dest:
            return '1' if is_entrada else '5'
        elif '2 - OPERAÇÃO INTERESTADUAL' in destino_op or uf_emit != uf_dest:
            return '2' if is_entrada else '6'
        elif '3 - OPERAÇÃO COM EXTERIOR' in destino_op:
            return '3' if is_entrada else '7'
        
        return '?'
    
    def processar_pergunta(self, pergunta: str) -> str:
        """Processa uma pergunta usando o agente"""
        try:
            resultado = self.agent_executor.invoke({"input": pergunta})
            return resultado["output"]
        except Exception as e:
            return f"Erro ao processar pergunta: {str(e)}"