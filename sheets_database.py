"""
Implementação do banco de dados usando Google Sheets
"""
from sheets_config import init_sheets
from datetime import date, datetime
import os

# Cache das planilhas
_sheets_cache = None

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


def criar_item(nome, quantidade_total, descricao=None, localizacao=None):
    """Cria um novo item no estoque"""
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
    except (IndexError, KeyError, ValueError):
        # Se a aba estiver vazia ou sem dados válidos, começa do ID 1
        next_id = 1
    
    # Adiciona novo item
    sheet_itens.append_row([next_id, nome, quantidade_total, descricao or '', localizacao or ''])
    
    # Retorna objeto similar ao modelo Item
    class Item:
        def __init__(self, id, nome, quantidade_total, descricao=None, localizacao=None):
            self.id = id
            self.nome = nome
            self.quantidade_total = quantidade_total
            self.descricao = descricao or ''
            self.localizacao = localizacao or ''
            self.compromissos = []
    
    return Item(next_id, nome, quantidade_total, descricao, localizacao)


def listar_itens():
    """Lista todos os itens do estoque"""
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    try:
        # Tenta obter todos os registros
        records = sheet_itens.get_all_records()
    except (IndexError, KeyError):
        # Se a aba estiver vazia ou sem cabeçalhos, retorna lista vazia
        return []
    
    class Item:
        def __init__(self, id, nome, quantidade_total, descricao=None, localizacao=None):
            self.id = int(id) if id else None
            self.nome = nome
            self.quantidade_total = int(quantidade_total) if quantidade_total else 0
            self.descricao = descricao or ''
            self.localizacao = localizacao or ''
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
                    record.get('Localização', '')
                ))
            except (ValueError, TypeError):
                # Ignora registros inválidos
                continue
    
    return itens


def buscar_item_por_id(item_id):
    """Busca um item pelo ID"""
    itens = listar_itens()
    for item in itens:
        if item.id == int(item_id):
            return item
    return None


def atualizar_item(item_id, nome, quantidade_total, descricao=None, localizacao=None):
    """Atualiza um item existente"""
    sheets = get_sheets()
    sheet_itens = sheets['sheet_itens']
    
    try:
        records = sheet_itens.get_all_records()
    except (IndexError, KeyError):
        return False
    
    # Busca a linha do item
    row_to_update = None
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(item_id):
            row_to_update = idx
            break
    
    if row_to_update:
        # Atualiza a linha com os novos valores (incluindo descrição e localização)
        sheet_itens.update(f'A{row_to_update}:E{row_to_update}', [[item_id, nome, quantidade_total, descricao or '', localizacao or '']])
        return True
    
    return False


def criar_compromisso(item_id, quantidade, data_inicio, data_fim, descricao=None, localizacao=None, contratante=None):
    """Cria um novo compromisso (aluguel)"""
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
    sheet_compromissos.append_row([
        next_id,
        item_id,
        quantidade,
        data_inicio_str,
        data_fim_str,
        descricao or '',
        localizacao or '',
        contratante or ''
    ])
    
    # Retorna objeto similar ao modelo Compromisso
    class Compromisso:
        def __init__(self, id, item_id, quantidade, data_inicio, data_fim, descricao, localizacao=None, contratante=None):
            self.id = id
            self.item_id = int(item_id)
            self.quantidade = int(quantidade)
            self.data_inicio = data_inicio if isinstance(data_inicio, date) else datetime.strptime(data_inicio, '%Y-%m-%d').date()
            self.data_fim = data_fim if isinstance(data_fim, date) else datetime.strptime(data_fim, '%Y-%m-%d').date()
            self.descricao = descricao or ''
            self.localizacao = localizacao or ''
            self.contratante = contratante or ''
            # Carrega o item relacionado
            self.item = buscar_item_por_id(item_id)
    
    return Compromisso(next_id, item_id, quantidade, data_inicio, data_fim, descricao, localizacao, contratante)


def listar_compromissos():
    """Lista todos os compromissos"""
    sheets = get_sheets()
    sheet_compromissos = sheets['sheet_compromissos']
    
    try:
        # Tenta obter todos os registros
        records = sheet_compromissos.get_all_records()
    except (IndexError, KeyError):
        # Se a aba estiver vazia ou sem cabeçalhos, retorna lista vazia
        return []
    
    class Compromisso:
        def __init__(self, id, item_id, quantidade, data_inicio, data_fim, descricao, localizacao=None, contratante=None):
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
            self.localizacao = localizacao or ''
            self.contratante = contratante or ''
            # Carrega o item relacionado
            self.item = buscar_item_por_id(item_id) if item_id else None
    
    compromissos = []
    for record in records:
        # Verifica se o registro tem os campos necessários
        if record and record.get('ID') and record.get('Item ID'):
            try:
                compromissos.append(Compromisso(
                    record.get('ID'),
                    record.get('Item ID'),
                    record.get('Quantidade', 0),
                    record.get('Data Início', ''),
                    record.get('Data Fim', ''),
                    record.get('Descrição', ''),
                    record.get('Localização', ''),
                    record.get('Contratante', '')
                ))
            except (ValueError, TypeError) as e:
                # Ignora registros inválidos
                continue
    
    return compromissos


def verificar_disponibilidade(item_id, data_consulta):
    """Verifica a disponibilidade de um item em uma data específica"""
    item = buscar_item_por_id(item_id)
    if not item:
        return None
    
    compromissos = listar_compromissos()
    
    # Filtra compromissos ativos na data de consulta para este item
    compromissos_ativos = [
        c for c in compromissos
        if c.item_id == int(item_id) and c.data_inicio <= data_consulta <= c.data_fim
    ]
    
    quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
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


def verificar_disponibilidade_todos_itens(data_consulta):
    """Verifica a disponibilidade de todos os itens em uma data específica"""
    itens = listar_itens()
    compromissos = listar_compromissos()
    
    resultados = []
    
    for item in itens:
        compromissos_ativos = [
            c for c in compromissos
            if c.item_id == item.id and c.data_inicio <= data_consulta <= c.data_fim
        ]
        
        quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
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


def deletar_compromisso(compromisso_id):
    """Deleta um compromisso"""
    sheets = get_sheets()
    sheet_compromissos = sheets['sheet_compromissos']
    
    # Busca a linha do compromisso
    try:
        records = sheet_compromissos.get_all_records()
    except (IndexError, KeyError):
        # Se a aba estiver vazia, não há nada para deletar
        return False
    
    for idx, record in enumerate(records, start=2):  # Começa em 2 porque linha 1 é cabeçalho
        if record and str(record.get('ID')) == str(compromisso_id):
            sheet_compromissos.delete_rows(idx)
            return True
    
    return False
