import os
import re
from datetime import date, datetime, timedelta
import calendar
import validacoes
import auditoria
from types import SimpleNamespace

_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL e chaves de acesso devem estar configurados.")
        from supabase import create_client
        _supabase_client = create_client(url, key)
    return _supabase_client

# --- HELPERS E DINAMISMO ---

def _date_parse(d):
    if d is None: return None
    if isinstance(d, date): return d
    if isinstance(d, str):
        try: return datetime.strptime(d[:10], '%Y-%m-%d').date()
        except: return None
    return d

def _slug_categoria(text):
    if not text: return ""
    return re.sub(r'[^a-z0-9_]', '', text.strip().lower().replace(' ', '_'))

def _slugify_label(text):
    return _slug_categoria(text)

def _labelify_column(text):
    return text.replace('_', ' ').title()

def registrar_movimentacao(item_id, quantidade, tipo, ref_id=None, desc=""):
    """Registra histórico: COMPRA, ALUGUEL_SAIDA, ALUGUEL_RETORNO, INSTALACAO, REMOCAO_PECA."""
    try:
        sb = get_supabase()
        sb.table('movimentacoes_estoque').insert({
            'item_id': int(item_id), 'quantidade': int(quantidade),
            'tipo': tipo, 'referencia_id': ref_id, 'descricao': desc,
            'data_movimentacao': datetime.now().isoformat()
        }).execute()
    except: pass

# --- MAPEAMENTO DE OBJETOS (CLASSES INTERNAS) ---

def _row_to_item(record, dados_categoria=None):
    class Item:
        def __init__(self):
            self.id = record.get('id')
            self.nome = record.get('nome', '')
            self.quantidade_total = record.get('quantidade_total') or 0
            self.categoria = record.get('categoria') or ''
            self.descricao = record.get('descricao') or ''
            self.cidade = record.get('cidade') or ''
            self.uf = (record.get('uf') or '')[:2].upper()
            self.endereco = record.get('endereco') or ''
            self.valor_compra = float(record.get('valor_compra') or 0.0)
            self.data_aquisicao = _date_parse(record.get('data_aquisicao'))
            self.dados_categoria = dados_categoria or record.get('dados_categoria') or {}
    return Item()

def _row_to_compromisso(record, item=None):
    class Compromisso:
        def __init__(self):
            self.id = record.get('id'); self.item_id = record.get('item_id')
            self.quantidade = record.get('quantidade') or 0
            self.data_inicio = _date_parse(record.get('data_inicio'))
            self.data_fim = _date_parse(record.get('data_fim'))
            self.descricao = record.get('descricao') or ''
            self.cidade = record.get('cidade') or ''
            self.uf = (record.get('uf') or '')[:2].upper()
            self.endereco = record.get('endereco') or ''
            self.contratante = record.get('contratante') or ''
            self._item = item
        @property
        def item(self):
            if self._item is None and self.item_id: self._item = buscar_item_por_id(self.item_id)
            return self._item
    return Compromisso()

# --- GESTÃO DE CATEGORIAS ---

def obter_categorias():
    sb = get_supabase()
    r = sb.table('categorias_itens').select('nome').order('nome').execute()
    return sorted([row['nome'] for row in (r.data or []) if row.get('nome')])

def obter_campos_categoria(categoria):
    """Lê as colunas reais da tabela no Supabase via RPC."""
    sb = get_supabase(); slug = _slug_categoria(categoria)
    try:
        r = sb.rpc('get_table_columns', {'t_name': slug}).execute()
        colunas = [row['column_name'] for row in (r.data or [])]
        ignore = ['id', 'item_id', 'created_at', 'dados_categoria']
        return [_labelify_column(c) for c in colunas if c not in ignore]
    except:
        return []

# --- CRUD DE ITENS (ESTOQUE) ---

def criar_item(nome, quantidade_total, categoria=None, valor_compra=0.0, data_aquisicao=None, **kwargs):
    sb = get_supabase()
    cat = categoria or 'Estrutura de Evento'
    campos_extra = kwargs.get('campos_categoria', {})
    
    # --- CURA PARA O ERRO 500 (JSON SERIALIZABLE) ---
    # Transforma o objeto date em string "AAAA-MM-DD" antes de enviar pro Supabase
    dt_fix = data_aquisicao
    if hasattr(dt_fix, 'isoformat'):
        dt_fix = dt_fix.isoformat()
    elif not dt_fix:
        dt_fix = date.today().isoformat()

    payload = {
        'nome': nome, 
        'quantidade_total': int(quantidade_total), 
        'categoria': cat,
        'valor_compra': float(valor_compra or 0.0), 
        'data_aquisicao': dt_fix, # Agora é uma string segura!
        'descricao': kwargs.get('descricao', ''), 
        'cidade': kwargs.get('cidade', ''),
        'uf': (kwargs.get('uf', ''))[:2].upper(), 
        'endereco': kwargs.get('endereco', ''),
        'dados_categoria': campos_extra
    }
    
    ins = sb.table('itens').insert(payload).execute()
    if not ins.data: raise Exception("Falha ao inserir no banco")
    
    item_id = ins.data[0]['id']
    registrar_movimentacao(item_id, quantidade_total, 'COMPRA')
    
    slug = _slug_categoria(cat)
    if slug and slug != 'itens':
        p_spec = {'item_id': item_id}
        for k, v in campos_extra.items(): p_spec[_slugify_label(k)] = v
        try: sb.table(slug).insert(p_spec).execute()
        except: pass
        
    return buscar_item_por_id(item_id)

def atualizar_item(item_id, nome, quantidade_total, categoria=None, **kwargs):
    sb = get_supabase()
    
    # Converte data para string se ela existir
    dt_aq = kwargs.get('data_aquisicao')
    if hasattr(dt_aq, 'isoformat'):
        dt_aq = dt_aq.isoformat()

    payload = {'nome': nome, 'quantidade_total': int(quantidade_total)}
    if dt_aq: payload['data_aquisicao'] = dt_aq
    
    for k in ['descricao', 'cidade', 'uf', 'endereco', 'valor_compra']:
        if k in kwargs and kwargs[k] is not None: 
            payload[k] = kwargs[k]
            
    if 'campos_categoria' in kwargs: payload['dados_categoria'] = kwargs['campos_categoria']
    
    sb.table('itens').update(payload).eq('id', int(item_id)).execute()
    
    slug = _slug_categoria(categoria or buscar_item_por_id(item_id).categoria)
    if slug and slug != 'itens' and 'campos_categoria' in kwargs:
        p_spec = {'item_id': int(item_id)}
        for label, valor in kwargs['campos_categoria'].items(): p_spec[_slugify_label(label)] = valor
        try: sb.table(slug).upsert(p_spec, on_conflict='item_id').execute()
        except: pass
        
    return buscar_item_por_id(item_id)

