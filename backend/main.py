"""
Backend FastAPI para o CRM de Gestão de Estoque
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import date, datetime, timedelta
from typing import List, Optional
import os
import sys
import secrets
from pydantic import BaseModel

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Carrega variáveis de ambiente do arquivo .env ANTES de usar os.getenv
try:
    from dotenv import load_dotenv
    # Tenta carregar .env da raiz do projeto
    env_path = os.path.join(root_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Carregado .env da raiz: {env_path}")
    # Também tenta carregar .env do backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    backend_env = os.path.join(backend_dir, '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
        print(f"✅ Carregado .env do backend: {backend_env}")
except ImportError:
    print("⚠️ python-dotenv não instalado, usando apenas variáveis de ambiente do sistema")
except Exception as e:
    print(f"⚠️ Erro ao carregar .env: {e}")

from models import Item, Compromisso, Carro

# Escolhe qual banco de dados usar baseado em variável de ambiente
# Por padrão, tenta usar Google Sheets (mesmo comportamento do Streamlit)
USE_GOOGLE_SHEETS = os.getenv('USE_GOOGLE_SHEETS', 'true').lower() == 'true'

# Inicializa o módulo de banco de dados apropriado
db_module = None
sheets_info = None

if USE_GOOGLE_SHEETS:
    try:
        import sheets_database as db_module
        # Tenta inicializar Google Sheets
        try:
            sheets_info = db_module.get_sheets()
            spreadsheet_url = sheets_info.get('spreadsheet_url', 'N/A')
            print(f"✅ Conectado ao Google Sheets: {spreadsheet_url}")
        except FileNotFoundError as e:
            error_msg = str(e)
            print(f"❌ Erro: Arquivo credentials.json não encontrado!")
            print(f"   {error_msg}")
            print(f"   Por favor, coloque o arquivo credentials.json na raiz do projeto.")
            print("⚠️ Tentando usar SQLite como fallback...")
            USE_GOOGLE_SHEETS = False
            from models import init_db
            import database as db_module
            init_db()
            print("✅ Usando SQLite local")
        except Exception as e:
            error_msg = str(e)
            import traceback
            print(f"⚠️ Aviso: Erro ao conectar ao Google Sheets")
            print(f"   Detalhes: {error_msg}")
            print(f"   Traceback completo:")
            traceback.print_exc()
            print("⚠️ Tentando usar SQLite como fallback...")
            USE_GOOGLE_SHEETS = False
            from models import init_db
            import database as db_module
            init_db()
            print("✅ Usando SQLite local")
    except ImportError as e:
        print(f"❌ Erro ao importar sheets_database: {str(e)}")
        print("⚠️ Usando SQLite como fallback...")
        USE_GOOGLE_SHEETS = False
        from models import init_db
        import database as db_module
        init_db()
        print("✅ Usando SQLite local")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        print("⚠️ Usando SQLite como fallback...")
        USE_GOOGLE_SHEETS = False
        from models import init_db
        import database as db_module
        init_db()
        print("✅ Usando SQLite local")
else:
    from models import init_db
    import database as db_module
    init_db()
    print("✅ Usando SQLite local (USE_GOOGLE_SHEETS=false)")

app = FastAPI(
    title="CRM Gestão de Estoque",
    description="API para sistema de gestão de estoque e aluguéis",
    version="1.0.0"
)

# CORS - permite requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ============= MODELS PYDANTIC =============

class ItemCreate(BaseModel):
    nome: str
    quantidade_total: int
    categoria: str = "Estrutura de Evento"
    descricao: Optional[str] = None
    cidade: str
    uf: str
    endereco: Optional[str] = None
    placa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    campos_categoria: Optional[dict] = None

class ItemUpdate(BaseModel):
    nome: Optional[str] = None
    quantidade_total: Optional[int] = None
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    placa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    campos_categoria: Optional[dict] = None

class ItemResponse(BaseModel):
    id: int
    nome: str
    quantidade_total: int
    categoria: str
    descricao: Optional[str]
    cidade: str
    uf: str
    endereco: Optional[str]
    carro: Optional[dict] = None
    
    class Config:
        from_attributes = True

class CompromissoCreate(BaseModel):
    item_id: int
    quantidade: int
    data_inicio: date
    data_fim: date
    descricao: Optional[str] = None
    cidade: str
    uf: str
    endereco: Optional[str] = None
    contratante: Optional[str] = None

class CompromissoUpdate(BaseModel):
    item_id: Optional[int] = None
    quantidade: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    descricao: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    contratante: Optional[str] = None

class CompromissoResponse(BaseModel):
    id: int
    item_id: int
    quantidade: int
    data_inicio: date
    data_fim: date
    descricao: Optional[str]
    cidade: str
    uf: str
    endereco: Optional[str]
    contratante: Optional[str]
    item: Optional[ItemResponse] = None
    
    class Config:
        from_attributes = True

class DisponibilidadeRequest(BaseModel):
    item_id: Optional[int] = None
    data_consulta: date
    filtro_localizacao: Optional[str] = None
    filtro_categoria: Optional[str] = None

class DisponibilidadeResponse(BaseModel):
    item: ItemResponse
    quantidade_total: int
    quantidade_comprometida: int
    quantidade_disponivel: int
    compromissos_ativos: List[CompromissoResponse] = []

# ============= HELPERS =============

def item_to_dict(item: Item) -> dict:
    """Converte Item SQLAlchemy para dict"""
    result = {
        "id": item.id,
        "nome": item.nome,
        "quantidade_total": item.quantidade_total,
        "categoria": item.categoria or "",
        "descricao": item.descricao,
        "cidade": item.cidade,
        "uf": item.uf,
        "endereco": item.endereco,
    }
    
    # Adiciona dados do carro se existir
    if hasattr(item, 'carro') and item.carro:
        result["carro"] = {
            "placa": item.carro.placa,
            "marca": item.carro.marca,
            "modelo": item.carro.modelo,
            "ano": item.carro.ano
        }
    
    # Adiciona dados_categoria se existir
    if hasattr(item, 'dados_categoria') and item.dados_categoria:
        result["dados_categoria"] = item.dados_categoria
    
    return result

def compromisso_to_dict(comp: Compromisso) -> dict:
    """Converte Compromisso SQLAlchemy para dict"""
    result = {
        "id": comp.id,
        "item_id": comp.item_id,
        "quantidade": comp.quantidade,
        "data_inicio": comp.data_inicio.isoformat() if isinstance(comp.data_inicio, date) else comp.data_inicio,
        "data_fim": comp.data_fim.isoformat() if isinstance(comp.data_fim, date) else comp.data_fim,
        "descricao": comp.descricao,
        "cidade": comp.cidade,
        "uf": comp.uf,
        "endereco": comp.endereco,
        "contratante": comp.contratante,
    }
    
    # Adiciona item se disponível
    if hasattr(comp, 'item') and comp.item:
        result["item"] = item_to_dict(comp.item)
    
    return result

# ============= AUTENTICAÇÃO =============

# Credenciais - lê do ambiente ou usa valores padrão
# O .env já foi carregado no início do arquivo
APP_USUARIO = os.getenv('APP_USUARIO', 'star')
APP_SENHA = os.getenv('APP_SENHA', 'maiko')

# Debug: mostra qual usuário está configurado (sem mostrar senha)
print(f"🔐 Credenciais carregadas - Usuário: {APP_USUARIO}")
if APP_USUARIO != 'star' or APP_SENHA != 'maiko':
    print("✅ Usando credenciais do .env ou variáveis de ambiente")
else:
    print("⚠️ Usando credenciais padrão (star/maiko)")

# Armazenamento simples de tokens (em produção, use Redis ou banco de dados)
active_tokens = {}

def generate_token():
    """Gera um token simples"""
    return secrets.token_urlsafe(32)

class LoginRequest(BaseModel):
    usuario: str
    senha: str

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    """Endpoint de login"""
    if credentials.usuario == APP_USUARIO and credentials.senha == APP_SENHA:
        token = generate_token()
        active_tokens[token] = {
            "usuario": credentials.usuario,
            "created_at": datetime.now()
        }
        return {
            "success": True,
            "token": token,
            "usuario": credentials.usuario
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos"
        )

@app.post("/api/auth/logout")
async def logout(token: str = Depends(HTTPBearer())):
    """Endpoint de logout"""
    token_value = token.credentials
    if token_value in active_tokens:
        del active_tokens[token_value]
    return {"success": True}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Verifica se o token é válido"""
    token = credentials.credentials
    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    return active_tokens[token]

