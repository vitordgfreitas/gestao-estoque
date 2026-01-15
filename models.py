from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
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
    
    compromissos = relationship("Compromisso", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Item(nome='{self.nome}', quantidade_total={self.quantidade_total})>"


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
    
    def __repr__(self):
        return f"<Compromisso(item_id={self.item_id}, quantidade={self.quantidade}, data_inicio={self.data_inicio}, data_fim={self.data_fim})>"


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
