from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import date
import os

Base = declarative_base()

class Item(Base):
    __tablename__ = 'itens'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    quantidade_total = Column(Integer, nullable=False)
    descricao = Column(String(500))
    cidade = Column(String(200), nullable=False)
    uf = Column(String(2), nullable=False)
    endereco = Column(String(500))
    categoria = Column(String(50), nullable=False, default='Estrutura de Evento')  # Nova coluna
    
    # Relacionamento com Carro (um para um)
    carro = relationship("Carro", back_populates="item", uselist=False, cascade="all, delete-orphan")
    compromissos = relationship("Compromisso", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Item(nome='{self.nome}', quantidade_total={self.quantidade_total}, categoria='{self.categoria}')>"


class Carro(Base):
    __tablename__ = 'carros'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('itens.id'), nullable=False, unique=True)
    placa = Column(String(10), nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(100), nullable=False)
    ano = Column(Integer, nullable=False)
    
    item = relationship("Item", back_populates="carro")
    
    def __repr__(self):
        return f"<Carro(item_id={self.item_id}, placa='{self.placa}', marca='{self.marca}', modelo='{self.modelo}', ano={self.ano})>"


class Compromisso(Base):
    __tablename__ = 'compromissos'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('itens.id'), nullable=False)
    quantidade = Column(Integer, nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    descricao = Column(String(500))
    cidade = Column(String(200), nullable=False)
    uf = Column(String(2), nullable=False)
    endereco = Column(String(500))
    contratante = Column(String(200))
    
    item = relationship("Item", back_populates="compromissos")
    contas_receber = relationship("ContaReceber", back_populates="compromisso", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Compromisso(item_id={self.item_id}, quantidade={self.quantidade}, data_inicio={self.data_inicio}, data_fim={self.data_fim})>"


class ContaReceber(Base):
    __tablename__ = 'contas_receber'
    
    id = Column(Integer, primary_key=True)
    compromisso_id = Column(Integer, ForeignKey('compromissos.id'), nullable=False)
    descricao = Column(String(500), nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date)
    status = Column(String(20), nullable=False, default='Pendente')  # Pendente, Pago, Vencido
    forma_pagamento = Column(String(50))  # Dinheiro, PIX, Cartão, Boleto, etc.
    observacoes = Column(String(1000))
    
    compromisso = relationship("Compromisso", back_populates="contas_receber")
    
    def calcular_status(self):
        """Calcula o status baseado nas datas"""
        hoje = date.today()
        if self.data_pagamento:
            return 'Pago'
        elif self.data_vencimento < hoje:
            return 'Vencido'
        else:
            return 'Pendente'
    
    def __repr__(self):
        return f"<ContaReceber(id={self.id}, compromisso_id={self.compromisso_id}, valor={self.valor}, status='{self.status}')>"


class ContaPagar(Base):
    __tablename__ = 'contas_pagar'
    
    id = Column(Integer, primary_key=True)
    descricao = Column(String(500), nullable=False)
    categoria = Column(String(50), nullable=False)  # Fornecedor, Manutenção, Despesa, Outro
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date)
    status = Column(String(20), nullable=False, default='Pendente')  # Pendente, Pago, Vencido
    fornecedor = Column(String(200))
    item_id = Column(Integer, ForeignKey('itens.id'))  # Opcional - para manutenção de itens específicos
    forma_pagamento = Column(String(50))  # Dinheiro, PIX, Cartão, Boleto, etc.
    observacoes = Column(String(1000))
    
    item = relationship("Item", backref="contas_pagar")
    
    def calcular_status(self):
        """Calcula o status baseado nas datas"""
        hoje = date.today()
        if self.data_pagamento:
            return 'Pago'
        elif self.data_vencimento < hoje:
            return 'Vencido'
        else:
            return 'Pendente'
    
    def __repr__(self):
        return f"<ContaPagar(id={self.id}, descricao='{self.descricao}', valor={self.valor}, status='{self.status}')>"


class Financiamento(Base):
    __tablename__ = 'financiamentos'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('itens.id'), nullable=False)
    valor_total = Column(Float, nullable=False)
    numero_parcelas = Column(Integer, nullable=False)
    valor_parcela = Column(Float, nullable=False)
    taxa_juros = Column(Float, nullable=False, default=0.0)  # Taxa de juros % ao mês
    data_inicio = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default='Ativo')  # Ativo, Quitado, Cancelado
    instituicao_financeira = Column(String(200))
    observacoes = Column(String(1000))
    
    item = relationship("Item", backref="financiamentos")
    parcelas = relationship("ParcelaFinanciamento", back_populates="financiamento", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Financiamento(id={self.id}, item_id={self.item_id}, valor_total={self.valor_total}, status='{self.status}')>"


class ParcelaFinanciamento(Base):
    __tablename__ = 'parcelas_financiamento'
    
    id = Column(Integer, primary_key=True)
    financiamento_id = Column(Integer, ForeignKey('financiamentos.id'), nullable=False)
    numero_parcela = Column(Integer, nullable=False)
    valor_original = Column(Float, nullable=False)
    valor_pago = Column(Float, nullable=False, default=0.0)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date)
    status = Column(String(20), nullable=False, default='Pendente')  # Pendente, Paga, Atrasada
    juros = Column(Float, nullable=False, default=0.0)
    multa = Column(Float, nullable=False, default=0.0)
    desconto = Column(Float, nullable=False, default=0.0)
    link_boleto = Column(String(500))  # URL do boleto
    
    financiamento = relationship("Financiamento", back_populates="parcelas")
    
    def calcular_status(self):
        """Calcula o status baseado nas datas"""
        hoje = date.today()
        if self.valor_pago >= self.valor_original:
            return 'Paga'
        elif self.data_vencimento < hoje:
            return 'Atrasada'
        else:
            return 'Pendente'
    
    def calcular_valor_total(self):
        """Calcula valor total da parcela (original + juros + multa - desconto)"""
        return self.valor_original + self.juros + self.multa - self.desconto
    
    def __repr__(self):
        return f"<ParcelaFinanciamento(id={self.id}, financiamento_id={self.financiamento_id}, parcela={self.numero_parcela}, status='{self.status}')>"


def get_engine():
    """Cria e retorna a engine do banco de dados"""
    os.makedirs('data', exist_ok=True)
    db_path = os.path.join('data', 'estoque.db')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    return engine


def init_db():
    """Inicializa o banco de dados criando as tabelas"""
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_session():
    """Retorna uma sessão do banco de dados"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