def listar_itens():
    sb = get_supabase(); r = sb.table('itens').select('*').execute()
    itens = []
    for row in (r.data or []):
        iid = row['id']; slug = _slug_categoria(row['categoria']); d_spec = {}
        if slug and slug != 'itens':
            try:
                r_s = sb.table(slug).select('*').eq('item_id', iid).execute()
                if r_s.data: d_spec = {_labelify_column(k): v for k, v in r_s.data[0].items() if k not in ['id', 'item_id']}
            except: pass
        itens.append(_row_to_item(row, dados_categoria={**row.get('dados_categoria', {}), **d_spec}))
    return itens

def buscar_item_por_id(item_id):
    sb = get_supabase(); r = sb.table('itens').select('*').eq('id', int(item_id)).execute()
    if not r.data: return None
    row = r.data[0]; slug = _slug_categoria(row['categoria']); d_spec = {}
    if slug and slug != 'itens':
        try:
            r_s = sb.table(slug).select('*').eq('item_id', int(item_id)).execute()
            if r_s.data: d_spec = {_labelify_column(k): v for k, v in r_s.data[0].items() if k not in ['id', 'item_id']}
        except: pass
    return _row_to_item(row, dados_categoria={**row.get('dados_categoria', {}), **d_spec})

def deletar_item(item_id):
    sb = get_supabase(); item = buscar_item_por_id(item_id)
    if item:
        slug = _slug_categoria(item.categoria)
        if slug: sb.table(slug).delete().eq('item_id', int(item_id)).execute()
        sb.table('pecas_carros').delete().or_(f"carro_id.eq.{item_id},peca_id.eq.{item_id}").execute()
    r = sb.table('itens').delete().eq('id', int(item_id)).execute()
    return r.data is not None

# --- CRUD DE COMPROMISSOS (ALUGUÉIS) ---

def criar_compromisso(item_id, quantidade, data_inicio, data_fim, **kwargs):
    sb = get_supabase()
    payload = {
        'item_id': int(item_id), 'quantidade': int(quantidade),
        'data_inicio': _date_parse(data_inicio).isoformat(),
        'data_fim': _date_parse(data_fim).isoformat(),
        'descricao': kwargs.get('descricao', ''), 'cidade': kwargs.get('cidade', ''),
        'uf': (kwargs.get('uf', ''))[:2].upper(), 'endereco': kwargs.get('endereco', ''),
        'contratante': kwargs.get('contratante', '')
    }
    ins = sb.table('compromissos').insert(payload).execute()
    if ins.data:
        registrar_movimentacao(item_id, -quantidade, 'ALUGUEL_SAIDA', ref_id=ins.data[0]['id'])
        return _row_to_compromisso(ins.data[0])
    raise Exception("Erro ao criar compromisso")

def listar_compromissos():
    sb = get_supabase()
    r = sb.table('compromissos').select('*').order('data_inicio').execute()
    return [_row_to_compromisso(row) for row in (r.data or [])]

def atualizar_compromisso_master(compromisso_id, dados_header, lista_itens=None):
    """
    Atualiza um contrato master e sincroniza sua lista de itens.
    Protegido contra erros de 'dict object has no attribute'.
    """
    sb = get_supabase()
    cid = int(compromisso_id)
    
    # 1. Buscar datas atuais no banco para garantir a validação caso não venham no header
    r_atual = sb.table('compromissos').select('data_inicio, data_fim').eq('id', cid).single().execute()
    if not r_atual.data:
        raise Exception("Contrato não encontrado para atualização.")
    
    # Resolvemos as datas usando .get() - se não vier no header, mantém a do banco
    d_inicio = dados_header.get('data_inicio') or r_atual.data['data_inicio']
    d_fim = dados_header.get('data_fim') or r_atual.data['data_fim']

    # 2. Validação de Estoque em Loop
    # Se lista_itens for None, validamos os itens que já estão no contrato contra as novas datas
    itens_para_validar = lista_itens
    if itens_para_validar is None:
        r_itens = sb.table('compromisso_itens').select('item_id, quantidade').eq('compromisso_id', cid).execute()
        itens_para_validar = r_itens.data or []

    for item in itens_para_validar:
        # Passamos excluir_compromisso_id para o motor ignorar a reserva atual deste contrato
        disp = verificar_disponibilidade_periodo(
            item_id=item['item_id'],
            data_inicio=d_inicio,
            data_fim=d_fim,
            excluir_compromisso_id=cid 
        )
        
        # item['quantidade'] ou item.get('quantidade') dependendo da origem
        qtd_solicitada = item.get('quantidade') if isinstance(item, dict) else item.quantidade
        
        if disp['disponivel_minimo'] < qtd_solicitada:
            nome = disp['item'].nome if hasattr(disp['item'], 'nome') else f"Item ID {item['item_id']}"
            raise Exception(f"Conflito de estoque para '{nome}' no novo período/quantidade.")

    # 3. Atualizar o Cabeçalho (Tabela compromissos)
    payload_h = dados_header.copy()
    
    # Conversão de datas para string ISO
    for f in ['data_inicio', 'data_fim']:
        if f in payload_h and payload_h[f]:
            val = payload_h[f]
            payload_h[f] = val.isoformat() if hasattr(val, 'isoformat') else str(val)

    if payload_h:
        sb.table('compromissos').update(payload_h).eq('id', cid).execute()

    # 4. Sincronizar Itens (Delete & Re-insert)
    if lista_itens is not None:
        # Limpa as associações antigas
        sb.table('compromisso_itens').delete().eq('compromisso_id', cid).execute()
        
        # Insere a nova configuração
        if lista_itens:
            payload_i = [
                {
                    "compromisso_id": cid,
                    "item_id": i['item_id'],
                    "quantidade": i['quantidade']
                } for i in lista_itens
            ]
            sb.table('compromisso_itens').insert(payload_i).execute()

    res_final = buscar_compromisso_por_id(cid)
    
    patch_data = {
        "item_id": None,   # Valor default para o tradutor não explodir
        "quantidade": 0,   # Valor default
        **res_final        # Sobrescreve com os dados reais (incluindo a lista de itens)
    }

    # Transforma em objeto com os atributos esperados
    from types import SimpleNamespace
    return SimpleNamespace(**patch_data)

