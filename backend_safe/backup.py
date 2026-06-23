"""
Sistema de backup automático e manual para Google Sheets
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
import json

# Tenta importar módulos de banco de dados
# Adiciona diretório raiz ao path
import sys
import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    import sheets_database as db_module
    USE_GOOGLE_SHEETS = True
except ImportError:
    USE_GOOGLE_SHEETS = False
    try:
        import database as db_module
    except ImportError:
        db_module = None


def criar_backup_google_sheets() -> Dict[str, str]:
    """
    Cria backup da planilha atual do Google Sheets
    
    Returns:
        Dict com informações do backup (id, nome, url, timestamp)
    """
    if not USE_GOOGLE_SHEETS:
        raise ValueError("Backup do Google Sheets só está disponível quando USE_GOOGLE_SHEETS=true")
    
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        import json as json_lib
        
        sheets = db_module.get_sheets()
        spreadsheet = sheets['spreadsheet']
        spreadsheet_id = spreadsheet.id
        
        # Obtém credenciais
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS não configurado")
        
        creds_dict = json_lib.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        
        # Cria cliente do Drive
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Cria cópia da planilha
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_backup = f"Backup_{timestamp}"
        
        # Obtém nome original da planilha
        try:
            file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields='name').execute()
            nome_original = file_metadata.get('name', 'Gestão de Estoque')
        except:
            nome_original = 'Gestão de Estoque'
        
        nome_backup_completo = f"{nome_original} - {nome_backup}"
        
        # Copia a planilha
        copied_file = drive_service.files().copy(
            fileId=spreadsheet_id,
            body={'name': nome_backup_completo}
        ).execute()
        
        backup_id = copied_file.get('id')
        backup_url = f"https://docs.google.com/spreadsheets/d/{backup_id}"
        
        return {
            'id': backup_id,
            'nome': nome_backup_completo,
            'url': backup_url,
            'timestamp': timestamp,
            'data_criacao': datetime.now().isoformat()
        }
    except Exception as e:
        raise ValueError(f"Erro ao criar backup: {str(e)}")


def listar_backups(max_backups: int = 50) -> List[Dict[str, str]]:
    """
    Lista backups disponíveis
    
    Args:
        max_backups: Número máximo de backups a retornar
        
    Returns:
        Lista de backups ordenados por data (mais recente primeiro)
    """
    if not USE_GOOGLE_SHEETS:
        return []
    
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        import json as json_lib
        
        sheets = db_module.get_sheets()
        spreadsheet = db_module.get_sheets()['spreadsheet']
        spreadsheet_id = spreadsheet.id
        
        # Obtém credenciais
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            return []
        
        creds_dict = json_lib.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            'https://www.googleapis.com/auth/drive'
        ])
        
        # Cria cliente do Drive
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Busca arquivos que são cópias desta planilha ou têm "Backup" no nome
        # Obtém nome da planilha original
        try:
            file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields='name').execute()
            nome_original = file_metadata.get('name', 'Gestão de Estoque')
        except:
            nome_original = 'Gestão de Estoque'
        
        # Busca arquivos com "Backup" no nome que pertencem à mesma conta
        query = f"name contains 'Backup' and name contains '{nome_original}' and trashed=false"
        results = drive_service.files().list(
            q=query,
            fields="files(id, name, createdTime, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
            pageSize=max_backups
        ).execute()
        
        backups = []
        for file in results.get('files', []):
            backups.append({
                'id': file.get('id'),
                'nome': file.get('name'),
                'url': file.get('webViewLink'),
                'data_criacao': file.get('createdTime'),
                'data_modificacao': file.get('modifiedTime')
            })
        
        return backups
    except Exception as e:
        print(f"Erro ao listar backups: {e}")
        return []


def restaurar_backup(backup_id: str) -> Dict[str, str]:
    """
    Restaura um backup específico (cria nova cópia da planilha de backup)
    
    Args:
        backup_id: ID da planilha de backup
        
    Returns:
        Dict com informações da planilha restaurada
    """
    if not USE_GOOGLE_SHEETS:
        raise ValueError("Restauração de backup só está disponível quando USE_GOOGLE_SHEETS=true")
    
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        import json as json_lib
        
        # Obtém credenciais
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS não configurado")
        
        creds_dict = json_lib.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            'https://www.googleapis.com/auth/drive'
        ])
        
        # Cria cliente do Drive
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Obtém informações do backup
        backup_file = drive_service.files().get(fileId=backup_id, fields='name').execute()
        nome_backup = backup_file.get('name', 'Backup')
        
        # Cria cópia do backup (restauração)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_restaurado = f"Restaurado_{timestamp}"
        
        copied_file = drive_service.files().copy(
            fileId=backup_id,
            body={'name': nome_restaurado}
        ).execute()
        
        backup_id_restaurado = copied_file.get('id')
        backup_url_restaurado = f"https://docs.google.com/spreadsheets/d/{backup_id_restaurado}"
        
        return {
            'id': backup_id_restaurado,
            'nome': nome_restaurado,
            'url': backup_url_restaurado,
            'timestamp': timestamp,
            'data_restauracao': datetime.now().isoformat(),
            'backup_original': nome_backup
        }
    except Exception as e:
        raise ValueError(f"Erro ao restaurar backup: {str(e)}")


def exportar_backup_json() -> str:
    """
    Exporta todos os dados em formato JSON
    
    Returns:
        String JSON com todos os dados
    """
    try:
        itens = db_module.listar_itens()
        compromissos = db_module.listar_compromissos()
        
        # Converte para dicts
        dados = {
            'itens': [],
            'compromissos': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for item in itens:
            item_dict = {
                'id': item.id,
                'nome': item.nome,
                'quantidade_total': item.quantidade_total,
                'categoria': item.categoria,
                'descricao': item.descricao,
                'cidade': item.cidade,
                'uf': item.uf,
                'endereco': item.endereco
            }
            if hasattr(item, 'carro') and item.carro:
                item_dict['carro'] = {
                    'placa': item.carro.placa,
                    'marca': item.carro.marca,
                    'modelo': item.carro.modelo,
                    'ano': item.carro.ano
                }
            if hasattr(item, 'dados_categoria') and item.dados_categoria:
                item_dict['dados_categoria'] = item.dados_categoria
            dados['itens'].append(item_dict)
        
        for comp in compromissos:
            comp_dict = {
                'id': comp.id,
                'item_id': comp.item_id,
                'quantidade': comp.quantidade,
                'data_inicio': comp.data_inicio.isoformat() if hasattr(comp.data_inicio, 'isoformat') else str(comp.data_inicio),
                'data_fim': comp.data_fim.isoformat() if hasattr(comp.data_fim, 'isoformat') else str(comp.data_fim),
                'descricao': comp.descricao,
                'cidade': comp.cidade,
                'uf': comp.uf,
                'endereco': comp.endereco,
                'contratante': comp.contratante
            }
            dados['compromissos'].append(comp_dict)
        
        return json.dumps(dados, ensure_ascii=False, indent=2)
    except Exception as e:
        raise ValueError(f"Erro ao exportar backup JSON: {str(e)}")


def limpar_backups_antigos(dias_manter: int = 30) -> int:
    """
    Remove backups mais antigos que o número de dias especificado
    
    Args:
        dias_manter: Número de dias de backups a manter
        
    Returns:
        Número de backups removidos
    """
    if not USE_GOOGLE_SHEETS:
        return 0
    
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        from datetime import timedelta
        import json as json_lib
        
        # Obtém credenciais
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            return 0
        
        creds_dict = json_lib.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            'https://www.googleapis.com/auth/drive'
        ])
        
        # Cria cliente do Drive
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Calcula data limite
        data_limite = datetime.now() - timedelta(days=dias_manter)
        data_limite_str = data_limite.isoformat() + 'Z'
        
        # Busca backups antigos
        query = f"name contains 'Backup' and modifiedTime < '{data_limite_str}' and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        
        backups_antigos = results.get('files', [])
        removidos = 0
        
        for backup in backups_antigos:
            try:
                drive_service.files().delete(fileId=backup['id']).execute()
                removidos += 1
            except:
                pass
        
        return removidos
    except Exception as e:
        print(f"Erro ao limpar backups antigos: {e}")
        return 0
