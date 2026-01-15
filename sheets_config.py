"""
Configuração e autenticação do Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# Escopos necessários para acessar Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    """
    Retorna um cliente autenticado do Google Sheets
    
    Requer arquivo de credenciais em:
    - Variável de ambiente GOOGLE_CREDENTIALS (JSON como string)
    - Ou arquivo credentials.json na raiz do projeto
    """
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    
    if credentials_json:
        # Usa credenciais da variável de ambiente
        creds_dict = json.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    elif os.path.exists(credentials_path):
        # Usa arquivo de credenciais
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    else:
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {credentials_path}\n"
            "Por favor, configure as credenciais do Google Sheets.\n"
            "Veja GOOGLE_SHEETS_SETUP.md para instruções."
        )
    
    return gspread.authorize(creds)


def get_or_create_spreadsheet(client, spreadsheet_id=None, spreadsheet_name="Gestão de Estoque"):
    """
    Obtém uma planilha do Google Sheets existente
    
    Args:
        client: Cliente gspread autenticado
        spreadsheet_id: ID da planilha existente (OBRIGATÓRIO)
        spreadsheet_name: Nome da planilha (não usado se spreadsheet_id fornecido)
    
    Returns:
        Objeto spreadsheet do gspread
    """
    if spreadsheet_id:
        try:
            return client.open_by_key(spreadsheet_id)
        except gspread.exceptions.APIError as e:
            error_info = e.response.json() if hasattr(e, 'response') else {}
            if error_info.get('error', {}).get('code') == 403:
                raise Exception(
                    f"Erro de permissão ao acessar planilha.\n"
                    f"Verifique se:\n"
                    f"1. A planilha foi compartilhada com o email da conta de serviço\n"
                    f"2. O email da conta de serviço tem permissão de Editor\n"
                    f"3. O ID da planilha está correto: {spreadsheet_id}\n"
                    f"Erro original: {str(e)}"
                )
            raise Exception(f"Erro ao abrir planilha com ID {spreadsheet_id}: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao abrir planilha com ID {spreadsheet_id}: {str(e)}")
    else:
        raise Exception(
            "ID da planilha não fornecido!\n"
            "Configure a variável de ambiente GOOGLE_SHEET_ID ou use configurar_id.bat\n"
            "Não é possível criar nova planilha automaticamente devido a limitações."
        )


def init_sheets(spreadsheet_id=None, spreadsheet_name="Gestão de Estoque"):
    """
    Inicializa as planilhas necessárias
    
    Returns:
        dict com as planilhas (worksheets) configuradas
    """
    client = get_sheets_client()
    spreadsheet = get_or_create_spreadsheet(client, spreadsheet_id, spreadsheet_name)
    
    # Nomes das abas
    sheet_itens_name = "Itens"
    sheet_compromissos_name = "Compromissos"
    
    # Lista todas as abas existentes
    existing_worksheets = [ws.title for ws in spreadsheet.worksheets()]
    
    # Obtém ou cria aba de Itens
    if sheet_itens_name in existing_worksheets:
        # Aba já existe, apenas obtém referência
        sheet_itens = spreadsheet.worksheet(sheet_itens_name)
        # Verifica se tem cabeçalhos, se não tiver, adiciona
        try:
            header = sheet_itens.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                # Se a primeira célula não for 'ID', adiciona cabeçalhos na primeira linha
                sheet_itens.insert_row(["ID", "Nome", "Quantidade Total", "Descrição", "Cidade", "UF", "Endereço"], 1)
            else:
                # Verifica se todas as colunas existem, se não, adiciona
                headers = sheet_itens.row_values(1)
                if len(headers) < 7:
                    # Adiciona colunas faltantes
                    if len(headers) < 4:
                        sheet_itens.update('D1', [['Descrição']])
                    if len(headers) < 5:
                        sheet_itens.update('E1', [['Cidade']])
                    if len(headers) < 6:
                        sheet_itens.update('F1', [['UF']])
                    if len(headers) < 7:
                        sheet_itens.update('G1', [['Endereço']])
                # Verifica se as colunas estão corretas
                headers = sheet_itens.row_values(1)
                if len(headers) >= 5 and headers[4] != "Cidade":
                    sheet_itens.update('E1', [['Cidade']])
                if len(headers) >= 6 and headers[5] != "UF":
                    sheet_itens.update('F1', [['UF']])
                if len(headers) >= 7 and headers[6] != "Endereço":
                    sheet_itens.update('G1', [['Endereço']])
        except Exception:
            # Se houver erro ao ler, tenta adicionar cabeçalhos apenas se a aba estiver vazia
            try:
                all_values = sheet_itens.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_itens.append_row(["ID", "Nome", "Quantidade Total", "Descrição", "Cidade", "UF", "Endereço"])
            except Exception:
                pass  # Ignora erros ao verificar/inserir cabeçalhos
    else:
        # Aba não existe, cria nova
        sheet_itens = spreadsheet.add_worksheet(title=sheet_itens_name, rows=1000, cols=10)
        # Cabeçalhos
        sheet_itens.append_row(["ID", "Nome", "Quantidade Total", "Descrição", "Cidade", "UF", "Endereço"])
    
    # Obtém ou cria aba de Compromissos
    if sheet_compromissos_name in existing_worksheets:
        # Aba já existe, apenas obtém referência
        sheet_compromissos = spreadsheet.worksheet(sheet_compromissos_name)
        # Verifica se tem cabeçalhos, se não tiver, adiciona
        try:
            header = sheet_compromissos.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                # Se a primeira célula não for 'ID', adiciona cabeçalhos na primeira linha
                sheet_compromissos.insert_row(["ID", "Item ID", "Quantidade", "Data Início", "Data Fim", "Descrição", "Cidade", "UF", "Endereço", "Contratante"], 1)
            else:
                # Verifica se todas as colunas existem, se não, adiciona
                headers = sheet_compromissos.row_values(1)
                if len(headers) < 10:
                    # Adiciona colunas faltantes
                    if len(headers) < 7:
                        sheet_compromissos.update('G1', [['Cidade']])
                    if len(headers) < 8:
                        sheet_compromissos.update('H1', [['UF']])
                    if len(headers) < 9:
                        sheet_compromissos.update('I1', [['Endereço']])
                    if len(headers) < 10:
                        sheet_compromissos.update('J1', [['Contratante']])
                # Verifica se as colunas estão corretas
                headers = sheet_compromissos.row_values(1)
                if len(headers) >= 7 and headers[6] != "Cidade":
                    sheet_compromissos.update('G1', [['Cidade']])
                if len(headers) >= 8 and headers[7] != "UF":
                    sheet_compromissos.update('H1', [['UF']])
                if len(headers) >= 9 and headers[8] != "Endereço":
                    sheet_compromissos.update('I1', [['Endereço']])
                if len(headers) >= 10 and headers[9] != "Contratante":
                    sheet_compromissos.update('J1', [['Contratante']])
        except Exception:
            # Se houver erro ao ler, tenta adicionar cabeçalhos apenas se a aba estiver vazia
            try:
                all_values = sheet_compromissos.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_compromissos.append_row(["ID", "Item ID", "Quantidade", "Data Início", "Data Fim", "Descrição", "Cidade", "UF", "Endereço", "Contratante"])
            except Exception:
                pass  # Ignora erros ao verificar/inserir cabeçalhos
    else:
        # Aba não existe, cria nova
        sheet_compromissos = spreadsheet.add_worksheet(title=sheet_compromissos_name, rows=1000, cols=10)
        # Cabeçalhos
        sheet_compromissos.append_row(["ID", "Item ID", "Quantidade", "Data Início", "Data Fim", "Descrição", "Cidade", "UF", "Endereço", "Contratante"])
    
    return {
        'spreadsheet': spreadsheet,
        'sheet_itens': sheet_itens,
        'sheet_compromissos': sheet_compromissos,
        'spreadsheet_id': spreadsheet.id,
        'spreadsheet_url': spreadsheet.url
    }