def buscar_compromisso_por_id(cid):
    sb = get_supabase()
    # Buscamos o compromisso e trazemos os itens vinculados
    r = sb.table('compromissos').select('*, compromisso_itens(*, itens(*))').eq('id', cid).single().execute()
    return r.data if r.data else None

def atualizar_compromisso(compromisso_id, data_header, lista_itens=None):
    sb = get_supabase()
    
    # 1. Validação de Disponibilidade (se a lista de itens ou as datas mudaram)
    if lista_itens is not None or 'data_inicio' in data_header or 'data_fim' in data_header:
        # Precisamos buscar os itens atuais se a lista_itens for None para validar as novas datas
        itens_para_validar = lista_itens
        if itens_para_validar is None:
            r_atual = sb.table('compromisso_itens').select('item_id, quantidade').eq('compromisso_id', compromisso_id).execute()
            itens_para_validar = r_atual.data

        # Datas para validação
        d_inicio = data_header.get('data_inicio')
        d_fim = data_header.get('data_fim')
        
        # Se não mudou a data no header, buscamos a data atual do banco
        if not d_inicio or not d_fim:
            comp_atual = sb.table('compromissos').select('data_inicio, data_fim').eq('id', compromisso_id).single().execute()
            d_inicio = d_inicio or comp_atual.data['data_inicio']
            d_fim = d_fim or comp_atual.data['data_fim']

        # Loop de validação para cada item
        for item in itens_para_validar:
            # Importante: passar o compromisso_id para EXCLUIR este contrato da conta de estoque
            disp = verificar_disponibilidade_periodo(
                item_id=item['item_id'],
                data_inicio=d_inicio,
                data_fim=d_fim,
                excluir_compromisso_id=compromisso_id 
            )
            if disp['disponivel_minimo'] < item['quantidade']:
                raise Exception(f"Estoque insuficiente para o item ID {item['item_id']}. Disponível: {disp['disponivel_minimo']}")

    # 2. Atualizar o cabeçalho (compromissos)
    if data_header:
        # Converter datas para string se existirem
        for field in ['data_inicio', 'data_fim']:
            if field in data_header and hasattr(data_header[field], 'isoformat'):
                data_header[field] = data_header[field].isoformat()
        
        sb.table('compromissos').update(data_header).eq('id', compromisso_id).execute()

    # 3. Sincronizar Itens
    if lista_itens is not None:
        # Remove os antigos
        sb.table('compromisso_itens').delete().eq('compromisso_id', compromisso_id).execute()
        
        # Insere os novos
        if lista_itens:
            payload_itens = [
                {
                    "compromisso_id": compromisso_id,
                    "item_id": i['item_id'],
                    "quantidade": i['quantidade']
                } for i in lista_itens
            ]
            sb.table('compromisso_itens').insert(payload_itens).execute()

    return buscar_compromisso_por_id(compromisso_id)
def criar_compromisso_master(dados_header, lista_itens):
    """
    Cria um contrato master com múltiplos itens. 
    Blindado contra erros de atributo e dicionário.
    """
    sb = get_supabase()
    
    # Acesso seguro via .get() para evitar o erro 'dict object has no attribute'
    d_inicio = dados_header.get('data_inicio')
    d_fim = dados_header.get('data_fim')

    # 1. Validação de Estoque antes de qualquer inserção
    for item in lista_itens:
        disp = verificar_disponibilidade_periodo(
            item_id=item['item_id'],
            data_inicio=d_inicio,
            data_fim=d_fim
        )
        
        # disp['disponivel_minimo'] vem do motor de cálculo que já ajustamos
        if disp['disponivel_minimo'] < item.get('quantidade', 0):
            nome_item = disp['item'].nome if hasattr(disp['item'], 'nome') else "Item"
            raise Exception(f"Estoque insuficiente para {nome_item}. Disponível: {disp['disponivel_minimo']}")

    # 2. Preparar Payload do Cabeçalho
    # Fazemos uma cópia para não alterar o dicionário original
    payload = dados_header.copy()
    
    # Garantimos que as datas sejam strings ISO para o Supabase
    for campo in ['data_inicio', 'data_fim']:
        if campo in payload and payload[campo]:
            val = payload[campo]
            payload[campo] = val.isoformat() if hasattr(val, 'isoformat') else str(val)

    # 3. Inserir o Contrato (Compromisso Master)
    # Se o erro de constraint NULL persistir, certifique-se de que rodou o SQL: 
    # ALTER TABLE compromissos ALTER COLUMN item_id DROP NOT NULL;
    res_h = sb.table('compromissos').insert(payload).execute()
    if not res_h.data:
        raise Exception("Erro ao criar cabeçalho do contrato")
    
    contrato_id = res_h.data[0]['id']

    # 4. Inserir Itens do Contrato
    payload_itens = [
        {
            "compromisso_id": contrato_id,
            "item_id": i['item_id'],
            "quantidade": i['quantidade']
        } for i in lista_itens
    ]
    
    sb.table('compromisso_itens').insert(payload_itens).execute()
    
    res_final = buscar_compromisso_por_id(contrato_id)
    
    patch_data = {
        "item_id": None,   # Valor default para o tradutor não explodir
        "quantidade": 0,   # Valor default
        **res_final        # Sobrescreve com os dados reais (incluindo a lista de itens)
    }

    # Transforma em objeto com os atributos esperados
    from types import SimpleNamespace
    return SimpleNamespace(**patch_data)

def deletar_compromisso(compromisso_id):
    sb = get_supabase()
    # O CASCADE no banco cuida dos itens em compromisso_itens
    res = sb.table('compromissos').delete().eq('id', compromisso_id).execute()
    return res.data

# --- CRUD DE PEÇAS EM CARROS (ASSOCIAÇÕES) ---

def criar_peca_carro(peca_id, carro_id, quantidade=1, data_instalacao=None, observacoes=None):
    sb = get_supabase()
    peca = buscar_item_por_id(peca_id)
    custo = peca.valor_compra if peca else 0
    
    # --- FIX DATA SERIALIZATION ---
    dt_fix = data_instalacao
    if hasattr(dt_fix, 'isoformat'):
        dt_fix = dt_fix.isoformat()
    elif not dt_fix:
        dt_fix = date.today().isoformat()

    payload = {
        'peca_id': int(peca_id), 
        'carro_id': int(carro_id), 
        'quantidade': int(quantidade),
        'custo_na_data': float(custo), 
        'data_instalacao': dt_fix,
        'observacoes': observacoes or ''
    }
    
    ins = sb.table('pecas_carros').insert(payload).execute()
    if not ins.data: raise Exception("Erro ao inserir associação de peça")
    
    registrar_movimentacao(peca_id, -quantidade, 'INSTALACAO', ref_id=carro_id)
    return ins.data[0] # Retorna o dicionário criado

