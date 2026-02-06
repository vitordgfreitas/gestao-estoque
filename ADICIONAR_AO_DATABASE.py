"""
FUNÇÕES PARA ADICIONAR AO database.py

Copie todo o conteúdo deste arquivo e cole no FINAL de database.py
(após a última função existente)
"""

from models import get_session, PecaCarro, Item
from sqlalchemy.orm import joinedload
from datetime import date
import auditoria

# ============= PEÇAS EM CARROS =============

def criar_peca_carro(peca_id, carro_id, quantidade=1, data_instalacao=None, observacoes=None):
    """Associa uma peça a um carro"""
    session = get_session()
    try:
        # Verifica se peça existe e é da categoria correta
        peca = session.query(Item).filter(Item.id == peca_id).first()
        if not peca:
            raise ValueError(f"Peça {peca_id} não encontrada")
        if peca.categoria != "Peças de Carro":
            raise ValueError(f"Item {peca_id} não é uma peça de carro (categoria: {peca.categoria})")
        
        # Verifica se carro existe e é da categoria correta
        carro = session.query(Item).filter(Item.id == carro_id).first()
        if not carro:
            raise ValueError(f"Carro {carro_id} não encontrado")
        if carro.categoria != "Carros":
            raise ValueError(f"Item {carro_id} não é um carro (categoria: {carro.categoria})")
        
        # Cria associação
        associacao = PecaCarro(
            peca_id=peca_id,
            carro_id=carro_id,
            quantidade=quantidade,
            data_instalacao=data_instalacao or date.today(),
            observacoes=observacoes
        )
        
        session.add(associacao)
        session.commit()
        session.refresh(associacao)
        
        # Carrega relacionamentos
        if associacao.peca:
            session.expunge(associacao.peca)
        if associacao.carro:
            session.expunge(associacao.carro)
        session.expunge(associacao)
        
        auditoria.registrar_auditoria('CREATE', 'Pecas_Carros', associacao.id, valores_novos={
            'peca_id': peca_id,
            'carro_id': carro_id,
            'quantidade': quantidade
        })
        
        return associacao
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_pecas_carros(carro_id=None, peca_id=None):
    """Lista associações de peças em carros com filtros opcionais"""
    session = get_session()
    try:
        query = session.query(PecaCarro).options(
            joinedload(PecaCarro.peca),
            joinedload(PecaCarro.carro)
        )
        
        if carro_id:
            query = query.filter(PecaCarro.carro_id == carro_id)
        if peca_id:
            query = query.filter(PecaCarro.peca_id == peca_id)
        
        associacoes = query.all()
        
        # Desanexa objetos da sessão
        for associacao in associacoes:
            if associacao.peca:
                session.expunge(associacao.peca)
            if associacao.carro:
                session.expunge(associacao.carro)
            session.expunge(associacao)
        
        return associacoes
    finally:
        session.close()


def buscar_peca_carro_por_id(associacao_id):
    """Busca uma associação peça-carro por ID"""
    session = get_session()
    try:
        associacao = session.query(PecaCarro).options(
            joinedload(PecaCarro.peca),
            joinedload(PecaCarro.carro)
        ).filter(PecaCarro.id == associacao_id).first()
        
        if associacao:
            if associacao.peca:
                session.expunge(associacao.peca)
            if associacao.carro:
                session.expunge(associacao.carro)
            session.expunge(associacao)
        
        return associacao
    finally:
        session.close()


def atualizar_peca_carro(associacao_id, quantidade=None, data_instalacao=None, observacoes=None):
    """Atualiza uma associação peça-carro"""
    session = get_session()
    try:
        associacao = session.query(PecaCarro).filter(PecaCarro.id == associacao_id).first()
        if not associacao:
            return None
        
        valores_antigos = {
            'quantidade': associacao.quantidade,
            'data_instalacao': str(associacao.data_instalacao) if associacao.data_instalacao else None,
            'observacoes': associacao.observacoes
        }
        
        if quantidade is not None:
            associacao.quantidade = quantidade
        if data_instalacao is not None:
            associacao.data_instalacao = data_instalacao
        if observacoes is not None:
            associacao.observacoes = observacoes
        
        session.commit()
        session.refresh(associacao)
        
        if associacao.peca:
            session.expunge(associacao.peca)
        if associacao.carro:
            session.expunge(associacao.carro)
        session.expunge(associacao)
        
        auditoria.registrar_auditoria('UPDATE', 'Pecas_Carros', associacao_id, valores_antigos=valores_antigos, valores_novos={
            'quantidade': associacao.quantidade,
            'data_instalacao': str(associacao.data_instalacao) if associacao.data_instalacao else None,
            'observacoes': associacao.observacoes
        })
        
        return associacao
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def deletar_peca_carro(associacao_id):
    """Remove uma associação peça-carro"""
    session = get_session()
    try:
        associacao = session.query(PecaCarro).filter(PecaCarro.id == associacao_id).first()
        if not associacao:
            return False
        
        valores_antigos = {
            'peca_id': associacao.peca_id,
            'carro_id': associacao.carro_id,
            'quantidade': associacao.quantidade
        }
        
        session.delete(associacao)
        session.commit()
        
        auditoria.registrar_auditoria('DELETE', 'Pecas_Carros', associacao_id, valores_antigos=valores_antigos)
        
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
