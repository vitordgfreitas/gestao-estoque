"""
Implementação do banco de dados usando Google Sheets
"""
from sheets_config import init_sheets
from datetime import date, datetime
import os
import time
import gspread
import validacoes
import auditoria
import random

# Cache das planilhas
_sheets_cache = None

# Cache de dados para reduzir chamadas à API
_data_cache = {
    'itens': None,
    'compromissos': None,
    'contas_receber': None,
    'contas_pagar': None,
    'cache_time': None,
    'cache_ttl': 30  # Time to live em segundos
}

def _clear_cache():
    """Limpa o cache de dados"""
    global _data_cache
    _data_cache = {
        'itens': None,
        'compromissos': None,
        'contas_receber': None,
        'contas_pagar': None,
        'cache_time': None,
        'cache_ttl': 30
    }

def _is_cache_valid():
    """Verifica se o cache ainda é válido"""
    if _data_cache['cache_time'] is None:
        return False
    return (time.time() - _data_cache['cache_time']) < _data_cache['cache_ttl']

# Rate Limiter para evitar exceder limites da API
class RateLimiter:
    """Limita a taxa de requisições à API do Google Sheets"""
    def __init__(self, max_calls=50, period=60):
        self.max_calls = max_calls  # Máximo de chamadas
        self.period = period  # Período em segundos
        self.calls = []  # Timestamps das chamadas
    
    def wait_if_needed(self):
        """Aguarda se necessário para não exceder o limite"""
        now = time.time()
        # Remove chamadas antigas (fora do período)
        self.calls = [t for t in self.calls if now - t < self.period]
        
        # Se atingiu o limite, espera até a chamada mais antiga expirar
        if len(self.calls) >= self.max_calls:
            oldest_call = self.calls[0]
            sleep_time = self.period - (now - oldest_call) + 0.1  # +0.1 para margem
            if sleep_time > 0:
                print(f"[RATE_LIMIT] Aguardando {sleep_time:.1f}s para não exceder limite...")
                time.sleep(sleep_time)
                # Remove a chamada mais antiga após esperar
                self.calls.pop(0)
        
        # Registra esta chamada
        self.calls.append(time.time())

# Instância global do rate limiter
_rate_limiter = RateLimiter(max_calls=50, period=60)  # 50 chamadas por minuto (margem de segurança)