def listar_pecas_carros(carro_id=None, peca_id=None):
    sb = get_supabase(); q = sb.table('pecas_carros').select('*')
    if carro_id: q = q.eq('carro_id', int(carro_id))
    if peca_id: q = q.eq('peca_id', int(peca_id))
    r = q.execute()
    class Row:
        def __init__(self, d):
            self.id=d['id']; self.peca_id=d['peca_id']; self.carro_id=d['carro_id']
            self.quantidade=d['quantidade']; self.data_instalacao=_date_parse(d['data_instalacao'])
            self.observacoes=d.get('observacoes','')
    return [Row(x) for x in (r.data or [])]

def buscar_peca_carro_por_id(associacao_id):
    sb = get_supabase()
    r = sb.table('pecas_carros').select('*').eq('id', int(associacao_id)).execute()
    if not r.data: return None
    row = r.data[0]
    class Row:
        def __init__(self):
            self.id=row['id']; self.peca_id=row['peca_id']; self.carro_id=row['carro_id']
            self.quantidade=row['quantidade']; self.data_instalacao=_date_parse(row['data_instalacao'])
            self.observacoes=row.get('observacoes','')
    return Row()

def atualizar_peca_carro(associacao_id, quantidade=None, data_instalacao=None, observacoes=None):
    sb = get_supabase()
    
    r_antiga = sb.table('pecas_carros').select('*').eq('id', int(associacao_id)).execute()
    if not r_antiga.data: return None
    dados_antigos = r_antiga.data[0]

    payload = {}
    if quantidade is not None: payload['quantidade'] = int(quantidade)
    if observacoes is not None: payload['observacoes'] = observacoes
    
    if data_instalacao:
        dt_fix = data_instalacao
        # CORREÇÃO AQUI: 'data_instalacao' e não 'data_installation'
        payload['data_instalacao'] = dt_fix.isoformat() if hasattr(dt_fix, 'isoformat') else str(dt_fix)
    
    if quantidade is not None:
        diff = dados_antigos['quantidade'] - int(quantidade)
        if diff != 0:
            registrar_movimentacao(dados_antigos['peca_id'], diff, 'AJUSTE_INSTALACAO', ref_id=dados_antigos['carro_id'])
    
    r = sb.table('pecas_carros').update(payload).eq('id', int(associacao_id)).execute()
    return r.data[0] if r.data else None

def deletar_peca_carro(associacao_id):
    sb = get_supabase()
    r_assoc = sb.table('pecas_carros').select('*').eq('id', associacao_id).single().execute()
    if r_assoc.data:
        # Quando removemos a peça do carro, ela volta para o estoque disponível (+)
        registrar_movimentacao(r_assoc.data['peca_id'], r_assoc.data['quantidade'], 'REMOCAO_PECA', ref_id=r_assoc.data['carro_id'])
    r = sb.table('pecas_carros').delete().eq('id', int(associacao_id)).execute()
    return len(r.data) > 0

# --- MOTOR DE DISPONIBILIDADE (TOTAL - ALUGADO - INSTALADO) ---

def verificar_disponibilidade(item_id, data_consulta, filtro_loc=None):
    item = buscar_item_por_id(item_id)
    if not item: return None
    dt = _date_parse(data_consulta)
    sb = get_supabase()
    
    # 1. Alugado na data
    # Mudança crucial: selecionamos '*' para ter todos os campos necessários para o objeto
    r_c = sb.table('compromissos').select('*').eq('item_id', item_id).lte('data_inicio', dt.isoformat()).gte('data_fim', dt.isoformat()).execute()
    
    # CONVERSÃO AQUI: Transformamos a lista de dicts em lista de Objetos Compromisso
    comps_raw = r_c.data or []
    comps_objetos = [_row_to_compromisso(row) for row in comps_raw]

    # Aplicamos o filtro de localização nos objetos (usando .cidade e .uf em vez de chaves)
    if filtro_loc:
        p = filtro_loc.split(" - ")
        if len(p) == 2:
            comps_objetos = [c for c in comps_objetos if c.cidade == p[0] and c.uf == p[1].upper()]
    
    qtd_alugada = sum(c.quantidade for c in comps_objetos)

    # 2. Instalado em carros
    r_i = sb.table('pecas_carros').select('quantidade').eq('peca_id', item_id).lte('data_instalacao', dt.isoformat()).execute()
    qtd_inst = sum(p['quantidade'] for p in (r_i.data or []))
    
    disponivel = item.quantidade_total - qtd_alugada - qtd_inst
    
    return {
        'item': item, 
        'quantidade_total': item.quantidade_total,
        'quantidade_comprometida': qtd_alugada, 
        'quantidade_instalada': qtd_inst,
        'quantidade_disponivel': max(0, disponivel), 
        # Agora retornamos objetos, o main.py vai ficar feliz!
        'compromissos_ativos': comps_objetos 
    }

def verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=None, **kwargs):
    item = buscar_item_por_id(item_id)
    if not item: return None
    
    d_ini = _date_parse(data_inicio)
    d_fim = _date_parse(data_fim)
    sb = get_supabase()
    
    # CORREÇÃO: Forçamos a query a olhar APENAS para a tabela de relação.
    # Se o erro 500 persistir, verifique se a VIEW 'view_saude_ativo' foi realmente recriada.
    r = sb.table('compromisso_itens') \
      .select('quantidade, compromissos(id, data_inicio, data_fim)') \
      .eq('item_id', item_id) \
      .execute()
    
    dados_relacionamento = r.data or []
    
    todos_comps = []
    for rel in dados_relacionamento:
        raw_comp = rel.get('compromissos')
        if not raw_comp: continue
        
        # Criamos um objeto "on-the-fly" para o motor de data funcionar
        # sem depender de mappers antigos que podem estar buscando colunas deletadas
        from types import SimpleNamespace
        comp_obj = SimpleNamespace(
            id=raw_comp['id'],
            data_inicio=_date_parse(raw_comp['data_inicio']),
            data_fim=_date_parse(raw_comp['data_fim']),
            quantidade=int(rel.get('quantidade', 0))
        )
        todos_comps.append(comp_obj)
    
    # Filtra apenas os que batem com o período
    comps = [
        c for c in todos_comps 
        if c.data_inicio <= d_fim and c.data_fim >= d_ini
    ]
    
    # Exclui o contrato atual em caso de edição
    if excluir_compromisso_id:
        comps = [c for c in comps if c.id != int(excluir_compromisso_id)]
    
    # 2. Busca peças instaladas (mantendo sua lógica original)
    pecas_r = sb.table('pecas_carros').select('quantidade, data_instalacao').eq('peca_id', item_id).execute()
    pecas_data = pecas_r.data or []
    
    max_occ = 0
    total_alugado_no_pico = 0  # <--- NOVA VARIÁVEL
    total_instalado_no_pico = 0 # <--- NOVA VARIÁVEL
    curr = d_ini
    
    # 3. Motor de estoque dia a dia (mantendo sua lógica original)
    while curr <= d_fim:
        # Soma o que está alugado (agora pegando a quantidade correta do Master)
        dia_alugado = sum(c.quantidade for c in comps if c.data_inicio <= curr <= c.data_fim)
        
        # Soma o que está instalado em carros
        dia_instalado = sum(
            p['quantidade'] for p in pecas_data 
            if p['data_instalacao'] is None or _date_parse(p['data_instalacao']) <= curr
        )
        
        ocupacao_hoje = dia_alugado + dia_instalado
        if ocupacao_hoje >= max_occ:
            max_occ = ocupacao_hoje
            total_alugado_no_pico = dia_alugado
            total_instalado_no_pico = dia_instalado
        curr += timedelta(days=1)
    
    # Retorno idêntico ao original para não quebrar o Frontend
    return {
        'item': item, 
        'quantidade_total': item.quantidade_total, 
        'max_comprometido': max_occ, 
        'qtd_alugada': total_alugado_no_pico,   # <--- RETORNO ADICIONAL
        'qtd_instalada': total_instalado_no_pico, # <--- RETORNO ADICIONAL
        'disponivel_minimo': max(0, item.quantidade_total - max_occ)
    }
def verificar_disponibilidade_todos_itens(data_consulta, filtro_localizacao=None):
    """Varre todos os itens calculando disponibilidade na data via Master Contract"""
    sb = get_supabase()
    
    # 1. Busca todos os itens (Ativos)
    query = sb.table('itens').select('*')
    if filtro_localizacao and filtro_localizacao != 'Todas as Localizações':
        cidade, uf = filtro_localizacao.split(' - ')
        query = query.eq('cidade', cidade).eq('uf', uf)
    
    res_itens = query.execute()
    lista_itens = res_itens.data or []
    
    resultados = []
    for item in lista_itens:
        # Reutilizamos a lógica MASTER que já está corrigida
        # Ela olha para compromisso_itens e não para a coluna deletada
        status = verificar_disponibilidade_periodo(
            item_id=item['id'],
            data_inicio=data_consulta,
            data_fim=data_consulta
        )
        
        resultados.append({
            'item': SimpleNamespace(**item), # Objeto para o tradutor
            'quantidade_total': status['quantidade_total'],
            'quantidade_comprometida': status['max_comprometido'],
            'quantidade_disponivel': status['disponivel_minimo'],
        })
        
    return resultados


# ---------- Financiamentos ----------
def criar_financiamento_item(financiamento_id, item_id, valor_proporcional=0.0):
    sb = get_supabase()
    sb.table('financiamentos_itens').insert({
        'financiamento_id': int(financiamento_id),
        'item_id': int(item_id),
        'valor_proporcional': float(valor_proporcional)
    }).execute()

def listar_itens_financiamento(financiamento_id):
    sb = get_supabase()
    r = sb.table('financiamentos_itens').select('*').eq('financiamento_id', int(financiamento_id)).execute()
    return [{'item_id': x['item_id'], 'valor_proporcional': float(x.get('valor_proporcional') or 0)} for x in (r.data or [])]

def criar_financiamento(item_id=None, valor_total=None, numero_parcelas=None, taxa_juros=None, data_inicio=None, valor_entrada=0.0, instituicao_financeira=None, observacoes=None, parcelas_customizadas=None, itens_ids=None, codigo_contrato=None):
    if item_id and not itens_ids:
        itens_ids = [item_id]
    if not itens_ids:
        raise ValueError("É necessário fornecer pelo menos um item (itens_ids)")
    valor_total = round(float(valor_total), 2)
    valor_entrada = round(float(valor_entrada), 2)
    taxa_juros = round(float(taxa_juros), 6)
    if taxa_juros >= 100:
        taxa_juros = taxa_juros / 10000
    elif taxa_juros >= 1:
        taxa_juros = taxa_juros / 100
    valor_financiado = round(valor_total - valor_entrada, 2)
    if valor_financiado <= 0:
        raise ValueError("Valor financiado deve ser maior que zero")
    data_inicio = _date_parse(data_inicio)
    if not parcelas_customizadas and taxa_juros > 0:
        i, n = taxa_juros, numero_parcelas
        valor_parcela = valor_financiado * (i * ((1 + i) ** n)) / (((1 + i) ** n) - 1)
    else:
        valor_parcela = valor_financiado / numero_parcelas if not parcelas_customizadas else 0
    valor_parcela = round(valor_parcela, 2)
    sb = get_supabase()
    payload = {
        'codigo_contrato': codigo_contrato or '',
        'item_id': int(itens_ids[0]) if itens_ids else None,
        'valor_total': valor_total,
        'valor_entrada': valor_entrada,
        'numero_parcelas': len(parcelas_customizadas) if parcelas_customizadas else numero_parcelas,
        'valor_parcela': valor_parcela,
        'taxa_juros': taxa_juros,
        'data_inicio': data_inicio.isoformat(),
        'status': 'Ativo',
        'instituicao_financeira': instituicao_financeira or '',
        'observacoes': observacoes or ''
    }
    ins = sb.table('financiamentos').insert(payload).execute()
    if not ins.data or len(ins.data) == 0:
        raise Exception("Erro ao criar financiamento")
    fin_id = ins.data[0]['id']
    for iid in itens_ids:
        criar_financiamento_item(fin_id, iid, 0.0)
    if parcelas_customizadas:
        for idx, pc in enumerate(parcelas_customizadas):
            dv = pc.get('data_vencimento')
            if isinstance(dv, str):
                dv = _date_parse(dv)
            sb.table('parcelas_financiamento').insert({
                'financiamento_id': fin_id,
                'numero_parcela': pc.get('numero', idx + 1),
                'valor_original': round(float(pc.get('valor', 0)), 2),
                'valor_pago': 0,
                'data_vencimento': dv.isoformat() if hasattr(dv, 'isoformat') else str(dv),
                'status': 'Pendente'
            }).execute()
    else:
        for i in range(1, numero_parcelas + 1):
            if i == 1:
                data_venc = data_inicio
            else:
                ano, mes = data_inicio.year, data_inicio.month + (i - 1)
                while mes > 12:
                    mes -= 12
                    ano += 1
                try:
                    data_venc = date(ano, mes, data_inicio.day)
                except ValueError:
                    data_venc = date(ano, mes, calendar.monthrange(ano, mes)[1])
            sb.table('parcelas_financiamento').insert({
                'financiamento_id': fin_id,
                'numero_parcela': i,
                'valor_original': valor_parcela,
                'valor_pago': 0,
                'data_vencimento': data_venc.isoformat(),
                'status': 'Pendente'
            }).execute()
    auditoria.registrar_auditoria('CREATE', 'Financiamentos', fin_id, valores_novos={'itens_ids': itens_ids})
    return buscar_financiamento_por_id(fin_id)

