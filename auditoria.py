"""
Sistema de auditoria para rastreamento de mudanças
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Tenta importar módulos de banco de dados
try:
    import sheets_database as db_module
    USE_GOOGLE_SHEETS = True
except ImportError:
    USE_GOOGLE_SHEETS = False
    try:
        import database as db_module
    except ImportError:
        db_module = None


def registrar_auditoria(
    acao: str,
    tabela: str,
    registro_id: int,
    valores_antigos: Optional[Dict[str, Any]] = None,
    valores_novos: Optional[Dict[str, Any]] = None,
    usuario: Optional[str] = None
):
    """
    Registra uma ação de auditoria
    
    Args:
        acao: Ação realizada (CREATE, UPDATE, DELETE)
        tabela: Nome da tabela/aba afetada
        registro_id: ID do registro afetado
        valores_antigos: Valores antes da mudança (dict)
        valores_novos: Valores após a mudança (dict)
        usuario: Nome do usuário que fez a ação
    """
    try:
        if USE_GOOGLE_SHEETS:
            _registrar_auditoria_sheets(acao, tabela, registro_id, valores_antigos, valores_novos, usuario)
        else:
            _registrar_auditoria_sqlite(acao, tabela, registro_id, valores_antigos, valores_novos, usuario)
    except Exception as e:
        # Não falha a operação principal se a auditoria falhar
        print(f"Erro ao registrar auditoria: {e}")


def _registrar_auditoria_sheets(
    acao: str,
    tabela: str,
    registro_id: int,
    valores_antigos: Optional[Dict[str, Any]] = None,
    valores_novos: Optional[Dict[str, Any]] = None,
    usuario: Optional[str] = None
):
    """Registra auditoria no Google Sheets"""
    try:
        sheets = db_module.get_sheets()
        spreadsheet = sheets['spreadsheet']
        
        # Obtém ou cria aba de Auditoria
        try:
            sheet_auditoria = spreadsheet.worksheet("Auditoria")
        except Exception:
            # Cria aba de Auditoria
            sheet_auditoria = spreadsheet.add_worksheet(title="Auditoria", rows=1000, cols=10)
            # Adiciona cabeçalhos
            sheet_auditoria.append_row([
                "ID", "Timestamp", "Usuário", "Ação", "Tabela", 
                "Registro ID", "Valores Antigos", "Valores Novos"
            ])
            # Formata cabeçalho
            header_range = sheet_auditoria.get_range(1, 1, 1, 8)
            header_range.format({
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.26, "green": 0.52, "blue": 0.96},
                "textStyle": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}
            })
        
        # Busca próximo ID
        try:
            all_records = sheet_auditoria.get_all_records()
            if all_records:
                valid_ids = [int(r.get('ID', 0)) for r in all_records if r and r.get('ID')]
                next_id = max(valid_ids) + 1 if valid_ids else 1
            else:
                next_id = 1
        except Exception:
            next_id = 1
        
        # Prepara valores
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        usuario_str = usuario or "Sistema"
        valores_antigos_str = json.dumps(valores_antigos, ensure_ascii=False, default=str) if valores_antigos else ""
        valores_novos_str = json.dumps(valores_novos, ensure_ascii=False, default=str) if valores_novos else ""
        
        # Adiciona registro
        sheet_auditoria.append_row([
            next_id,
            timestamp,
            usuario_str,
            acao,
            tabela,
            registro_id,
            valores_antigos_str,
            valores_novos_str
        ])
    except Exception as e:
        print(f"Erro ao registrar auditoria no Google Sheets: {e}")


def _registrar_auditoria_sqlite(
    acao: str,
    tabela: str,
    registro_id: int,
    valores_antigos: Optional[Dict[str, Any]] = None,
    valores_novos: Optional[Dict[str, Any]] = None,
    usuario: Optional[str] = None
):
    """Registra auditoria no SQLite"""
    try:
        from models import get_session, Base
        from sqlalchemy import Column, Integer, String, DateTime
        from datetime import datetime
        
        # Define modelo de Auditoria dinamicamente se não existir
        if not hasattr(db_module, 'Auditoria'):
            class Auditoria(Base):
                __tablename__ = 'auditoria'
                id = Column(Integer, primary_key=True)
                usuario = Column(String(100))
                acao = Column(String(20))
                tabela = Column(String(50))
                registro_id = Column(Integer)
                valores_antigos = Column(String(1000))
                valores_novos = Column(String(1000))
                timestamp = Column(DateTime, default=datetime.now)
            
            # Cria tabela se não existir
            Base.metadata.create_all(db_module.get_engine())
            db_module.Auditoria = Auditoria
        
        session = db_module.get_session()
        try:
            auditoria = db_module.Auditoria(
                usuario=usuario or "Sistema",
                acao=acao,
                tabela=tabela,
                registro_id=registro_id,
                valores_antigos=json.dumps(valores_antigos, ensure_ascii=False, default=str) if valores_antigos else None,
                valores_novos=json.dumps(valores_novos, ensure_ascii=False, default=str) if valores_novos else None,
                timestamp=datetime.now()
            )
            session.add(auditoria)
            session.commit()
        finally:
            session.close()
    except Exception as e:
        print(f"Erro ao registrar auditoria no SQLite: {e}")


def obter_historico(tabela: str, registro_id: int) -> list:
    """
    Obtém histórico de mudanças de um registro
    
    Args:
        tabela: Nome da tabela
        registro_id: ID do registro
        
    Returns:
        Lista de registros de auditoria
    """
    try:
        if USE_GOOGLE_SHEETS:
            return _obter_historico_sheets(tabela, registro_id)
        else:
            return _obter_historico_sqlite(tabela, registro_id)
    except Exception as e:
        print(f"Erro ao obter histórico: {e}")
        return []


def _obter_historico_sheets(tabela: str, registro_id: int) -> list:
    """Obtém histórico do Google Sheets"""
    try:
        sheets = db_module.get_sheets()
        spreadsheet = sheets['spreadsheet']
        
        try:
            sheet_auditoria = spreadsheet.worksheet("Auditoria")
            records = sheet_auditoria.get_all_records()
            
            # Filtra por tabela e registro_id
            historico = []
            for record in records:
                if record and record.get('Tabela') == tabela and record.get('Registro ID') == registro_id:
                    try:
                        valores_antigos = json.loads(record.get('Valores Antigos', '{}') or '{}')
                    except:
                        valores_antigos = {}
                    
                    try:
                        valores_novos = json.loads(record.get('Valores Novos', '{}') or '{}')
                    except:
                        valores_novos = {}
                    
                    historico.append({
                        'id': record.get('ID'),
                        'timestamp': record.get('Timestamp'),
                        'usuario': record.get('Usuário'),
                        'acao': record.get('Ação'),
                        'tabela': record.get('Tabela'),
                        'registro_id': record.get('Registro ID'),
                        'valores_antigos': valores_antigos,
                        'valores_novos': valores_novos
                    })
            
            # Ordena por timestamp (mais recente primeiro)
            historico.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return historico
        except Exception:
            return []
    except Exception:
        return []


def _obter_historico_sqlite(tabela: str, registro_id: int) -> list:
    """Obtém histórico do SQLite"""
    try:
        from models import get_session
        
        session = db_module.get_session()
        try:
            if hasattr(db_module, 'Auditoria'):
                registros = session.query(db_module.Auditoria).filter(
                    db_module.Auditoria.tabela == tabela,
                    db_module.Auditoria.registro_id == registro_id
                ).order_by(db_module.Auditoria.timestamp.desc()).all()
                
                historico = []
                for reg in registros:
                    try:
                        valores_antigos = json.loads(reg.valores_antigos or '{}')
                    except:
                        valores_antigos = {}
                    
                    try:
                        valores_novos = json.loads(reg.valores_novos or '{}')
                    except:
                        valores_novos = {}
                    
                    historico.append({
                        'id': reg.id,
                        'timestamp': reg.timestamp.isoformat() if reg.timestamp else '',
                        'usuario': reg.usuario,
                        'acao': reg.acao,
                        'tabela': reg.tabela,
                        'registro_id': reg.registro_id,
                        'valores_antigos': valores_antigos,
                        'valores_novos': valores_novos
                    })
                
                return historico
            return []
        finally:
            session.close()
    except Exception:
        return []