def _retry_with_backoff(func, max_retries=5, initial_delay=2.0):
    """
    Executa uma função com retry exponencial em caso de erro 429
    
    Args:
        func: Função a ser executada (sem argumentos)
        max_retries: Número máximo de tentativas (aumentado para 5)
        initial_delay: Delay inicial em segundos (aumentado para 2.0)
    
    Returns:
        Resultado da função
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Aplica rate limiting antes de cada tentativa
            _rate_limiter.wait_if_needed()
            return func()
        except gspread.exceptions.APIError as e:
            # Verifica se é erro 429
            error_dict = getattr(e, 'response', None)
            if error_dict and hasattr(error_dict, 'json'):
                try:
                    error_dict = error_dict.json()
                except:
                    error_dict = {}
            elif not isinstance(error_dict, dict):
                error_dict = {}
            
            error_code = error_dict.get('code', 0) if error_dict else 0
            error_message = str(e)
            
            is_rate_limit = (
                error_code == 429 or 
                '429' in error_message or 
                'Quota exceeded' in error_message or 
                'RATE_LIMIT_EXCEEDED' in error_message
            )
            
            if is_rate_limit and attempt < max_retries - 1:
                # Calcula delay com backoff exponencial + jitter
                delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"[RETRY] Erro 429 - Tentativa {attempt + 1}/{max_retries}. Aguardando {delay:.1f}s...")
                time.sleep(delay)
                last_error = e
                continue
            else:
                # Não é erro 429 ou esgotou tentativas
                raise e
        except Exception as e:
            # Outros erros não fazem retry
            raise e
    
    # Se chegou aqui, esgotou todas as tentativas
    if last_error:
        raise last_error

def _handle_api_error(e, operation_name):
    """Trata erros da API do Google Sheets"""
    if isinstance(e, gspread.exceptions.APIError):
        # Tenta extrair informações do erro
        error_message = str(e)
        error_dict = getattr(e, 'response', None)
        
        # Se response for um objeto Response do requests, pega o json
        if error_dict and hasattr(error_dict, 'json'):
            try:
                error_dict = error_dict.json()
            except:
                error_dict = {}
        elif not isinstance(error_dict, dict):
            error_dict = {}
        
        error_code = error_dict.get('code', 0) if error_dict else 0
        
        # Verifica se é erro 429 (quota exceeded)
        if error_code == 429 or '429' in error_message or 'Quota exceeded' in error_message or 'RATE_LIMIT_EXCEEDED' in error_message:
            raise Exception(
                f"[!] Limite de Requisicoes do Google Sheets Excedido!\n\n"
                f"O Google Sheets tem um limite de 60 requisicoes de leitura por minuto.\n\n"
                f"Operacao: {operation_name}\n\n"
                f"Solucoes:\n"
                f"1. Aguarde 1-2 minutos antes de tentar novamente\n"
                f"2. Evite fazer muitas operacoes em sequencia\n"
                f"3. Use SQLite local para desenvolvimento/testes (configure USE_GOOGLE_SHEETS=false)\n"
                f"4. Solicite aumento de quota no Google Cloud Console se necessario"
            )
    # Re-raise o erro original se não for 429
    raise e

def get_sheets():
    """Obtém ou inicializa as planilhas"""
    global _sheets_cache
    
    if _sheets_cache is None:
        spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
        spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Gestão de Estoque')
        
        # Se não tiver ID configurado, usa o ID padrão fornecido pelo usuário
        if not spreadsheet_id:
            spreadsheet_id = "1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE"
            import warnings
            warnings.warn(
                "GOOGLE_SHEET_ID não configurado. Usando ID padrão. "
                "Configure com: configurar_id.bat ou variável de ambiente GOOGLE_SHEET_ID"
            )
        
        _sheets_cache = init_sheets(spreadsheet_id, spreadsheet_name)
    
    return _sheets_cache


def obter_categorias():
    """Obtém todas as categorias cadastradas na tabela Categorias_Itens"""
    sheets = get_sheets()
    sheet_categorias = sheets['sheet_categorias_itens']
    
    try:
        records = _retry_with_backoff(lambda: sheet_categorias.get_all_records())
        categorias = []
        for record in records:
            if record and record.get('Nome'):
                categoria = record.get('Nome').strip()
                if categoria:
                    categorias.append(categoria)
        
        # Retorna lista ordenada de categorias
        return sorted(categorias) if categorias else []
    except Exception as e:
        print(f"Erro ao obter categorias: {e}")
        return []


def obter_campos_categoria(categoria):
    """Obtém os campos específicos de uma categoria lendo os cabeçalhos da aba com o nome da categoria
    
    Args:
        categoria: Nome da categoria
        
    Returns:
        Lista de nomes de campos (cabeçalhos) da aba da categoria, ou lista vazia se a aba não existir
    """
    sheets = get_sheets()
    spreadsheet = sheets['spreadsheet']
    
    try:
        # Tenta obter a aba com o nome da categoria
        worksheet = spreadsheet.worksheet(categoria)
        # Lê a primeira linha (cabeçalhos)
        headers = worksheet.row_values(1)
        # Remove campos padrão que não são específicos da categoria
        # Campos padrão: ID, Item ID (são gerenciados pelo sistema)
        campos_especificos = [h for h in headers if h not in ['ID', 'Item ID', '']]
        return campos_especificos
    except gspread.exceptions.WorksheetNotFound:
        # Aba não existe, retorna lista vazia
        return []
    except Exception:
        # Outro erro, retorna lista vazia
        return []


def criar_categoria(nome_categoria):
    """Cria uma nova categoria na tabela Categorias_Itens
    
    Args:
        nome_categoria: Nome da categoria a ser criada
        
    Returns:
        ID da categoria criada ou None se já existir
    """
    sheets = get_sheets()
    sheet_categorias = sheets['sheet_categorias_itens']
    
    # Verifica se categoria já existe
    try:
        records = _retry_with_backoff(lambda: sheet_categorias.get_all_records())
        for record in records:
            if record.get('Nome', '').strip().lower() == nome_categoria.strip().lower():
                return record.get('ID')  # Já existe
    except Exception as e:
        print(f"Erro ao verificar categorias existentes: {e}")
    
    # Cria nova categoria
    try:
        # Obtém último ID
        all_values = _retry_with_backoff(lambda: sheet_categorias.get_all_values())
        if len(all_values) > 1:
            ultimo_id = max([int(row[0]) for row in all_values[1:] if row and row[0].isdigit()])
        else:
            ultimo_id = 0
        
        novo_id = ultimo_id + 1
        data_criacao = datetime.now().strftime('%Y-%m-%d')
        
        # Adiciona nova categoria
        sheet_categorias.append_row([novo_id, nome_categoria.strip(), data_criacao])
        
        # Também cria a aba para a categoria
        obter_ou_criar_aba_categoria(nome_categoria)
        
        return novo_id
    except Exception as e:
        print(f"Erro ao criar categoria: {e}")
        return None


def obter_ou_criar_aba_categoria(categoria):
    """Obtém ou cria a aba para uma categoria específica
    
    Args:
        categoria: Nome da categoria
        
    Returns:
        Worksheet da categoria
    """
    sheets = get_sheets()
    spreadsheet = sheets['spreadsheet']
    
    try:
        worksheet = spreadsheet.worksheet(categoria)
        # Verifica se tem cabeçalhos, se não tiver, adiciona padrão
        try:
            headers = worksheet.row_values(1)
            if not headers or len(headers) == 0:
                # Adiciona cabeçalhos padrão: ID, Item ID
                worksheet.append_row(['ID', 'Item ID'])
        except Exception:
            worksheet.append_row(['ID', 'Item ID'])
        return worksheet
    except gspread.exceptions.WorksheetNotFound:
        # Cria nova aba
        worksheet = spreadsheet.add_worksheet(title=categoria, rows=1000, cols=10)
        # Adiciona cabeçalhos padrão
        worksheet.append_row(['ID', 'Item ID'])
        return worksheet


def verificar_placa_existe(placa: str, excluir_item_id: int = None) -> bool:
    """Verifica se uma placa já existe no sistema
    
    Args:
        placa: Placa a verificar
        excluir_item_id: ID do item a excluir da verificação (útil para atualizações)
        
    Returns:
        True se a placa existe, False caso contrário
    """
    try:
        sheets = get_sheets()
        spreadsheet = sheets['spreadsheet']
        
        # Verifica na aba Carros
        try:
            sheet_carros = spreadsheet.worksheet("Carros")
            records = sheet_carros.get_all_records()
            
            placa_upper = placa.upper().strip().replace('-', '').replace(' ', '')
            
            for record in records:
                if record and record.get('Placa'):
                    placa_existente = record.get('Placa').upper().strip().replace('-', '').replace(' ', '')
                    item_id_existente = record.get('Item ID')
                    
                    if placa_existente == placa_upper:
                        # Se está atualizando o mesmo item, não considera duplicata
                        if excluir_item_id and item_id_existente == excluir_item_id:
                            continue
                        return True
        except gspread.exceptions.WorksheetNotFound:
            pass
        
        return False
    except Exception:
        return False


def verificar_nome_categoria_existe(nome: str, categoria: str, excluir_item_id: int = None) -> bool:
    """Verifica se um nome já existe na categoria
    
    Args:
        nome: Nome do item
        categoria: Categoria do item
        excluir_item_id: ID do item a excluir da verificação (útil para atualizações)
        
    Returns:
        True se o nome existe na categoria, False caso contrário
    """
    try:
        sheets = get_sheets()
        sheet_itens = sheets['sheet_itens']
        records = sheet_itens.get_all_records()
        
        nome_lower = nome.lower().strip()
        
        for record in records:
            if record and record.get('Nome') and record.get('Categoria'):
                nome_existente = record.get('Nome').lower().strip()
                categoria_existente = record.get('Categoria').strip()
                item_id_existente = record.get('ID')
                
                if nome_existente == nome_lower and categoria_existente == categoria:
                    # Se está atualizando o mesmo item, não considera duplicata
                    if excluir_item_id and item_id_existente == excluir_item_id:
                        continue
                    return True
        
        return False
    except Exception:
        return False


def criar_item(nome, quantidade_total, categoria=None, descricao=None, cidade=None, uf=None, endereco=None, placa=None, marca=None, modelo=None, ano=None, campos_categoria=None):
    """Cria um novo item no estoque
    
    Args:
        nome: Nome do item
        quantidade_total: Quantidade total disponível
        categoria: Categoria do item
        descricao: Descrição opcional do item
        cidade: Cidade onde o item está localizado (obrigatório)
        uf: UF onde o item está localizado (obrigatório)
        endereco: Endereço opcional do item
        placa: Placa do carro (obrigatório se categoria='Carros')
        marca: Marca do carro (obrigatório se categoria='Carros')
        modelo: Modelo do carro (obrigatório se categoria='Carros')
        ano: Ano do carro (obrigatório se categoria='Carros')
        campos_categoria: Dicionário com campos específicos da categoria {nome_campo: valor}
    """
    # Se campos de carros vieram em campos_categoria, extrai para os parâmetros corretos
    if categoria == 'Carros' and campos_categoria:
        if not placa and 'Placa' in campos_categoria:
            placa = campos_categoria.get('Placa')
        if not marca and 'Marca' in campos_categoria:
            marca = campos_categoria.get('Marca')
        if not modelo and 'Modelo' in campos_categoria:
            modelo = campos_categoria.get('Modelo')
        if not ano and 'Ano' in campos_categoria:
            ano = campos_categoria.get('Ano')
    
    # Validações robustas
    valido, msg_erro = validacoes.validar_item_completo(
        nome=nome,
        categoria=categoria or '',
        cidade=cidade or '',
        uf=uf or '',
        quantidade_total=quantidade_total,
        placa=placa,
        marca=marca,
        modelo=modelo,
        ano=ano,
        campos_categoria=campos_categoria
    )
    
    if not valido:
        raise ValueError(msg_erro)
    
    # Validação de duplicatas
    if verificar_nome_categoria_existe(nome, categoria or ''):
        raise ValueError(f"Item '{nome}' já existe na categoria '{categoria}'")
    
    if categoria == 'Carros' and placa:
        if verificar_placa_existe(placa):
            raise ValueError(f"Placa {placa} já cadastrada")
    
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    # Busca o próximo ID
    try:
        all_records = sheet_itens.get_all_records()
        if all_records:
            # Filtra apenas registros válidos com ID
            valid_ids = [int(record.get('ID', 0)) for record in all_records if record and record.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_item (buscar próximo ID)")
    except (IndexError, KeyError, ValueError):
        # Se a aba estiver vazia ou sem dados válidos, começa do ID 1
        next_id = 1
    
    # Adiciona novo item
    try:
        sheet_itens.append_row([next_id, nome, quantidade_total, categoria, descricao or '', cidade, uf.upper()[:2], endereco or ''])
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_item (adicionar linha)")
    
    # Se houver campos específicos da categoria, salva na aba da categoria
    if campos_categoria or categoria == 'Carros':
        # Para compatibilidade com código antigo, trata Carros especialmente
        if categoria == 'Carros':
            sheet_categoria = obter_ou_criar_aba_categoria(categoria)
            try:
                all_records_cat = sheet_categoria.get_all_records()
                if all_records_cat:
                    valid_ids_cat = [int(record.get('ID', 0)) for record in all_records_cat if record and record.get('ID')]
                    next_cat_id = max(valid_ids_cat) + 1 if valid_ids_cat else 1
                else:
                    next_cat_id = 1
            except (IndexError, KeyError, ValueError):
                next_cat_id = 1
            
            # Lê cabeçalhos da aba
            headers = sheet_categoria.row_values(1)
            # Prepara valores na ordem dos cabeçalhos
            valores = [next_cat_id, next_id]  # ID, Item ID
            for header in headers[2:]:  # Pula ID e Item ID
                if header == 'Placa':
                    valores.append(placa.upper().strip() if placa else '')
                elif header == 'Marca':
                    valores.append(marca.strip() if marca else '')
                elif header == 'Modelo':
                    valores.append(modelo.strip() if modelo else '')
                elif header == 'Ano':
                    valores.append(int(ano) if ano else '')
                else:
                    # Usa campos_categoria se fornecido
                    valores.append(campos_categoria.get(header, '') if campos_categoria else '')
            
            try:
                sheet_categoria.append_row(valores)
            except gspread.exceptions.APIError as e:
                _handle_api_error(e, "criar_item (adicionar categoria)")
        elif campos_categoria:
            # Para outras categorias, usa campos_categoria
            sheet_categoria = obter_ou_criar_aba_categoria(categoria)
            try:
                all_records_cat = sheet_categoria.get_all_records()
                if all_records_cat:
                    valid_ids_cat = [int(record.get('ID', 0)) for record in all_records_cat if record and record.get('ID')]
                    next_cat_id = max(valid_ids_cat) + 1 if valid_ids_cat else 1
                else:
                    next_cat_id = 1
            except (IndexError, KeyError, ValueError):
                next_cat_id = 1
            
            # Lê cabeçalhos da aba
            headers = sheet_categoria.row_values(1)
            # Prepara valores na ordem dos cabeçalhos
            valores = [next_cat_id, next_id]  # ID, Item ID
            for header in headers[2:]:  # Pula ID e Item ID
                valores.append(campos_categoria.get(header, ''))
            
            try:
                sheet_categoria.append_row(valores)
            except gspread.exceptions.APIError as e:
                _handle_api_error(e, "criar_item (adicionar categoria)")
    
    # Limpa cache para forçar atualização na próxima leitura
    _clear_cache()
    
    # Retorna objeto similar ao modelo Item
    class Item:
        def __init__(self, id, nome, quantidade_total, categoria=None, descricao=None, cidade=None, uf=None, endereco=None, carro=None, dados_categoria=None):
            self.id = id
            self.nome = nome
            self.quantidade_total = quantidade_total
            self.categoria = categoria or ''
            self.descricao = descricao or ''
            self.cidade = cidade or ''
            self.uf = (uf or '').upper()[:2]
            self.endereco = endereco or ''
            self.carro = carro
            self.dados_categoria = dados_categoria or {}
            self.compromissos = []
    
    # Busca dados da categoria se aplicável
    carro_obj = None
    dados_cat_obj = None
    
    if categoria == 'Carros':
        class Carro:
            def __init__(self, item_id, placa, marca, modelo, ano):
                self.item_id = item_id
                self.placa = placa
                self.marca = marca
                self.modelo = modelo
                self.ano = ano
        
        # Garante valores seguros para o objeto Carro
        placa_safe = (placa or '').upper().strip() if placa else ''
        marca_safe = (marca or '').strip() if marca else ''
        modelo_safe = (modelo or '').strip() if modelo else ''
        ano_safe = int(ano) if ano and str(ano).isdigit() else 0
        
        carro_obj = Carro(next_id, placa_safe, marca_safe, modelo_safe, ano_safe)
        dados_cat_obj = {'carro': carro_obj}
    elif campos_categoria:
        dados_cat_obj = campos_categoria
    
    return Item(next_id, nome, quantidade_total, categoria, descricao, cidade, uf, endereco, carro_obj, dados_cat_obj)


def listar_itens():
    """Lista todos os itens do estoque"""
    # CACHE PERMANENTEMENTE DESABILITADO - Sempre recarrega do Sheets
    # Isso garante que sempre temos os dados mais recentes
    
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    # Usa retry para lidar com erro 429
    try:
        # Tenta obter todos os registros
        records = _retry_with_backoff(lambda: sheet_itens.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_itens")
    except (IndexError, KeyError):
        # Se a aba estiver vazia ou sem cabeçalhos, retorna lista vazia
        return []
    
    # Busca dados de categorias específicas dinamicamente
    dados_categoria_dict = {}
    spreadsheet = sheets['spreadsheet']
    
    # Obtém todas as categorias únicas dos itens
    try:
        categorias = set()
        for record in records:
            if record and record.get('Categoria'):
                categoria = record.get('Categoria').strip()
                if categoria:  # Todas as categorias podem ter aba específica
                    categorias.add(categoria)
        
        # Para cada categoria, tenta ler dados da aba correspondente
        for categoria in categorias:
            try:
                sheet_categoria = spreadsheet.worksheet(categoria)
                categoria_records = sheet_categoria.get_all_records()
                for cat_record in categoria_records:
                    if cat_record and cat_record.get('Item ID'):
                        item_id = int(cat_record.get('Item ID'))
                        dados_categoria_dict[item_id] = {'categoria': categoria, 'dados': cat_record}
            except (gspread.exceptions.WorksheetNotFound, IndexError, KeyError, ValueError, gspread.exceptions.APIError) as e:
                # Aba não existe ou erro ao ler, continua
                print(f"[WARN] Erro ao ler aba '{categoria}': {type(e).__name__}")
                pass
    except Exception as e:
        # Em caso de erro geral, continua sem dados de categoria
        print(f"[ERROR] Erro ao processar categorias: {type(e).__name__} - {str(e)}")
        pass
    
    # Classe Carro mantida apenas para compatibilidade com código antigo que ainda usa item.carro
    class Carro:
        def __init__(self, item_id, placa=None, marca=None, modelo=None, ano=None):
            self.item_id = item_id
            self.placa = placa or ''
            self.marca = marca or ''
            self.modelo = modelo or ''
            self.ano = int(ano) if ano else 0
    
    class Item:
        def __init__(self, id, nome, quantidade_total, categoria=None, descricao=None, cidade=None, uf=None, endereco=None, carro=None, dados_categoria=None):
            self.id = int(id) if id else None
            self.nome = nome
            self.quantidade_total = int(quantidade_total) if quantidade_total else 0
            self.categoria = categoria or ''
            self.descricao = descricao or ''
            self.cidade = cidade or ''
            self.uf = (uf or '').upper()[:2]
            self.endereco = endereco or ''
            self.carro = carro
            self.dados_categoria = dados_categoria or {}
            self.compromissos = []
    
    itens = []
    for record in records:
        # Verifica se o registro tem os campos necessários
        if record and record.get('ID') and record.get('Nome'):
            try:
                item_id = int(record.get('ID'))
                categoria = record.get('Categoria', '') or ''
                
                # Busca dados da categoria se existir
                carro_obj = None
                dados_categoria_obj = None
                
                if item_id in dados_categoria_dict:
                    cat_info = dados_categoria_dict[item_id]
                    cat_data = cat_info['dados']
                    
                    # Armazena dados dinamicamente para todas as categorias
                    dados_categoria_obj = cat_data
                    
                    # Para compatibilidade com código antigo que ainda usa item.carro
                    # Cria objeto Carro apenas se a categoria for Carros e tiver os campos esperados
                    if cat_info['categoria'] == 'Carros':
                        carro_obj = Carro(
                            item_id,
                            cat_data.get('Placa', ''),
                            cat_data.get('Marca', ''),
                            cat_data.get('Modelo', ''),
                            cat_data.get('Ano', 0)
                        )
                
                itens.append(Item(
                    record.get('ID'),
                    record.get('Nome'),
                    record.get('Quantidade Total', 0),
                    categoria,
                    record.get('Descrição', ''),
                    record.get('Cidade', ''),
                    record.get('UF', ''),
                    record.get('Endereço', ''),
                    carro_obj,
                    dados_categoria_obj
                ))
            except (ValueError, TypeError):
                # Ignora registros inválidos
                continue
    
    # Atualiza cache
    _data_cache['itens'] = itens
    _data_cache['cache_time'] = time.time()
    
    return itens


def buscar_item_por_id(item_id):
    """Busca um item pelo ID"""
    itens = listar_itens()
    for item in itens:
        if item.id == int(item_id):
            return item
    return None


def atualizar_item(item_id, nome, quantidade_total, categoria=None, descricao=None, cidade=None, uf=None, endereco=None, placa=None, marca=None, modelo=None, ano=None, campos_categoria=None):
    """Atualiza um item existente
    
    Args:
        item_id: ID do item
        nome: Nome do item
        quantidade_total: Quantidade total disponível
        categoria: Categoria do item
        descricao: Descrição opcional do item
        cidade: Cidade onde o item está localizado (obrigatório)
        uf: UF onde o item está localizado (obrigatório)
        endereco: Endereço opcional do item
        placa: Placa do carro (obrigatório se categoria='Carros' e não usar campos_categoria)
        marca: Marca do carro (obrigatório se categoria='Carros' e não usar campos_categoria)
        modelo: Modelo do carro (obrigatório se categoria='Carros' e não usar campos_categoria)
        ano: Ano do carro (obrigatório se categoria='Carros' e não usar campos_categoria)
        campos_categoria: Dicionário com campos específicos da categoria {nome_campo: valor}
    """
    # Busca item atual para obter valores padrão
    item_atual = buscar_item_por_id(item_id)
    if not item_atual:
        raise ValueError(f"Item com ID {item_id} não encontrado")
    
    # Usa valores atuais se não fornecidos
    categoria_final = categoria if categoria is not None else (item_atual.categoria or '')
    cidade_final = cidade if cidade else (item_atual.cidade or '')
    uf_final = uf if uf else (item_atual.uf or '')
    
    # Se campos de carros vieram em campos_categoria, extrai para os parâmetros corretos
    if categoria_final == 'Carros' and campos_categoria:
        if not placa and 'Placa' in campos_categoria:
            placa = campos_categoria.get('Placa')
        if not marca and 'Marca' in campos_categoria:
            marca = campos_categoria.get('Marca')
        if not modelo and 'Modelo' in campos_categoria:
            modelo = campos_categoria.get('Modelo')
        if not ano and 'Ano' in campos_categoria:
            ano = campos_categoria.get('Ano')
    
    # Validações robustas
    valido, msg_erro = validacoes.validar_item_completo(
        nome=nome,
        categoria=categoria_final,
        cidade=cidade_final,
        uf=uf_final,
        quantidade_total=quantidade_total,
        placa=placa,
        marca=marca,
        modelo=modelo,
        ano=ano,
        campos_categoria=campos_categoria
    )
    
    if not valido:
        raise ValueError(msg_erro)
    
    # Validação de duplicatas (excluindo o item atual)
    if verificar_nome_categoria_existe(nome, categoria_final, excluir_item_id=item_id):
        raise ValueError(f"Item '{nome}' já existe na categoria '{categoria_final}'")
    
    if categoria_final == 'Carros' and placa:
        if verificar_placa_existe(placa, excluir_item_id=item_id):
            raise ValueError(f"Placa {placa} já cadastrada")
    
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    try:
        records = sheet_itens.get_all_records()
    except (IndexError, KeyError):
        return None
    
    # Busca a linha do item
    row_to_update = None
    categoria_atual = ''
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(item_id):
            row_to_update = idx
            categoria_atual = record.get('Categoria', '') or ''
            break
    
    if row_to_update:
        # Se categoria não foi fornecida, mantém a atual
        if categoria is None:
            categoria = categoria_atual
        
        # Validação para carros
        if categoria == 'Carros':
            if not placa or not marca or not modelo or not ano:
                raise ValueError("Para carros, placa, marca, modelo e ano são obrigatórios")
        
        # Prepara valores antigos para auditoria
        valores_antigos = {
            'id': item_id,
            'nome': item_atual.nome,
            'quantidade_total': item_atual.quantidade_total,
            'categoria': item_atual.categoria,
            'descricao': item_atual.descricao,
            'cidade': item_atual.cidade,
            'uf': item_atual.uf,
            'endereco': item_atual.endereco
        }
        if hasattr(item_atual, 'carro') and item_atual.carro:
            valores_antigos.update({
                'placa': item_atual.carro.placa,
                'marca': item_atual.carro.marca,
                'modelo': item_atual.carro.modelo,
                'ano': item_atual.carro.ano
            })
        
        # Atualiza a linha do item (incluindo categoria)
        sheet_itens.update(f'A{row_to_update}:H{row_to_update}', [[item_id, nome, quantidade_total, categoria, descricao or '', cidade, uf.upper()[:2], endereco or '']])
        
        # Prepara valores novos para auditoria
        valores_novos = {
            'id': item_id,
            'nome': nome,
            'quantidade_total': quantidade_total,
            'categoria': categoria_final,
            'descricao': descricao,
            'cidade': cidade_final,
            'uf': uf_final,
            'endereco': endereco
        }
        if categoria_final == 'Carros' and placa:
            valores_novos.update({
                'placa': placa,
                'marca': marca,
                'modelo': modelo,
                'ano': ano
            })
        
        # Registra auditoria
        auditoria.registrar_auditoria('UPDATE', 'Itens', item_id, valores_antigos, valores_novos)
        
        # Gerencia dados específicos da categoria (carros ou campos_categoria)
        if campos_categoria or categoria == 'Carros':
            try:
                sheet_categoria = obter_ou_criar_aba_categoria(categoria)
                categoria_records = sheet_categoria.get_all_records()
                categoria_row = None
                
                # Busca linha existente na aba da categoria
                for idx, record in enumerate(categoria_records, start=2):
                    if record and str(record.get('Item ID')) == str(item_id):
                        categoria_row = idx
                        break
                
                if categoria == 'Carros':
                    # Para Carros, usa campos antigos se campos_categoria não fornecido
                    if not campos_categoria:
                        campos_categoria = {
                            'Placa': placa.upper().strip() if placa else '',
                            'Marca': marca.strip() if marca else '',
                            'Modelo': modelo.strip() if modelo else '',
                            'Ano': int(ano) if ano else ''
                        }
                    
                    if categoria_row:
                        # Atualiza registro existente
                        headers = sheet_categoria.row_values(1)
                        valores = []
                        for header in headers[2:]:  # Pula ID e Item ID
                            valores.append(campos_categoria.get(header, ''))
                        # Atualiza a partir da coluna C (índice 3)
                        col_inicio = 3
                        col_fim = col_inicio + len(valores) - 1
                        sheet_categoria.update(f'{chr(64 + col_inicio)}{categoria_row}:{chr(64 + col_fim)}{categoria_row}', [valores])
                    else:
                        # Cria novo registro
                        try:
                            all_records = sheet_categoria.get_all_records()
                            if all_records:
                                valid_ids = [int(r.get('ID', 0)) for r in all_records if r and r.get('ID')]
                                next_cat_id = max(valid_ids) + 1 if valid_ids else 1
                            else:
                                next_cat_id = 1
                        except (IndexError, KeyError, ValueError):
                            next_cat_id = 1
                        
                        headers = sheet_categoria.row_values(1)
                        valores = [next_cat_id, item_id]
                        for header in headers[2:]:
                            valores.append(campos_categoria.get(header, ''))
                        sheet_categoria.append_row(valores)
                elif campos_categoria:
                    # Para outras categorias com campos_categoria
                    if categoria_row:
                        # Atualiza registro existente
                        headers = sheet_categoria.row_values(1)
                        valores = []
                        for header in headers[2:]:
                            valores.append(campos_categoria.get(header, ''))
                        col_inicio = 3
                        col_fim = col_inicio + len(valores) - 1
                        sheet_categoria.update(f'{chr(64 + col_inicio)}{categoria_row}:{chr(64 + col_fim)}{categoria_row}', [valores])
                    else:
                        # Cria novo registro
                        try:
                            all_records = sheet_categoria.get_all_records()
                            if all_records:
                                valid_ids = [int(r.get('ID', 0)) for r in all_records if r and r.get('ID')]
                                next_cat_id = max(valid_ids) + 1 if valid_ids else 1
                            else:
                                next_cat_id = 1
                        except (IndexError, KeyError, ValueError):
                            next_cat_id = 1
                        
                        headers = sheet_categoria.row_values(1)
                        valores = [next_cat_id, item_id]
                        for header in headers[2:]:
                            valores.append(campos_categoria.get(header, ''))
                        sheet_categoria.append_row(valores)
                
                # Se mudou de categoria, remove registro da categoria antiga
                if categoria_atual != categoria and categoria_atual:
                    try:
                        sheet_categoria_antiga = obter_ou_criar_aba_categoria(categoria_atual)
                        records_antiga = sheet_categoria_antiga.get_all_records()
                        for idx, record in enumerate(records_antiga, start=2):
                            if record and str(record.get('Item ID')) == str(item_id):
                                sheet_categoria_antiga.delete_rows(idx)
                                break
                    except:
                        pass
            except (IndexError, KeyError, ValueError, gspread.exceptions.APIError) as e:
                # Se houver erro ao gerenciar categoria, continua
                pass
        else:
            # Se não há campos_categoria e mudou de categoria, remove registro da categoria antiga
            if categoria_atual != categoria and categoria_atual:
                try:
                    sheet_categoria_antiga = obter_ou_criar_aba_categoria(categoria_atual)
                    records_antiga = sheet_categoria_antiga.get_all_records()
                    for idx, record in enumerate(records_antiga, start=2):
                        if record and str(record.get('Item ID')) == str(item_id):
                            sheet_categoria_antiga.delete_rows(idx)
                            break
                except:
                    pass
        
        _clear_cache()
        return buscar_item_por_id(item_id)
    
    return None


def criar_compromisso(item_id, quantidade, data_inicio, data_fim, descricao=None, cidade=None, uf=None, endereco=None, contratante=None):
    """Cria um novo compromisso (aluguel)
    
    Args:
        item_id: ID do item
        quantidade: Quantidade alugada
        data_inicio: Data de início do aluguel
        data_fim: Data de fim do aluguel
        descricao: Descrição opcional do compromisso
        cidade: Cidade do compromisso (obrigatório)
        uf: UF do compromisso (obrigatório)
        endereco: Endereço opcional do compromisso
        contratante: Nome do contratante (opcional)
    """
    if not cidade or not uf:
        raise ValueError("Cidade e UF são obrigatórios")
    
    sheets = get_sheets()
    sheet_compromissos = sheets['sheet_compromissos']
    
    # Busca o próximo ID
    try:
        all_records = sheet_compromissos.get_all_records()
        if all_records:
            # Filtra apenas registros válidos com ID
            valid_ids = [int(record.get('ID', 0)) for record in all_records if record and record.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except (IndexError, KeyError, ValueError):
        # Se a aba estiver vazia ou sem dados válidos, começa do ID 1
        next_id = 1
    
    # Formata datas
    data_inicio_str = data_inicio.strftime('%Y-%m-%d') if isinstance(data_inicio, date) else str(data_inicio)
    data_fim_str = data_fim.strftime('%Y-%m-%d') if isinstance(data_fim, date) else str(data_fim)
    
    # Adiciona novo compromisso
    try:
        sheet_compromissos.append_row([
            next_id,
            item_id,
            quantidade,
            data_inicio_str,
            data_fim_str,
            descricao or '',
            cidade,
            uf.upper()[:2],
            endereco or '',
            contratante or ''
        ])
        
        # Registra auditoria
        valores_novos = {
            'id': next_id,
            'item_id': item_id,
            'quantidade': quantidade,
            'data_inicio': data_inicio_str,
            'data_fim': data_fim_str,
            'descricao': descricao,
            'cidade': cidade,
            'uf': uf,
            'endereco': endereco,
            'contratante': contratante
        }
        auditoria.registrar_auditoria('CREATE', 'Compromissos', next_id, valores_novos=valores_novos)
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_compromisso (adicionar linha)")
    
    # Limpa cache para forçar atualização na próxima leitura
    _clear_cache()
    
    # Retorna objeto similar ao modelo Compromisso
    class Compromisso:
        def __init__(self, id, item_id, quantidade, data_inicio, data_fim, descricao, cidade=None, uf=None, endereco=None, contratante=None):
            self.id = id
            self.item_id = int(item_id)
            self.quantidade = int(quantidade)
            self.data_inicio = data_inicio if isinstance(data_inicio, date) else datetime.strptime(data_inicio, '%Y-%m-%d').date()
            self.data_fim = data_fim if isinstance(data_fim, date) else datetime.strptime(data_fim, '%Y-%m-%d').date()
            self.descricao = descricao or ''
            self.cidade = cidade or ''
            self.uf = (uf or '').upper()[:2]
            self.endereco = endereco or ''
            self.contratante = contratante or ''
            # Carrega o item relacionado (lazy loading - só quando necessário)
            self._item_id = int(item_id)
            self._item_cache = None
        
        def _get_item(self):
            """Carrega o item apenas quando necessário (lazy loading)"""
            if self._item_cache is None:
                self._item_cache = buscar_item_por_id(self._item_id)
            return self._item_cache
        
        # Propriedade para compatibilidade
        @property
        def item(self):
            return self._get_item()
    
    return Compromisso(next_id, item_id, quantidade, data_inicio, data_fim, descricao, cidade, uf, endereco, contratante)


def listar_compromissos():
    """Lista todos os compromissos"""
    # Verifica cache primeiro
    if _is_cache_valid() and _data_cache['compromissos'] is not None:
        return _data_cache['compromissos']
    
    sheets = get_sheets()
    sheet_compromissos = sheets['sheet_compromissos']
    
    # Usa retry para lidar com erro 429
    try:
        # Tenta obter todos os registros
        records = _retry_with_backoff(lambda: sheet_compromissos.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_compromissos")
    except (IndexError, KeyError):
        # Se a aba estiver vazia ou sem cabeçalhos, retorna lista vazia
        return []
    
    # Carrega todos os itens de uma vez para evitar múltiplas chamadas à API
    itens_dict = {}
    try:
        itens_list = listar_itens()
        itens_dict = {item.id: item for item in itens_list}
    except Exception:
        # Se falhar ao carregar itens, continua sem cache
        pass
    
    class Compromisso:
        def __init__(self, id, item_id, quantidade, data_inicio, data_fim, descricao, cidade=None, uf=None, endereco=None, contratante=None, item_cache=None):
            self.id = int(id) if id else None
            self.item_id = int(item_id) if item_id else None
            self.quantidade = int(quantidade) if quantidade else 0
            
            # Converte strings de data para objetos date
            if isinstance(data_inicio, str) and data_inicio:
                try:
                    self.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                except ValueError:
                    # Tenta outros formatos
                    try:
                        self.data_inicio = datetime.strptime(data_inicio, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_inicio = date.today()
            else:
                self.data_inicio = data_inicio if isinstance(data_inicio, date) else date.today()
            
            if isinstance(data_fim, str) and data_fim:
                try:
                    self.data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                except ValueError:
                    # Tenta outros formatos
                    try:
                        self.data_fim = datetime.strptime(data_fim, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_fim = date.today()
            else:
                self.data_fim = data_fim if isinstance(data_fim, date) else date.today()
            
            self.descricao = descricao or ''
            self.cidade = cidade or ''
            self.uf = (uf or '').upper()[:2]
            self.endereco = endereco or ''
            self.contratante = contratante or ''
            # Usa cache de itens se fornecido, senão lazy loading
            self._item_id = int(item_id) if item_id else None
            self._item_cache = item_cache if item_cache else None
        
        def _get_item(self):
            """Carrega o item apenas quando necessário (lazy loading)"""
            if self._item_cache is None and self._item_id:
                self._item_cache = buscar_item_por_id(self._item_id)
            return self._item_cache
        
        # Propriedade para compatibilidade
        @property
        def item(self):
            return self._get_item()
    
    compromissos = []
    for record in records:
        # Verifica se o registro tem os campos necessários
        if record and record.get('ID') and record.get('Item ID'):
            try:
                item_id = int(record.get('Item ID'))
                # Usa item do cache se disponível
                item_cache = itens_dict.get(item_id)
                compromissos.append(Compromisso(
                    record.get('ID'),
                    item_id,
                    record.get('Quantidade', 0),
                    record.get('Data Início', ''),
                    record.get('Data Fim', ''),
                    record.get('Descrição', ''),
                    record.get('Cidade', ''),
                    record.get('UF', ''),
                    record.get('Endereço', ''),
                    record.get('Contratante', ''),
                    item_cache=item_cache
                ))
            except (ValueError, TypeError) as e:
                # Ignora registros inválidos
                continue
    
    # Atualiza cache
    _data_cache['compromissos'] = compromissos
    _data_cache['cache_time'] = time.time()
    
    return compromissos


def verificar_disponibilidade(item_id, data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de um item em uma data específica
    
    Args:
        item_id: ID do item
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localização
    """
    item = buscar_item_por_id(item_id)
    if not item:
        return None
    
    compromissos = listar_compromissos()
    
    # Filtra compromissos ativos na data de consulta para este item
    # Se há filtro de localização, filtra por cidade e UF (formato: "Cidade - UF")
    compromissos_ativos = []
    for c in compromissos:
        if c.item_id == int(item_id) and c.data_inicio <= data_consulta <= c.data_fim:
            if filtro_localizacao:
                cidade_uf = filtro_localizacao.split(" - ")
                if len(cidade_uf) == 2:
                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                    if hasattr(c, 'cidade') and hasattr(c, 'uf') and c.cidade == cidade_filtro and c.uf == uf_filtro.upper():
                        compromissos_ativos.append(c)
                else:
                    compromissos_ativos.append(c)
            else:
                compromissos_ativos.append(c)
    
    quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
    
    # Se há filtro de localização e o item não está nessa localização,
    # considera que não há itens disponíveis naquela localização
    if filtro_localizacao:
        cidade_uf = filtro_localizacao.split(" - ")
        if len(cidade_uf) == 2:
            cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
            item_na_localizacao = (hasattr(item, 'cidade') and hasattr(item, 'uf') and 
                                  item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
            if not item_na_localizacao:
                # Item não está na localização, então disponível = 0 (ou negativo se houver compromissos)
                quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        else:
            quantidade_disponivel = item.quantidade_total - quantidade_comprometida
    else:
        quantidade_disponivel = item.quantidade_total - quantidade_comprometida
    
    return {
        'item': item,
        'quantidade_total': item.quantidade_total,
        'quantidade_comprometida': quantidade_comprometida,
        'quantidade_disponivel': quantidade_disponivel,
        'compromissos_ativos': compromissos_ativos
    }


def verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=None):
    """Verifica se há disponibilidade suficiente em todo o período para um novo compromisso"""
    from datetime import timedelta
    
    item = buscar_item_por_id(item_id)
    if not item:
        return None
    
    compromissos = listar_compromissos()
    
    # Filtra compromissos que se sobrepõem com o período
    compromissos_sobrepostos = [
        c for c in compromissos
        if c.item_id == int(item_id) 
        and c.data_inicio <= data_fim 
        and c.data_fim >= data_inicio
        and (excluir_compromisso_id is None or c.id != excluir_compromisso_id)
    ]
    
    # Encontra o dia com maior comprometimento no período
    max_comprometido = 0
    data_atual = data_inicio
    
    while data_atual <= data_fim:
        compromissos_no_dia = [
            c for c in compromissos_sobrepostos
            if c.data_inicio <= data_atual <= c.data_fim
        ]
        comprometido_no_dia = sum(c.quantidade for c in compromissos_no_dia)
        max_comprometido = max(max_comprometido, comprometido_no_dia)
        
        if data_atual >= data_fim:
            break
        data_atual += timedelta(days=1)
    
    return {
        'item': item,
        'quantidade_total': item.quantidade_total,
        'max_comprometido': max_comprometido,
        'disponivel_minimo': item.quantidade_total - max_comprometido
    }


