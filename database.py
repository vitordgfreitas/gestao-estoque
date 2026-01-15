from models import get_session, Item, Compromisso
from datetime import date
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

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
    session = get_session()
    try:
        if not cidade or not uf:
            raise ValueError("Cidade e UF são obrigatórios")
        
        item = Item(
            nome=nome, 
            quantidade_total=quantidade_total,
            descricao=descricao,
            cidade=cidade,
            uf=uf.upper()[:2],  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
            endereco=endereco
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        session.expunge(item)
        return item
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_itens():
    """Lista todos os itens do estoque"""
    session = get_session()
    try:
        # Carrega os relacionamentos antes de desanexar
        itens = session.query(Item).options(joinedload(Item.compromissos)).all()
        # Desanexa todos os objetos da sessão
        for item in itens:
            session.expunge(item)
        return itens
    finally:
        session.close()


def buscar_item_por_id(item_id):
    """Busca um item pelo ID"""
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if item:
            session.expunge(item)
        return item
    finally:
        session.close()


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
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if item:
            if not cidade or not uf:
                raise ValueError("Cidade e UF são obrigatórios")
            
            item.nome = nome
            item.quantidade_total = quantidade_total
            item.descricao = descricao
            item.cidade = cidade
            item.uf = uf.upper()[:2]  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
            item.endereco = endereco
            session.commit()
            session.refresh(item)
            session.expunge(item)
            return item
        return None
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


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
    session = get_session()
    try:
        if not cidade or not uf:
            raise ValueError("Cidade e UF são obrigatórios")
        
        compromisso = Compromisso(
            item_id=item_id,
            quantidade=quantidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            descricao=descricao,
            cidade=cidade,
            uf=uf.upper()[:2],  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
            endereco=endereco,
            contratante=contratante
        )
        session.add(compromisso)
        session.commit()
        session.refresh(compromisso)
        # Carrega o relacionamento com Item antes de desanexar
        compromisso.item  # Força o carregamento do relacionamento
        # Desanexa o objeto da sessão para poder ser usado depois que a sessão fechar
        session.expunge(compromisso)
        if compromisso.item:
            session.expunge(compromisso.item)
        return compromisso
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_compromissos():
    """Lista todos os compromissos"""
    session = get_session()
    try:
        # Carrega o relacionamento com Item antes de desanexar
        compromissos = session.query(Compromisso).options(joinedload(Compromisso.item)).all()
        # Desanexa todos os objetos da sessão
        for compromisso in compromissos:
            session.expunge(compromisso)
            # Também desanexa o item relacionado
            if compromisso.item:
                session.expunge(compromisso.item)
        return compromissos
    finally:
        session.close()


def verificar_disponibilidade(item_id, data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de um item em uma data específica
    
    Args:
        item_id: ID do item
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localização
    """
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None
        
        # Busca compromissos que estão ativos na data de consulta
        compromissos_ativos_query = session.query(Compromisso).filter(
            and_(
                Compromisso.item_id == item_id,
                Compromisso.data_inicio <= data_consulta,
                Compromisso.data_fim >= data_consulta
            )
        )
        
        # Se há filtro de localização, aplica filtro adicional (formato: "Cidade - UF")
        if filtro_localizacao:
            cidade_uf = filtro_localizacao.split(" - ")
            if len(cidade_uf) == 2:
                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                compromissos_ativos_query = compromissos_ativos_query.filter(
                    and_(
                        Compromisso.cidade == cidade_filtro,
                        Compromisso.uf == uf_filtro.upper()
                    )
                )
        
        compromissos_ativos = compromissos_ativos_query.all()
        
        quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
        
        # Se há filtro de localização e o item não está nessa localização,
        # considera que não há itens disponíveis naquela localização
        if filtro_localizacao:
            cidade_uf = filtro_localizacao.split(" - ")
            if len(cidade_uf) == 2:
                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                item_na_localizacao = (item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                if not item_na_localizacao:
                    # Item não está na localização, então disponível = 0 (ou negativo se houver compromissos)
                    quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        else:
            quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        
        # Desanexa objetos da sessão antes de retornar
        session.expunge(item)
        for comp in compromissos_ativos:
            session.expunge(comp)
        
        return {
            'item': item,
            'quantidade_total': item.quantidade_total,
            'quantidade_comprometida': quantidade_comprometida,
            'quantidade_disponivel': quantidade_disponivel,
            'compromissos_ativos': compromissos_ativos
        }
    finally:
        session.close()


def verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=None):
    """Verifica se há disponibilidade suficiente em todo o período para um novo compromisso"""
    from datetime import timedelta
    
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None
        
        # Busca compromissos que se sobrepõem com o período solicitado
        # Dois períodos se sobrepõem se: inicio1 <= fim2 AND inicio2 <= fim1
        compromissos_sobrepostos = session.query(Compromisso).filter(
            and_(
                Compromisso.item_id == item_id,
                Compromisso.data_inicio <= data_fim,
                Compromisso.data_fim >= data_inicio
            )
        ).all()
        
        # Exclui o próprio compromisso se estiver editando
        if excluir_compromisso_id:
            compromissos_sobrepostos = [c for c in compromissos_sobrepostos if c.id != excluir_compromisso_id]
        
        # Encontra o dia com maior comprometimento no período
        max_comprometido = 0
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            compromissos_no_dia = [c for c in compromissos_sobrepostos 
                                  if c.data_inicio <= data_atual <= c.data_fim]
            comprometido_no_dia = sum(c.quantidade for c in compromissos_no_dia)
            max_comprometido = max(max_comprometido, comprometido_no_dia)
            
            # Incrementa a data
            if data_atual >= data_fim:
                break
            data_atual += timedelta(days=1)
        
        # Desanexa objeto da sessão antes de retornar
        session.expunge(item)
        
        return {
            'item': item,
            'quantidade_total': item.quantidade_total,
            'max_comprometido': max_comprometido,
            'disponivel_minimo': item.quantidade_total - max_comprometido
        }
    finally:
        session.close()


def verificar_disponibilidade_todos_itens(data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de todos os itens em uma data específica
    
    Args:
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localização
    """
    session = get_session()
    try:
        itens = session.query(Item).all()
        resultados = []
        
        for item in itens:
            compromissos_ativos_query = session.query(Compromisso).filter(
                and_(
                    Compromisso.item_id == item.id,
                    Compromisso.data_inicio <= data_consulta,
                    Compromisso.data_fim >= data_consulta
                )
            )
            
            # Se há filtro de localização, aplica filtro adicional (formato: "Cidade - UF")
            if filtro_localizacao:
                cidade_uf = filtro_localizacao.split(" - ")
                if len(cidade_uf) == 2:
                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                    compromissos_ativos_query = compromissos_ativos_query.filter(
                        and_(
                            Compromisso.cidade == cidade_filtro,
                            Compromisso.uf == uf_filtro.upper()
                        )
                    )
            
            compromissos_ativos = compromissos_ativos_query.all()
            
            quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
            
            # Se há filtro de localização e o item não está nessa localização,
            # considera que não há itens disponíveis naquela localização
            if filtro_localizacao:
                cidade_uf = filtro_localizacao.split(" - ")
                if len(cidade_uf) == 2:
                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                    item_na_localizacao = (item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                    if not item_na_localizacao:
                        # Item não está na localização, então disponível = 0 (ou negativo se houver compromissos)
                        quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                    else:
                        quantidade_disponivel = item.quantidade_total - quantidade_comprometida
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            
            # Desanexa objeto da sessão
            session.expunge(item)
            
            resultados.append({
                'item': item,
                'quantidade_total': item.quantidade_total,
                'quantidade_comprometida': quantidade_comprometida,
                'quantidade_disponivel': quantidade_disponivel
            })
        
        return resultados
    finally:
        session.close()


def deletar_item(item_id):
    """Deleta um item e todos os seus compromissos"""
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if item:
            session.delete(item)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


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
    session = get_session()
    try:
        compromisso = session.query(Compromisso).filter(Compromisso.id == compromisso_id).first()
        if compromisso:
            if not cidade or not uf:
                raise ValueError("Cidade e UF são obrigatórios")
            
            compromisso.item_id = item_id
            compromisso.quantidade = quantidade
            compromisso.data_inicio = data_inicio
            compromisso.data_fim = data_fim
            compromisso.descricao = descricao
            compromisso.cidade = cidade
            compromisso.uf = uf.upper()[:2]  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
            compromisso.endereco = endereco
            compromisso.contratante = contratante
            session.commit()
            session.refresh(compromisso)
            compromisso.item  # Força o carregamento do relacionamento
            session.expunge(compromisso)
            if compromisso.item:
                session.expunge(compromisso.item)
            return compromisso
        return None
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def deletar_compromisso(compromisso_id):
    """Deleta um compromisso"""
    session = get_session()
    try:
        compromisso = session.query(Compromisso).filter(Compromisso.id == compromisso_id).first()
        if compromisso:
            session.delete(compromisso)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