# ============= ROTAS =============

@app.get("/")
async def root():
    """Informações sobre a API e status da conexão"""
    db_type = "Google Sheets" if USE_GOOGLE_SHEETS else "SQLite"
    info = {
        "message": "CRM Gestão de Estoque API",
        "version": "1.0.0",
        "database": db_type
    }
    if USE_GOOGLE_SHEETS and sheets_info:
        info["spreadsheet_url"] = sheets_info.get('spreadsheet_url', 'N/A')
        info["spreadsheet_id"] = sheets_info.get('spreadsheet_id', 'N/A')
    return info

@app.get("/api/health")
async def health():
    """Health check da API"""
    return {"status": "ok"}

@app.get("/api/debug")
async def debug():
    """Endpoint de debug para verificar conexão e dados"""
    try:
        db_type = "Google Sheets" if USE_GOOGLE_SHEETS else "SQLite"
        info = {
            "database_type": db_type,
            "use_google_sheets": USE_GOOGLE_SHEETS
        }
        
        if USE_GOOGLE_SHEETS and sheets_info:
            info["spreadsheet_url"] = sheets_info.get('spreadsheet_url', 'N/A')
            info["spreadsheet_id"] = sheets_info.get('spreadsheet_id', 'N/A')
        
        # Tentar contar itens e compromissos
        try:
            itens = db_module.listar_itens()
            compromissos = db_module.listar_compromissos()
            info["itens_count"] = len(itens)
            info["compromissos_count"] = len(compromissos)
            info["status"] = "connected"
        except Exception as e:
            info["status"] = "error"
            info["error"] = str(e)
            
        return info
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============= ITENS =============