def verificar_disponibilidade_todos_itens(data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de todos os itens em uma data específica
    
    Args:
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localização
    """
    itens = listar_itens()
    compromissos = listar_compromissos()
    
    resultados = []
    
    for item in itens:
        # Filtra compromissos ativos na data de consulta para este item
        # Se há filtro de localização, filtra por cidade e UF (formato: "Cidade - UF")
        compromissos_ativos = []
        for c in compromissos:
            if c.item_id == item.id and c.data_inicio <= data_consulta <= c.data_fim:
                if filtro_localizacao:
                    cidade_uf = filtro_localizacao.split(" - ")
                    if len(cidade_uf) == 2:
                        cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                        if hasattr(c, 'cidade') and hasattr(c, 'uf') and c.cidade == cidade_filtro and c.uf == uf_filtro.upper():
                            compromissos_ativos.append(c)
                    else:
                        compromissos_ativos.append(c)
                else:
                    compromissos_ativos.append(c)
        
        quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
        
        # Se há filtro de localização e o item não está nessa localização,
        # considera que não há itens disponíveis naquela localização
        if filtro_localizacao:
            cidade_uf = filtro_localizacao.split(" - ")
            if len(cidade_uf) == 2:
                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                item_na_localizacao = (hasattr(item, 'cidade') and hasattr(item, 'uf') and 
                                      item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                if not item_na_localizacao:
                    # Item não está na localização, então disponível = 0 (ou negativo se houver compromissos)
                    quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        else:
            quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        
        resultados.append({
            'item': item,
            'quantidade_total': item.quantidade_total,
            'quantidade_comprometida': quantidade_comprometida,
            'quantidade_disponivel': quantidade_disponivel
        })
    
    return resultados


def deletar_item(item_id):
    """Deleta um item e todos os seus compromissos"""
    # Verifica se o item existe
    item = buscar_item_por_id(item_id)
    if not item:
        raise ValueError(f"Item com ID {item_id} não encontrado")
    
    # Verifica se há compromissos ativos
    compromissos = listar_compromissos()
    compromissos_ativos = [c for c in compromissos if c.item_id == item_id]
    
    if compromissos_ativos:
        hoje = date.today()
        compromissos_futuros = [
            c for c in compromissos_ativos 
            if isinstance(c.data_fim, date) and c.data_fim >= hoje
        ]
        
        if compromissos_futuros:
            raise ValueError(
                f"Não é possível deletar o item. Existem {len(compromissos_futuros)} compromisso(s) ativo(s) ou futuro(s). "
                f"Delete os compromissos primeiro ou aguarde sua conclusão."
            )
    
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    # Busca a linha do item
    try:
        records = sheet_itens.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "deletar_item")
    except (IndexError, KeyError):
        # Se a aba estiver vazia, não há nada para deletar
        return False
    
    row_to_delete = None
    
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(item_id):
            row_to_delete = idx
            break
    
    if row_to_delete:
        # Prepara valores antigos para auditoria antes de deletar
        valores_antigos = {
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
            valores_antigos.update({
                'placa': item.carro.placa,
                'marca': item.carro.marca,
                'modelo': item.carro.modelo,
                'ano': item.carro.ano
            })
        
        sheet_itens.delete_rows(row_to_delete)
        
        # Registra auditoria
        auditoria.registrar_auditoria('DELETE', 'Itens', item_id, valores_antigos=valores_antigos)
        
        # Deleta compromissos relacionados
        sheet_compromissos = sheets['sheet_compromissos']
        try:
            comp_records = sheet_compromissos.get_all_records()
            rows_to_delete = []
            
            for idx, record in enumerate(comp_records, start=2):
                if record and str(record.get('Item ID')) == str(item_id):
                    rows_to_delete.append(idx)
            
            # Deleta em ordem reversa para não afetar índices
            for row in reversed(rows_to_delete):
                sheet_compromissos.delete_rows(row)
        except (IndexError, KeyError):
            # Se a aba de compromissos estiver vazia, apenas continua
            pass
        
        return True
    
    return False


def atualizar_compromisso(compromisso_id, item_id, quantidade, data_inicio, data_fim, descricao=None, cidade=None, uf=None, endereco=None, contratante=None):
    """Atualiza um compromisso existente
    
    Args:
        compromisso_id: ID do compromisso
        item_id: ID do item
        quantidade: Quantidade alugada
        data_inicio: Data de início do aluguel
        data_fim: Data de fim do aluguel
        descricao: Descrição opcional do compromisso
        cidade: Cidade do compromisso (obrigatório)
        uf: UF do compromisso (obrigatório)
        endereco: Endereço opcional do compromisso
        contratante: Nome do contratante (opcional)
    """
    # Verifica se o compromisso existe
    compromissos = listar_compromissos()
    compromisso_atual = next((c for c in compromissos if c.id == compromisso_id), None)
    if not compromisso_atual:
        raise ValueError(f"Compromisso com ID {compromisso_id} não encontrado")
    
    # Verifica se o item existe
    item = buscar_item_por_id(item_id)
    if not item:
        raise ValueError(f"Item com ID {item_id} não encontrado")
    
    # Verifica disponibilidade (excluindo o compromisso atual)
    disponibilidade = verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=compromisso_id)
    if not disponibilidade:
        raise ValueError(f"Erro ao verificar disponibilidade do item {item_id}")
    
    quantidade_disponivel = disponibilidade.get('disponivel_minimo', 0)
    
    # Validações robustas
    valido, msg_erro = validacoes.validar_compromisso_completo(
        item_id=item_id,
        quantidade=quantidade,
        data_inicio=data_inicio,
        data_fim=data_fim,
        cidade=cidade or '',
        uf=uf or '',
        quantidade_disponivel=quantidade_disponivel
    )
    
    if not valido:
        raise ValueError(msg_erro)
    
    sheets = get_sheets()
    sheet_compromissos = sheets['sheet_compromissos']
    
    try:
        records = sheet_compromissos.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "atualizar_compromisso")
    except (IndexError, KeyError):
        return None
    
    # Busca a linha do compromisso
    row_to_update = None
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(compromisso_id):
            row_to_update = idx
            break
    
    if row_to_update:
        # Formata datas
        data_inicio_str = data_inicio.strftime('%Y-%m-%d') if isinstance(data_inicio, date) else str(data_inicio)
        data_fim_str = data_fim.strftime('%Y-%m-%d') if isinstance(data_fim, date) else str(data_fim)
        
        # Atualiza a linha com os novos valores
        sheet_compromissos.update(f'A{row_to_update}:J{row_to_update}', [[
            compromisso_id,
            item_id,
            quantidade,
            data_inicio_str,
            data_fim_str,
            descricao or '',
            cidade,
            uf.upper()[:2],
            endereco or '',
            contratante or ''
        ]])
        _clear_cache()
        # Retorna o compromisso atualizado
        compromissos = listar_compromissos()
        for comp in compromissos:
            if comp.id == compromisso_id:
                return comp
        return None
    
    return None


def deletar_compromisso(compromisso_id):
    """Deleta um compromisso"""
    sheets = get_sheets()
    sheet_compromissos = sheets['sheet_compromissos']
    
    # Busca a linha do compromisso
    try:
        records = sheet_compromissos.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "deletar_compromisso")
    except (IndexError, KeyError):
        # Se a aba estiver vazia, não há nada para deletar
        return False
    
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(compromisso_id):
            try:
                # Prepara valores antigos para auditoria antes de deletar
                valores_antigos = {
                    'id': compromisso_id,
                    'item_id': record.get('Item ID'),
                    'quantidade': record.get('Quantidade'),
                    'data_inicio': record.get('Data Início'),
                    'data_fim': record.get('Data Fim'),
                    'descricao': record.get('Descrição'),
                    'cidade': record.get('Cidade'),
                    'uf': record.get('UF'),
                    'endereco': record.get('Endereço'),
                    'contratante': record.get('Contratante')
                }
                
                sheet_compromissos.delete_rows(idx)
                
                # Registra auditoria
                auditoria.registrar_auditoria('DELETE', 'Compromissos', compromisso_id, valores_antigos=valores_antigos)
                
                # Limpa cache para forçar atualização na próxima leitura
                _clear_cache()
                return True
            except gspread.exceptions.APIError as e:
                _handle_api_error(e, "deletar_compromisso (deletar linha)")
    
    return False


# ============= FINANCIAMENTOS =============

def criar_financiamento_item(financiamento_id, item_id, valor_proporcional):
    """Associa um item a um financiamento (relacionamento many-to-many)"""
    sheets = get_sheets()
    sheet_fin_itens = sheets['sheet_financiamentos_itens']
    
    # Busca próximo ID
    try:
        all_records = sheet_fin_itens.get_all_records()
        if all_records:
            valid_ids = [int(record.get('ID', 0)) for record in all_records if record and record.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except (IndexError, KeyError, ValueError):
        next_id = 1
    
    # Arredonda valor proporcional para 2 casas decimais
    valor_proporcional = round(float(valor_proporcional), 2)
    
    # Adiciona o registro
    sheet_fin_itens.append_row([next_id, financiamento_id, item_id, valor_proporcional])
    
    return next_id


def listar_itens_financiamento(financiamento_id):
    """Lista todos os itens associados a um financiamento"""
    sheets = get_sheets()
    sheet_fin_itens = sheets['sheet_financiamentos_itens']
    
    try:
        all_records = sheet_fin_itens.get_all_records()
        # Filtra registros que pertencem ao financiamento
        itens = []
        for record in all_records:
            if record and record.get('Financiamento ID') == financiamento_id:
                # Valor proporcional não é usado, sempre 0.0
                itens.append({
                    'id': record.get('ID'),
                    'item_id': record.get('Item ID'),
                    'valor_proporcional': 0.0
                })
        return itens
    except Exception as e:
        print(f"Erro ao listar itens do financiamento {financiamento_id}: {str(e)}")
        return []


def criar_financiamento(item_id=None, valor_total=None, numero_parcelas=None, taxa_juros=None, data_inicio=None, valor_entrada=0.0, instituicao_financeira=None, observacoes=None, parcelas_customizadas=None, itens_ids=None, codigo_contrato=None):
    """
    Cria um novo financiamento e gera as parcelas automaticamente.
    
    Args:
        item_id: ID do item (compatibilidade reversa - uso único item)
        itens_ids: Lista de IDs dos itens para múltiplos itens
        codigo_contrato: Código do contrato do financiamento
        valor_total: Valor total do financiamento
        numero_parcelas: Número de parcelas
        taxa_juros: Taxa de juros mensal (decimal)
        data_inicio: Data de início
        valor_entrada: Valor da entrada
        instituicao_financeira: Nome da instituição
        observacoes: Observações
        parcelas_customizadas: Lista de parcelas customizadas
    """
    from datetime import timedelta
    import calendar
    
    sheets = get_sheets()
    sheet_financiamentos = sheets['sheet_financiamentos']
    sheet_parcelas = sheets['sheet_parcelas_financiamento']
    
    # Compatibilidade reversa: se item_id for fornecido e não houver itens_ids
    if item_id and not itens_ids:
        itens_ids = [item_id]
    
    # Validação: deve ter itens_ids
    if not itens_ids:
        raise ValueError("É necessário fornecer pelo menos um item (itens_ids)")
    
    # Busca próximo ID de financiamento
    try:
        all_records = sheet_financiamentos.get_all_records()
        if all_records:
            valid_ids = [int(record.get('ID', 0)) for record in all_records if record and record.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except (IndexError, KeyError, ValueError):
        next_id = 1
    
    # Converte valores para float e arredonda
    valor_total = round(float(valor_total), 2)
    valor_entrada = round(float(valor_entrada), 2)
    taxa_juros = round(float(taxa_juros), 6)
    
    # Garante que taxa está em formato decimal (< 1) antes de salvar
    # Isso garante consistência independente do formato recebido
    if taxa_juros >= 100:  # Ex: 1550 → 0.0155 (1.55%)
        taxa_juros = taxa_juros / 10000
    elif taxa_juros >= 1:  # Ex: 1.55 → 0.0155 (1.55%)
        taxa_juros = taxa_juros / 100
    # Se < 1, já está correto (0.0155)
    
    # Calcula valor financiado (deduz entrada)
    valor_financiado = round(valor_total - valor_entrada, 2)
    
    if valor_financiado <= 0:
        raise ValueError("Valor financiado deve ser maior que zero")
    
    # Calcula valor da parcela com juros (Sistema Price - parcelas fixas)
    # PMT = PV * (i * (1+i)^n) / ((1+i)^n - 1)
    # onde: PMT = valor da parcela, PV = valor financiado, i = taxa mensal, n = número de parcelas
    if not parcelas_customizadas and taxa_juros > 0:
        i = taxa_juros  # Taxa mensal (ex: 0.01 para 1%)
        n = numero_parcelas
        if i > 0:
            # Sistema Price (parcelas fixas com juros compostos)
            valor_parcela = valor_financiado * (i * ((1 + i) ** n)) / (((1 + i) ** n) - 1)
        else:
            valor_parcela = valor_financiado / numero_parcelas
    else:
        valor_parcela = valor_financiado / numero_parcelas if not parcelas_customizadas else 0
    
    # Formata data
    data_inicio_str = data_inicio.strftime('%Y-%m-%d') if isinstance(data_inicio, date) else str(data_inicio)
    
    # Adiciona financiamento
    try:
        # Arredonda valores antes de salvar (garante 2 casas decimais)
        valor_parcela_rounded = round(valor_parcela, 2)
        valor_entrada_rounded = round(valor_entrada, 2)
        
        # Garante que valores inteiros sejam salvos como float (ex: 80000.0)
        # Isso evita que o Google Sheets interprete como inteiro
        if valor_total == int(valor_total):
            valor_total = float(f"{valor_total:.2f}")
        if valor_entrada_rounded == int(valor_entrada_rounded):
            valor_entrada_rounded = float(f"{valor_entrada_rounded:.2f}")
        if valor_parcela_rounded == int(valor_parcela_rounded):
            valor_parcela_rounded = float(f"{valor_parcela_rounded:.2f}")
        
        # Usa update ao invés de append_row para garantir formatação correta
        # Headers: ID | Código Contrato | Valor Total | Valor Entrada | Numero Parcelas | Valor Parcela | Taxa Juros | Data Inicio | Status | Instituicao Financeira | Observacoes | Valor Presente
        row_num = len(sheet_financiamentos.get_all_values()) + 1
        sheet_financiamentos.append_row([
            next_id,                        # A: ID
            codigo_contrato or '',          # B: Código Contrato (ex-Item ID)
            '',                             # C: Valor Total (placeholder)
            '',                             # D: Valor Entrada (placeholder)
            numero_parcelas,                # E: Numero Parcelas
            '',                             # F: Valor Parcela (placeholder)
            float(taxa_juros),              # G: Taxa Juros
            data_inicio_str,                # H: Data Inicio
            'Ativo',                        # I: Status
            instituicao_financeira or '',   # J: Instituicao Financeira
            observacoes or '',              # K: Observacoes
            0.0                             # L: Valor Presente (usuário preencherá no Sheets)
        ])
        # Agora atualiza os valores numéricos com formatação explícita
        sheet_financiamentos.update_cell(row_num, 3, valor_total)  # Valor Total (coluna C)
        sheet_financiamentos.update_cell(row_num, 4, valor_entrada_rounded)  # Valor Entrada (coluna D)
        sheet_financiamentos.update_cell(row_num, 6, valor_parcela_rounded)  # Valor Parcela (coluna F)
        
        # Cria registros na tabela Financiamentos_Itens (relacionamento many-to-many)
        # Como não temos valores individuais, salvamos 0 ou podemos dividir igualmente
        for item_id in itens_ids:
            criar_financiamento_item(next_id, item_id, 0.0)  # Valor proporcional não é usado
        
        # Gera parcelas
        data_venc = data_inicio if isinstance(data_inicio, date) else datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        parcelas_ids = []
        
        # Busca próximo ID de parcela uma vez antes do loop (mais eficiente)
        try:
            all_parcelas = sheet_parcelas.get_all_records()
            if all_parcelas:
                valid_parcela_ids = [int(p.get('ID', 0)) for p in all_parcelas if p and p.get('ID')]
                next_parcela_id = max(valid_parcela_ids) + 1 if valid_parcela_ids else 1
            else:
                next_parcela_id = 1
        except (IndexError, KeyError, ValueError):
            next_parcela_id = 1
        
        if parcelas_customizadas:
            # Usa parcelas customizadas
            for idx, parcela_custom in enumerate(parcelas_customizadas):
                parcela_id = next_parcela_id + idx
                
                # Converte data_vencimento se necessário
                if isinstance(parcela_custom.get('data_vencimento'), str):
                    data_vencimento = datetime.strptime(parcela_custom['data_vencimento'], '%Y-%m-%d').date()
                else:
                    data_vencimento = parcela_custom['data_vencimento']
                
                try:
                    # Arredonda valor da parcela antes de salvar (2 casas decimais)
                    valor_parcela_custom = round(float(parcela_custom.get('valor', 0)), 2)
                    # Garante que valores inteiros sejam salvos como float
                    if valor_parcela_custom == int(valor_parcela_custom):
                        valor_parcela_custom = float(f"{valor_parcela_custom:.2f}")
                    # Adiciona linha primeiro, depois atualiza valor com update_cell para garantir formatação
                    row_parcela_custom_num = len(sheet_parcelas.get_all_values()) + 1
                    sheet_parcelas.append_row([
                        parcela_id,
                        next_id,
                        parcela_custom.get('numero', idx + 1),
                        '',  # Placeholder - será atualizado com update_cell
                        0.0,  # Valor pago inicialmente 0
                        data_vencimento.strftime('%Y-%m-%d') if isinstance(data_vencimento, date) else str(data_vencimento),
                        '',  # Data pagamento vazia
                        'Pendente',
                        '',  # Link Boleto vazio
                        ''   # Link Comprovante vazio
                    ])
                    # Atualiza valor da parcela com update_cell para garantir que seja salvo como decimal
                    sheet_parcelas.update_cell(row_parcela_custom_num, 4, valor_parcela_custom)
                    parcelas_ids.append(parcela_id)
                except Exception as e:
                    raise Exception(f"Erro ao criar parcela customizada {idx + 1}: {str(e)}")
        else:
            # Gera parcelas automaticamente (fixas)
            for i in range(1, numero_parcelas + 1):
                parcela_id = next_parcela_id + i - 1
                
                # Calcula data de vencimento (mes seguinte)
                if i == 1:
                    data_vencimento = data_venc
                else:
                    # Adiciona meses usando relativedelta ou cálculo manual
                    meses_adicionar = i - 1
                    ano = data_venc.year
                    mes = data_venc.month + meses_adicionar
                    # Ajusta ano se necessário
                    while mes > 12:
                        mes -= 12
                        ano += 1
                    # Ajusta para último dia do mês se necessário
                    try:
                        data_vencimento = date(ano, mes, data_venc.day)
                    except ValueError:
                        # Se o dia não existe no mês (ex: 31/02), usa último dia do mês
                        ultimo_dia = calendar.monthrange(ano, mes)[1]
                        data_vencimento = date(ano, mes, ultimo_dia)
                
                try:
                    # Arredonda valor da parcela antes de salvar (2 casas decimais)
                    valor_parcela_rounded = round(float(valor_parcela), 2)
                    # Garante que valores inteiros sejam salvos como float
                    if valor_parcela_rounded == int(valor_parcela_rounded):
                        valor_parcela_rounded = float(f"{valor_parcela_rounded:.2f}")
                    # Adiciona linha primeiro, depois atualiza valor com update_cell para garantir formatação
                    row_parcela_num = len(sheet_parcelas.get_all_values()) + 1
                    sheet_parcelas.append_row([
                        parcela_id,
                        next_id,
                        i,
                        '',  # Placeholder - será atualizado com update_cell
                        0.0,  # Valor pago inicialmente 0
                        data_vencimento.strftime('%Y-%m-%d'),
                        '',  # Data pagamento vazia
                        'Pendente',
                        '',  # Link Boleto vazio
                        ''   # Link Comprovante vazio
                    ])
                    # Atualiza valor da parcela com update_cell para garantir que seja salvo como decimal
                    sheet_parcelas.update_cell(row_parcela_num, 4, valor_parcela_rounded)
                    parcelas_ids.append(parcela_id)
                except Exception as e:
                    raise Exception(f"Erro ao criar parcela {i} de {numero_parcelas}: {str(e)}")
        
        auditoria.registrar_auditoria('CREATE', 'Financiamentos', next_id, valores_novos={
            'itens': itens_ids,
            'valor_total': valor_total,
            'numero_parcelas': numero_parcelas
        })
        
        _clear_cache()
        
        # Retorna objeto similar ao modelo Financiamento
        class Financiamento:
            def __init__(self, id, valor_total, numero_parcelas, valor_parcela, taxa_juros, data_inicio, status, instituicao_financeira, observacoes, valor_entrada, codigo_contrato):
                self.id = int(id)
                self.codigo_contrato = codigo_contrato or ''
                self.valor_total = round(float(valor_total), 2)
                self.valor_entrada = round(float(valor_entrada), 2)
                self.numero_parcelas = int(numero_parcelas)
                self.valor_parcela = round(float(valor_parcela), 2)
                # Converte vírgula para ponto e normaliza taxa_juros
                if not taxa_juros or (isinstance(taxa_juros, str) and taxa_juros.strip() == ''):
                    self.taxa_juros = 0.0
                else:
                    taxa_str = str(taxa_juros).replace('%', '').replace(',', '.').strip()
                    try:
                        taxa_float = float(taxa_str)
                        if taxa_float >= 100:
                            taxa_float = taxa_float / 10000
                        elif taxa_float >= 1:
                            taxa_float = taxa_float / 100
                        self.taxa_juros = round(taxa_float, 6)
                    except (ValueError, TypeError):
                        self.taxa_juros = 0.0
                self.data_inicio = data_inicio if isinstance(data_inicio, date) else datetime.strptime(data_inicio, '%Y-%m-%d').date()
                self.status = status or 'Ativo'
                self.instituicao_financeira = instituicao_financeira or ''
                self.observacoes = observacoes or ''
                self._itens_cache = None
                self._parcelas_cache = None
            
            def _get_itens(self):
                if self._itens_cache is None:
                    # Busca os itens associados ao financiamento
                    fin_itens = listar_itens_financiamento(self.id)
                    todos_itens = listar_itens()
                    self._itens_cache = []
                    for fin_item in fin_itens:
                        item_obj = next((item for item in todos_itens if item.id == fin_item['item_id']), None)
                        if item_obj:
                            # Adiciona informações do item + valor proporcional
                            self._itens_cache.append({
                                'id': item_obj.id,
                                'nome': item_obj.nome,
                                'valor': fin_item['valor_proporcional'],
                                'item': item_obj
                            })
                return self._itens_cache
            
            @property
            def itens(self):
                return self._get_itens()
            
            # Compatibilidade: retorna o primeiro item se houver
            @property
            def item_id(self):
                itens = self.itens
                return itens[0]['id'] if itens else None
            
            @property
            def item(self):
                itens = self.itens
                return itens[0]['item'] if itens else None
            
            def _get_parcelas(self):
                if self._parcelas_cache is None:
                    self._parcelas_cache = listar_parcelas_financiamento(financiamento_id=self.id)
                return self._parcelas_cache
            
            @property
            def parcelas(self):
                return self._get_parcelas()
        
        return Financiamento(next_id, valor_total, numero_parcelas, valor_parcela, taxa_juros, data_inicio_str, 'Ativo', instituicao_financeira, observacoes, valor_entrada, codigo_contrato)
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_financiamento")
    except Exception as e:
        raise Exception(f"Erro ao criar financiamento: {str(e)}")


def listar_financiamentos(status=None, item_id=None):
    """Lista financiamentos com filtros opcionais"""
    sheets = get_sheets()
    sheet_financiamentos = sheets['sheet_financiamentos']
    
    # Usa retry para lidar com erro 429
    try:
        records = _retry_with_backoff(lambda: sheet_financiamentos.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_financiamentos")
    except (IndexError, KeyError):
        return []
    
    class Financiamento:
        def __init__(self, id, valor_total, valor_entrada, numero_parcelas, valor_parcela, taxa_juros, data_inicio, status, instituicao_financeira, observacoes, codigo_contrato):
            self.id = int(id) if id else None
            self.codigo_contrato = codigo_contrato or ''
            self.valor_total = round(float(valor_total), 2) if valor_total else 0.0
            self.valor_entrada = round(float(valor_entrada), 2) if valor_entrada else 0.0
            self.numero_parcelas = int(numero_parcelas) if numero_parcelas else 0
            self.valor_parcela = round(float(valor_parcela), 2) if valor_parcela else 0.0
            # Converte vírgula para ponto e normaliza taxa_juros
            if not taxa_juros or (isinstance(taxa_juros, str) and taxa_juros.strip() == ''):
                self.taxa_juros = 0.0
            else:
                taxa_str = str(taxa_juros).replace('%', '').replace(',', '.').strip()
                try:
                    taxa_float = float(taxa_str)
                    if taxa_float >= 100:
                        taxa_float = taxa_float / 10000
                    elif taxa_float >= 1:
                        taxa_float = taxa_float / 100
                    self.taxa_juros = round(taxa_float, 6)
                except (ValueError, TypeError):
                    self.taxa_juros = 0.0
            if isinstance(data_inicio, str) and data_inicio:
                try:
                    self.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        self.data_inicio = datetime.strptime(data_inicio, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_inicio = date.today()
            else:
                self.data_inicio = data_inicio if isinstance(data_inicio, date) else date.today()
            self.status = status or 'Ativo'
            self.instituicao_financeira = instituicao_financeira or ''
            self.observacoes = observacoes or ''
            self._itens_cache = None
            self._parcelas_cache = None
        
        def _get_itens(self):
            if self._itens_cache is None:
                # Busca os itens associados ao financiamento
                fin_itens = listar_itens_financiamento(self.id)
                todos_itens = listar_itens()
                self._itens_cache = []
                for fin_item in fin_itens:
                    item_obj = next((item for item in todos_itens if item.id == fin_item['item_id']), None)
                    if item_obj:
                        self._itens_cache.append({
                            'id': item_obj.id,
                            'nome': item_obj.nome,
                            'valor': fin_item['valor_proporcional'],
                            'item': item_obj
                        })
            return self._itens_cache
        
        @property
        def itens(self):
            return self._get_itens()
        
        # Compatibilidade: retorna o primeiro item se houver
        @property
        def item_id(self):
            itens = self.itens
            return itens[0]['id'] if itens else None
        
        @property
        def item(self):
            itens = self.itens
            return itens[0]['item'] if itens else None
        
        def _get_parcelas(self):
            if self._parcelas_cache is None:
                self._parcelas_cache = listar_parcelas_financiamento(financiamento_id=self.id)
            return self._parcelas_cache
        
        @property
        def parcelas(self):
            return self._get_parcelas()
    
    financiamentos = []
    for record in records:
        if record and record.get('ID'):
            try:
                # Lê e converte valores, garantindo que sejam números
                valor_total_raw = record.get('Valor Total', 0)
                valor_parcela_raw = record.get('Valor Parcela', 0)
                
                # Converte valores para float e arredonda
                # Google Sheets pode retornar como string formatada ou número
                def parse_value(val):
                    """
                    Parse value from Google Sheets.
                    IMPORTANTE: Google Sheets formatado como "Número" remove vírgula e multiplica por 100
                    Ex: 42421,41 vira 4242141 (sem decimal)
                    """
                    if val is None:
                        return 0.0
                    
                    if isinstance(val, (int, float)):
                        val_float = float(val)
                        
                        # Se o número for inteiro ou tiver apenas .0, pode estar faltando decimal
                        # Ex: 4242141.0 deveria ser 42421.41
                        if val_float == int(val_float):  # É um número inteiro (ex: 4242141.0)
                            # Verifica se os últimos 2 dígitos sugerem centavos
                            val_int = int(val_float)
                            if val_int >= 100:  # Só faz sentido dividir se >= 100
                                # SEMPRE divide por 100 para valores formatados como "Número" no Sheets
                                return round(val_float / 100, 2)
                        
                        return round(val_float, 2)
                    
                    if isinstance(val, str):
                        # Clean Brazilian formatting (ex: "80.000,50" → 80000.50)
                        val_clean = val.replace(' ', '').strip()
                        
                        if ',' in val_clean and '.' in val_clean:
                            # Format: "80.000,50" → remove dots (thousands), comma becomes dot (decimal)
                            val_clean = val_clean.replace('.', '').replace(',', '.')
                        elif ',' in val_clean:
                            # Format: "80000,50" → comma becomes dot
                            val_clean = val_clean.replace(',', '.')
                        
                        try:
                            return round(float(val_clean), 2)
                        except (ValueError, TypeError):
                            return 0.0
                    
                    return 0.0
                
                valor_total_conv = parse_value(valor_total_raw)
                valor_parcela_conv = parse_value(valor_parcela_raw)
                
                print(f"[DEBUG] Financiamento ID {record.get('ID')}: valor_parcela_raw={valor_parcela_raw}, valor_parcela_conv={valor_parcela_conv}")
                
                # Pega valor de entrada (nova coluna)
                valor_entrada_raw = record.get('Valor Entrada', 0)
                valor_entrada_conv = parse_value(valor_entrada_raw)
                
                fin = Financiamento(
                    record.get('ID'),
                    valor_total_conv,
                    valor_entrada_conv,
                    record.get('Numero Parcelas', 0),
                    valor_parcela_conv,
                    record.get('Taxa Juros', 0),
                    record.get('Data Inicio', ''),
                    record.get('Status', 'Ativo'),
                    record.get('Instituicao Financeira', ''),
                    record.get('Observacoes', ''),
                    record.get('Código Contrato', '') or record.get('Codigo Contrato', '')  # Suporta ambos
                )
                
                # Aplica filtros
                if status and fin.status != status:
                    continue
                if item_id and fin.item_id != int(item_id):
                    continue
                
                financiamentos.append(fin)
            except (ValueError, TypeError):
                continue
    
    return financiamentos


def buscar_financiamento_por_id(financiamento_id):
    """Busca um financiamento por ID"""
    financiamentos = listar_financiamentos()
    return next((f for f in financiamentos if f.id == financiamento_id), None)


def atualizar_financiamento(financiamento_id, valor_total=None, taxa_juros=None, status=None, instituicao_financeira=None, observacoes=None):
    """Atualiza um financiamento e recalcula parcelas se necessário"""
    sheets = get_sheets()
    sheet_financiamentos = sheets['sheet_financiamentos']
    sheet_parcelas = sheets['sheet_parcelas_financiamento']
    
    try:
        records = _retry_with_backoff(lambda: sheet_financiamentos.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "atualizar_financiamento")
    except (IndexError, KeyError):
        return None
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(financiamento_id):
            valores_antigos = record.copy()
            
            # Obtém valores atuais para recálculo
            valor_total_atual = valor_total if valor_total is not None else record.get('Valor Total', 0)
            taxa_juros_atual = taxa_juros if taxa_juros is not None else record.get('Taxa Juros', 0)
            numero_parcelas = record.get('Numero Parcelas', 0)
            
            # Se valor_total ou taxa_juros mudaram, precisa recalcular valor_parcela
            recalcular_parcelas = False
            novo_valor_parcela = None
            
            if valor_total is not None or taxa_juros is not None:
                # Recalcula valor da parcela usando Sistema Price
                valor_total_float = float(valor_total_atual)
                taxa_juros_float = float(taxa_juros_atual)
                
                if taxa_juros_float > 0 and numero_parcelas > 0:
                    i = taxa_juros_float
                    n = numero_parcelas
                    novo_valor_parcela = valor_total_float * (i * ((1 + i) ** n)) / (((1 + i) ** n) - 1)
                else:
                    novo_valor_parcela = valor_total_float / numero_parcelas if numero_parcelas > 0 else 0
                
                novo_valor_parcela = round(novo_valor_parcela, 2)
                recalcular_parcelas = True
            
            # Atualiza valores na planilha de financiamentos
            # Garante que valores sejam salvos como float, mesmo que sejam inteiros
            if valor_total is not None:
                valor_total_rounded = round(float(valor_total), 2)
                # Garante que valores inteiros sejam salvos como float
                if valor_total_rounded == int(valor_total_rounded):
                    valor_total_rounded = float(f"{valor_total_rounded:.2f}")
                sheet_financiamentos.update_cell(i, 3, valor_total_rounded)
            if taxa_juros is not None:
                sheet_financiamentos.update_cell(i, 6, float(taxa_juros))
            if novo_valor_parcela is not None:
                # Garante que valores inteiros sejam salvos como float
                if novo_valor_parcela == int(novo_valor_parcela):
                    novo_valor_parcela = float(f"{novo_valor_parcela:.2f}")
                sheet_financiamentos.update_cell(i, 5, novo_valor_parcela)  # Coluna 5 = Valor Parcela
            if status is not None:
                sheet_financiamentos.update_cell(i, 8, status)
            if instituicao_financeira is not None:
                sheet_financiamentos.update_cell(i, 9, instituicao_financeira)
            if observacoes is not None:
                sheet_financiamentos.update_cell(i, 10, observacoes)
            
            # Se precisa recalcular parcelas, atualiza todas as parcelas pendentes
            if recalcular_parcelas and novo_valor_parcela is not None:
                try:
                    parcelas_records = sheet_parcelas.get_all_records()
                    # Obtém cabeçalhos para encontrar a coluna correta
                    headers = sheet_parcelas.row_values(1)
                    valor_original_col = headers.index('Valor Original') + 1 if 'Valor Original' in headers else 4
                    
                    for idx, parcela_record in enumerate(parcelas_records, start=2):  # Começa na linha 2
                        if str(parcela_record.get('Financiamento ID')) == str(financiamento_id):
                            parcela_status = parcela_record.get('Status', 'Pendente')
                            # Só atualiza parcelas pendentes (não pagas)
                            if parcela_status in ['Pendente', 'Atrasada']:
                                # Garante que valores inteiros sejam salvos como float
                                valor_parcela_to_save = novo_valor_parcela
                                if valor_parcela_to_save == int(valor_parcela_to_save):
                                    valor_parcela_to_save = float(f"{valor_parcela_to_save:.2f}")
                                sheet_parcelas.update_cell(idx, valor_original_col, valor_parcela_to_save)
                except Exception as e:
                    # Se der erro ao atualizar parcelas, continua mesmo assim
                    print(f"Aviso: Erro ao atualizar parcelas: {e}")
            
            auditoria.registrar_auditoria('UPDATE', 'Financiamentos', financiamento_id, valores_antigos=valores_antigos, valores_novos={
                'valor_total': valor_total,
                'taxa_juros': taxa_juros,
                'status': status,
                'valor_parcela': novo_valor_parcela
            })
            
            _clear_cache()
            return buscar_financiamento_por_id(financiamento_id)
    
    return None


def deletar_financiamento(financiamento_id):
    """Deleta um financiamento, suas parcelas e relacionamentos com itens"""
    sheets = get_sheets()
    sheet_financiamentos = sheets['sheet_financiamentos']
    sheet_parcelas = sheets['sheet_parcelas_financiamento']
    sheet_fin_itens = sheets['sheet_financiamentos_itens']
    
    try:
        records = _retry_with_backoff(lambda: sheet_financiamentos.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "deletar_financiamento")
    except (IndexError, KeyError):
        return False
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(financiamento_id):
            valores_antigos = record.copy()
            
            # 1. Deleta relacionamentos Financiamento-Itens
            try:
                fin_itens_records = sheet_fin_itens.get_all_records()
                fin_itens_para_deletar = []
                for j, fin_item_record in enumerate(fin_itens_records, start=2):
                    if fin_item_record and str(fin_item_record.get('Financiamento ID')) == str(financiamento_id):
                        fin_itens_para_deletar.append(j)
                
                # Deleta de trás para frente para não afetar índices
                for idx in reversed(fin_itens_para_deletar):
                    sheet_fin_itens.delete_rows(idx)
                
                print(f"✅ Deletados {len(fin_itens_para_deletar)} relacionamentos Financiamento-Itens")
            except Exception as e:
                print(f"❌ Erro ao deletar Financiamento-Itens: {str(e)}")
                # Continua mesmo se não conseguir deletar relacionamentos
            
            # 2. Deleta parcelas
            try:
                parcelas_records = sheet_parcelas.get_all_records()
                parcelas_para_deletar = []
                for j, parcela_record in enumerate(parcelas_records, start=2):
                    if parcela_record and str(parcela_record.get('Financiamento ID')) == str(financiamento_id):
                        parcelas_para_deletar.append(j)
                
                # Deleta de trás para frente para não afetar índices
                for idx in reversed(parcelas_para_deletar):
                    sheet_parcelas.delete_rows(idx)
                
                print(f"✅ Deletadas {len(parcelas_para_deletar)} parcelas")
            except Exception as e:
                print(f"❌ Erro ao deletar parcelas: {str(e)}")
                # Continua mesmo se não conseguir deletar parcelas
            
            # 3. Deleta financiamento
            try:
                sheet_financiamentos.delete_rows(i)
                auditoria.registrar_auditoria('DELETE', 'Financiamentos', financiamento_id, valores_antigos=valores_antigos)
                _clear_cache()
                return True
            except gspread.exceptions.APIError as e:
                _handle_api_error(e, "deletar_financiamento")
    
    return False


def listar_parcelas_financiamento(financiamento_id=None, status=None):
    """Lista parcelas de financiamento com filtros opcionais"""
    sheets = get_sheets()
    sheet_parcelas = sheets['sheet_parcelas_financiamento']
    
    # Usa retry para lidar com erro 429
    try:
        records = _retry_with_backoff(lambda: sheet_parcelas.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_parcelas_financiamento")
    except (IndexError, KeyError):
        return []
    
    class ParcelaFinanciamento:
        def __init__(self, id, financiamento_id, numero_parcela, valor_original, valor_pago, data_vencimento, data_pagamento, status, link_boleto=None, link_comprovante=None):
            self.id = int(id) if id else None
            self.financiamento_id = int(financiamento_id) if financiamento_id else None
            self.numero_parcela = int(numero_parcela) if numero_parcela else 0
            # Função auxiliar para parse de valores
            def parse_val(val):
                if val is None:
                    return 0.0
                if isinstance(val, (int, float)):
                    val_float = float(val)
                    
                    # CORRECAO DEFINITIVA: Detecta valores com decimal faltando (1k-999k)
                    if 1000 <= val_float < 1000000:
                        cents_part = int(val_float) % 100
                        if cents_part != 0:
                            return round(val_float / 100, 2)
                    
                    # Para valores MUITO grandes (>= 1 milhão)
                    if val_float >= 1000000 and val_float < 1000000000:
                        for divisor in [100000, 10000, 1000, 100]:
                            test_val = val_float / divisor
                            if 1 <= test_val < 100000:
                                return round(test_val, 2)
                    
                    return round(val_float, 2)
                if isinstance(val, str):
                    val_clean = val.replace(' ', '').strip()
                    if ',' in val_clean:
                        if '.' in val_clean:
                            val_clean = val_clean.replace('.', '').replace(',', '.')
                        else:
                            val_clean = val_clean.replace(',', '.')
                    elif val_clean.count('.') > 1:
                        parts = val_clean.split('.')
                        val_clean = ''.join(parts[:-1]) + '.' + parts[-1]
                    try:
                        val_float = float(val_clean)
                        
                        # CORRECAO DEFINITIVA: Detecta valores com decimal faltando (1k-999k)
                        if 1000 <= val_float < 1000000:
                            cents_part = int(val_float) % 100
                            if cents_part != 0:
                                return round(val_float / 100, 2)
                        
                        # Para valores MUITO grandes (>= 1 milhão)
                        if val_float >= 1000000 and val_float < 1000000000:
                            for divisor in [100000, 10000, 1000, 100]:
                                test_val = val_float / divisor
                                if 1 <= test_val < 100000:
                                    return round(test_val, 2)
                        
                        return round(val_float, 2)
                    except (ValueError, TypeError):
                        return 0.0
                return round(float(val), 2)
            
            self.valor_original = parse_val(valor_original)
            self.valor_pago = parse_val(valor_pago)
            self.link_boleto = link_boleto or ''
            self.link_comprovante = link_comprovante or ''
            if isinstance(data_vencimento, str) and data_vencimento:
                try:
                    self.data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        self.data_vencimento = datetime.strptime(data_vencimento, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_vencimento = date.today()
            else:
                self.data_vencimento = data_vencimento if isinstance(data_vencimento, date) else date.today()
            
            if data_pagamento and isinstance(data_pagamento, str):
                try:
                    self.data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        self.data_pagamento = datetime.strptime(data_pagamento, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_pagamento = None
            else:
                self.data_pagamento = data_pagamento if isinstance(data_pagamento, date) else None
            
            # Recalcula status
            hoje = date.today()
            if self.valor_pago >= self.valor_original:
                self.status = 'Paga'
            elif self.data_vencimento < hoje:
                self.status = 'Atrasada'
            else:
                self.status = status or 'Pendente'
            
            self._financiamento_cache = None
        
        def _get_financiamento(self):
            if self._financiamento_cache is None:
                self._financiamento_cache = buscar_financiamento_por_id(self.financiamento_id)
            return self._financiamento_cache
        
        @property
        def financiamento(self):
            return self._get_financiamento()
    
    parcelas = []
    for record in records:
        if record and record.get('ID'):
            try:
                parcela = ParcelaFinanciamento(
                    record.get('ID'),
                    record.get('Financiamento ID'),
                    record.get('Numero Parcela', 0),
                    record.get('Valor Original', 0),
                    record.get('Valor Pago', 0),
                    record.get('Data Vencimento', ''),
                    record.get('Data Pagamento', ''),
                    record.get('Status', 'Pendente'),
                    record.get('Link Boleto', ''),
                    record.get('Link Comprovante', '')
                )
                
                # Aplica filtros
                if financiamento_id and parcela.financiamento_id != int(financiamento_id):
                    continue
                if status and parcela.status != status:
                    continue
                
                parcelas.append(parcela)
            except (ValueError, TypeError):
                continue
    
    return parcelas


def pagar_parcela_financiamento(parcela_id, valor_pago, data_pagamento=None, juros=0.0, multa=0.0, desconto=0.0):
    """Registra pagamento de uma parcela"""
    if data_pagamento is None:
        data_pagamento = date.today()
    
    sheets = get_sheets()
    sheet_parcelas = sheets['sheet_parcelas_financiamento']
    
    try:
        records = _retry_with_backoff(lambda: sheet_parcelas.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "pagar_parcela_financiamento")
    except (IndexError, KeyError):
        return None
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(parcela_id):
            valores_antigos = record.copy()
            
            valor_pago_total = float(valor_pago) + float(juros) + float(multa) - float(desconto)
            # Função auxiliar para parse de valores
            def parse_val_pagar(val):
                if val is None:
                    return 0.0
                if isinstance(val, (int, float)):
                    val_float = float(val)
                    
                    # CORRECAO DEFINITIVA: Detecta valores com decimal faltando (1k-999k)
                    if 1000 <= val_float < 1000000:
                        cents_part = int(val_float) % 100
                        if cents_part != 0:
                            return round(val_float / 100, 2)
                    
                    # Para valores MUITO grandes (>= 1 milhão)
                    if val_float >= 1000000 and val_float < 1000000000:
                        for divisor in [100000, 10000, 1000, 100]:
                            test_val = val_float / divisor
                            if 1 <= test_val < 100000:
                                return round(test_val, 2)
                    
                    return round(val_float, 2)
                if isinstance(val, str):
                    val_clean = val.replace(' ', '').strip()
                    if ',' in val_clean:
                        if '.' in val_clean:
                            val_clean = val_clean.replace('.', '').replace(',', '.')
                        else:
                            val_clean = val_clean.replace(',', '.')
                    elif val_clean.count('.') > 1:
                        parts = val_clean.split('.')
                        val_clean = ''.join(parts[:-1]) + '.' + parts[-1]
                    try:
                        val_float = float(val_clean)
                        
                        # CORRECAO DEFINITIVA: Detecta valores com decimal faltando (1k-999k)
                        if 1000 <= val_float < 1000000:
                            cents_part = int(val_float) % 100
                            if cents_part != 0:
                                return round(val_float / 100, 2)
                        
                        # Para valores MUITO grandes (>= 1 milhão)
                        if val_float >= 1000000 and val_float < 1000000000:
                            for divisor in [100000, 10000, 1000, 100]:
                                test_val = val_float / divisor
                                if 1 <= test_val < 100000:
                                    return round(test_val, 2)
                        
                        return round(val_float, 2)
                    except (ValueError, TypeError):
                        return 0.0
                return round(float(val), 2)
            valor_original = parse_val_pagar(record.get('Valor Original', 0))
            
            # Atualiza valores
            sheet_parcelas.update_cell(i, 5, valor_pago_total)  # Valor Pago
            sheet_parcelas.update_cell(i, 7, data_pagamento.strftime('%Y-%m-%d'))  # Data Pagamento
            sheet_parcelas.update_cell(i, 8, 'Paga' if valor_pago_total >= valor_original else 'Pendente')  # Status
            sheet_parcelas.update_cell(i, 9, float(juros))  # Juros
            sheet_parcelas.update_cell(i, 10, float(multa))  # Multa
            sheet_parcelas.update_cell(i, 11, float(desconto))  # Desconto
            
            # Verifica se financiamento foi quitado
            financiamento_id = record.get('Financiamento ID')
            if financiamento_id:
                parcelas = listar_parcelas_financiamento(financiamento_id=financiamento_id)
                todas_pagas = all(p.status == 'Paga' for p in parcelas)
                if todas_pagas:
                    atualizar_financiamento(financiamento_id, status='Quitado')
            
            auditoria.registrar_auditoria('UPDATE', 'Parcelas Financiamento', parcela_id, valores_antigos=valores_antigos, valores_novos={
                'valor_pago': valor_pago_total,
                'data_pagamento': str(data_pagamento)
            })
            
            _clear_cache()
            # Retorna a parcela atualizada corretamente
            parcelas_atualizadas = listar_parcelas_financiamento()
            parcela_atualizada = next((p for p in parcelas_atualizadas if p.id == parcela_id), None)
            return parcela_atualizada
    
    return None


def atualizar_parcela_financiamento(parcela_id, status=None, link_boleto=None, link_comprovante=None, valor_original=None, data_vencimento=None):
    """Atualiza uma parcela de financiamento"""
    sheets = get_sheets()
    sheet_parcelas = sheets['sheet_parcelas_financiamento']
    
    try:
        records = _retry_with_backoff(lambda: sheet_parcelas.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "atualizar_parcela_financiamento")
    except (IndexError, KeyError):
        return None
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(parcela_id):
            valores_antigos = record.copy()
            
            # Mapeia colunas (baseado nos headers SEM Juros, Multa, Desconto)
            # ID=1, Financiamento ID=2, Numero Parcela=3, Valor Original=4, Valor Pago=5, 
            # Data Vencimento=6, Data Pagamento=7, Status=8, Link Boleto=9, Link Comprovante=10
            
            if status is not None:
                sheet_parcelas.update_cell(i, 8, status)  # Status
            if link_boleto is not None:
                sheet_parcelas.update_cell(i, 9, link_boleto)  # Link Boleto
            if link_comprovante is not None:
                sheet_parcelas.update_cell(i, 10, link_comprovante)  # Link Comprovante
            if valor_original is not None:
                sheet_parcelas.update_cell(i, 4, float(valor_original))  # Valor Original
            if data_vencimento is not None:
                if isinstance(data_vencimento, date):
                    sheet_parcelas.update_cell(i, 6, data_vencimento.strftime('%Y-%m-%d'))  # Data Vencimento
                else:
                    sheet_parcelas.update_cell(i, 6, str(data_vencimento))
            
            auditoria.registrar_auditoria('UPDATE', 'Parcelas Financiamento', parcela_id, valores_antigos=valores_antigos, valores_novos={
                'status': status,
                'link_boleto': link_boleto,
                'valor_original': valor_original,
                'data_vencimento': str(data_vencimento) if data_vencimento else None
            })
            
            _clear_cache()
            parcelas_atualizadas = listar_parcelas_financiamento()
            return next((p for p in parcelas_atualizadas if p.id == parcela_id), None)
    
    return None


# ============= CONTAS A RECEBER =============

def criar_conta_receber(compromisso_id, descricao, valor, data_vencimento, forma_pagamento=None, observacoes=None):
    """Cria uma nova conta a receber vinculada a um compromisso"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_receber']
    sheet_compromissos = sheets['sheet_compromissos']
    
    # Verifica se compromisso existe
    try:
        compromissos = sheet_compromissos.get_all_records()
        compromisso_existe = any(str(c.get('ID')) == str(compromisso_id) for c in compromissos if c)
        if not compromisso_existe:
            raise ValueError(f"Compromisso {compromisso_id} não encontrado")
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_conta_receber")
    
    # Busca próximo ID
    try:
        all_records = sheet_contas.get_all_records()
        if all_records:
            valid_ids = [int(r.get('ID', 0)) for r in all_records if r and r.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except (IndexError, KeyError, ValueError):
        next_id = 1
    
    # Calcula status inicial
    hoje = date.today()
    status = 'Vencido' if data_vencimento < hoje else 'Pendente'
    
    # Formata data
    data_vencimento_str = data_vencimento.strftime('%Y-%m-%d') if isinstance(data_vencimento, date) else str(data_vencimento)
    
    try:
        sheet_contas.append_row([
            next_id,
            compromisso_id,
            descricao or '',
            float(valor),
            data_vencimento_str,
            '',  # Data Pagamento vazia
            status,
            forma_pagamento or '',
            observacoes or ''
        ])
        
        auditoria.registrar_auditoria('CREATE', 'Contas a Receber', next_id, valores_novos={
            'compromisso_id': compromisso_id,
            'descricao': descricao,
            'valor': valor,
            'data_vencimento': data_vencimento_str
        })
        
        _clear_cache()
        
        # Retorna objeto compatível
        class ContaReceber:
            def __init__(self, id, compromisso_id, descricao, valor, data_vencimento, data_pagamento, status, forma_pagamento, observacoes):
                self.id = int(id) if id else None
                self.compromisso_id = int(compromisso_id) if compromisso_id else None
                self.descricao = descricao or ''
                self.valor = float(valor) if valor else 0.0
                if isinstance(data_vencimento, str) and data_vencimento:
                    try:
                        self.data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            self.data_vencimento = datetime.strptime(data_vencimento, '%d/%m/%Y').date()
                        except ValueError:
                            self.data_vencimento = date.today()
                else:
                    self.data_vencimento = data_vencimento if isinstance(data_vencimento, date) else date.today()
                self.data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date() if data_pagamento and isinstance(data_pagamento, str) else (data_pagamento if isinstance(data_pagamento, date) else None)
                self.status = status or 'Pendente'
                self.forma_pagamento = forma_pagamento or ''
                self.observacoes = observacoes or ''
        
        return ContaReceber(next_id, compromisso_id, descricao, valor, data_vencimento_str, '', status, forma_pagamento, observacoes)
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_conta_receber")
    except Exception as e:
        raise Exception(f"Erro ao criar conta a receber: {str(e)}")


def listar_contas_receber(status=None, data_inicio=None, data_fim=None, compromisso_id=None):
    """Lista contas a receber com filtros opcionais"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_receber']
    
    try:
        records = sheet_contas.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_contas_receber")
    except (IndexError, KeyError):
        return []
    
    class ContaReceber:
        def __init__(self, id, compromisso_id, descricao, valor, data_vencimento, data_pagamento, status, forma_pagamento, observacoes):
            self.id = int(id) if id else None
            self.compromisso_id = int(compromisso_id) if compromisso_id else None
            self.descricao = descricao or ''
            self.valor = float(valor) if valor else 0.0
            if isinstance(data_vencimento, str) and data_vencimento:
                try:
                    self.data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        self.data_vencimento = datetime.strptime(data_vencimento, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_vencimento = date.today()
            else:
                self.data_vencimento = data_vencimento if isinstance(data_vencimento, date) else date.today()
            self.data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date() if data_pagamento and isinstance(data_pagamento, str) else (data_pagamento if isinstance(data_pagamento, date) else None)
            self.status = status or 'Pendente'
            self.forma_pagamento = forma_pagamento or ''
            self.observacoes = observacoes or ''
    
    contas = []
    hoje = date.today()
    
    for record in records:
        if not record or not record.get('ID'):
            continue
        
        conta = ContaReceber(
            record.get('ID'),
            record.get('Compromisso ID'),
            record.get('Descrição'),
            record.get('Valor'),
            record.get('Data Vencimento'),
            record.get('Data Pagamento'),
            record.get('Status'),
            record.get('Forma Pagamento'),
            record.get('Observações')
        )
        
        # Recalcula status
        if conta.data_pagamento:
            conta.status = 'Pago'
        elif conta.data_vencimento < hoje:
            conta.status = 'Vencido'
        else:
            conta.status = 'Pendente'
        
        # Aplica filtros
        if status and conta.status != status:
            continue
        if compromisso_id and conta.compromisso_id != compromisso_id:
            continue
        if data_inicio and conta.data_vencimento < data_inicio:
            continue
        if data_fim and conta.data_vencimento > data_fim:
            continue
        
        contas.append(conta)
    
    return contas


def atualizar_conta_receber(conta_id, descricao=None, valor=None, data_vencimento=None, data_pagamento=None, status=None, forma_pagamento=None, observacoes=None):
    """Atualiza uma conta a receber"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_receber']
    
    try:
        records = sheet_contas.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "atualizar_conta_receber")
    except (IndexError, KeyError):
        return None
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(conta_id):
            valores_antigos = record.copy()
            
            # Headers: ID=1, Compromisso ID=2, Descrição=3, Valor=4, Data Vencimento=5, 
            # Data Pagamento=6, Status=7, Forma Pagamento=8, Observações=9
            
            if descricao is not None:
                sheet_contas.update_cell(i, 3, descricao)
            if valor is not None:
                sheet_contas.update_cell(i, 4, float(valor))
            if data_vencimento is not None:
                if isinstance(data_vencimento, date):
                    sheet_contas.update_cell(i, 5, data_vencimento.strftime('%Y-%m-%d'))
                else:
                    sheet_contas.update_cell(i, 5, str(data_vencimento))
            if data_pagamento is not None:
                if isinstance(data_pagamento, date):
                    sheet_contas.update_cell(i, 6, data_pagamento.strftime('%Y-%m-%d'))
                else:
                    sheet_contas.update_cell(i, 6, str(data_pagamento) if data_pagamento else '')
            if forma_pagamento is not None:
                sheet_contas.update_cell(i, 8, forma_pagamento)
            if observacoes is not None:
                sheet_contas.update_cell(i, 9, observacoes)
            
            # Recalcula status
            hoje = date.today()
            if data_pagamento:
                novo_status = 'Pago'
            elif data_vencimento:
                data_venc = data_vencimento if isinstance(data_vencimento, date) else datetime.strptime(str(data_vencimento), '%Y-%m-%d').date()
                novo_status = 'Vencido' if data_venc < hoje else 'Pendente'
            elif status:
                novo_status = status
            else:
                # Usa data_vencimento do record atual
                data_venc_str = record.get('Data Vencimento', '')
                if data_venc_str:
                    try:
                        data_venc = datetime.strptime(data_venc_str, '%Y-%m-%d').date()
                        novo_status = 'Vencido' if data_venc < hoje else 'Pendente'
                    except:
                        novo_status = record.get('Status', 'Pendente')
                else:
                    novo_status = record.get('Status', 'Pendente')
            
            sheet_contas.update_cell(i, 7, novo_status)
            
            auditoria.registrar_auditoria('UPDATE', 'Contas a Receber', conta_id, valores_antigos=valores_antigos, valores_novos={
                'descricao': descricao,
                'valor': valor,
                'data_vencimento': str(data_vencimento) if data_vencimento else None,
                'data_pagamento': str(data_pagamento) if data_pagamento else None,
                'status': novo_status
            })
            
            _clear_cache()
            contas_atualizadas = listar_contas_receber()
            return next((c for c in contas_atualizadas if c.id == conta_id), None)
    
    return None


def marcar_conta_receber_paga(conta_id, data_pagamento=None, forma_pagamento=None):
    """Marca uma conta a receber como paga"""
    if data_pagamento is None:
        data_pagamento = date.today()
    return atualizar_conta_receber(conta_id, data_pagamento=data_pagamento, status='Pago', forma_pagamento=forma_pagamento)


def deletar_conta_receber(conta_id):
    """Deleta uma conta a receber"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_receber']
    
    try:
        records = sheet_contas.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "deletar_conta_receber")
    except (IndexError, KeyError):
        return False
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(conta_id):
            valores_antigos = record.copy()
            sheet_contas.delete_rows(i)
            
            auditoria.registrar_auditoria('DELETE', 'Contas a Receber', conta_id, valores_antigos=valores_antigos)
            _clear_cache()
            return True
    
    return False


# ============= CONTAS A PAGAR =============

def criar_conta_pagar(descricao, categoria, valor, data_vencimento, fornecedor=None, item_id=None, forma_pagamento=None, observacoes=None):
    """Cria uma nova conta a pagar"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_pagar']
    sheet_itens = sheets['sheet_itens']
    
    # Verifica se item existe (se fornecido)
    if item_id:
        try:
            itens = sheet_itens.get_all_records()
            item_existe = any(str(i.get('ID')) == str(item_id) for i in itens if i)
            if not item_existe:
                raise ValueError(f"Item {item_id} não encontrado")
        except gspread.exceptions.APIError as e:
            _handle_api_error(e, "criar_conta_pagar")
    
    # Busca próximo ID
    try:
        all_records = sheet_contas.get_all_records()
        if all_records:
            valid_ids = [int(r.get('ID', 0)) for r in all_records if r and r.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except (IndexError, KeyError, ValueError):
        next_id = 1
    
    # Calcula status inicial
    hoje = date.today()
    status = 'Vencido' if data_vencimento < hoje else 'Pendente'
    
    # Formata data
    data_vencimento_str = data_vencimento.strftime('%Y-%m-%d') if isinstance(data_vencimento, date) else str(data_vencimento)
    
    try:
        sheet_contas.append_row([
            next_id,
            descricao or '',
            categoria or '',
            float(valor),
            data_vencimento_str,
            '',  # Data Pagamento vazia
            status,
            fornecedor or '',
            item_id or '',
            forma_pagamento or '',
            observacoes or ''
        ])
        
        auditoria.registrar_auditoria('CREATE', 'Contas a Pagar', next_id, valores_novos={
            'descricao': descricao,
            'categoria': categoria,
            'valor': valor,
            'data_vencimento': data_vencimento_str
        })
        
        _clear_cache()
        
        # Retorna objeto compatível
        class ContaPagar:
            def __init__(self, id, descricao, categoria, valor, data_vencimento, data_pagamento, status, fornecedor, item_id, forma_pagamento, observacoes):
                self.id = int(id) if id else None
                self.descricao = descricao or ''
                self.categoria = categoria or ''
                self.valor = float(valor) if valor else 0.0
                if isinstance(data_vencimento, str) and data_vencimento:
                    try:
                        self.data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            self.data_vencimento = datetime.strptime(data_vencimento, '%d/%m/%Y').date()
                        except ValueError:
                            self.data_vencimento = date.today()
                else:
                    self.data_vencimento = data_vencimento if isinstance(data_vencimento, date) else date.today()
                self.data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date() if data_pagamento and isinstance(data_pagamento, str) else (data_pagamento if isinstance(data_pagamento, date) else None)
                self.status = status or 'Pendente'
                self.fornecedor = fornecedor or ''
                self.item_id = int(item_id) if item_id else None
                self.forma_pagamento = forma_pagamento or ''
                self.observacoes = observacoes or ''
        
        return ContaPagar(next_id, descricao, categoria, valor, data_vencimento_str, '', status, fornecedor, item_id, forma_pagamento, observacoes)
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_conta_pagar")
    except Exception as e:
        raise Exception(f"Erro ao criar conta a pagar: {str(e)}")


def listar_contas_pagar(status=None, data_inicio=None, data_fim=None, categoria=None):
    """Lista contas a pagar com filtros opcionais"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_pagar']
    
    try:
        records = sheet_contas.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_contas_pagar")
    except (IndexError, KeyError):
        return []
    
    class ContaPagar:
        def __init__(self, id, descricao, categoria, valor, data_vencimento, data_pagamento, status, fornecedor, item_id, forma_pagamento, observacoes):
            self.id = int(id) if id else None
            self.descricao = descricao or ''
            self.categoria = categoria or ''
            self.valor = float(valor) if valor else 0.0
            if isinstance(data_vencimento, str) and data_vencimento:
                try:
                    self.data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        self.data_vencimento = datetime.strptime(data_vencimento, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_vencimento = date.today()
            else:
                self.data_vencimento = data_vencimento if isinstance(data_vencimento, date) else date.today()
            self.data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date() if data_pagamento and isinstance(data_pagamento, str) else (data_pagamento if isinstance(data_pagamento, date) else None)
            self.status = status or 'Pendente'
            self.fornecedor = fornecedor or ''
            self.item_id = int(item_id) if item_id else None
            self.forma_pagamento = forma_pagamento or ''
            self.observacoes = observacoes or ''
    
    contas = []
    hoje = date.today()
    
    for record in records:
        if not record or not record.get('ID'):
            continue
        
        conta = ContaPagar(
            record.get('ID'),
            record.get('Descrição'),
            record.get('Categoria'),
            record.get('Valor'),
            record.get('Data Vencimento'),
            record.get('Data Pagamento'),
            record.get('Status'),
            record.get('Fornecedor'),
            record.get('Item ID'),
            record.get('Forma Pagamento'),
            record.get('Observações')
        )
        
        # Recalcula status
        if conta.data_pagamento:
            conta.status = 'Pago'
        elif conta.data_vencimento < hoje:
            conta.status = 'Vencido'
        else:
            conta.status = 'Pendente'
        
        # Aplica filtros
        if status and conta.status != status:
            continue
        if categoria and conta.categoria != categoria:
            continue
        if data_inicio and conta.data_vencimento < data_inicio:
            continue
        if data_fim and conta.data_vencimento > data_fim:
            continue
        
        contas.append(conta)
    
    return contas


def atualizar_conta_pagar(conta_id, descricao=None, categoria=None, valor=None, data_vencimento=None, data_pagamento=None, status=None, fornecedor=None, item_id=None, forma_pagamento=None, observacoes=None):
    """Atualiza uma conta a pagar"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_pagar']
    
    try:
        records = sheet_contas.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "atualizar_conta_pagar")
    except (IndexError, KeyError):
        return None
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(conta_id):
            valores_antigos = record.copy()
            
            # Headers: ID=1, Descrição=2, Categoria=3, Valor=4, Data Vencimento=5,
            # Data Pagamento=6, Status=7, Fornecedor=8, Item ID=9, Forma Pagamento=10, Observações=11
            
            if descricao is not None:
                sheet_contas.update_cell(i, 2, descricao)
            if categoria is not None:
                sheet_contas.update_cell(i, 3, categoria)
            if valor is not None:
                sheet_contas.update_cell(i, 4, float(valor))
            if data_vencimento is not None:
                if isinstance(data_vencimento, date):
                    sheet_contas.update_cell(i, 5, data_vencimento.strftime('%Y-%m-%d'))
                else:
                    sheet_contas.update_cell(i, 5, str(data_vencimento))
            if data_pagamento is not None:
                if isinstance(data_pagamento, date):
                    sheet_contas.update_cell(i, 6, data_pagamento.strftime('%Y-%m-%d'))
                else:
                    sheet_contas.update_cell(i, 6, str(data_pagamento) if data_pagamento else '')
            if fornecedor is not None:
                sheet_contas.update_cell(i, 8, fornecedor)
            if item_id is not None:
                sheet_contas.update_cell(i, 9, item_id if item_id else '')
            if forma_pagamento is not None:
                sheet_contas.update_cell(i, 10, forma_pagamento)
            if observacoes is not None:
                sheet_contas.update_cell(i, 11, observacoes)
            
            # Recalcula status
            hoje = date.today()
            if data_pagamento:
                novo_status = 'Pago'
            elif data_vencimento:
                data_venc = data_vencimento if isinstance(data_vencimento, date) else datetime.strptime(str(data_vencimento), '%Y-%m-%d').date()
                novo_status = 'Vencido' if data_venc < hoje else 'Pendente'
            elif status:
                novo_status = status
            else:
                # Usa data_vencimento do record atual
                data_venc_str = record.get('Data Vencimento', '')
                if data_venc_str:
                    try:
                        data_venc = datetime.strptime(data_venc_str, '%Y-%m-%d').date()
                        novo_status = 'Vencido' if data_venc < hoje else 'Pendente'
                    except:
                        novo_status = record.get('Status', 'Pendente')
                else:
                    novo_status = record.get('Status', 'Pendente')
            
            sheet_contas.update_cell(i, 7, novo_status)
            
            auditoria.registrar_auditoria('UPDATE', 'Contas a Pagar', conta_id, valores_antigos=valores_antigos, valores_novos={
                'descricao': descricao,
                'categoria': categoria,
                'valor': valor,
                'data_vencimento': str(data_vencimento) if data_vencimento else None,
                'data_pagamento': str(data_pagamento) if data_pagamento else None,
                'status': novo_status
            })
            
            _clear_cache()
            contas_atualizadas = listar_contas_pagar()
            return next((c for c in contas_atualizadas if c.id == conta_id), None)
    
    return None


def marcar_conta_pagar_paga(conta_id, data_pagamento=None, forma_pagamento=None):
    """Marca uma conta a pagar como paga"""
    if data_pagamento is None:
        data_pagamento = date.today()
    return atualizar_conta_pagar(conta_id, data_pagamento=data_pagamento, status='Pago', forma_pagamento=forma_pagamento)


def deletar_conta_pagar(conta_id):
    """Deleta uma conta a pagar"""
    sheets = get_sheets()
    sheet_contas = sheets['sheet_contas_pagar']
    
    try:
        records = sheet_contas.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "deletar_conta_pagar")
    except (IndexError, KeyError):
        return False
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(conta_id):
            valores_antigos = record.copy()
            sheet_contas.delete_rows(i)
            
            auditoria.registrar_auditoria('DELETE', 'Contas a Pagar', conta_id, valores_antigos=valores_antigos)
            _clear_cache()
            return True
    
    return False


