import zipfile
import os
import shutil
from pathlib import Path
from typing import List

def extrair_zip(zip_path: Path, destino: Path) -> List[Path]:
    """
    Extrai arquivos de um ZIP para o diretório de destino
    
    Args:
        zip_path: Caminho do arquivo ZIP
        destino: Diretório de destino
        
    Returns:
        Lista de arquivos extraídos
    """
    arquivos_extraidos = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Listar arquivos no ZIP
            lista_arquivos = zip_ref.namelist()
            
            # Extrair todos os arquivos
            zip_ref.extractall(destino)
            
            # Coletar caminhos dos arquivos extraídos
            for arquivo in lista_arquivos:
                arquivo_path = destino / arquivo
                if arquivo_path.exists() and arquivo_path.is_file():
                    arquivos_extraidos.append(arquivo_path)
        
        return arquivos_extraidos
        
    except zipfile.BadZipFile:
        raise ValueError("Arquivo ZIP inválido ou corrompido")
    except Exception as e:
        raise Exception(f"Erro ao extrair ZIP: {str(e)}")

def limpar_diretorio_temp(diretorio: Path):
    """
    Remove todos os arquivos de um diretório temporário
    
    Args:
        diretorio: Caminho do diretório a ser limpo
    """
    if diretorio.exists():
        for item in diretorio.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f"Erro ao remover {item}: {e}")

def validar_arquivos_csv(diretorio: Path, arquivos_necessarios: List[str]) -> dict:
    """
    Valida se os arquivos CSV necessários existem no diretório
    
    Args:
        diretorio: Diretório onde procurar os arquivos
        arquivos_necessarios: Lista de nomes de arquivos necessários
        
    Returns:
        Dicionário com status da validação
    """
    resultado = {
        "valido": True,
        "arquivos_encontrados": [],
        "arquivos_faltando": [],
        "mensagem": ""
    }
    
    arquivos_no_dir = [f.name for f in diretorio.glob("*.csv")]
    
    for arquivo in arquivos_necessarios:
        if arquivo in arquivos_no_dir:
            resultado["arquivos_encontrados"].append(arquivo)
        else:
            resultado["arquivos_faltando"].append(arquivo)
            resultado["valido"] = False
    
    if resultado["valido"]:
        resultado["mensagem"] = "Todos os arquivos necessários foram encontrados!"
    else:
        resultado["mensagem"] = f"Arquivos faltando: {', '.join(resultado['arquivos_faltando'])}"
    
    return resultado

def obter_tamanho_arquivo(arquivo_path: Path) -> str:
    """
    Retorna o tamanho de um arquivo em formato legível
    
    Args:
        arquivo_path: Caminho do arquivo
        
    Returns:
        String com tamanho formatado
    """
    if not arquivo_path.exists():
        return "Arquivo não encontrado"
    
    tamanho_bytes = arquivo_path.stat().st_size
    
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} bytes"
    elif tamanho_bytes < 1024 * 1024:
        return f"{tamanho_bytes / 1024:.2f} KB"
    else:
        return f"{tamanho_bytes / (1024 * 1024):.2f} MB"

def criar_estrutura_diretorios():
    """Cria a estrutura de diretórios necessária para a aplicação"""
    diretorios = [
        Path("uploads"),
        Path("temp_csvs"),
        Path("static")
    ]
    
    for diretorio in diretorios:
        diretorio.mkdir(exist_ok=True)
        print(f"✅ Diretório criado/verificado: {diretorio}")

def formatar_chave_acesso(chave: str) -> dict:
    """
    Formata e extrai informações de uma chave de acesso de 44 dígitos
    
    Args:
        chave: Chave de acesso de 44 dígitos
        
    Returns:
        Dicionário com as informações extraídas
    """
    if len(chave) != 44:
        return {"erro": "Chave de acesso deve ter 44 dígitos"}
    
    return {
        "chave_completa": chave,
        "uf": chave[0:2],
        "ano_mes": chave[2:6],
        "cnpj": chave[6:20],
        "modelo": chave[20:22],
        "serie": chave[22:25],
        "numero_nf": chave[25:34],
        "tipo_emissao": chave[34:35],
        "codigo_numerico": chave[35:43],
        "digito_verificador": chave[43:44]
    }

def gerar_relatorio_basico(df_cabecalho, df_itens, df_cfop) -> str:
    """
    Gera um relatório básico sobre os dados carregados
    
    Args:
        df_cabecalho: DataFrame com dados de cabeçalho
        df_itens: DataFrame com itens
        df_cfop: DataFrame com tabela CFOP
        
    Returns:
        String com o relatório
    """
    relatorio = "="*60 + "\n"
    relatorio += "RELATÓRIO DE DADOS CARREGADOS\n"
    relatorio += "="*60 + "\n\n"
    
    relatorio += f"📊 Notas Fiscais (Cabeçalho): {len(df_cabecalho)}\n"
    relatorio += f"📦 Total de Itens: {len(df_itens)}\n"
    relatorio += f"📋 Códigos CFOP cadastrados: {len(df_cfop)}\n\n"
    
    # Estatísticas de UF
    if 'UF EMITENTE' in df_cabecalho.columns:
        relatorio += "🗺️ Estados Emitentes:\n"
        ufs = df_cabecalho['UF EMITENTE'].value_counts()
        for uf, count in ufs.head(5).items():
            relatorio += f"   - {uf}: {count} notas\n"
        relatorio += "\n"
    
    # Tipos de operação
    if 'DESTINO DA OPERAÇÃO' in df_cabecalho.columns:
        relatorio += "🔄 Tipos de Operação:\n"
        tipos = df_cabecalho['DESTINO DA OPERAÇÃO'].value_counts()
        for tipo, count in tipos.items():
            relatorio += f"   - {tipo}: {count} notas\n"
        relatorio += "\n"
    
    relatorio += "="*60 + "\n"
    
    return relatorio