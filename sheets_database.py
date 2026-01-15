"""
Implementação do banco de dados usando Google Sheets
"""
from sheets_config import init_sheets
from datetime import date, datetime
import os
import time
import gspread

# Cache das planilhas
_sheets_cache = None

# Cache de dados para reduzir chamadas à API
_data_cache = {
    'itens': None,
    'compromissos': None,
    'cache_time': None,
    'cache_ttl': 30  # Time to live em segundos
}

def _clear_cache():
    """Limpa o cache de dados"""
    global _data_cache
    _data_cache = {
        'itens': None,
        'compromissos': None,
        'cache_time': None,
        'cache_ttl': 30
    }

def _is_cache_valid():
    """Verifica se o cache ainda é válido"""
    if _data_cache['cache_time'] is None:
        return False
    return (time.time() - _data_cache['cache_time']) < _data_cache['cache_ttl']

def _handle_api_error(e, operation_name):
    """Trata erros da API do Google Sheets"""
    if isinstance(e, gspread.exceptions.APIError):
        # Tenta extrair informações do erro
        error_code = getattr(e, 'response', {}).get('status', 0) if hasattr(e, 'response') else 0
        error_message = str(e)
        
        # Verifica se é erro 429 (quota exceeded)
        if error_code == 429 or '429' in error_message or 'Quota exceeded' in error_message or 'RATE_LIMIT_EXCEEDED' in error_message:
            raise Exception(
                f"⚠️ Limite de Requisições do Google Sheets Excedido!\n\n"
                f"O Google Sheets tem um limite de 60 requisições de leitura por minuto.\n\n"
                f"Operação: {operation_name}\n\n"
                f"Soluções:\n"
                f"1. Aguarde 1-2 minutos antes de tentar novamente\n"
                f"2. Evite fazer muitas operações em sequência\n"
                f"3. Use SQLite local para desenvolvimento/testes (configure USE_GOOGLE_SHEETS=false)\n"
                f"4. Solicite aumento de quota no Google Cloud Console se necessário"
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


def criar_item(nome, quantidade_total, descricao=None, cidade=None, uf=None, endereco=None):
    """Cria um novo item no estoque
    
    Args:
        nome: Nome do item
        quantidade_total: Quantidade total disponível
        descricao: Descrição opcional do item
        cidade: Cidade onde o item está localizado (obrigatório)
        uf: UF onde o item está localizado (obrigatório)
        endereco: Endereço opcional do item
    """
    if not cidade or not uf:
        raise ValueError("Cidade e UF são obrigatórios")
    
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
        sheet_itens.append_row([next_id, nome, quantidade_total, descricao or '', cidade, uf.upper()[:2], endereco or ''])
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "criar_item (adicionar linha)")
    
    # Limpa cache para forçar atualização na próxima leitura
    _clear_cache()
    
    # Retorna objeto similar ao modelo Item
    class Item:
        def __init__(self, id, nome, quantidade_total, descricao=None, cidade=None, uf=None, endereco=None):
            self.id = id
            self.nome = nome
            self.quantidade_total = quantidade_total
            self.descricao = descricao or ''
            self.cidade = cidade or ''
            self.uf = (uf or '').upper()[:2]
            self.endereco = endereco or ''
            self.compromissos = []
    
    return Item(next_id, nome, quantidade_total, descricao, cidade, uf, endereco)


def listar_itens():
    """Lista todos os itens do estoque"""
    # Verifica cache primeiro
    if _is_cache_valid() and _data_cache['itens'] is not None:
        return _data_cache['itens']
    
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    try:
        # Tenta obter todos os registros
        records = sheet_itens.get_all_records()
    except gspread.exceptions.APIError as e:
        _handle_api_error(e, "listar_itens")
    except (IndexError, KeyError):
        # Se a aba estiver vazia ou sem cabeçalhos, retorna lista vazia
        return []
    
    class Item:
        def __init__(self, id, nome, quantidade_total, descricao=None, cidade=None, uf=None, endereco=None):
            self.id = int(id) if id else None
            self.nome = nome
            self.quantidade_total = int(quantidade_total) if quantidade_total else 0
            self.descricao = descricao or ''
            self.cidade = cidade or ''
            self.uf = (uf or '').upper()[:2]
            self.endereco = endereco or ''
            self.compromissos = []
    
    itens = []
    for record in records:
        # Verifica se o registro tem os campos necessários
        if record and record.get('ID') and record.get('Nome'):
            try:
                itens.append(Item(
                    record.get('ID'),
                    record.get('Nome'),
                    record.get('Quantidade Total', 0),
                    record.get('Descrição', ''),
                    record.get('Cidade', ''),
                    record.get('UF', ''),
                    record.get('Endereço', '')
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


def atualizar_item(item_id, nome, quantidade_total, descricao=None, cidade=None, uf=None, endereco=None):
    """Atualiza um item existente
    
    Args:
        item_id: ID do item
        nome: Nome do item
        quantidade_total: Quantidade total disponível
        descricao: Descrição opcional do item
        cidade: Cidade onde o item está localizado (obrigatório)
        uf: UF onde o item está localizado (obrigatório)
        endereco: Endereço opcional do item
    """
    if not cidade or not uf:
        raise ValueError("Cidade e UF são obrigatórios")
    
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    try:
        records = sheet_itens.get_all_records()
    except (IndexError, KeyError):
        return None
    
    # Busca a linha do item
    row_to_update = None
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(item_id):
            row_to_update = idx
            break
    
    if row_to_update:
        # Atualiza a linha com os novos valores (incluindo descrição, cidade, uf e endereço)
        sheet_itens.update(f'A{row_to_update}:G{row_to_update}', [[item_id, nome, quantidade_total, descricao or '', cidade, uf.upper()[:2], endereco or '']])
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
    
    try:
        # Tenta obter todos os registros
        records = sheet_compromissos.get_all_records()
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
        sheet_itens.delete_rows(row_to_delete)
        
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
    if not cidade or not uf:
        raise ValueError("Cidade e UF são obrigatórios")
    
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
                sheet_compromissos.delete_rows(idx)
                # Limpa cache para forçar atualização na próxima leitura
                _clear_cache()
                return True
            except gspread.exceptions.APIError as e:
                _handle_api_error(e, "deletar_compromisso (deletar linha)")
    
    return False