# ============= FUNÇÕES DE CÁLCULO FINANCEIRO =============

def calcular_saldo_periodo(data_inicio, data_fim):
    """Calcula saldo (receitas - despesas) em um período"""
    receitas = listar_contas_receber(data_inicio=data_inicio, data_fim=data_fim)
    despesas = listar_contas_pagar(data_inicio=data_inicio, data_fim=data_fim)
    
    receitas_pagas = sum(c.valor for c in receitas if c.status == 'Pago')
    despesas_pagas = sum(c.valor for c in despesas if c.status == 'Pago')
    
    return {
        'receitas': receitas_pagas,
        'despesas': despesas_pagas,
        'saldo': receitas_pagas - despesas_pagas,
        'total_receitas': len(receitas),
        'total_despesas': len(despesas)
    }


def obter_fluxo_caixa(data_inicio, data_fim):
    """Retorna fluxo de caixa por período (agrupado por mês)"""
    receitas = listar_contas_receber(data_inicio=data_inicio, data_fim=data_fim)
    despesas = listar_contas_pagar(data_inicio=data_inicio, data_fim=data_fim)
    
    fluxo = {}
    
    for conta in receitas:
        if conta.status == 'Pago':
            mes = conta.data_pagamento.strftime('%Y-%m') if conta.data_pagamento else conta.data_vencimento.strftime('%Y-%m')
            if mes not in fluxo:
                fluxo[mes] = {'receitas': 0, 'despesas': 0}
            fluxo[mes]['receitas'] += conta.valor
    
    for conta in despesas:
        if conta.status == 'Pago':
            mes = conta.data_pagamento.strftime('%Y-%m') if conta.data_pagamento else conta.data_vencimento.strftime('%Y-%m')
            if mes not in fluxo:
                fluxo[mes] = {'receitas': 0, 'despesas': 0}
            fluxo[mes]['despesas'] += conta.valor
    
    # Converte para lista ordenada
    resultado = []
    for mes in sorted(fluxo.keys()):
        resultado.append({
            'mes': mes,
            'receitas': fluxo[mes]['receitas'],
            'despesas': fluxo[mes]['despesas'],
            'saldo': fluxo[mes]['receitas'] - fluxo[mes]['despesas']
        })
    
    return resultado


