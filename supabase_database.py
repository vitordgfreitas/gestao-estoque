"""
Implementação do banco de dados usando Supabase (PostgreSQL).
Interface compatível com sheets_database e database para o backend FastAPI.
"""
import os
import re
from datetime import date, datetime, timedelta
import calendar
import validacoes
import auditoria

_supabase_client = None

def get_supabase():
    """Obtém o cliente Supabase (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL e SUPABASE_SERVICE_KEY (ou SUPABASE_KEY) devem estar configurados. "
                "Configure no .env ou nas variáveis de ambiente."
            )
        from supabase import create_client
        _supabase_client = create_client(url, key)
    return _supabase_client

# Compatibilidade: main.py pode chamar get_sheets() no Sheets; Supabase não tem "sheets"
def get_sheets():
    """Retorna info do projeto (compatibilidade com código que verifica conexão)."""
    sb = get_supabase()
    return {
        'spreadsheet_url': os.getenv('SUPABASE_URL', ''),
        'spreadsheet_id': 'supabase',
        'database': 'supabase'
    }

def _clear_cache():
    """Compatibilidade com sheets_database (cache não usado aqui)."""
    pass

def _date_parse(d):
    """Converte string ou date para date."""
    if d is None:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.strptime(d[:10], '%Y-%m-%d').date()
    return d

def registrar_movimentacao(item_id, quantidade, tipo, ref_id=None, desc=""):
    """
    Registra toda entrada e saída de estoque.
    tipo: 'COMPRA', 'ALUGUEL_SAIDA', 'ALUGUEL_RETORNO', 'INSTALACAO', 'MANUTENCAO'
    """
    sb = get_supabase()
    payload = {
        'item_id': int(item_id),
        'quantidade': int(quantidade),
        'tipo': tipo,
        'referencia_id': ref_id,
        'descricao': desc,
        'data_movimentacao': datetime.now().isoformat()
    }
    sb.table('movimentacoes_estoque').insert(payload).execute()

def obter_campos_categoria(categoria):
    sb = get_supabase()
    slug = _slug_categoria(categoria) # sua função de slug existente
    try:
        # Chama o RPC que criamos no SQL
        r = sb.rpc('get_table_columns', {'t_name': slug}).execute()
        colunas = [row['column_name'] for row in (r.data or [])]
        
        # Filtramos o que NÃO deve aparecer no formulário
        ignore = ['id', 'item_id', 'created_at', 'dados_categoria']
        # Retorna formatado: 'placa' -> 'Placa'
        return [c.replace('_', ' ').title() for c in colunas if c not in ignore]
    except:
        return []

def _row_to_item(record, carro=None, dados_categoria=None):
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
            
            # --- NOVOS CAMPOS FINANCEIROS ---
            self.valor_compra = float(record.get('valor_compra') or 0.0)
            self.data_aquisicao = _date_parse(record.get('data_aquisicao'))
            
            self.carro = carro
            self.dados_categoria = dados_categoria or (record.get('dados_categoria') or {})
    return Item()

def _row_to_carro(record):
    class Carro:
        def __init__(self):
            self.item_id = record.get('item_id')
            self.placa = record.get('placa') or ''
            self.marca = record.get('marca') or ''
            self.modelo = record.get('modelo') or ''
            self.ano = int(record.get('ano') or 0)
            self.chassi = record.get('chassi') or ''
            self.renavam = record.get('renavam') or ''
    return Carro()

# Mapeamento Container: nome do campo no frontend -> coluna na tabela container
_CAMPOS_CONTAINER_FRONT_TO_DB = {
    'Tara': 'tara', 'Carga Máxima': 'carga_maxima', 'Comprimento': 'comprimento',
    'Largura': 'largura', 'Altura': 'altura', 'Capacidade': 'capacidade', 'Cor': 'cor', 'Modelo': 'modelo'
}
_CAMPOS_CONTAINER_DB_TO_FRONT = {v: k for k, v in _CAMPOS_CONTAINER_FRONT_TO_DB.items()}

# ---------- Categorias ----------
def obter_categorias():
    sb = get_supabase()
    r = sb.table('categorias_itens').select('nome').order('nome').execute()
    return sorted([row['nome'] for row in (r.data or []) if row.get('nome')])

def obter_campos_categoria(categoria):
    """Retorna os campos obrigatórios/desejados para cada categoria (formulário)."""
    if categoria == 'Carros':
        return ['Placa', 'Marca', 'Modelo', 'Ano', 'Chassi', 'Renavam']
    if categoria == 'Container':
        return ['Tara', 'Carga Máxima', 'Comprimento', 'Largura', 'Altura', 'Capacidade', 'Cor', 'Modelo']
    if categoria == 'Pecas':
        return ['Marca']
    return []

def _slug_categoria(nome_categoria):
    """Gera nome de tabela válido para PostgreSQL: só letras minúsculas, números e underscore."""
    s = (nome_categoria or '').strip().lower()
    s = re.sub(r'[\s\-]+', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    return s or 'categoria'

def criar_categoria(nome_categoria):
    sb = get_supabase()
    existentes = obter_categorias()
    if nome_categoria.strip() in existentes:
        return None
    r = sb.table('categorias_itens').insert({
        'nome': nome_categoria.strip(),
        'data_criacao': date.today().isoformat()
    }).execute()
    if r.data and len(r.data) > 0:
        cat_id = r.data[0].get('id')
        # Criar tabela no SQL para essa categoria (id, item_id, dados_categoria)
        slug = _slug_categoria(nome_categoria)
        if slug:
            try:
                sb.rpc('criar_tabela_categoria', {'nome_tabela': slug}).execute()
            except Exception as e:
                # Categoria já foi criada; falha só na tabela (ex.: função não existe ainda)
                import traceback
                print(f"[Supabase] Aviso: não foi possível criar tabela da categoria '{nome_categoria}' ({slug}): {e}")
                traceback.print_exc()
        return cat_id
    return None

# ---------- Itens ----------
def _campos_categoria_para_carro(campos_categoria, placa, marca, modelo, ano):
    """Extrai placa, marca, modelo, ano, chassi, renavam de campos_categoria ou args."""
    c = campos_categoria or {}
    return (
        placa or c.get('Placa') or '',
        marca or c.get('Marca') or '',
        modelo or c.get('Modelo') or '',
        ano if ano is not None else (int(c['Ano']) if c.get('Ano') not in (None, '') else None),
        (c.get('Chassi') or '').strip(),
        (c.get('Renavam') or '').strip()
    )

def _campos_categoria_para_container(campos_categoria):
    """Converte campos_categoria (frontend) para dict de colunas da tabela container."""
    c = campos_categoria or {}
    out = {}
    for front, col in _CAMPOS_CONTAINER_FRONT_TO_DB.items():
        v = c.get(front)
        if v is not None and v != '':
            try:
                out[col] = float(v) if isinstance(v, str) and v.replace('.', '').replace(',', '').replace('-', '').isdigit() else v
            except (ValueError, TypeError):
                out[col] = v
    return out

def criar_item(nome, quantidade_total, categoria=None, valor_compra=0, data_aquisicao=None, **kwargs):
    sb = get_supabase()
    cat = categoria or 'Estrutura de Evento'
    campos_recebidos = kwargs.get('campos_categoria', {})

    # 1. Tabela Base
    payload_itens = {
        'nome': nome, 'quantidade_total': int(quantidade_total),
        'categoria': cat, 'valor_compra': float(valor_compra or 0),
        'data_aquisicao': data_aquisicao or date.today().isoformat(),
        'descricao': kwargs.get('descricao', ''),
        'cidade': kwargs.get('cidade', ''),
        'uf': (kwargs.get('uf', ''))[:2].upper(),
        'dados_categoria': campos_recebidos
    }
    ins = sb.table('itens').insert(payload_itens).execute()
    item_id = ins.data[0]['id']

    # 2. Log de Compra
    registrar_movimentacao(item_id, quantidade_total, 'COMPRA')

    # 3. Tabela Específica (Mapeamento Dinâmico)
    slug = _slug_categoria(cat)
    if slug and slug not in ('itens', 'compromissos'):
        payload_cat = {'item_id': item_id}
        for label, valor in campos_recebidos.items():
            payload_cat[_slugify_label(label)] = valor # 'Placa' -> 'placa'
        
        try:
            sb.table(slug).insert(payload_cat).execute()
        except Exception as e:
            print(f"Erro ao inserir em {slug}: {e}")

    return buscar_item_por_id(item_id)

def _container_row_to_dados_categoria(record):
    """Converte linha da tabela container em dict de dados_categoria (nomes do frontend)."""
    if not record:
        return {}
    out = {}
    for col, front in _CAMPOS_CONTAINER_DB_TO_FRONT.items():
        v = record.get(col)
        if v is not None:
            out[front] = v
    return out

def listar_itens():
    sb = get_supabase()
    r = sb.table('itens').select('*').execute()
    carros_r = sb.table('carros').select('*').execute()
    carros_by_item = {c['item_id']: c for c in (carros_r.data or [])}
    try:
        container_r = sb.table('container').select('*').execute()
        container_by_item = {c['item_id']: c for c in (container_r.data or [])}
    except Exception:
        container_by_item = {}
    itens = []
    for row in (r.data or []):
        carro = None
        dados_cat = dict(row.get('dados_categoria') or {})
        iid = row.get('id')
        if iid in carros_by_item:
            carro = _row_to_carro(carros_by_item[iid])
            c = carros_by_item[iid]
            dados_cat = {'Placa': c.get('placa'), 'Marca': c.get('marca'), 'Modelo': c.get('modelo'), 'Ano': c.get('ano'), 'Chassi': c.get('chassi'), 'Renavam': c.get('renavam'), **dados_cat}
        elif iid in container_by_item:
            dados_cat = {**_container_row_to_dados_categoria(container_by_item[iid]), **dados_cat}
        else:
            cat = row.get('categoria') or ''
            slug = _slug_categoria(cat)
            if slug and slug not in ('carros', 'container'):
                try:
                    slug_r = sb.table(slug).select('*').eq('item_id', iid).execute()
                    if slug_r.data and len(slug_r.data) > 0:
                        dc = (slug_r.data[0].get('dados_categoria') or {})
                        dados_cat = {**dc, **dados_cat}
                except Exception:
                    pass
        itens.append(_row_to_item(row, carro=carro, dados_categoria=dados_cat))
    return itens

def buscar_item_por_id(item_id):
    sb = get_supabase()
    r = sb.table('itens').select('*').eq('id', int(item_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    row = r.data[0]
    carro = None
    dados_cat = dict(row.get('dados_categoria') or {})
    cat = row.get('categoria') or ''
    if cat == 'Carros':
        cr = sb.table('carros').select('*').eq('item_id', int(item_id)).execute()
        if cr.data and len(cr.data) > 0:
            carro = _row_to_carro(cr.data[0])
            c = cr.data[0]
            dados_cat = {'Placa': c.get('placa'), 'Marca': c.get('marca'), 'Modelo': c.get('modelo'), 'Ano': c.get('ano'), 'Chassi': c.get('chassi'), 'Renavam': c.get('renavam'), **dados_cat}
    elif cat == 'Container':
        try:
            cont = sb.table('container').select('*').eq('item_id', int(item_id)).execute()
            if cont.data and len(cont.data) > 0:
                dados_cat = {**_container_row_to_dados_categoria(cont.data[0]), **dados_cat}
        except Exception:
            pass
    else:
        slug = _slug_categoria(cat)
        if slug and slug not in ('carros', 'container'):
            try:
                slug_r = sb.table(slug).select('*').eq('item_id', int(item_id)).execute()
                if slug_r.data and len(slug_r.data) > 0:
                    dc = slug_r.data[0].get('dados_categoria') or {}
                    dados_cat = {**dc, **dados_cat}
            except Exception:
                pass
    return _row_to_item(row, carro=carro, dados_categoria=dados_cat)

def _remover_item_da_tabela_categoria(sb, item_id, categoria):
    """Remove o item da tabela da categoria (carros, container ou slug), se existir."""
    if categoria == 'Carros':
        sb.table('carros').delete().eq('item_id', int(item_id)).execute()
    elif categoria == 'Container':
        try:
            sb.table('container').delete().eq('item_id', int(item_id)).execute()
        except Exception:
            pass
    else:
        slug = _slug_categoria(categoria)
        if slug and slug not in ('carros', 'container'):
            try:
                sb.table(slug).delete().eq('item_id', int(item_id)).execute()
            except Exception:
                pass

def atualizar_item(item_id, nome, quantidade_total, categoria=None, descricao=None, cidade=None, uf=None, endereco=None, placa=None, marca=None, modelo=None, ano=None, campos_categoria=None):
    item_atual = buscar_item_por_id(item_id)
    if not item_atual:
        raise ValueError(f"Item com ID {item_id} não encontrado")
    categoria_final = categoria if categoria is not None else (item_atual.categoria or '')
    cidade_final = cidade or item_atual.cidade or ''
    uf_final = uf or item_atual.uf or ''
    if categoria_final == 'Carros' and campos_categoria:
        placa, marca, modelo, ano, _, _ = _campos_categoria_para_carro(campos_categoria, placa, marca, modelo, ano)
    valido, msg = validacoes.validar_item_completo(
        nome=nome, categoria=categoria_final, cidade=cidade_final, uf=uf_final,
        quantidade_total=quantidade_total, placa=placa, marca=marca, modelo=modelo, ano=ano, campos_categoria=campos_categoria
    )
    if not valido:
        raise ValueError(msg)
    sb = get_supabase()
    dados_cat = campos_categoria if campos_categoria is not None else (item_atual.dados_categoria or {})

    # 1) Sempre atualizar a tabela itens (todos os campos)
    payload = {
        'nome': nome,
        'quantidade_total': int(quantidade_total),
        'descricao': descricao if descricao is not None else item_atual.descricao,
        'cidade': cidade_final,
        'uf': uf_final[:2].upper(),
        'endereco': endereco if endereco is not None else item_atual.endereco,
        'dados_categoria': dados_cat
    }
    if categoria is not None:
        payload['categoria'] = categoria_final
    sb.table('itens').update(payload).eq('id', int(item_id)).execute()

    # 2) Sincronizar tabela da categoria: remover da antiga (se mudou) e inserir/atualizar na atual
    cat_antiga = item_atual.categoria or ''
    if categoria is not None and cat_antiga != categoria_final:
        _remover_item_da_tabela_categoria(sb, item_id, cat_antiga)

    if categoria_final == 'Carros' and (placa and marca and modelo and ano is not None):
        _, _, _, _, chassi, renavam = _campos_categoria_para_carro(campos_categoria or {}, placa, marca, modelo, ano)
        carro_row = {
            'item_id': int(item_id), 'placa': placa.upper().strip(), 'marca': marca.strip(),
            'modelo': modelo.strip(), 'ano': int(ano),
            'chassi': (chassi or '')[:50] if chassi else None,
            'renavam': (renavam or '')[:20] if renavam else None
        }
        cr = sb.table('carros').select('id').eq('item_id', int(item_id)).execute()
        if cr.data and len(cr.data) > 0:
            sb.table('carros').update(carro_row).eq('item_id', int(item_id)).execute()
        else:
            sb.table('carros').insert(carro_row).execute()
    elif categoria_final == 'Container':
        row_data = _campos_categoria_para_container(dados_cat)
        try:
            cont = sb.table('container').select('id').eq('item_id', int(item_id)).execute()
            if cont.data and len(cont.data) > 0:
                sb.table('container').update(row_data).eq('item_id', int(item_id)).execute()
            else:
                sb.table('container').insert({'item_id': int(item_id), **row_data}).execute()
        except Exception as e:
            print(f"[Supabase] Aviso: atualizar container: {e}")
    else:
        slug = _slug_categoria(categoria_final)
        if slug and slug not in ('carros', 'container'):
            try:
                slug_r = sb.table(slug).select('id').eq('item_id', int(item_id)).execute()
                row_slug = {'item_id': int(item_id), 'dados_categoria': dados_cat}
                if slug_r.data and len(slug_r.data) > 0:
                    sb.table(slug).update(row_slug).eq('item_id', int(item_id)).execute()
                else:
                    sb.table(slug).insert(row_slug).execute()
            except Exception as e:
                print(f"[Supabase] Aviso: atualizar tabela categoria '{categoria_final}': {e}")

    auditoria.registrar_auditoria('UPDATE', 'Itens', item_id, valores_novos=payload)
    return buscar_item_por_id(item_id)

def deletar_item(item_id):
    """Remove o item da tabela itens e também da tabela da categoria (carros, container ou slug)."""
    sb = get_supabase()
    item = buscar_item_por_id(item_id)
    if item:
        # 1) Remover explicitamente da tabela da categoria
        categoria = item.categoria or ''
        _remover_item_da_tabela_categoria(sb, item_id, categoria)
    # 2) Remover da tabela itens (CASCADE no DB também remove nas categorias; remoção explícita acima garante tabelas dinâmicas)
    r = sb.table('itens').delete().eq('id', int(item_id)).execute()
    return r.data is not None and len(r.data) > 0


# ---------- Compromissos ----------
def _row_to_compromisso(record, item=None):
    class Compromisso:
        def __init__(self):
            self.id = record.get('id')
            self.item_id = record.get('item_id')
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
            if self._item is None and self.item_id:
                self._item = buscar_item_por_id(self.item_id)
            return self._item
    return Compromisso()

def criar_compromisso(item_id, quantidade, data_inicio, data_fim, descricao=None, cidade=None, uf=None, endereco=None, contratante=None):
    if not cidade or not uf:
        raise ValueError("Cidade e UF são obrigatórios")
    sb = get_supabase()
    data_inicio = _date_parse(data_inicio)
    data_fim = _date_parse(data_fim)
    ins = sb.table('compromissos').insert({
        'item_id': int(item_id),
        'quantidade': int(quantidade),
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat(),
        'descricao': descricao or '',
        'cidade': cidade,
        'uf': uf[:2].upper(),
        'endereco': endereco or '',
        'contratante': contratante or ''
    }).execute()
    if not ins.data or len(ins.data) == 0:
        raise Exception("Erro ao criar compromisso")
    row = ins.data[0]
    auditoria.registrar_auditoria('CREATE', 'Compromissos', row['id'], valores_novos=row)
    return _row_to_compromisso(row)

def listar_compromissos():
    sb = get_supabase()
    r = sb.table('compromissos').select('*').order('data_inicio', desc=False).execute()
    itens_cache = {}
    out = []
    for row in (r.data or []):
        iid = row.get('item_id')
        if iid and iid not in itens_cache:
            itens_cache[iid] = buscar_item_por_id(iid)
        out.append(_row_to_compromisso(row, item=itens_cache.get(iid)))
    return out

def atualizar_compromisso(compromisso_id, item_id, quantidade, data_inicio, data_fim, descricao=None, cidade=None, uf=None, endereco=None, contratante=None):
    sb = get_supabase()
    payload = {}
    if item_id is not None:
        payload['item_id'] = int(item_id)
    if quantidade is not None:
        payload['quantidade'] = int(quantidade)
    if data_inicio is not None:
        payload['data_inicio'] = _date_parse(data_inicio).isoformat()
    if data_fim is not None:
        payload['data_fim'] = _date_parse(data_fim).isoformat()
    if descricao is not None:
        payload['descricao'] = descricao
    if cidade is not None:
        payload['cidade'] = cidade
    if uf is not None:
        payload['uf'] = uf[:2].upper()
    if endereco is not None:
        payload['endereco'] = endereco
    if contratante is not None:
        payload['contratante'] = contratante
    if not payload:
        return buscar_compromisso_por_id(compromisso_id)
    sb.table('compromissos').update(payload).eq('id', int(compromisso_id)).execute()
    return buscar_compromisso_por_id(compromisso_id)

def buscar_compromisso_por_id(compromisso_id):
    sb = get_supabase()
    r = sb.table('compromissos').select('*').eq('id', int(compromisso_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    row = r.data[0]
    item = buscar_item_por_id(row['item_id']) if row.get('item_id') else None
    return _row_to_compromisso(row, item=item)

def deletar_compromisso(compromisso_id):
    sb = get_supabase()
    r = sb.table('compromissos').delete().eq('id', int(compromisso_id)).execute()
    return r.data is not None and len(r.data) > 0


# ---------- Disponibilidade (inclui peças instaladas) ----------
def listar_pecas_carros(carro_id=None, peca_id=None):
    sb = get_supabase()
    q = sb.table('pecas_carros').select('*')
    if carro_id is not None:
        q = q.eq('carro_id', int(carro_id))
    if peca_id is not None:
        q = q.eq('peca_id', int(peca_id))
    r = q.execute()
    class PecaCarroRow:
        def __init__(self, row):
            self.id = row.get('id')
            self.peca_id = row.get('peca_id')
            self.carro_id = row.get('carro_id')
            self.quantidade = row.get('quantidade') or 1
            self.data_instalacao = _date_parse(row.get('data_instalacao'))
            self.observacoes = row.get('observacoes') or ''
    return [PecaCarroRow(x) for x in (r.data or [])]

# No Supabase a categoria de peças chama-se "Pecas" (tabela pecas)
CATEGORIA_PECAS_SUPABASE = 'Pecas'

def criar_peca_carro(peca_id, carro_id, quantidade=1, data_instalacao=None, observacoes=None):
    """Associa uma peça (item) a um carro (item). Peça deve ser categoria 'Pecas', carro deve ser 'Carros'."""
    sb = get_supabase()
    peca = buscar_item_por_id(peca_id)
    if not peca:
        raise ValueError(f"Peça {peca_id} não encontrada")
    cat_peca = (getattr(peca, 'categoria', '') or '').strip()
    if cat_peca != CATEGORIA_PECAS_SUPABASE:
        raise ValueError(f"Item {peca_id} não é uma peça (categoria: {peca.categoria}). No Supabase use categoria '{CATEGORIA_PECAS_SUPABASE}'.")
    carro = buscar_item_por_id(carro_id)
    if not carro:
        raise ValueError(f"Carro {carro_id} não encontrado")
    if (getattr(carro, 'categoria', '') or '') != 'Carros':
        raise ValueError(f"Item {carro_id} não é um carro (categoria: {carro.categoria})")
    payload = {
        'peca_id': int(peca_id),
        'carro_id': int(carro_id),
        'quantidade': int(quantidade),
        'observacoes': observacoes or ''
    }
    if data_instalacao is not None:
        payload['data_instalacao'] = _date_parse(data_instalacao).isoformat()
    ins = sb.table('pecas_carros').insert(payload).execute()
    if not ins.data or len(ins.data) == 0:
        raise Exception("Erro ao criar associação peça-carro")
    auditoria.registrar_auditoria('CREATE', 'Pecas_Carros', ins.data[0]['id'], valores_novos=payload)
    return buscar_peca_carro_por_id(ins.data[0]['id'])

def buscar_peca_carro_por_id(associacao_id):
    sb = get_supabase()
    r = sb.table('pecas_carros').select('*').eq('id', int(associacao_id)).execute()
    if not r.data or len(r.data) == 0:
        return None
    row = r.data[0]
    class PecaCarroRow:
        def __init__(self):
            self.id = row.get('id')
            self.peca_id = row.get('peca_id')
            self.carro_id = row.get('carro_id')
            self.quantidade = row.get('quantidade') or 1
            self.data_instalacao = _date_parse(row.get('data_instalacao'))
            self.observacoes = row.get('observacoes') or ''
    return PecaCarroRow()

def atualizar_peca_carro(associacao_id, quantidade=None, data_instalacao=None, observacoes=None):
    sb = get_supabase()
    payload = {}
    if quantidade is not None:
        payload['quantidade'] = int(quantidade)
    if data_instalacao is not None:
        payload['data_instalacao'] = _date_parse(data_instalacao).isoformat()
    if observacoes is not None:
        payload['observacoes'] = observacoes
    if payload:
        sb.table('pecas_carros').update(payload).eq('id', int(associacao_id)).execute()
    return buscar_peca_carro_por_id(associacao_id)

def deletar_peca_carro(associacao_id):
    sb = get_supabase()
    r = sb.table('pecas_carros').delete().eq('id', int(associacao_id)).execute()
    return r.data is not None and len(r.data) > 0

def verificar_disponibilidade(item_id, data_consulta, filtro_localizacao=None):
    item = buscar_item_por_id(item_id)
    if not item:
        return None
        
    data_consulta = _date_parse(data_consulta)
    sb = get_supabase()
    
    # 1. Busca compromissos (Rentals)
    # Em vez de listar todos, filtramos direto no banco para performance
    query_comp = sb.table('compromissos').select('*').eq('item_id', int(item_id))
    r_comp = query_comp.execute()
    compromissos = [_row_to_compromisso(c) for c in (r_comp.data or [])]
    
    # Filtra compromissos ativos na data
    compromissos_ativos = [c for c in compromissos if c.data_inicio <= data_consulta <= c.data_fim]
    
    # 2. Aplica sua lógica de Filtro de Localização nos Compromissos
    if filtro_localizacao:
        cidade_uf = filtro_localizacao.split(" - ")
        if len(cidade_uf) == 2:
            cidade_f, uf_f = cidade_uf[0], cidade_uf[1]
            compromissos_ativos = [c for c in compromissos_ativos if getattr(c, 'cidade', '') == cidade_f and getattr(c, 'uf', '') == uf_f.upper()]

    quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)

    # 3. Busca peças instaladas (Ativo Imobilizado)
    # Filtramos por data_instalacao para saber se na data da consulta a peça já estava no carro
    pecas_r = sb.table('pecas_carros').select('quantidade, data_instalacao').eq('peca_id', int(item_id)).execute()
    
    quantidade_instalada = sum(
        p['quantidade'] for p in (pecas_r.data or [])
        if p['data_instalacao'] is None or _date_parse(p['data_instalacao']) <= data_consulta
    )

    # 4. Cálculo final considerando a Localização do Item
    total_ocupado = quantidade_comprometida + quantidade_instalada
    
    if filtro_localizacao:
        cidade_uf = filtro_localizacao.split(" - ")
        if len(cidade_uf) == 2:
            cidade_f, uf_f = cidade_uf[0], cidade_uf[1]
            # Verifica se o item físico está nesta cidade
            item_na_loc = (getattr(item, 'cidade', '') == cidade_f and getattr(item, 'uf', '') == uf_f.upper())
            quantidade_disponivel = (item.quantidade_total - total_ocupado) if item_na_loc else 0
        else:
            quantidade_disponivel = item.quantidade_total - total_ocupado
    else:
        quantidade_disponivel = item.quantidade_total - total_ocupado

    return {
        'item': item,
        'quantidade_total': item.quantidade_total,
        'quantidade_comprometida': quantidade_comprometida,
        'quantidade_instalada': quantidade_instalada,
        'quantidade_disponivel': max(0, quantidade_disponivel),
        'compromissos_ativos': compromissos_ativos,
        'valor_patrimonial_unitario': getattr(item, 'valor_compra', 0) # Inteligência Financeira
    }

def verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=None):
    item = buscar_item_por_id(item_id)
    if not item:
        return None
        
    data_inicio = _date_parse(data_inicio)
    data_fim = _date_parse(data_fim)
    
    # Busca compromissos que colidem com o período
    sb = get_supabase()
    r_comp = sb.table('compromissos').select('*').eq('item_id', int(item_id)).execute()
    compromissos = [_row_to_compromisso(c) for c in (r_comp.data or [])]
    
    compromissos = [c for c in compromissos if c.data_inicio <= data_fim and c.data_fim >= data_inicio]
    
    if excluir_compromisso_id:
        compromissos = [c for c in compromissos if c.id != excluir_compromisso_id]

    # Lógica de "Pior Cenário": Verifica dia a dia qual o pico de ocupação
    max_comprometido = 0
    d = data_inicio
    while d <= data_fim:
        no_dia = sum(c.quantidade for c in compromissos if c.data_inicio <= d <= c.data_fim)
        # Somamos o que está instalado nos carros também para esse dia
        # (Considerando que peças instaladas raramente saem, mas a data_instalacao importa)
        pecas_r = sb.table('pecas_carros').select('quantidade, data_instalacao').eq('peca_id', int(item_id)).execute()
        qtd_inst_no_dia = sum(
            p['quantidade'] for p in (pecas_r.data or [])
            if p['data_instalacao'] is None or _date_parse(p['data_instalacao']) <= d
        )
        
        total_ocupado_no_dia = no_dia + qtd_inst_no_dia
        max_comprometido = max(max_comprometido, total_ocupado_no_dia)
        d += timedelta(days=1)

    return {
        'item': item,
        'quantidade_total': item.quantidade_total,
        'max_ocupado_no_periodo': max_comprometido,
        'disponivel_minimo': max(0, item.quantidade_total - max_comprometido)
    }
    

def verificar_disponibilidade_todos_itens(data_consulta, filtro_localizacao=None):
    resultados = []
    for item in listar_itens():
        disp = verificar_disponibilidade(item.id, data_consulta, filtro_localizacao)
        if disp:
            resultados.append({
                'item': disp['item'],
                'quantidade_total': disp['quantidade_total'],
                'quantidade_comprometida': disp['quantidade_comprometida'],
                'quantidade_instalada': disp.get('quantidade_instalada', 0),
                'quantidade_disponivel': disp['quantidade_disponivel']
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