@app.get("/api/itens", response_model=List[dict])
async def listar_itens():
    """Lista todos os itens"""
    try:
        if db_module is None:
            raise HTTPException(status_code=500, detail="Database module not initialized")
        itens = db_module.listar_itens()
        return [item_to_dict(item) for item in itens]
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/itens/{item_id}", response_model=dict)
async def buscar_item(item_id: int):
    """Busca um item por ID"""
    try:
        item = db_module.buscar_item_por_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return item_to_dict(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/itens", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_item(item: ItemCreate):
    """Cria um novo item"""
    try:
        novo_item = db_module.criar_item(
            nome=item.nome,
            quantidade_total=item.quantidade_total,
            categoria=item.categoria,
            descricao=item.descricao,
            cidade=item.cidade,
            uf=item.uf,
            endereco=item.endereco,
            placa=item.placa,
            marca=item.marca,
            modelo=item.modelo,
            ano=item.ano,
            campos_categoria=item.campos_categoria
        )
        return item_to_dict(novo_item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/itens/{item_id}", response_model=dict)
async def atualizar_item(item_id: int, item: ItemUpdate):
    """Atualiza um item existente"""
    try:
        item_atualizado = db_module.atualizar_item(
            item_id=item_id,
            nome=item.nome,
            quantidade_total=item.quantidade_total,
            categoria=item.categoria,
            descricao=item.descricao,
            cidade=item.cidade,
            uf=item.uf,
            endereco=item.endereco,
            placa=item.placa,
            marca=item.marca,
            modelo=item.modelo,
            ano=item.ano,
            campos_categoria=item.campos_categoria
        )
        if not item_atualizado:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return item_to_dict(item_atualizado)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_item(item_id: int):
    """Deleta um item"""
    try:
        sucesso = db_module.deletar_item(item_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= COMPROMISSOS =============

@app.get("/api/compromissos", response_model=List[dict])
async def listar_compromissos():
    """Lista todos os compromissos"""
    try:
        if db_module is None:
            raise HTTPException(status_code=500, detail="Database module not initialized")
        compromissos = db_module.listar_compromissos()
        return [compromisso_to_dict(comp) for comp in compromissos]
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/compromissos/{compromisso_id}", response_model=dict)
async def buscar_compromisso(compromisso_id: int):
    """Busca um compromisso por ID"""
    try:
        compromissos = db_module.listar_compromissos()
        comp = next((c for c in compromissos if c.id == compromisso_id), None)
        if not comp:
            raise HTTPException(status_code=404, detail="Compromisso não encontrado")
        return compromisso_to_dict(comp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compromissos", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_compromisso(compromisso: CompromissoCreate):
    """Cria um novo compromisso"""
    try:
        # Verifica disponibilidade antes de criar
        disponibilidade = db_module.verificar_disponibilidade_periodo(
            compromisso.item_id,
            compromisso.data_inicio,
            compromisso.data_fim
        )
        
        if disponibilidade['disponivel_minimo'] < compromisso.quantidade:
            raise HTTPException(
                status_code=400,
                detail=f"Quantidade insuficiente! Disponível: {disponibilidade['disponivel_minimo']}, Solicitado: {compromisso.quantidade}"
            )
        
        novo_compromisso = db_module.criar_compromisso(
            item_id=compromisso.item_id,
            quantidade=compromisso.quantidade,
            data_inicio=compromisso.data_inicio,
            data_fim=compromisso.data_fim,
            descricao=compromisso.descricao,
            cidade=compromisso.cidade,
            uf=compromisso.uf,
            endereco=compromisso.endereco,
            contratante=compromisso.contratante
        )
        return compromisso_to_dict(novo_compromisso)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/compromissos/{compromisso_id}", response_model=dict)
async def atualizar_compromisso(compromisso_id: int, compromisso: CompromissoUpdate):
    """Atualiza um compromisso existente"""
    try:
        # Busca compromisso atual
        compromissos = db_module.listar_compromissos()
        comp_atual = next((c for c in compromissos if c.id == compromisso_id), None)
        if not comp_atual:
            raise HTTPException(status_code=404, detail="Compromisso não encontrado")
        
        # Usa valores do compromisso atual se não fornecidos
        item_id = compromisso.item_id or comp_atual.item_id
        quantidade = compromisso.quantidade or comp_atual.quantidade
        data_inicio = compromisso.data_inicio or comp_atual.data_inicio
        data_fim = compromisso.data_fim or comp_atual.data_fim
        
        # Verifica disponibilidade se mudou período ou quantidade
        if compromisso.data_inicio or compromisso.data_fim or compromisso.quantidade:
            disponibilidade = db_module.verificar_disponibilidade_periodo(
                item_id,
                data_inicio,
                data_fim,
                excluir_compromisso_id=compromisso_id
            )
            
            if disponibilidade['disponivel_minimo'] < quantidade:
                raise HTTPException(
                    status_code=400,
                    detail=f"Quantidade insuficiente! Disponível: {disponibilidade['disponivel_minimo']}, Solicitado: {quantidade}"
                )
        
        compromisso_atualizado = db_module.atualizar_compromisso(
            compromisso_id=compromisso_id,
            item_id=item_id,
            quantidade=quantidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            descricao=compromisso.descricao,
            cidade=compromisso.cidade,
            uf=compromisso.uf,
            endereco=compromisso.endereco,
            contratante=compromisso.contratante
        )
        
        if not compromisso_atualizado:
            raise HTTPException(status_code=404, detail="Compromisso não encontrado")
        
        return compromisso_to_dict(compromisso_atualizado)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/compromissos/{compromisso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_compromisso(compromisso_id: int):
    """Deleta um compromisso"""
    try:
        sucesso = db_module.deletar_compromisso(compromisso_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Compromisso não encontrado")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= DISPONIBILIDADE =============

@app.post("/api/disponibilidade", response_model=dict)
async def verificar_disponibilidade(request: DisponibilidadeRequest):
    """Verifica disponibilidade de itens"""
    try:
        if request.item_id:
            # Verifica disponibilidade de um item específico
            disponibilidade = db_module.verificar_disponibilidade(
                request.item_id,
                request.data_consulta,
                request.filtro_localizacao
            )
            if not disponibilidade:
                raise HTTPException(status_code=404, detail="Item não encontrado")
            
            return {
                "item": item_to_dict(disponibilidade['item']),
                "quantidade_total": disponibilidade['quantidade_total'],
                "quantidade_comprometida": disponibilidade['quantidade_comprometida'],
                "quantidade_disponivel": disponibilidade['quantidade_disponivel'],
                "compromissos_ativos": [compromisso_to_dict(c) for c in disponibilidade.get('compromissos_ativos', [])]
            }
        else:
            # Verifica disponibilidade de todos os itens
            resultados = db_module.verificar_disponibilidade_todos_itens(
                request.data_consulta,
                request.filtro_localizacao
            )
            
            # Aplica filtro de categoria se fornecido
            if request.filtro_categoria:
                resultados = [
                    r for r in resultados
                    if getattr(r['item'], 'categoria', '') == request.filtro_categoria
                ]
            
            return {
                "resultados": [
                    {
                        "item": item_to_dict(r['item']),
                        "quantidade_total": r['quantidade_total'],
                        "quantidade_comprometida": r['quantidade_comprometida'],
                        "quantidade_disponivel": r['quantidade_disponivel']
                    }
                    for r in resultados
                ]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= CATEGORIAS E CAMPOS =============

@app.get("/api/categorias", response_model=List[str])
async def listar_categorias():
    """Lista todas as categorias disponíveis"""
    try:
        if db_module is None:
            raise HTTPException(status_code=500, detail="Database module not initialized")
        
        # Tenta usar obter_categorias se disponível (Google Sheets)
        if hasattr(db_module, 'obter_categorias'):
            categorias = db_module.obter_categorias()
        else:
            # Fallback: obtém categorias dos itens existentes (SQLite)
            itens = db_module.listar_itens()
            categorias = sorted(set([
                getattr(item, 'categoria', '') or ''
                for item in itens
                if getattr(item, 'categoria', '')
            ]))
        
        return categorias if categorias else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categorias/{categoria}/campos", response_model=List[str])
async def obter_campos_categoria(categoria: str):
    """Obtém os campos específicos de uma categoria"""
    try:
        if db_module is None:
            raise HTTPException(status_code=500, detail="Database module not initialized")
        
        # Tenta usar obter_campos_categoria se disponível (Google Sheets)
        if hasattr(db_module, 'obter_campos_categoria'):
            campos = db_module.obter_campos_categoria(categoria)
        else:
            # Fallback: retorna lista vazia para SQLite (não suporta campos dinâmicos)
            campos = []
        
        return campos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ESTATÍSTICAS =============

@app.get("/api/stats")
async def obter_estatisticas():
    """Retorna estatísticas gerais"""
    try:
        itens = db_module.listar_itens()
        compromissos = db_module.listar_compromissos()
        hoje = date.today()
        
        compromissos_ativos = [
            c for c in compromissos
            if c.data_inicio <= hoje <= c.data_fim
        ]
        
        compromissos_proximos = [
            c for c in compromissos
            if c.data_inicio <= hoje + timedelta(days=7) and c.data_inicio >= hoje
        ]
        
        compromissos_vencidos = [
            c for c in compromissos
            if c.data_fim < hoje
        ]
        
        total_quantidade_itens = sum(getattr(item, 'quantidade_total', 0) for item in itens)
        quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
        taxa_ocupacao = (quantidade_comprometida / total_quantidade_itens * 100) if total_quantidade_itens > 0 else 0
        
        # Estatísticas por categoria
        categorias_stats = {}
        for item in itens:
            cat = getattr(item, 'categoria', 'Sem Categoria') or 'Sem Categoria'
            if cat not in categorias_stats:
                categorias_stats[cat] = {'total': 0, 'quantidade': 0}
            categorias_stats[cat]['total'] += 1
            categorias_stats[cat]['quantidade'] += getattr(item, 'quantidade_total', 0)
        
        # Compromissos por mês (últimos 6 meses)
        compromissos_por_mes = {}
        for comp in compromissos:
            mes_key = comp.data_inicio.strftime('%Y-%m')
            if mes_key not in compromissos_por_mes:
                compromissos_por_mes[mes_key] = 0
            compromissos_por_mes[mes_key] += 1
        
        # Últimos 6 meses ordenados
        meses_ordenados = sorted(compromissos_por_mes.keys())[-6:]
        compromissos_mensais = [
            {
                'mes': datetime.strptime(mes, '%Y-%m').strftime('%b/%Y'),
                'total': compromissos_por_mes[mes]
            }
            for mes in meses_ordenados
        ]
        
        return {
            "total_itens": len(itens),
            "total_compromissos": len(compromissos),
            "compromissos_ativos": len(compromissos_ativos),
            "compromissos_proximos": len(compromissos_proximos),
            "compromissos_vencidos": len(compromissos_vencidos),
            "taxa_ocupacao": round(taxa_ocupacao, 2),
            "total_quantidade_itens": total_quantidade_itens,
            "quantidade_comprometida": quantidade_comprometida,
            "quantidade_disponivel": total_quantidade_itens - quantidade_comprometida,
            "categorias": categorias_stats,
            "compromissos_mensais": compromissos_mensais
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/info")
async def obter_info():
    """Retorna informações sobre a API e conexão"""
    try:
        db_type = "Google Sheets" if USE_GOOGLE_SHEETS else "SQLite"
        info = {
            "database": db_type,
            "use_google_sheets": USE_GOOGLE_SHEETS
        }
        if USE_GOOGLE_SHEETS and sheets_info:
            info["spreadsheet_url"] = sheets_info.get('spreadsheet_url', None)
            info["spreadsheet_id"] = sheets_info.get('spreadsheet_id', None)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