def listar_financiamentos(status=None, item_id=None):
    sb = get_supabase()
    q = sb.table('financiamentos').select('*').order('id', desc=True)
    if status:
        q = q.eq('status', status)
    if item_id:
        fi = sb.table('financiamentos_itens').select('financiamento_id').eq('item_id', int(item_id)).execute()
        fin_ids = [x['financiamento_id'] for x in (fi.data or [])]
        if not fin_ids:
            return []
        q = q.in_('id', fin_ids)
    r = q.execute()
    return [_row_to_financiamento(row) for row in (r.data or [])]

def _row_to_financiamento(row, itens_list=None):
    class Financiamento:
        def __init__(self):
            self.id = row.get('id')
            self.codigo_contrato = row.get('codigo_contrato') or ''
            self.item_id = row.get('item_id')
            self.valor_total = round(float(row.get('valor_total') or 0), 2)
            self.valor_entrada = round(float(row.get('valor_entrada') or 0), 2)
            self.numero_parcelas = row.get('numero_parcelas') or 0
            self.valor_parcela = round(float(row.get('valor_parcela') or 0), 2)
            self.taxa_juros = round(float(row.get('taxa_juros') or 0), 6)
            self.data_inicio = _date_parse(row.get('data_inicio'))
            self.status = row.get('status') or 'Ativo'
            self.instituicao_financeira = row.get('instituicao_financeira') or ''
            self.observacoes = row.get('observacoes') or ''
            self._itens_list = itens_list
            self.valor_presente = 0.0
        @property
        def itens(self):
            if self._itens_list is None:
                self._itens_list = _financiamento_itens_list(self.id)
            return self._itens_list
    return Financiamento()

def _financiamento_itens_list(financiamento_id):
    fi = listar_itens_financiamento(financiamento_id)
    todos = listar_itens()
    out = []
    for x in fi:
        item = next((i for i in todos if i.id == x['item_id']), None)
        if item:
            out.append({'id': item.id, 'nome': item.nome, 'valor': x['valor_proporcional']})
    return out

