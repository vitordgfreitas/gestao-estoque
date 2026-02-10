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
    credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    
    if credentials_json:
        # Usa credenciais da variável de ambiente
        try:
            # Remove espaços em branco e quebras de linha extras
            credentials_json = credentials_json.strip()
            
            # Tenta fazer parse do JSON
            # Se falhar, tenta remover quebras de linha e espaços extras
            try:
                creds_dict = json.loads(credentials_json)
            except json.JSONDecodeError:
                # Tenta corrigir: remove quebras de linha e espaços extras entre chaves
                import re
                # Remove quebras de linha e espaços extras, mas mantém estrutura
                fixed_json = re.sub(r'\s+', ' ', credentials_json)
                fixed_json = fixed_json.replace('{ ', '{').replace(' }', '}')
                fixed_json = fixed_json.replace('[ ', '[').replace(' ]', ']')
                try:
                    creds_dict = json.loads(fixed_json)
                except json.JSONDecodeError:
                    # Última tentativa: tenta parse linha por linha se tiver quebras
                    if '\n' in credentials_json:
                        # Remove todas as quebras de linha
                        single_line = credentials_json.replace('\n', '').replace('\r', '')
                        creds_dict = json.loads(single_line)
                    else:
                        raise
            
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        except json.JSONDecodeError as e:
            error_msg = (
                f"ERRO: GOOGLE_CREDENTIALS tem JSON invalido!\n"
                f"Detalhes: {str(e)}\n"
                f"SOLUCAO:\n"
                f"1. Acesse: https://www.freeformatter.com/json-formatter.html\n"
                f"2. Cole seu JSON completo\n"
                f"3. Clique em 'Minify' (compactar em uma linha)\n"
                f"4. Copie o resultado\n"
                f"5. No Render: Settings -> Environment -> GOOGLE_CREDENTIALS\n"
                f"6. Cole o JSON minificado (uma linha so)\n"
                f"Primeiros 100 caracteres recebidos: {credentials_json[:100]}..."
            )
            raise ValueError(error_msg)
        except Exception as e:
            raise ValueError(f"Erro ao processar GOOGLE_CREDENTIALS: {str(e)}")
    else:
        # Tenta encontrar credentials.json na raiz do projeto
        # Primeiro tenta o caminho padrão (raiz do projeto)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = script_dir  # sheets_config.py está na raiz
        credentials_path = os.path.join(root_dir, 'credentials.json')
        
        # Se não encontrar, tenta o caminho customizado da variável de ambiente
        if not os.path.exists(credentials_path):
            custom_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
            if custom_path and os.path.exists(custom_path):
                credentials_path = custom_path
            else:
                        # Tenta vários caminhos possíveis
                possible_paths = [
                    os.path.join(root_dir, 'credentials.json'),  # Raiz do projeto (onde está sheets_config.py)
                    os.path.join(os.getcwd(), 'credentials.json'),  # Diretório atual
                    os.path.join(os.path.dirname(os.getcwd()), 'credentials.json'),  # Um nível acima
                ]
                
                # Adiciona caminho do backend se estiver rodando de lá
                if 'backend' in os.getcwd():
                    backend_parent = os.path.dirname(os.getcwd())
                    possible_paths.append(os.path.join(backend_parent, 'credentials.json'))
                
                credentials_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        credentials_path = path
                        break
        
        if credentials_path and os.path.exists(credentials_path):
            # Usa arquivo de credenciais
            creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        else:
            searched_paths = '\n'.join([f"  - {p}" for p in possible_paths])
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado.\n"
                f"Procurado em:\n{searched_paths}\n"
                f"Por favor, coloque o arquivo credentials.json na raiz do projeto.\n"
                f"Diretório atual: {os.getcwd()}\n"
                f"Diretório do script: {root_dir}"
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
    sheet_carros_name = "Carros"
    sheet_contas_receber_name = "Contas a Receber"
    sheet_contas_pagar_name = "Contas a Pagar"
    sheet_financiamentos_name = "Financiamentos"
    sheet_parcelas_financiamento_name = "Parcelas Financiamento"
    
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
                sheet_itens.insert_row(["ID", "Nome", "Quantidade Total", "Categoria", "Descrição", "Cidade", "UF", "Endereço"], 1)
            else:
                # Verifica se todas as colunas existem, se não, adiciona
                headers = sheet_itens.row_values(1)
                expected_headers = ["ID", "Nome", "Quantidade Total", "Categoria", "Descrição", "Cidade", "UF", "Endereço"]
                for i, expected_header in enumerate(expected_headers):
                    if i >= len(headers) or headers[i] != expected_header:
                        # Adiciona ou atualiza a coluna na posição correta
                        col_letter = chr(65 + i)  # A=65, B=66, etc.
                        sheet_itens.update(f'{col_letter}1', [[expected_header]])
                headers = sheet_itens.row_values(1)  # Atualiza headers após modificações
        except Exception:
            # Se houver erro ao ler, tenta adicionar cabeçalhos apenas se a aba estiver vazia
            try:
                all_values = sheet_itens.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_itens.append_row(["ID", "Nome", "Quantidade Total", "Categoria", "Descrição", "Cidade", "UF", "Endereço"])
            except Exception:
                pass  # Ignora erros ao verificar/inserir cabeçalhos
    else:
        # Aba não existe, cria nova
        sheet_itens = spreadsheet.add_worksheet(title=sheet_itens_name, rows=1000, cols=10)
        # Cabeçalhos
        sheet_itens.append_row(["ID", "Nome", "Quantidade Total", "Categoria", "Descrição", "Cidade", "UF", "Endereço"])
    
    # Obtém ou cria aba de Carros
    if sheet_carros_name in existing_worksheets:
        sheet_carros = spreadsheet.worksheet(sheet_carros_name)
        # NÃO VERIFICA/CORRIGE HEADERS - deixa como está para evitar problemas
        # Headers devem ser corrigidos manualmente se necessário
    else:
        sheet_carros = spreadsheet.add_worksheet(title=sheet_carros_name, rows=1000, cols=10)
        sheet_carros.append_row(["ID", "Item ID", "Placa", "Chassi", "Renavam", "Marca", "Modelo", "Ano"])
    
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
    
    # Obtém ou cria aba de Contas a Receber
    if sheet_contas_receber_name in existing_worksheets:
        sheet_contas_receber = spreadsheet.worksheet(sheet_contas_receber_name)
        try:
            header = sheet_contas_receber.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                sheet_contas_receber.insert_row(["ID", "Compromisso ID", "Descrição", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Forma Pagamento", "Observações"], 1)
            else:
                headers = sheet_contas_receber.row_values(1)
                expected_headers = ["ID", "Compromisso ID", "Descrição", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Forma Pagamento", "Observações"]
                for i, expected_header in enumerate(expected_headers):
                    if i >= len(headers) or headers[i] != expected_header:
                        col_letter = chr(65 + i)
                        sheet_contas_receber.update(f'{col_letter}1', [[expected_header]])
        except Exception:
            try:
                all_values = sheet_contas_receber.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_contas_receber.append_row(["ID", "Compromisso ID", "Descrição", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Forma Pagamento", "Observações"])
            except Exception:
                pass
    else:
        sheet_contas_receber = spreadsheet.add_worksheet(title=sheet_contas_receber_name, rows=1000, cols=10)
        sheet_contas_receber.append_row(["ID", "Compromisso ID", "Descrição", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Forma Pagamento", "Observações"])
    
    # Obtém ou cria aba de Contas a Pagar
    if sheet_contas_pagar_name in existing_worksheets:
        sheet_contas_pagar = spreadsheet.worksheet(sheet_contas_pagar_name)
        try:
            header = sheet_contas_pagar.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                sheet_contas_pagar.insert_row(["ID", "Descrição", "Categoria", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Fornecedor", "Item ID", "Forma Pagamento", "Observações"], 1)
            else:
                headers = sheet_contas_pagar.row_values(1)
                expected_headers = ["ID", "Descrição", "Categoria", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Fornecedor", "Item ID", "Forma Pagamento", "Observações"]
                for i, expected_header in enumerate(expected_headers):
                    if i >= len(headers) or headers[i] != expected_header:
                        col_letter = chr(65 + i)
                        sheet_contas_pagar.update(f'{col_letter}1', [[expected_header]])
        except Exception:
            try:
                all_values = sheet_contas_pagar.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_contas_pagar.append_row(["ID", "Descrição", "Categoria", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Fornecedor", "Item ID", "Forma Pagamento", "Observações"])
            except Exception:
                pass
    else:
        sheet_contas_pagar = spreadsheet.add_worksheet(title=sheet_contas_pagar_name, rows=1000, cols=11)
        sheet_contas_pagar.append_row(["ID", "Descrição", "Categoria", "Valor", "Data Vencimento", "Data Pagamento", "Status", "Fornecedor", "Item ID", "Forma Pagamento", "Observações"])
    
    # Obtém ou cria aba de Financiamentos
    if sheet_financiamentos_name in existing_worksheets:
        sheet_financiamentos = spreadsheet.worksheet(sheet_financiamentos_name)
        # NÃO VERIFICA/CORRIGE HEADERS - deixa como está para evitar problemas
        # Headers devem ser corrigidos manualmente se necessário
    else:
        sheet_financiamentos = spreadsheet.add_worksheet(title=sheet_financiamentos_name, rows=1000, cols=11)
        sheet_financiamentos.append_row(["ID", "Código Contrato", "Valor Total", "Valor Entrada", "Numero Parcelas", "Valor Parcela", "Taxa Juros", "Data Inicio", "Status", "Instituicao Financeira", "Observacoes"])
    
    # Obtém ou cria aba de Parcelas Financiamento
    if sheet_parcelas_financiamento_name in existing_worksheets:
        sheet_parcelas = spreadsheet.worksheet(sheet_parcelas_financiamento_name)
        try:
            header = sheet_parcelas.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                sheet_parcelas.insert_row(["ID", "Financiamento ID", "Numero Parcela", "Valor Original", "Valor Pago", "Data Vencimento", "Data Pagamento", "Status", "Juros", "Multa", "Desconto", "Link Boleto", "Link Comprovante"], 1)
            else:
                headers = sheet_parcelas.row_values(1)
                expected_headers = ["ID", "Financiamento ID", "Numero Parcela", "Valor Original", "Valor Pago", "Data Vencimento", "Data Pagamento", "Status", "Juros", "Multa", "Desconto", "Link Boleto", "Link Comprovante"]
                for i, expected_header in enumerate(expected_headers):
                    if i >= len(headers) or headers[i] != expected_header:
                        col_letter = chr(65 + i)
                        sheet_parcelas.update(f'{col_letter}1', [[expected_header]])
        except Exception:
            try:
                all_values = sheet_parcelas.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_parcelas.append_row(["ID", "Financiamento ID", "Numero Parcela", "Valor Original", "Valor Pago", "Data Vencimento", "Data Pagamento", "Status", "Juros", "Multa", "Desconto", "Link Boleto", "Link Comprovante"])
            except Exception:
                pass
    else:
        sheet_parcelas = spreadsheet.add_worksheet(title=sheet_parcelas_financiamento_name, rows=1000, cols=13)
        sheet_parcelas.append_row(["ID", "Financiamento ID", "Numero Parcela", "Valor Original", "Valor Pago", "Data Vencimento", "Data Pagamento", "Status", "Juros", "Multa", "Desconto", "Link Boleto", "Link Comprovante"])
    
    # Obtém ou cria aba de Categorias_Itens
    sheet_categorias_itens_name = "Categorias_Itens"
    if sheet_categorias_itens_name in existing_worksheets:
        sheet_categorias_itens = spreadsheet.worksheet(sheet_categorias_itens_name)
        try:
            header = sheet_categorias_itens.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                sheet_categorias_itens.insert_row(["ID", "Nome", "Data Criacao"], 1)
            else:
                headers = sheet_categorias_itens.row_values(1)
                expected_headers = ["ID", "Nome", "Data Criacao"]
                for i, expected_header in enumerate(expected_headers):
                    if i >= len(headers) or headers[i] != expected_header:
                        col_letter = chr(65 + i)
                        sheet_categorias_itens.update(f'{col_letter}1', [[expected_header]])
        except Exception:
            try:
                all_values = sheet_categorias_itens.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_categorias_itens.append_row(["ID", "Nome", "Data Criacao"])
            except Exception:
                pass
    else:
        sheet_categorias_itens = spreadsheet.add_worksheet(title=sheet_categorias_itens_name, rows=1000, cols=3)
        sheet_categorias_itens.append_row(["ID", "Nome", "Data Criacao"])
    
    # Obtém ou cria aba de Financiamentos_Itens (relacionamento many-to-many)
    sheet_financiamentos_itens_name = "Financiamentos_Itens"
    if sheet_financiamentos_itens_name in existing_worksheets:
        sheet_financiamentos_itens = spreadsheet.worksheet(sheet_financiamentos_itens_name)
        try:
            header = sheet_financiamentos_itens.get('A1')
            if not header or (isinstance(header, list) and len(header) > 0 and header[0][0] != 'ID'):
                sheet_financiamentos_itens.insert_row(["ID", "Financiamento ID", "Item ID", "Valor Proporcional"], 1)
            else:
                headers = sheet_financiamentos_itens.row_values(1)
                expected_headers = ["ID", "Financiamento ID", "Item ID", "Valor Proporcional"]
                for i, expected_header in enumerate(expected_headers):
                    if i >= len(headers) or headers[i] != expected_header:
                        col_letter = chr(65 + i)
                        sheet_financiamentos_itens.update(f'{col_letter}1', [[expected_header]])
        except Exception:
            try:
                all_values = sheet_financiamentos_itens.get_all_values()
                if not all_values or len(all_values) == 0:
                    sheet_financiamentos_itens.append_row(["ID", "Financiamento ID", "Item ID", "Valor Proporcional"])
            except Exception:
                pass
    else:
        sheet_financiamentos_itens = spreadsheet.add_worksheet(title=sheet_financiamentos_itens_name, rows=1000, cols=4)
        sheet_financiamentos_itens.append_row(["ID", "Financiamento ID", "Item ID", "Valor Proporcional"])
    
    return {
        'spreadsheet': spreadsheet,
        'sheet_itens': sheet_itens,
        'sheet_compromissos': sheet_compromissos,
        'sheet_carros': sheet_carros,
        'sheet_contas_receber': sheet_contas_receber,
        'sheet_contas_pagar': sheet_contas_pagar,
        'sheet_financiamentos': sheet_financiamentos,
        'sheet_parcelas_financiamento': sheet_parcelas,
        'sheet_categorias_itens': sheet_categorias_itens,
        'sheet_financiamentos_itens': sheet_financiamentos_itens,
        'spreadsheet_id': spreadsheet.id,
        'spreadsheet_url': spreadsheet.url
    }