# ============= PEÇAS EM CARROS =============

def criar_peca_carro(peca_id, carro_id, quantidade=1, data_instalacao=None, observacoes=None):
    """Associa uma peça a um carro"""
    sheets = get_sheets()
    spreadsheet = sheets['spreadsheet']
    
    # Obtém ou cria aba de Peças em Carros
    try:
        sheet_pecas_carros = spreadsheet.worksheet("Pecas_Carros")
    except gspread.exceptions.WorksheetNotFound:
        sheet_pecas_carros = spreadsheet.add_worksheet(title="Pecas_Carros", rows=1000, cols=10)
        sheet_pecas_carros.append_row(["ID", "Peca ID", "Carro ID", "Quantidade", "Data Instalacao", "Observacoes"])
    
    # Verifica se peça e carro existem
    try:
        itens = listar_itens()
        peca = next((i for i in itens if i.id == peca_id), None)
        carro = next((i for i in itens if i.id == carro_id), None)
        
        if not peca:
            raise ValueError(f"Peça {peca_id} não encontrada")
        if peca.categoria != "Peças de Carro":
            raise ValueError(f"Item {peca_id} não é uma peça de carro (categoria: {peca.categoria})")
        
        if not carro:
            raise ValueError(f"Carro {carro_id} não encontrado")
        if carro.categoria != "Carros":
            raise ValueError(f"Item {carro_id} não é um carro (categoria: {carro.categoria})")
    except Exception as e:
        raise ValueError(f"Erro ao verificar itens: {str(e)}")
    
    # Gera próximo ID
    try:
        all_records = _retry_with_backoff(lambda: sheet_pecas_carros.get_all_records())
        if all_records:
            valid_ids = [int(record.get('ID', 0)) for record in all_records if record and record.get('ID')]
            next_id = max(valid_ids) + 1 if valid_ids else 1
        else:
            next_id = 1
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_peca_carro (buscar próximo ID)")
    except (IndexError, KeyError, ValueError):
        next_id = 1
    
    # Formata data
    if data_instalacao is None:
        data_instalacao = date.today()
    data_instalacao_str = data_instalacao.strftime('%Y-%m-%d') if isinstance(data_instalacao, date) else str(data_instalacao)
    
    # Adiciona associação
    try:
        sheet_pecas_carros.append_row([
            next_id,
            peca_id,
            carro_id,
            quantidade,
            data_instalacao_str,
            observacoes or ''
        ])
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_peca_carro (adicionar linha)")
    
    # Limpa cache
    _clear_cache()
    
    # Retorna objeto similar ao modelo PecaCarro
    class PecaCarro:
        def __init__(self, id, peca_id, carro_id, quantidade, data_instalacao, observacoes):
            self.id = int(id)
            self.peca_id = int(peca_id)
            self.carro_id = int(carro_id)
            self.quantidade = int(quantidade)
            if isinstance(data_instalacao, str) and data_instalacao:
                try:
                    self.data_instalacao = datetime.strptime(data_instalacao, '%Y-%m-%d').date()
                except ValueError:
                    self.data_instalacao = date.today()
            else:
                self.data_instalacao = data_instalacao if isinstance(data_instalacao, date) else date.today()
            self.observacoes = observacoes or ''
    
    return PecaCarro(next_id, peca_id, carro_id, quantidade, data_instalacao_str, observacoes)