def buscar_financiamento_por_id(financiamento_id):
    sb = get_supabase()
    r = sb.table('financiamentos').select('*').eq('id', int(financiamento_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_financiamento(r.data[0], itens_list=_financiamento_itens_list(int(financiamento_id)))

def atualizar_financiamento(financiamento_id, valor_total=None, taxa_juros=None, status=None, instituicao_financeira=None, observacoes=None):
    sb = get_supabase()
    payload = {}
    if valor_total is not None:
        payload['valor_total'] = round(float(valor_total), 2)
    if taxa_juros is not None:
        payload['taxa_juros'] = round(float(taxa_juros), 6)
    if status is not None:
        payload['status'] = status
    if instituicao_financeira is not None:
        payload['instituicao_financeira'] = instituicao_financeira
    if observacoes is not None:
        payload['observacoes'] = observacoes
    if payload:
        sb.table('financiamentos').update(payload).eq('id', int(financiamento_id)).execute()
    return buscar_financiamento_por_id(financiamento_id)

def deletar_financiamento(financiamento_id):
    sb = get_supabase()
    sb.table('parcelas_financiamento').delete().eq('financiamento_id', int(financiamento_id)).execute()
    sb.table('financiamentos_itens').delete().eq('financiamento_id', int(financiamento_id)).execute()
    r = sb.table('financiamentos').delete().eq('id', int(financiamento_id)).execute()
    return r.data is not None and len(r.data) > 0

def listar_parcelas_financiamento(financiamento_id=None, status=None):
    sb = get_supabase()
    q = sb.table('parcelas_financiamento').select('*')
    if financiamento_id is not None:
        q = q.eq('financiamento_id', int(financiamento_id))
    if status:
        q = q.eq('status', status)
    r = q.order('numero_parcela').execute()
    class Parcela:
        def __init__(self, row):
            self.id = row.get('id')
            self.financiamento_id = row.get('financiamento_id')
            self.numero_parcela = row.get('numero_parcela')
            self.valor_original = round(float(row.get('valor_original') or 0), 2)
            self.valor_pago = round(float(row.get('valor_pago') or 0), 2)
            self.data_vencimento = _date_parse(row.get('data_vencimento'))
            self.data_pagamento = _date_parse(row.get('data_pagamento'))
            self.status = row.get('status') or 'Pendente'
            self.link_boleto = row.get('link_boleto')
            self.link_comprovante = row.get('link_comprovante')
            self.juros = 0.0
            self.multa = 0.0
            self.desconto = 0.0
    return [Parcela(x) for x in (r.data or [])]

def atualizar_parcela_financiamento(parcela_id, status=None, link_boleto=None, link_comprovante=None, valor_original=None, data_vencimento=None):
    sb = get_supabase()
    payload = {}
    if status is not None:
        payload['status'] = status
    if link_boleto is not None:
        payload['link_boleto'] = link_boleto
    if link_comprovante is not None:
        payload['link_comprovante'] = link_comprovante
    if valor_original is not None:
        payload['valor_original'] = round(float(valor_original), 2)
    if data_vencimento is not None:
        payload['data_vencimento'] = _date_parse(data_vencimento).isoformat()
    if payload:
        sb.table('parcelas_financiamento').update(payload).eq('id', int(parcela_id)).execute()
    r = sb.table('parcelas_financiamento').select('*').eq('id', int(parcela_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    class Parcela:
        def __init__(self, row):
            self.id = row.get('id')
            self.financiamento_id = row.get('financiamento_id')
            self.numero_parcela = row.get('numero_parcela')
            self.valor_original = round(float(row.get('valor_original') or 0), 2)
            self.valor_pago = round(float(row.get('valor_pago') or 0), 2)
            self.data_vencimento = _date_parse(row.get('data_vencimento'))
            self.data_pagamento = _date_parse(row.get('data_pagamento'))
            self.status = row.get('status') or 'Pendente'
            self.link_boleto = row.get('link_boleto')
            self.link_comprovante = row.get('link_comprovante')
    return Parcela(r.data[0])

def pagar_parcela_financiamento(parcela_id, valor_pago, data_pagamento=None, juros=0.0, multa=0.0, desconto=0.0):
    if data_pagamento is None:
        data_pagamento = date.today()
    else:
        data_pagamento = _date_parse(data_pagamento)
    sb = get_supabase()
    r = sb.table('parcelas_financiamento').select('*').eq('id', int(parcela_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    valor_pago = round(float(valor_pago), 2)
    sb.table('parcelas_financiamento').update({
        'valor_pago': valor_pago,
        'data_pagamento': data_pagamento.isoformat(),
        'status': 'Paga'
    }).eq('id', int(parcela_id)).execute()
    r2 = sb.table('parcelas_financiamento').select('*').eq('id', int(parcela_id)).execute()
    if not r2.data or len(r2.data) == 0:
        return None
    row = r2.data[0]
    class Parcela:
        def __init__(self):
            self.id = row.get('id')
            self.financiamento_id = row.get('financiamento_id')
            self.numero_parcela = row.get('numero_parcela')
            self.valor_original = round(float(row.get('valor_original') or 0), 2)
            self.valor_pago = round(float(row.get('valor_pago') or 0), 2)
            self.data_vencimento = _date_parse(row.get('data_vencimento'))
            self.data_pagamento = _date_parse(row.get('data_pagamento'))
            self.status = row.get('status') or 'Paga'
            self.link_boleto = row.get('link_boleto')
            self.link_comprovante = row.get('link_comprovante')
    return Parcela()


# ---------- Contas a receber ----------
def criar_conta_receber(compromisso_id, descricao, valor, data_vencimento, forma_pagamento=None, observacoes=None):
    sb = get_supabase()
    r = sb.table('compromissos').select('id').eq('id', int(compromisso_id)).execute()
    if not r.data or len(r.data) == 0:
        raise ValueError(f"Compromisso {compromisso_id} não encontrado")
    data_vencimento = _date_parse(data_vencimento)
    status = 'Vencido' if data_vencimento < date.today() else 'Pendente'
    ins = sb.table('contas_receber').insert({
        'compromisso_id': int(compromisso_id),
        'descricao': descricao,
        'valor': round(float(valor), 2),
        'data_vencimento': data_vencimento.isoformat(),
        'status': status,
        'forma_pagamento': forma_pagamento or '',
        'observacoes': observacoes or ''
    }).execute()
    if not ins.data or len(ins.data) == 0:
        raise Exception("Erro ao criar conta a receber")
    return ins.data[0]

def listar_contas_receber(status=None, data_inicio=None, data_fim=None, compromisso_id=None):
    sb = get_supabase()
    q = sb.table('contas_receber').select('*')
    if status:
        q = q.eq('status', status)
    if compromisso_id is not None:
        q = q.eq('compromisso_id', int(compromisso_id))
    if data_inicio:
        q = q.gte('data_vencimento', _date_parse(data_inicio).isoformat())
    if data_fim:
        q = q.lte('data_vencimento', _date_parse(data_fim).isoformat())
    r = q.execute()
    hoje = date.today()
    out = []
    for row in (r.data or []):
        class ContaReceber:
            pass
        c = ContaReceber()
        c.id = row.get('id')
        c.compromisso_id = row.get('compromisso_id')
        c.descricao = row.get('descricao') or ''
        c.valor = float(row.get('valor') or 0)
        c.data_vencimento = _date_parse(row.get('data_vencimento'))
        c.data_pagamento = _date_parse(row.get('data_pagamento'))
        c.status = row.get('status') or 'Pendente'
        if c.data_pagamento:
            c.status = 'Pago'
        elif c.data_vencimento and c.data_vencimento < hoje:
            c.status = 'Vencido'
        c.forma_pagamento = row.get('forma_pagamento') or ''
        c.observacoes = row.get('observacoes') or ''
        out.append(c)
    return out

def _row_to_conta_receber(row):
    class ContaReceber:
        pass
    c = ContaReceber()
    c.id = row.get('id')
    c.compromisso_id = row.get('compromisso_id')
    c.descricao = row.get('descricao') or ''
    c.valor = float(row.get('valor') or 0)
    c.data_vencimento = _date_parse(row.get('data_vencimento'))
    c.data_pagamento = _date_parse(row.get('data_pagamento'))
    c.status = row.get('status') or 'Pendente'
    c.forma_pagamento = row.get('forma_pagamento') or ''
    c.observacoes = row.get('observacoes') or ''
    return c

def atualizar_conta_receber(conta_id, descricao=None, valor=None, data_vencimento=None, data_pagamento=None, status=None, forma_pagamento=None, observacoes=None):
    sb = get_supabase()
    payload = {}
    if descricao is not None:
        payload['descricao'] = descricao
    if valor is not None:
        payload['valor'] = round(float(valor), 2)
    if data_vencimento is not None:
        payload['data_vencimento'] = _date_parse(data_vencimento).isoformat()
    if data_pagamento is not None:
        payload['data_pagamento'] = _date_parse(data_pagamento).isoformat()
    if status is not None:
        payload['status'] = status
    if forma_pagamento is not None:
        payload['forma_pagamento'] = forma_pagamento
    if observacoes is not None:
        payload['observacoes'] = observacoes
    if payload:
        sb.table('contas_receber').update(payload).eq('id', int(conta_id)).execute()
    r = sb.table('contas_receber').select('*').eq('id', int(conta_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_conta_receber(r.data[0])

def deletar_conta_receber(conta_id):
    sb = get_supabase()
    r = sb.table('contas_receber').delete().eq('id', int(conta_id)).execute()
    return r.data is not None and len(r.data) > 0

def marcar_conta_receber_paga(conta_id, data_pagamento=None, forma_pagamento=None):
    if data_pagamento is None:
        data_pagamento = date.today()
    else:
        data_pagamento = _date_parse(data_pagamento)
    sb = get_supabase()
    payload = {'data_pagamento': data_pagamento.isoformat(), 'status': 'Pago'}
    if forma_pagamento is not None:
        payload['forma_pagamento'] = forma_pagamento
    sb.table('contas_receber').update(payload).eq('id', int(conta_id)).execute()
    r = sb.table('contas_receber').select('*').eq('id', int(conta_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_conta_receber(r.data[0])


# ---------- Contas a pagar ----------
def criar_conta_pagar(descricao, categoria, valor, data_vencimento, fornecedor=None, item_id=None, forma_pagamento=None, observacoes=None):
    sb = get_supabase()
    data_vencimento = _date_parse(data_vencimento)
    status = 'Vencido' if data_vencimento < date.today() else 'Pendente'
    payload = {
        'descricao': descricao,
        'categoria': categoria,
        'valor': round(float(valor), 2),
        'data_vencimento': data_vencimento.isoformat(),
        'status': status,
        'fornecedor': fornecedor or '',
        'forma_pagamento': forma_pagamento or '',
        'observacoes': observacoes or ''
    }
    if item_id is not None:
        payload['item_id'] = int(item_id)
    ins = sb.table('contas_pagar').insert(payload).execute()
    if not ins.data or len(ins.data) == 0:
        raise Exception("Erro ao criar conta a pagar")
    return _row_to_conta_pagar(ins.data[0])

def _row_to_conta_pagar(row):
    class ContaPagar:
        pass
    c = ContaPagar()
    c.id = row.get('id')
    c.descricao = row.get('descricao') or ''
    c.categoria = row.get('categoria') or ''
    c.valor = float(row.get('valor') or 0)
    c.data_vencimento = _date_parse(row.get('data_vencimento'))
    c.data_pagamento = _date_parse(row.get('data_pagamento'))
    c.status = row.get('status') or 'Pendente'
    c.fornecedor = row.get('fornecedor')
    c.item_id = row.get('item_id')
    c.forma_pagamento = row.get('forma_pagamento') or ''
    c.observacoes = row.get('observacoes') or ''
    return c

def listar_contas_pagar(status=None, data_inicio=None, data_fim=None, categoria=None):
    sb = get_supabase()
    q = sb.table('contas_pagar').select('*')
    if status:
        q = q.eq('status', status)
    if data_inicio:
        q = q.gte('data_vencimento', _date_parse(data_inicio).isoformat())
    if data_fim:
        q = q.lte('data_vencimento', _date_parse(data_fim).isoformat())
    if categoria:
        q = q.eq('categoria', categoria)
    r = q.execute()
    hoje = date.today()
    out = []
    for row in (r.data or []):
        class ContaPagar:
            pass
        c = ContaPagar()
        c.id = row.get('id')
        c.descricao = row.get('descricao') or ''
        c.categoria = row.get('categoria') or ''
        c.valor = float(row.get('valor') or 0)
        c.data_vencimento = _date_parse(row.get('data_vencimento'))
        c.data_pagamento = _date_parse(row.get('data_pagamento'))
        c.status = row.get('status') or 'Pendente'
        if c.data_pagamento:
            c.status = 'Pago'
        elif c.data_vencimento and c.data_vencimento < hoje:
            c.status = 'Vencido'
        c.fornecedor = row.get('fornecedor')
        c.item_id = row.get('item_id')
        c.forma_pagamento = row.get('forma_pagamento') or ''
        c.observacoes = row.get('observacoes') or ''
        out.append(c)
    return out

def atualizar_conta_pagar(conta_id, descricao=None, categoria=None, valor=None, data_vencimento=None, data_pagamento=None, status=None, fornecedor=None, item_id=None, forma_pagamento=None, observacoes=None):
    sb = get_supabase()
    payload = {}
    for k, v in [('descricao', descricao), ('categoria', categoria), ('fornecedor', fornecedor), ('forma_pagamento', forma_pagamento), ('observacoes', observacoes), ('status', status)]:
        if v is not None:
            payload[k] = v
    if valor is not None:
        payload['valor'] = round(float(valor), 2)
    if data_vencimento is not None:
        payload['data_vencimento'] = _date_parse(data_vencimento).isoformat()
    if data_pagamento is not None:
        payload['data_pagamento'] = _date_parse(data_pagamento).isoformat()
    if item_id is not None:
        payload['item_id'] = int(item_id)
    if payload:
        sb.table('contas_pagar').update(payload).eq('id', int(conta_id)).execute()
    r = sb.table('contas_pagar').select('*').eq('id', int(conta_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_conta_pagar(r.data[0])

def deletar_conta_pagar(conta_id):
    sb = get_supabase()
    r = sb.table('contas_pagar').delete().eq('id', int(conta_id)).execute()
    return r.data is not None and len(r.data) > 0

def obter_fluxo_caixa(data_inicio, data_fim):
    """Retorna fluxo de caixa por período (agrupado por mês)."""
    data_inicio = _date_parse(data_inicio)
    data_fim = _date_parse(data_fim)
    receitas = listar_contas_receber(data_inicio=data_inicio, data_fim=data_fim)
    despesas = listar_contas_pagar(data_inicio=data_inicio, data_fim=data_fim)
    fluxo = {}
    for conta in receitas:
        if conta.status == 'Pago' and conta.data_pagamento:
            mes = conta.data_pagamento.strftime('%Y-%m')
            if mes not in fluxo:
                fluxo[mes] = {'receitas': 0, 'despesas': 0}
            fluxo[mes]['receitas'] += conta.valor
    for conta in despesas:
        if conta.status == 'Pago' and conta.data_pagamento:
            mes = conta.data_pagamento.strftime('%Y-%m')
            if mes not in fluxo:
                fluxo[mes] = {'receitas': 0, 'despesas': 0}
            fluxo[mes]['despesas'] += conta.valor
    return [
        {'mes': mes, 'receitas': fluxo[mes]['receitas'], 'despesas': fluxo[mes]['despesas'],
         'saldo': fluxo[mes]['receitas'] - fluxo[mes]['despesas']}
        for mes in sorted(fluxo.keys())
    ]


def marcar_conta_pagar_paga(conta_id, data_pagamento=None, forma_pagamento=None):
    if data_pagamento is None:
        data_pagamento = date.today()
    else:
        data_pagamento = _date_parse(data_pagamento)
    sb = get_supabase()
    payload = {'data_pagamento': data_pagamento.isoformat(), 'status': 'Pago'}
    if forma_pagamento is not None:
        payload['forma_pagamento'] = forma_pagamento
    sb.table('contas_pagar').update(payload).eq('id', int(conta_id)).execute()
    r = sb.table('contas_pagar').select('*').eq('id', int(conta_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_conta_pagar(r.data[0])
