# 🧾 Sistema de Validação CFOP - Notas Fiscais

Sistema inteligente para análise e validação automática de códigos CFOP (Código Fiscal de Operações e Prestações) em Notas Fiscais Eletrônicas brasileiras, utilizando Inteligência Artificial.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![LangChain](https://img.shields.io/badge/LangChain-0.1-orange)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple)

---

## 🎯 Funcionalidades

- ✅ **Validação Automática de CFOP** usando IA (GPT-4)
- 📊 **Análise de Notas Fiscais** em lote ou individual
- 🤖 **Agente Inteligente** com LangChain para consultas em linguagem natural
- 📤 **Upload de Arquivos** via interface web intuitiva
- 🔍 **Detecção de Divergências** entre CFOP informado e inferido
- 📋 **Relatórios Detalhados** com justificativas fiscais
- 🌐 **Interface Web** moderna e responsiva
- 📚 **API REST** completa com Swagger/OpenAPI

---

## 🏗️ Arquitetura
```
┌─────────────────┐
│   Interface Web │  ← Usuário interage
└────────┬────────┘
         │
    ┌────▼─────┐
    │ FastAPI  │  ← API REST
    └────┬─────┘
         │
    ┌────▼──────────┐
    │   LangChain   │  ← Orquestração IA
    │   + OpenAI    │
    └────┬──────────┘
         │
    ┌────▼─────────┐
    │ Validador    │  ← Lógica de negócio
    │ CFOP         │
    └──────────────┘
```

---

## 📦 Tecnologias Utilizadas

### Backend
- **FastAPI** - Framework web moderno e rápido
- **LangChain** - Framework para aplicações com LLM
- **OpenAI GPT-4** - Modelo de linguagem para análise
- **Pandas** - Processamento de dados CSV
- **Python 3.9+** - Linguagem base

### DevOps
- **ngrok** - Túnel para exposição pública
- **Uvicorn** - Servidor ASGI
- **Google Colab** - Ambiente de execução

### Frontend
- **HTML5/CSS3** - Interface web
- **JavaScript** - Interatividade
- **Swagger UI** - Documentação API

---

## 🚀 Instalação e Uso

### Opção 1: Google Colab (Recomendado)

Siga o guia completo: **[GUIA_SETUP_COLAB.md](GUIA_SETUP_COLAB.md)**

Resumo rápido:
```python
# 1. Clonar repositório
!git clone https://github.com/seu-usuario/validador-cfop.git
%cd validador-cfop

# 2. Instalar dependências
!pip install -r requirements.txt

# 3. Configurar secrets e iniciar
# (Ver guia completo para detalhes)
```

### Opção 2: Local
```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/validador-cfop.git
cd validador-cfop

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env
echo "OPENAI_API_KEY=sua-chave-aqui" > .env

# 5. Executar
uvicorn main:app --reload
```

Acesse: http://localhost:8000

---

## 📊 Formato dos Dados

### Entrada: Arquivo ZIP contendo 3 CSVs

#### 1️⃣ 202401_NFs_Cabecalho.csv
Informações gerais das Notas Fiscais:
```csv
CHAVE DE ACESSO,NÚMERO,NATUREZA DA OPERAÇÃO,UF EMITENTE,UF DESTINATÁRIO,DESTINO DA OPERAÇÃO,...
41240106267630001509550010035101291224888487,3510129,Outras Entradas - Dev Remessa Escola,PR,PA,2 - OPERAÇÃO INTERESTADUAL,...
```

#### 2️⃣ 202401_NFs_Itens.csv
Itens detalhados das Notas Fiscais:
```csv
CHAVE DE ACESSO,NÚMERO,DESCRIÇÃO DO PRODUTO/SERVIÇO,CFOP,QUANTIDADE,VALOR TOTAL,...
41240106267630001509550010035101291224888487,3510129,COLECAO SPE EF1 4ANO VOL 1 AL,2949,1.0,522.5,...
```

#### 3️⃣ CFOP.csv
Tabela de códigos CFOP:
```csv
CFOP,DESCRIÇÃO,APLICAÇÃO
1102,Compra para comercialização,Classificam-se neste código as compras...
2949,Outra entrada de mercadoria ou prestação de serviço não especificada,...
```

---

## 🤖 Como Funciona

### 1. Inferência de CFOP

O sistema analisa diversos campos para inferir o CFOP correto:

**Passo 1 - Tipo de Operação:**
- Palavras-chave na "NATUREZA DA OPERAÇÃO"
- Entrada: "COMPRA", "ENTRADA", "DEVOLUÇÃO"
- Saída: "VENDA", "REMESSA"

**Passo 2 - Âmbito da Operação:**
- Comparação de UF Emitente vs UF Destinatário
- Campo "DESTINO DA OPERAÇÃO"
- Resultado: 1xxx, 2xxx, 3xxx (entrada) ou 5xxx, 6xxx, 7xxx (saída)

**Passo 3 - Natureza Específica:**
- Análise detalhada da operação
- Consulta à tabela CFOP
- Aplicação de regras fiscais

**Passo 4 - Validação:**
- Compara CFOP inferido vs CFOP informado
- Gera alertas de divergência
- Justifica a classificação

### 2. Agente Inteligente

Utiliza LangChain com ferramentas especializadas:
- 🔍 `buscar_nota_cabecalho` - Busca dados gerais da NF
- 📦 `buscar_itens_nota` - Lista itens da NF
- 📋 `buscar_cfop` - Consulta tabela CFOP
- ✅ `validar_todas_notas` - Validação em lote
- 🔑 `buscar_por_chave_acesso` - Busca por chave completa
- Mais 3 ferramentas auxiliares...

---

## 💬 Exemplos de Uso

### Interface de Chat

**Você:**
> Validar CFOP de todas as notas fiscais

**IA:**
> ✅ VALIDAÇÃO COMPLETA
> 
> Total de itens analisados: 1.247
> Divergências encontradas: 3
> 
> ITENS COM DIVERGÊNCIA:
> - Nota 3510129: CFOP 2949 (esperado 2xxx) - Outras Entradas - Dev Remessa Escola
> - Nota 2525: CFOP 6403 (esperado 6xxx) - VENDA DE MERCADORIA FORA DO ESTADO
> ...

---

## 📖 API Reference

### Endpoints Principais

#### `GET /`
Página inicial com menu de navegação

#### `GET /upload`
Interface de upload de arquivos ZIP

#### `GET /analise`
Interface de análise com chat IA

#### `POST /processar_upload/`
Processa upload do ZIP com CSVs

#### `POST /analisar/`
Análise com agente IA

#### `GET /status`
Status da aplicação

---

## 🔒 Segurança

- 🔑 API Keys armazenadas em variáveis de ambiente
- 🚫 Validação de tipos de arquivo (apenas .zip)
- 🧹 Limpeza automática de arquivos temporários
- ⚠️ Tratamento de erros robusto
- 📝 Logs de todas operações

---

## 🎓 Regras de Negócio

### Tabela de CFOPs (Primeiro Dígito)

| Dígito | Tipo      | Âmbito         |
|--------|-----------|----------------|
| 1      | Entrada   | Interno        |
| 2      | Entrada   | Interestadual  |
| 3      | Entrada   | Exterior       |
| 5      | Saída     | Interno        |
| 6      | Saída     | Interestadual  |
| 7      | Saída     | Exterior       |

---

## 📝 Roadmap

- [x] Sistema básico de validação
- [x] Interface web
- [x] Agente IA com LangChain
- [x] Upload de arquivos
- [ ] Exportação de relatórios (PDF, Excel)
- [ ] Dashboard com estatísticas
- [ ] Integração com banco de dados
- [ ] Autenticação de usuários
- [ ] API de webhook para notificações
- [ ] Suporte a múltiplos períodos

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Add MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

- **Seu Nome** - *Desenvolvimento inicial* - [seu-usuario](https://github.com/seu-usuario)

---

## 🙏 Agradecimentos

- Receita Federal do Brasil - Documentação de CFOP
- OpenAI - GPT-4
- LangChain - Framework IA
- FastAPI - Framework web
- Comunidade Python Brasil

---

## 📞 Suporte

- 📧 Email: seu-email@exemplo.com
- 💬 Issues: [GitHub Issues](https://github.com/seu-usuario/validador-cfop/issues)
- 📖 Documentação: [Wiki](https://github.com/seu-usuario/validador-cfop/wiki)

---

## 🌟 Se este projeto foi útil, deixe uma ⭐!

**Sistema de Validação Inteligente de CFOP**
*Desenvolvido com FastAPI + LangChain + OpenAI GPT-4*

---

*Última atualização: Outubro 2025*