def listar_pecas_carros(carro_id=None, peca_id=None):
    """Lista associações de peças em carros com filtros opcionais"""
    sheets = get_sheets()
    spreadsheet = sheets['spreadsheet']
    
    # Obtém aba de Peças em Carros
    try:
        sheet_pecas_carros = spreadsheet.worksheet("Pecas_Carros")
    except gspread.exceptions.WorksheetNotFound:
        return []
    
    try:
        records = _retry_with_backoff(lambda: sheet_pecas_carros.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_pecas_carros")
    except (IndexError, KeyError):
        return []
    
    class PecaCarro:
        def __init__(self, id, peca_id, carro_id, quantidade, data_instalacao, observacoes):
            self.id = int(id) if id else None
            self.peca_id = int(peca_id) if peca_id else None
            self.carro_id = int(carro_id) if carro_id else None
            self.quantidade = int(quantidade) if quantidade else 1
            if isinstance(data_instalacao, str) and data_instalacao:
                try:
                    self.data_instalacao = datetime.strptime(data_instalacao, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        self.data_instalacao = datetime.strptime(data_instalacao, '%d/%m/%Y').date()
                    except ValueError:
                        self.data_instalacao = date.today()
            else:
                self.data_instalacao = data_instalacao if isinstance(data_instalacao, date) else date.today()
            self.observacoes = observacoes or ''
    
    associacoes = []
    for record in records:
        if record and record.get('ID'):
            try:
                associacao = PecaCarro(
                    record.get('ID'),
                    record.get('Peca ID'),
                    record.get('Carro ID'),
                    record.get('Quantidade', 1),
                    record.get('Data Instalacao', ''),
                    record.get('Observacoes', '')
                )
                
                # Aplica filtros
                if carro_id and associacao.carro_id != int(carro_id):
                    continue
                if peca_id and associacao.peca_id != int(peca_id):
                    continue
                
                associacoes.append(associacao)
            except (ValueError, TypeError):
                continue
    
    return associacoes


def buscar_peca_carro_por_id(associacao_id):
    """Busca uma associação peça-carro por ID"""
    associacoes = listar_pecas_carros()
    return next((a for a in associacoes if a.id == associacao_id), None)


def atualizar_peca_carro(associacao_id, quantidade=None, data_instalacao=None, observacoes=None):
    """Atualiza uma associação peça-carro"""
    sheets = get_sheets()
    spreadsheet = sheets['spreadsheet']
    
    try:
        sheet_pecas_carros = spreadsheet.worksheet("Pecas_Carros")
    except gspread.exceptions.WorksheetNotFound:
        return None
    
    try:
        records = _retry_with_backoff(lambda: sheet_pecas_carros.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "atualizar_peca_carro")
    except (IndexError, KeyError):
        return None
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(associacao_id):
            valores_antigos = record.copy()
            
            # Atualiza valores
            if quantidade is not None:
                sheet_pecas_carros.update_cell(i, 4, int(quantidade))
            if data_instalacao is not None:
                data_str = data_instalacao.strftime('%Y-%m-%d') if isinstance(data_instalacao, date) else str(data_instalacao)
                sheet_pecas_carros.update_cell(i, 5, data_str)
            if observacoes is not None:
                sheet_pecas_carros.update_cell(i, 6, observacoes)
            
            # Limpa cache
            _clear_cache()
            
            # Retorna associação atualizada
            return buscar_peca_carro_por_id(associacao_id)
    
    return None


def deletar_peca_carro(associacao_id):
    """Remove uma associação peça-carro"""
    sheets = get_sheets()
    spreadsheet = sheets['spreadsheet']
    
    try:
        sheet_pecas_carros = spreadsheet.worksheet("Pecas_Carros")
    except gspread.exceptions.WorksheetNotFound:
        return False
    
    try:
        records = _retry_with_backoff(lambda: sheet_pecas_carros.get_all_records())
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "deletar_peca_carro")
    except (IndexError, KeyError):
        return False
    
    for i, record in enumerate(records, start=2):
        if record and str(record.get('ID')) == str(associacao_id):
            valores_antigos = record.copy()
            
            try:
                sheet_pecas_carros.delete_rows(i)
                auditoria.registrar_auditoria('DELETE', 'Pecas_Carros', associacao_id, valores_antigos=valores_antigos)
                _clear_cache()
                return True
            except gspread.exceptions.APIError as e:
                _handle_api_error(e, "deletar_peca_carro (deletar linha)")
    
    return False
