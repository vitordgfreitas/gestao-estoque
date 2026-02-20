"""
Backend FastAPI para o CRM de Gestão de Estoque
"""
from fastapi import FastAPI, HTTPException, Depends, status, Body, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from types import SimpleNamespace
from datetime import date, datetime, timedelta
from typing import List, Optional
import os
import sys
import secrets
from pydantic import BaseModel

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# IMPORTANTE: No Render, as variáveis DEVEM estar no painel Settings → Environment
# O código lê DIRETAMENTE de os.getenv() - funciona tanto local quanto no Render
# Carrega .env apenas em desenvolvimento local (se existir)
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

try:
    from dotenv import load_dotenv
    # Só carrega .env se não estiver no Render (onde variáveis vêm do painel)
    if not os.getenv('RENDER'):
        # Tenta carregar .env da raiz do projeto
        env_path = os.path.join(root_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            if DEBUG_MODE:
                print(f"✅ Carregado .env da raiz: {env_path}")
        elif DEBUG_MODE:
            print(f"⚠️ Arquivo .env não encontrado em: {env_path}")
        
        # Também tenta carregar .env do backend
        backend_env = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(backend_env):
            load_dotenv(backend_env, override=True)
            if DEBUG_MODE:
                print(f"✅ Carregado .env do backend: {backend_env}")
except ImportError:
    if DEBUG_MODE:
        print("⚠️ python-dotenv não instalado. Instale com: pip install python-dotenv")
except Exception as e:
    if DEBUG_MODE:
        print(f"⚠️ Erro ao carregar .env: {e}")

from models import Item, Compromisso, Carro
import auditoria
# Importa módulo de backup
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
try:
    import backup
except ImportError:
    backup = None

# Escolhe qual banco de dados usar baseado em variável de ambiente
# Por padrão, tenta usar Google Sheets (mesmo comportamento do Streamlit)
USE_GOOGLE_SHEETS = os.getenv('USE_GOOGLE_SHEETS', 'true').lower() == 'true'

# Supabase: carregado opcionalmente; o frontend pode alternar via header X-Use-Database: supabase
db_module_supabase = None
SUPABASE_AVAILABLE = False
if os.getenv('SUPABASE_URL') and (os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')):
    try:
        import supabase_database as db_module_supabase
        SUPABASE_AVAILABLE = True
        if DEBUG_MODE:
            print("✅ Supabase disponível (use header X-Use-Database: supabase para alternar)")
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Supabase não carregado: {e}")
        db_module_supabase = None

# Inicializa o módulo de banco de dados apropriado (padrão: Sheets ou SQLite)
db_module = None
sheets_info = None

if USE_GOOGLE_SHEETS:
    try:
        import sheets_database as db_module
        # Tenta inicializar Google Sheets
        try:
            sheets_info = db_module.get_sheets()
            spreadsheet_url = sheets_info.get('spreadsheet_url', 'N/A')
            if DEBUG_MODE:
                print(f"✅ Conectado ao Google Sheets: {spreadsheet_url}")
        except FileNotFoundError as e:
            error_msg = str(e)
            print(f"❌ Erro: Arquivo credentials.json não encontrado!")
            if DEBUG_MODE:
                print(f"   {error_msg}")
                print(f"   Por favor, coloque o arquivo credentials.json na raiz do projeto.")
            print("⚠️ Tentando usar SQLite como fallback...")
            USE_GOOGLE_SHEETS = False
            from models import init_db
            import database as db_module
            init_db()
            if DEBUG_MODE:
                print("✅ Usando SQLite local")
        except Exception as e:
            error_msg = str(e)
            import traceback
            print(f"⚠️ Aviso: Erro ao conectar ao Google Sheets")
            if DEBUG_MODE:
                print(f"   Detalhes: {error_msg}")
                print(f"   Traceback completo:")
                traceback.print_exc()
            print("⚠️ Tentando usar SQLite como fallback...")
            USE_GOOGLE_SHEETS = False
            from models import init_db
            import database as db_module
            init_db()
            if DEBUG_MODE:
                print("✅ Usando SQLite local")
    except ImportError as e:
        print(f"❌ Erro ao importar sheets_database: {str(e)}")
        print("⚠️ Usando SQLite como fallback...")
        USE_GOOGLE_SHEETS = False
        from models import init_db
        import database as db_module
        init_db()
        if DEBUG_MODE:
            print("✅ Usando SQLite local")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        print("⚠️ Usando SQLite como fallback...")
        USE_GOOGLE_SHEETS = False
        from models import init_db
        import database as db_module
        init_db()
        if DEBUG_MODE:
            print("✅ Usando SQLite local")
else:
    from models import init_db
    import database as db_module
    init_db()
    if DEBUG_MODE:
        print("✅ Usando SQLite local (USE_GOOGLE_SHEETS=false)")

app = FastAPI(
    title="CRM Gestão de Estoque",
    description="API para sistema de gestão de estoque e aluguéis",
    version="1.0.0"
)

# Limpa cache ao iniciar (força recarregamento dos dados)
@app.on_event("startup")
async def startup_event():
    """Executado quando o servidor inicia"""
    if USE_GOOGLE_SHEETS:
        try:
            print("[STARTUP] Limpando cache de dados...")
            db_module._clear_cache()
            print("[STARTUP] Cache limpo com sucesso")
        except Exception as e:
            print(f"[STARTUP] Erro ao limpar cache: {e}")

# Middleware adicional para garantir CORS e seleção de banco (Supabase vs Sheets)
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Adiciona headers CORS e define db_module por request (toggle Supabase)."""
    # Se for OPTIONS (preflight), retorna imediatamente com headers CORS
    if request.method == "OPTIONS":
        return JSONResponse(
            content={"message": "OK"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "3600",
            }
        )
    # Define qual banco usar neste request (header X-Use-Database: supabase | sheets)
    use_db = request.headers.get("X-Use-Database", "").strip().lower()
    if use_db == "supabase" and db_module_supabase is not None:
        request.state.db_module = db_module_supabase
    else:
        request.state.db_module = db_module
    # Processa request normal
    response = await call_next(request)
    
    # Adiciona headers CORS na resposta
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    
    return response

# Handler explícito para OPTIONS (preflight requests)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handler para requisições OPTIONS (preflight)"""
    return {"message": "OK"}

# CORS - permite requisições do frontend
# Em desenvolvimento, permite qualquer origem localhost
is_production = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER')
if not is_production:
    # Desenvolvimento: permite qualquer porta do localhost
    allow_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
    ]
    print(f"[CORS] Modo desenvolvimento - Origens permitidas: {allow_origins}")
else:
    # Produção: permite o frontend do Render
    # Usa wildcard temporariamente para garantir que funcione
    allow_origins = ["*"]  # Permite qualquer origem (temporário para debug)
    
    print(f"[CORS] Modo produção - CORS configurado para aceitar qualquer origem (wildcard)")
    print(f"[CORS] RENDER env: {os.getenv('RENDER')}")
    print(f"[CORS] FRONTEND_URL env: {os.getenv('FRONTEND_URL')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False if allow_origins == ["*"] else True,  # credentials=False quando wildcard
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight por 1 hora
)

# Security
security = HTTPBearer()

# Dependência para obter o db_module do request (permite toggle Supabase via header X-Use-Database)
def get_db(request: Request):
    return getattr(request.state, "db_module", db_module)

# Tratador global: retorna a mensagem de erro real no 500 para facilitar debug
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    err_msg = str(exc)
    err_type = type(exc).__name__
    tb = traceback.format_exc()
    if os.getenv('RENDER'):
        print(f"[500] {err_type}: {err_msg}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": err_msg,
            "error_type": err_type,
            "hint": (
                "Se estiver usando Supabase: verifique SUPABASE_URL e SUPABASE_SERVICE_KEY no Render, "
                "se rodou o supabase_schema.sql no Supabase e se o pacote 'supabase' está no requirements.txt. "
                "Se estiver usando Google Sheets: verifique GOOGLE_CREDENTIALS e quota."
            ),
        },
    )

# ============= MODELS PYDANTIC =============

class ItemCreate(BaseModel):
    nome: str
    quantidade_total: int
    categoria: str = "Estrutura de Evento"
    descricao: Optional[str] = None
    cidade: str
    uf: str
    endereco: Optional[str] = None
    valor_compra: Optional[float] = 0.0 # Agora o maestro reconhece essa nota
    data_aquisicao: Optional[date] = None
    campos_categoria: Optional[dict] = None

class ItemUpdate(BaseModel):
    nome: Optional[str] = None
    quantidade_total: Optional[int] = None
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    valor_compra: Optional[float] = None
    data_aquisicao: Optional[date] = None
    # CAMPOS ESSENCIAIS PARA CARROS:
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
    valor_compra: float = 0.0 # Adicionado para o Front conseguir ler
    data_aquisicao: Optional[date] = None # Adicionado para o Front conseguir ler
    carro: Optional[dict] = None
    dados_categoria: Optional[dict] = None
    
    class Config:
        from_attributes = True

class ItemAluguel(BaseModel):
    item_id: int
    quantidade: int

class CompromissoCreate(BaseModel):
    nome_contrato: str  # Nome identificador do contrato
    contratante: str
    data_inicio: date
    data_fim: date
    descricao: Optional[str] = None
    cidade: str
    uf: str
    endereco: Optional[str] = None
    valor_total_contrato: float = 0.0
    # A LISTA DE ITENS AGORA VEM AQUI:
    itens: List[ItemAluguel]

class ItemAluguelUpdate(BaseModel):
    id: Optional[int] = None      # Aceita 'id' vindo do front
    item_id: Optional[int] = None # Aceita 'item_id' vindo do front
    quantidade: int

class CompromissoUpdateMaster(BaseModel):
    nome_contrato: Optional[str] = None
    contratante: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    descricao: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    valor_total_contrato: Optional[float] = None
    itens: Optional[List[ItemAluguelUpdate]] = None

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
    itens: List[dict] = []
    
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
    quantidade_instalada: int
    quantidade_disponivel: int
    compromissos_ativos: List[CompromissoResponse] = []

# ============= MODELOS FINANCEIRO =============

class ContaReceberCreate(BaseModel):
    compromisso_id: int
    descricao: str
    valor: float
    data_vencimento: date
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

class ContaReceberUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    status: Optional[str] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

class ContaReceberResponse(BaseModel):
    id: int
    compromisso_id: int
    descricao: str
    valor: float
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    
    class Config:
        from_attributes = True

class ContaPagarCreate(BaseModel):
    descricao: str
    categoria: str
    valor: float
    data_vencimento: date
    fornecedor: Optional[str] = None
    item_id: Optional[int] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

class ContaPagarUpdate(BaseModel):
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    status: Optional[str] = None
    fornecedor: Optional[str] = None
    item_id: Optional[int] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

class ContaPagarResponse(BaseModel):
    id: int
    descricao: str
    categoria: str
    valor: float
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str
    fornecedor: Optional[str] = None
    item_id: Optional[int] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    
    class Config:
        from_attributes = True

class DashboardFinanceiroResponse(BaseModel):
    saldo_atual: float
    receitas_mes: float
    despesas_mes: float
    saldo_previsto: float
    contas_vencidas: int
    contas_a_vencer_7_dias: int
    receitas_pendentes: float
    despesas_pendentes: float

class FluxoCaixaResponse(BaseModel):
    mes: str
    receitas: float
    despesas: float
    saldo: float

# ============= MODELOS FINANCIAMENTO =============

class ParcelaCustomizada(BaseModel):
    numero: int
    valor: float
    data_vencimento: date

class ParcelaUpdate(BaseModel):
    status: Optional[str] = None
    link_boleto: Optional[str] = None
    link_comprovante: Optional[str] = None
    valor_original: Optional[float] = None
    data_vencimento: Optional[date] = None

class FinanciamentoCreate(BaseModel):
    itens_ids: Optional[List[int]] = None  # NOVO: múltiplos itens (apenas IDs)
    item_id: Optional[int] = None  # Compatibilidade reversa (deprecated)
    codigo_contrato: Optional[str] = None  # Código do contrato
    valor_total: float  # Valor total do bem
    valor_entrada: Optional[float] = 0.0  # Valor de entrada dado
    numero_parcelas: int
    taxa_juros: float  # Taxa de juros mensal em decimal (0.02 = 2%)
    data_inicio: date
    instituicao_financeira: Optional[str] = None
    observacoes: Optional[str] = None
    parcelas_customizadas: Optional[List[ParcelaCustomizada]] = None

class FinanciamentoUpdate(BaseModel):
    valor_total: Optional[float] = None
    valor_entrada: Optional[float] = None
    taxa_juros: Optional[float] = None
    status: Optional[str] = None
    instituicao_financeira: Optional[str] = None
    observacoes: Optional[str] = None

class FinanciamentoResponse(BaseModel):
    id: int
    item_id: int
    valor_total: float
    valor_entrada: float
    valor_financiado: float
    numero_parcelas: int
    valor_parcela: float
    taxa_juros: float
    data_inicio: date
    status: str
    instituicao_financeira: Optional[str] = None
    observacoes: Optional[str] = None
    
    class Config:
        from_attributes = True

class ParcelaFinanciamentoResponse(BaseModel):
    id: int
    financiamento_id: int
    numero_parcela: int
    valor_original: float
    valor_pago: float
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str
    juros: float
    multa: float
    desconto: float
    
    class Config:
        from_attributes = True

class PagarParcelaRequest(BaseModel):
    valor_pago: float
    data_pagamento: Optional[date] = None
    juros: Optional[float] = 0.0
    multa: Optional[float] = 0.0
    desconto: Optional[float] = 0.0

class ValorPresenteResponse(BaseModel):
    valor_presente: float
    taxa_desconto: float
    parcelas_restantes: int
    valor_total_restante: float

# ============= HELPERS =============

def item_to_dict(item: Item) -> dict:
    """Converte Item para dict, blindando contra erro de datas no JSON"""
    if not item: return {}
    
    # Pegamos os dados do objeto. Se for Supabase, ele tem esses atributos:
    result = {
        "id": getattr(item, 'id', None),
        "nome": getattr(item, 'nome', ''),
        "quantidade_total": int(getattr(item, 'quantidade_total', 0)),
        "categoria": getattr(item, 'categoria', '') or "",
        "descricao": getattr(item, 'descricao', ''),
        "cidade": getattr(item, 'cidade', ''),
        "uf": getattr(item, 'uf', ''),
        "endereco": getattr(item, 'endereco', ''),
        "valor_compra": float(getattr(item, 'valor_compra', 0.0) or 0.0),
    }

    # --- O PULO DO GATO: TRATAMENTO DE DATA ---
    data_aq = getattr(item, 'data_aquisicao', None)
    if data_aq:
        # Se for um objeto de data real, transforma em texto "2026-02-12"
        result["data_aquisicao"] = data_aq.isoformat() if hasattr(data_aq, 'isoformat') else str(data_aq)
    else:
        result["data_aquisicao"] = None

    # Mantém os dados dinâmicos
    if hasattr(item, 'dados_categoria'):
        result["dados_categoria"] = item.dados_categoria

    # Mantém a lógica de carro para o front não quebrar
    if hasattr(item, 'carro') and item.carro:
        result["carro"] = {
            "placa": getattr(item.carro, 'placa', ''),
            "marca": getattr(item.carro, 'marca', ''),
            "modelo": getattr(item.carro, 'modelo', ''),
            "ano": getattr(item.carro, 'ano', 0)
        }
    
    return result

def compromisso_to_dict(comp: Compromisso) -> dict:
    """Converte Compromisso para dict, tratando datas para o JSON"""
    if not comp: return {}
    
    # Garantimos que as datas virem texto (ISO format)
    d_inicio = comp.data_inicio.isoformat() if hasattr(comp.data_inicio, 'isoformat') else str(comp.data_inicio)
    d_fim = comp.data_fim.isoformat() if hasattr(comp.data_fim, 'isoformat') else str(comp.data_fim)

    result = {
        "id": comp.id,
        "item_id": comp.item_id,
        "quantidade": comp.quantidade,
        "data_inicio": d_inicio,
        "data_fim": d_fim,
        "descricao": comp.descricao or "",
        "cidade": comp.cidade or "",
        "uf": comp.uf or "",
        "endereco": comp.endereco or "",
        "contratante": comp.contratante or "",
    }
    
    # Se o compromisso carregar o item junto, usamos o item_to_dict que já corrigimos
    if hasattr(comp, 'item') and comp.item:
        result["item"] = item_to_dict(comp.item)
    
    return result

# ============= AUTENTICAÇÃO =============

# Credenciais - lê DIRETAMENTE do ambiente (Render ou .env)
# IMPORTANTE: NUNCA use valores padrão hardcoded em produção!
# No Render: configure em Settings → Environment → Add Environment Variable
app_usuario_raw = os.getenv('APP_USUARIO')
app_senha_raw = os.getenv('APP_SENHA')

# Verifica se está em produção (Render, Heroku, etc)
# Render define várias variáveis, vamos verificar todas
is_production = (
    os.getenv('RENDER') is not None or 
    os.getenv('DYNO') is not None or
    os.getenv('RENDER_SERVICE_NAME') is not None or
    os.getenv('RENDER_EXTERNAL_URL') is not None or
    os.getenv('RAILWAY_ENVIRONMENT') is not None or  # Variável padrão do Railway
    os.getenv('RAILWAY_STATIC_URL') is not None 
)

if is_production:
    # Em produção, EXIGE que as variáveis estejam configuradas
    if not app_usuario_raw or not app_senha_raw:
        raise ValueError(
            "ERRO CRÍTICO: APP_USUARIO e APP_SENHA devem estar configuradas no Render!\n"
            "Configure em: Settings → Environment → Add Environment Variable"
        )
    APP_USUARIO = app_usuario_raw.strip() if app_usuario_raw else ""
    APP_SENHA = app_senha_raw.strip() if app_senha_raw else ""
else:
    # Em desenvolvimento local
    if not app_usuario_raw or not app_senha_raw:
        raise ValueError(
            "APP_USUARIO e APP_SENHA devem estar configuradas no arquivo .env "
            "ou como variáveis de ambiente."
        )
    APP_USUARIO = app_usuario_raw.strip()
    APP_SENHA = app_senha_raw.strip()

# Cache de tokens válidos (em produção, considere Redis)
active_tokens = {}

def generate_token():
    """Gera um token seguro"""
    return secrets.token_urlsafe(32)

class LoginRequest(BaseModel):
    usuario: str
    senha: str

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    """Endpoint de login otimizado"""
    usuario_recebido = credentials.usuario.strip() if credentials.usuario else ""
    senha_recebida = credentials.senha.strip() if credentials.senha else ""
    usuario_esperado = APP_USUARIO.strip() if APP_USUARIO else ""
    senha_esperada = APP_SENHA.strip() if APP_SENHA else ""
    
    if usuario_recebido == usuario_esperado and senha_recebida == senha_esperada:
        token = generate_token()
        active_tokens[token] = {
            "usuario": credentials.usuario,
            "created_at": datetime.now()
        }
        print(f"[LOGIN] ✅ Login bem-sucedido para usuario: {usuario_recebido}")
        return {
            "success": True,
            "token": token,
            "usuario": credentials.usuario
        }
    else:
        print(f"[LOGIN] ❌ Login FALHOU - Credenciais incorretas")
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
async def root(db_module = Depends(get_db)):
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
async def health(db_module = Depends(get_db)):
    """Health check da API"""
    return {"status": "ok"}

@app.get("/api/debug")
async def debug(db_module = Depends(get_db)):
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
async def listar_itens(db_module = Depends(get_db)):
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

@app.get("/api/itens/buscar", response_model=dict)
async def buscar_itens(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    cidade: Optional[str] = None,
    uf: Optional[str] = None,
    ordenar_por: Optional[str] = "nome",
    ordem: Optional[str] = "asc",
    pagina: Optional[int] = 1,
    por_pagina: Optional[int] = 50,
    db_module = Depends(get_db)
):
    """Busca avançada de itens com filtros e paginação"""
    try:
        itens = db_module.listar_itens()
        
        # Aplica filtros
        itens_filtrados = itens
        
        if q:
            q_lower = q.lower()
            itens_filtrados = [
                item for item in itens_filtrados
                if q_lower in (item.nome or '').lower() or
                   q_lower in (item.categoria or '').lower() or
                   q_lower in (item.descricao or '').lower() or
                   q_lower in (item.cidade or '').lower()
            ]
        
        if categoria:
            itens_filtrados = [item for item in itens_filtrados if (item.categoria or '').strip() == categoria.strip()]
        
        if cidade:
            itens_filtrados = [item for item in itens_filtrados if (item.cidade or '').lower() == cidade.lower()]
        
        if uf:
            itens_filtrados = [item for item in itens_filtrados if (item.uf or '').upper() == uf.upper()]
        
        # Ordenação
        reverse_order = ordem.lower() == 'desc'
        if ordenar_por == 'nome':
            itens_filtrados.sort(key=lambda x: (x.nome or '').lower(), reverse=reverse_order)
        elif ordenar_por == 'categoria':
            itens_filtrados.sort(key=lambda x: (x.categoria or '').lower(), reverse=reverse_order)
        elif ordenar_por == 'quantidade':
            itens_filtrados.sort(key=lambda x: x.quantidade_total or 0, reverse=reverse_order)
        elif ordenar_por == 'cidade':
            itens_filtrados.sort(key=lambda x: (x.cidade or '').lower(), reverse=reverse_order)
        
        # Paginação
        total = len(itens_filtrados)
        inicio = (pagina - 1) * por_pagina
        fim = inicio + por_pagina
        itens_paginados = itens_filtrados[inicio:fim]
        
        return {
            "itens": [item_to_dict(item) for item in itens_paginados],
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/itens/{item_id}", response_model=dict)
async def buscar_item(item_id: int, db_module = Depends(get_db)):
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

from fastapi.encoders import jsonable_encoder # <--- Adicione este import

@app.post("/api/itens")
async def create_item(item: ItemCreate, db_module = Depends(get_db)):
    try:
        # Pega o valor_compra garantindo que seja float
        val_compra = float(item.valor_compra) if item.valor_compra is not None else 0.0
        
        novo_item = db_module.criar_item(
            nome=item.nome,
            quantidade_total=item.quantidade_total,
            categoria=item.categoria,
            descricao=item.descricao,
            cidade=item.cidade,
            uf=item.uf,
            endereco=item.endereco,
            valor_compra=val_compra, 
            data_aquisicao=item.data_aquisicao, # O db_module agora vai limpar isso
            campos_categoria=item.campos_categoria
        )
        
        # O jsonable_encoder é a proteção final contra erros de serialização
        return JSONResponse(content=jsonable_encoder(item_to_dict(novo_item)))
        
    except Exception as e:
        print(f"ERRO CRITICAL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/itens/{item_id}")
async def atualizar_item(item_id: int, item: ItemUpdate, db_module = Depends(get_db)):
    try:
        # Usamos o .dict() para passar os campos com segurança para o db_module
        item_data = item.dict(exclude_unset=True)
        
        item_atualizado = db_module.atualizar_item(
            item_id=item_id,
            **item_data # Isso passa placa, marca, etc., se existirem no objeto
        )
        
        if not item_atualizado:
            raise HTTPException(status_code=404, detail="Item não encontrado")
            
        return item_to_dict(item_atualizado)
    except Exception as e:
        print(f"❌ ERRO UPDATE: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_item(item_id: int, db_module = Depends(get_db)):
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

from types import SimpleNamespace # Importe no topo do arquivo

from types import SimpleNamespace
from typing import List

@app.get("/api/compromissos", response_model=List[dict])
async def listar_compromissos(db_module = Depends(get_db)):
    """Lista compromissos injetando o nome real e blindando o tradutor legado"""
    try:
        compromissos_brutos = db_module.listar_compromissos()
        
        resultado_final = []
        for comp_raw in compromissos_brutos:
            patch = {"item_id": 0, "quantidade": 0, **comp_raw}
            comp_obj = SimpleNamespace(**patch)
            d = compromisso_to_dict(comp_obj)
            
            # 2. PRIORIDADE TOTAL: Forçamos o nome real da coluna do banco
            # Se a coluna nome_contrato existir e tiver texto, ela MANDA.
            nome_real = comp_raw.get('nome_contrato')
            d['nome_contrato'] = nome_real if nome_real and str(nome_real).strip() else f"Contrato #{comp_raw.get('id')}"
            
            # SOBREPOSIÇÃO MANUAL: Garante que os dados do seu schema novo cheguem ao front
            # O seu compromisso_to_dict ignorava essas chaves
            d['valor_total_contrato'] = float(comp_raw.get('valor_total_contrato') or 0)
            d['compromisso_itens'] = comp_raw.get('compromisso_itens', [])
            
            resultado_final.append(d)
            
        return resultado_final
    except Exception as e:
        print(f"❌ ERRO LISTAR COMPROMISSOS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compromissos/buscar", response_model=dict)
async def buscar_compromissos(
    q: Optional[str] = None,
    item_id: Optional[int] = None,
    data_inicio_min: Optional[date] = None,
    data_inicio_max: Optional[date] = None,
    data_fim_min: Optional[date] = None,
    data_fim_max: Optional[date] = None,
    cidade: Optional[str] = None,
    uf: Optional[str] = None,
    contratante: Optional[str] = None,
    ordenar_por: Optional[str] = "data_inicio",
    ordem: Optional[str] = "asc",
    pagina: Optional[int] = 1,
    por_pagina: Optional[int] = 50,
    db_module = Depends(get_db)
):
    """Busca avançada de compromissos com filtros e paginação"""
    try:
        compromissos = db_module.listar_compromissos()
        
        # Aplica filtros
        compromissos_filtrados = compromissos
        
        if q:
            q_lower = q.lower()
            compromissos_filtrados = [
                comp for comp in compromissos_filtrados
                if q_lower in (comp.contratante or '').lower() or
                   q_lower in (comp.descricao or '').lower() or
                   (comp.item and q_lower in (comp.item.nome or '').lower())
            ]
        
        if item_id:
            compromissos_filtrados = [comp for comp in compromissos_filtrados if comp.item_id == item_id]
        
        if data_inicio_min:
            compromissos_filtrados = [
                comp for comp in compromissos_filtrados
                if isinstance(comp.data_inicio, date) and comp.data_inicio >= data_inicio_min
            ]
        
        if data_inicio_max:
            compromissos_filtrados = [
                comp for comp in compromissos_filtrados
                if isinstance(comp.data_inicio, date) and comp.data_inicio <= data_inicio_max
            ]
        
        if data_fim_min:
            compromissos_filtrados = [
                comp for comp in compromissos_filtrados
                if isinstance(comp.data_fim, date) and comp.data_fim >= data_fim_min
            ]
        
        if data_fim_max:
            compromissos_filtrados = [
                comp for comp in compromissos_filtrados
                if isinstance(comp.data_fim, date) and comp.data_fim <= data_fim_max
            ]
        
        if cidade:
            compromissos_filtrados = [comp for comp in compromissos_filtrados if (comp.cidade or '').lower() == cidade.lower()]
        
        if uf:
            compromissos_filtrados = [comp for comp in compromissos_filtrados if (comp.uf or '').upper() == uf.upper()]
        
        if contratante:
            compromissos_filtrados = [comp for comp in compromissos_filtrados if (comp.contratante or '').lower() == contratante.lower()]
        
        # Ordenação
        reverse_order = ordem.lower() == 'desc'
        if ordenar_por == 'data_inicio':
            compromissos_filtrados.sort(key=lambda x: x.data_inicio if isinstance(x.data_inicio, date) else date.min, reverse=reverse_order)
        elif ordenar_por == 'data_fim':
            compromissos_filtrados.sort(key=lambda x: x.data_fim if isinstance(x.data_fim, date) else date.min, reverse=reverse_order)
        elif ordenar_por == 'quantidade':
            compromissos_filtrados.sort(key=lambda x: x.quantidade or 0, reverse=reverse_order)
        elif ordenar_por == 'contratante':
            compromissos_filtrados.sort(key=lambda x: (x.contratante or '').lower(), reverse=reverse_order)
        
        # Paginação
        total = len(compromissos_filtrados)
        inicio = (pagina - 1) * por_pagina
        fim = inicio + por_pagina
        compromissos_paginados = compromissos_filtrados[inicio:fim]
        
        return {
            "compromissos": [compromisso_to_dict(comp) for comp in compromissos_paginados],
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compromissos/{compromisso_id}", response_model=dict)
async def buscar_compromisso(compromisso_id: int, db_module = Depends(get_db)):
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

@app.post("/api/compromissos", status_code=status.HTTP_201_CREATED)
async def criar_compromisso(
    compromisso_in: CompromissoCreate, 
    db_module = Depends(get_db)
):
    try:
        # 1. Transformamos o modelo Pydantic em um dicionário puro
        # Usamos o .dict() para que a função do banco receba chaves e não atributos
        dados_completos = compromisso_in.dict()
        
        # 2. Separamos os itens do cabeçalho
        # Removemos 'itens' do dicionário principal para passar como argumento separado
        lista_itens = dados_completos.pop('itens', [])
        dados_header = dados_completos
        
        # 3. Chamamos a função master do banco
        # Ela agora vai receber: 
        # dados_header -> {'nome_contrato': '...', 'data_inicio': '...', etc}
        # lista_itens  -> [{'item_id': 1, 'quantidade': 10}, ...]
        novo_contrato = db_module.criar_compromisso_master(dados_header, lista_itens)
        
        if not novo_contrato:
            raise HTTPException(status_code=400, detail="Erro ao criar contrato")
            
        # 4. Retornamos usando o tradutor blindado que já ajustamos
        return compromisso_to_dict(novo_contrato)

    except Exception as e:
        print(f"❌ ERRO NA ROTA CRIAR COMPROMISSO: {str(e)}")
        # Tratamento amigável para erro de estoque
        if "Estoque insuficiente" in str(e) or "Conflito" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/compromissos/{compromisso_id}")
async def atualizar_compromisso(compromisso_id: int, comp_in: CompromissoUpdateMaster, db_module = Depends(get_db)):
    try:
        # Extrai e normaliza a lista de itens (converte 'id' para 'item_id')
        lista_itens = None
        if comp_in.itens is not None:
            lista_itens = []
            for i in comp_in.itens:
                # Normalização: O banco quer 'item_id', o front pode mandar 'id'
                it_id = i.id if i.id is not None else i.item_id
                if it_id:
                    lista_itens.append({"item_id": it_id, "quantidade": i.quantidade})
            
        # Extrai o cabeçalho excluindo os itens
        dados_header = comp_in.dict(exclude={'itens'}, exclude_unset=True)
        
        # Chama a sua função master que já existe no db_module
        atualizado = db_module.atualizar_compromisso_master(compromisso_id, dados_header, lista_itens)
        
        # Retorno usando o mesmo remendo da listagem para manter o nome no front
        return {"status": "success", "id": compromisso_id}
    except ValueError as e:
        # 3. TRATAMENTO DE CONFLITO: Transforma o erro de estoque em um 400 amigável
        # Isso faz com que o Toast no React mostre a frase "Conflito de estoque..."
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ ERRO UPDATE COMPROMISSO: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
@app.delete("/api/compromissos/{compromisso_id}")
async def excluir_compromisso(compromisso_id: int, db_module = Depends(get_db)):
    try:
        resultado = db_module.deletar_compromisso(compromisso_id)
        if not resultado:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        return {"status": "success", "message": "Contrato e itens removidos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ============= DISPONIBILIDADE =============

from typing import Optional # Adicione no topo se não tiver

@app.get("/api/disponibilidade")
async def verificar_disponibilidade(
    item_id: Optional[int] = None, 
    data_consulta: Optional[str] = None, 
    data_inicio: Optional[str] = None, 
    data_fim: Optional[str] = None,
    filtro_categoria: Optional[str] = None, 
    filtro_localizacao: Optional[str] = None,
    db_module = Depends(get_db)
):
    try:
        # Mapeamento de Datas: 
        # Se vier data_consulta (Dashboard), usamos ela como início e fim.
        # Se vierem data_inicio/fim (Registro), usamos elas.
        inicio = data_inicio or data_consulta
        fim = data_fim or data_consulta

        if not inicio:
            raise HTTPException(status_code=400, detail="Data não informada")

        # 1. CASO: CONSULTA DE ITEM ESPECÍFICO (Seja no Dashboard ou no Registro)
        if item_id:
            resultado = db_module.verificar_disponibilidade_periodo(
                item_id=item_id,
                data_inicio=inicio,
                data_fim=fim
            )
            
            if not resultado:
                raise HTTPException(status_code=404, detail="Item não encontrado")
            
            return {
                "item": item_to_dict(resultado['item']),
                "quantidade_total": resultado['quantidade_total'],
                "max_comprometido": resultado['max_comprometido'],
                "quantidade_comprometida": resultado['qtd_alugada'], # <--- AQUI
                "quantidade_instalada": resultado['qtd_instalada'],
                "quantidade_disponivel": resultado['disponivel_minimo'], # Chave para o Front
                "compromissos_ativos": [compromisso_to_dict(c) for c in resultado.get('compromissos_atuais', [])]
            }
            
        # 2. CASO: DASHBOARD "VER TUDO" (item_id é None)
        else:
            resultados = db_module.verificar_disponibilidade_todos_itens(
                inicio, # Usando a data tratada
                filtro_localizacao
            )
            
            if filtro_categoria and filtro_categoria != 'Todas as Categorias':
                resultados = [
                    r for r in resultados
                    if getattr(r['item'], 'categoria', '') == filtro_categoria
                ]
            
            return {
                "resultados": [
                    {
                        "item": item_to_dict(r['item']),
                        "quantidade_total": r['quantidade_total'],
                        "quantidade_comprometida": r['quantidade_comprometida'],
                        "quantidade_disponivel": r['quantidade_disponivel']
                    } for r in resultados
                ]
            }

    except Exception as e:
        print(f"❌ ERRO 422/500 DISPONIBILIDADE: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= CATEGORIAS E CAMPOS =============

@app.get("/api/categorias", response_model=List[str])
async def listar_categorias(db_module = Depends(get_db)):
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

@app.post("/api/categorias", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_categoria(nome_categoria: str = Body(..., embed=True), token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Cria uma nova categoria e sua aba correspondente no Google Sheets"""
    try:
        if db_module is None:
            raise HTTPException(status_code=500, detail="Database module not initialized")
        
        # Validação
        if not nome_categoria or not nome_categoria.strip():
            raise HTTPException(status_code=400, detail="Nome da categoria não pode ser vazio")
        
        nome_categoria = nome_categoria.strip()
        
        # Verifica se categoria já existe
        if hasattr(db_module, 'obter_categorias'):
            categorias_existentes = db_module.obter_categorias()
            if nome_categoria in categorias_existentes:
                raise HTTPException(status_code=400, detail=f"Categoria '{nome_categoria}' já existe")
        
        # Cria categoria na tabela Categorias_Itens e aba no Google Sheets
        if hasattr(db_module, 'criar_categoria'):
            categoria_id = db_module.criar_categoria(nome_categoria)
            if categoria_id:
                return {
                    "success": True,
                    "message": f"Categoria '{nome_categoria}' criada com sucesso",
                    "categoria": nome_categoria,
                    "id": categoria_id
                }
            else:
                raise HTTPException(status_code=500, detail="Erro ao criar categoria")
        else:
            # Para SQLite, apenas retorna sucesso (categorias são criadas automaticamente ao adicionar item)
            return {
                "success": True,
                "message": f"Categoria '{nome_categoria}' será criada ao adicionar o primeiro item",
                "categoria": nome_categoria
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categorias/{categoria}/campos", response_model=List[str])
async def obter_campos_categoria(categoria: str, db_module = Depends(get_db)):
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
async def obter_estatisticas(db_module = Depends(get_db)):
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

@app.get("/api/auditoria/{tabela}/{registro_id}", response_model=dict)
async def obter_historico_auditoria(tabela: str, registro_id: int, db_module = Depends(get_db)):
    """Obtém histórico de mudanças de um registro"""
    try:
        historico = auditoria.obter_historico(tabela, registro_id)
        return {"historico": historico}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup/criar", response_model=dict)
async def criar_backup(db_module = Depends(get_db)):
    """Cria backup manual da planilha"""
    try:
        if backup is None:
            raise HTTPException(status_code=501, detail="Módulo de backup não disponível")
        resultado = backup.criar_backup_google_sheets()
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backup/listar", response_model=dict)
async def listar_backups(max_backups: Optional[int] = 50, db_module = Depends(get_db)):
    """Lista backups disponíveis"""
    try:
        if backup is None:
            return {"backups": [], "total": 0}
        backups = backup.listar_backups(max_backups=max_backups)
        return {"backups": backups, "total": len(backups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup/restaurar/{backup_id}", response_model=dict)
async def restaurar_backup_endpoint(backup_id: str, db_module = Depends(get_db)):
    """Restaura um backup específico"""
    try:
        if backup is None:
            raise HTTPException(status_code=501, detail="Módulo de backup não disponível")
        resultado = backup.restaurar_backup(backup_id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backup/exportar", response_model=dict)
async def exportar_backup_json(db_module = Depends(get_db)):
    """Exporta todos os dados em formato JSON"""
    try:
        if backup is None:
            raise HTTPException(status_code=501, detail="Módulo de backup não disponível")
        json_data = backup.exportar_backup_json()
        import json as json_lib
        return {"dados": json_lib.loads(json_data), "formato": "json"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/backup/limpar", response_model=dict)
async def limpar_backups_antigos_endpoint(dias_manter: Optional[int] = 30, db_module = Depends(get_db)):
    """Remove backups mais antigos que o número de dias especificado"""
    try:
        if backup is None:
            return {"removidos": 0, "dias_manter": dias_manter}
        removidos = backup.limpar_backups_antigos(dias_manter=dias_manter)
        return {"removidos": removidos, "dias_manter": dias_manter}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/info")
async def obter_info(db_module = Depends(get_db)):
    """Retorna informações sobre a API e conexão"""
    try:
        # Debug: mostra TODAS as variáveis de ambiente relacionadas
        env_debug = {
            "APP_USUARIO": os.getenv('APP_USUARIO'),
            "APP_SENHA": "***" if os.getenv('APP_SENHA') else None,
            "USE_GOOGLE_SHEETS": os.getenv('USE_GOOGLE_SHEETS'),
            "GOOGLE_SHEET_ID": os.getenv('GOOGLE_SHEET_ID'),
            "RENDER": os.getenv('RENDER'),  # Indica se está no Render
            "PORT": os.getenv('PORT'),
        }
        
        db_type = "Google Sheets" if USE_GOOGLE_SHEETS else "SQLite"
        info = {
            "database": db_type,
            "use_google_sheets": USE_GOOGLE_SHEETS,
            "env_vars": env_debug,
            "credentials_configured": {
                "usuario": APP_USUARIO,
                "senha_defined": bool(os.getenv('APP_SENHA'))
            }
        }
        if USE_GOOGLE_SHEETS and sheets_info:
            info["spreadsheet_url"] = sheets_info.get('spreadsheet_url', None)
            info["spreadsheet_id"] = sheets_info.get('spreadsheet_id', None)
        info["supabase_available"] = SUPABASE_AVAILABLE
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/clear")
async def limpar_cache(token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Limpa o cache de dados do Google Sheets"""
    try:
        if USE_GOOGLE_SHEETS:
            db_module._clear_cache()
            return {"message": "Cache limpo com sucesso", "success": True}
        else:
            return {"message": "Cache nao disponivel (usando SQLite)", "success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS FINANCEIRO =============

def conta_receber_to_dict(conta):
    """Converte ContaReceber para dict"""
    return {
        "id": conta.id,
        "compromisso_id": conta.compromisso_id,
        "descricao": conta.descricao,
        "valor": conta.valor,
        "data_vencimento": conta.data_vencimento.isoformat() if isinstance(conta.data_vencimento, date) else str(conta.data_vencimento),
        "data_pagamento": conta.data_pagamento.isoformat() if conta.data_pagamento and isinstance(conta.data_pagamento, date) else None,
        "status": conta.status,
        "forma_pagamento": conta.forma_pagamento,
        "observacoes": conta.observacoes
    }

def conta_pagar_to_dict(conta):
    """Converte ContaPagar para dict"""
    return {
        "id": conta.id,
        "descricao": conta.descricao,
        "categoria": conta.categoria,
        "valor": conta.valor,
        "data_vencimento": conta.data_vencimento.isoformat() if isinstance(conta.data_vencimento, date) else str(conta.data_vencimento),
        "data_pagamento": conta.data_pagamento.isoformat() if conta.data_pagamento and isinstance(conta.data_pagamento, date) else None,
        "status": conta.status,
        "fornecedor": conta.fornecedor,
        "item_id": conta.item_id,
        "forma_pagamento": conta.forma_pagamento,
        "observacoes": conta.observacoes
    }

@app.post("/api/contas-receber", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_conta_receber(conta: ContaReceberCreate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Cria uma nova conta a receber"""
    try:
        nova_conta = db_module.criar_conta_receber(
            compromisso_id=conta.compromisso_id,
            descricao=conta.descricao,
            valor=conta.valor,
            data_vencimento=conta.data_vencimento,
            forma_pagamento=conta.forma_pagamento,
            observacoes=conta.observacoes
        )
        return conta_receber_to_dict(nova_conta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contas-receber", response_model=List[dict])
async def listar_contas_receber(
    status: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    compromisso_id: Optional[int] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Lista contas a receber com filtros opcionais"""
    try:
        contas = db_module.listar_contas_receber(
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
            compromisso_id=compromisso_id
        )
        return [conta_receber_to_dict(c) for c in contas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/contas-receber/{conta_id}", response_model=dict)
async def atualizar_conta_receber(conta_id: int, conta: ContaReceberUpdate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Atualiza uma conta a receber"""
    try:
        conta_atualizada = db_module.atualizar_conta_receber(
            conta_id=conta_id,
            descricao=conta.descricao,
            valor=conta.valor,
            data_vencimento=conta.data_vencimento,
            data_pagamento=conta.data_pagamento,
            status=conta.status,
            forma_pagamento=conta.forma_pagamento,
            observacoes=conta.observacoes
        )
        if conta_atualizada is None:
            raise HTTPException(status_code=404, detail="Conta a receber não encontrada")
        return conta_receber_to_dict(conta_atualizada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/contas-receber/{conta_id}/pagar", response_model=dict)
async def marcar_conta_receber_paga(
    conta_id: int,
    data_pagamento: Optional[date] = None,
    forma_pagamento: Optional[str] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Marca uma conta a receber como paga"""
    try:
        conta_atualizada = db_module.marcar_conta_receber_paga(
            conta_id=conta_id,
            data_pagamento=data_pagamento,
            forma_pagamento=forma_pagamento
        )
        if conta_atualizada is None:
            raise HTTPException(status_code=404, detail="Conta a receber não encontrada")
        return conta_receber_to_dict(conta_atualizada)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/contas-receber/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_conta_receber(conta_id: int, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Deleta uma conta a receber"""
    try:
        sucesso = db_module.deletar_conta_receber(conta_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Conta a receber não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contas-pagar", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_conta_pagar(conta: ContaPagarCreate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Cria uma nova conta a pagar"""
    try:
        nova_conta = db_module.criar_conta_pagar(
            descricao=conta.descricao,
            categoria=conta.categoria,
            valor=conta.valor,
            data_vencimento=conta.data_vencimento,
            fornecedor=conta.fornecedor,
            item_id=conta.item_id,
            forma_pagamento=conta.forma_pagamento,
            observacoes=conta.observacoes
        )
        return conta_pagar_to_dict(nova_conta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contas-pagar", response_model=List[dict])
async def listar_contas_pagar(
    status: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    categoria: Optional[str] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Lista contas a pagar com filtros opcionais"""
    try:
        contas = db_module.listar_contas_pagar(
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria=categoria
        )
        return [conta_pagar_to_dict(c) for c in contas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/contas-pagar/{conta_id}", response_model=dict)
async def atualizar_conta_pagar(conta_id: int, conta: ContaPagarUpdate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Atualiza uma conta a pagar"""
    try:
        conta_atualizada = db_module.atualizar_conta_pagar(
            conta_id=conta_id,
            descricao=conta.descricao,
            categoria=conta.categoria,
            valor=conta.valor,
            data_vencimento=conta.data_vencimento,
            data_pagamento=conta.data_pagamento,
            status=conta.status,
            fornecedor=conta.fornecedor,
            item_id=conta.item_id,
            forma_pagamento=conta.forma_pagamento,
            observacoes=conta.observacoes
        )
        if conta_atualizada is None:
            raise HTTPException(status_code=404, detail="Conta a pagar não encontrada")
        return conta_pagar_to_dict(conta_atualizada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/contas-pagar/{conta_id}/pagar", response_model=dict)
async def marcar_conta_pagar_paga(
    conta_id: int,
    data_pagamento: Optional[date] = None,
    forma_pagamento: Optional[str] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Marca uma conta a pagar como paga"""
    try:
        conta_atualizada = db_module.marcar_conta_pagar_paga(
            conta_id=conta_id,
            data_pagamento=data_pagamento,
            forma_pagamento=forma_pagamento
        )
        if conta_atualizada is None:
            raise HTTPException(status_code=404, detail="Conta a pagar não encontrada")
        return conta_pagar_to_dict(conta_atualizada)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/contas-pagar/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_conta_pagar(conta_id: int, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Deleta uma conta a pagar"""
    try:
        sucesso = db_module.deletar_conta_pagar(conta_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Conta a pagar não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/dashboard", response_model=DashboardFinanceiroResponse)
async def obter_dashboard_financeiro(token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Obtém dados do dashboard financeiro"""
    try:
        hoje = date.today()
        inicio_mes = date(hoje.year, hoje.month, 1)
        fim_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1) if hoje.month < 12 else date(hoje.year + 1, 1, 1) - timedelta(days=1)
        proximos_7_dias = hoje + timedelta(days=7)
        
        # Receitas do mês (pagas)
        receitas_mes = db_module.listar_contas_receber(status='Pago', data_inicio=inicio_mes, data_fim=fim_mes)
        receitas_mes_valor = sum(c.valor for c in receitas_mes)
        
        # Despesas do mês (pagas)
        despesas_mes = db_module.listar_contas_pagar(status='Pago', data_inicio=inicio_mes, data_fim=fim_mes)
        despesas_mes_valor = sum(c.valor for c in despesas_mes)
        
        # Saldo atual (todas as receitas pagas - todas as despesas pagas)
        todas_receitas_pagas = db_module.listar_contas_receber(status='Pago')
        todas_despesas_pagas = db_module.listar_contas_pagar(status='Pago')
        saldo_atual = sum(c.valor for c in todas_receitas_pagas) - sum(c.valor for c in todas_despesas_pagas)
        
        # Receitas pendentes
        receitas_pendentes = db_module.listar_contas_receber(status='Pendente')
        receitas_pendentes_valor = sum(c.valor for c in receitas_pendentes)
        
        # Despesas pendentes
        despesas_pendentes = db_module.listar_contas_pagar(status='Pendente')
        despesas_pendentes_valor = sum(c.valor for c in despesas_pendentes)
        
        # Saldo previsto (saldo atual + receitas pendentes - despesas pendentes)
        saldo_previsto = saldo_atual + receitas_pendentes_valor - despesas_pendentes_valor
        
        # Contas vencidas
        contas_receber_vencidas = db_module.listar_contas_receber(status='Vencido')
        contas_pagar_vencidas = db_module.listar_contas_pagar(status='Vencido')
        contas_vencidas = len(contas_receber_vencidas) + len(contas_pagar_vencidas)
        
        # Contas a vencer em 7 dias
        contas_receber_proximas = [c for c in db_module.listar_contas_receber(status='Pendente') if c.data_vencimento <= proximos_7_dias]
        contas_pagar_proximas = [c for c in db_module.listar_contas_pagar(status='Pendente') if c.data_vencimento <= proximos_7_dias]
        contas_a_vencer_7_dias = len(contas_receber_proximas) + len(contas_pagar_proximas)
        
        return DashboardFinanceiroResponse(
            saldo_atual=saldo_atual,
            receitas_mes=receitas_mes_valor,
            despesas_mes=despesas_mes_valor,
            saldo_previsto=saldo_previsto,
            contas_vencidas=contas_vencidas,
            contas_a_vencer_7_dias=contas_a_vencer_7_dias,
            receitas_pendentes=receitas_pendentes_valor,
            despesas_pendentes=despesas_pendentes_valor
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/fluxo-caixa", response_model=List[FluxoCaixaResponse])
async def obter_fluxo_caixa(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Obtém fluxo de caixa por período"""
    try:
        if data_inicio is None:
            # Últimos 6 meses por padrão
            hoje = date.today()
            data_fim = hoje
            data_inicio = date(hoje.year, hoje.month - 5, 1) if hoje.month > 5 else date(hoje.year - 1, hoje.month + 7, 1)
        
        fluxo = db_module.obter_fluxo_caixa(data_inicio, data_fim)
        return [FluxoCaixaResponse(**item) for item in fluxo]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS FINANCIAMENTOS =============

def financiamento_to_dict(fin):
    """Converte Financiamento para dict com formatação precisa de decimais"""
    if isinstance(fin, dict):
        # Se já é dict, apenas arredonda valores
        if 'valor_total' in fin:
            fin['valor_total'] = round(float(fin['valor_total']), 2)
        if 'valor_entrada' in fin:
            fin['valor_entrada'] = round(float(fin['valor_entrada']), 2)
        if 'valor_parcela' in fin:
            fin['valor_parcela'] = round(float(fin['valor_parcela']), 2)
        if 'taxa_juros' in fin:
            fin['taxa_juros'] = round(float(fin['taxa_juros']), 7)
        if 'codigo_contrato' not in fin:
            fin['codigo_contrato'] = ''
        return fin
    
    # Calcula valores com precisão de 2 casas decimais
    codigo_contrato = getattr(fin, 'codigo_contrato', None) or ''
    valor_total = round(float(getattr(fin, 'valor_total', 0.0)), 2)
    valor_entrada = round(float(getattr(fin, 'valor_entrada', 0.0)), 2)
    valor_parcela = round(float(getattr(fin, 'valor_parcela', 0.0)), 2)
    taxa_juros = round(float(getattr(fin, 'taxa_juros', 0.0)), 7)  # Mais precisão para taxa
    valor_financiado = round(valor_total - valor_entrada, 2)
    
    # Busca itens associados ao financiamento
    itens = []
    if hasattr(fin, 'itens'):
        for item_info in fin.itens:
            itens.append({
                "id": item_info['id'],
                "nome": item_info['nome']
                # Não incluímos valor individual pois não é usado
            })
    
    return {
        "id": getattr(fin, 'id', None),
        "codigo_contrato": codigo_contrato,  # NOVO: Código do contrato
        "itens": itens,  # NOVO: lista de itens com seus valores
        "item_id": getattr(fin, 'item_id', None),  # Compatibilidade: primeiro item
        "valor_total": valor_total,
        "valor_entrada": valor_entrada,
        "valor_financiado": valor_financiado,
        "numero_parcelas": getattr(fin, 'numero_parcelas', 0),
        "valor_parcela": valor_parcela,
        "taxa_juros": taxa_juros,
        "data_inicio": fin.data_inicio.isoformat() if hasattr(fin, 'data_inicio') and isinstance(fin.data_inicio, date) else (str(fin.data_inicio) if hasattr(fin, 'data_inicio') else None),
        "status": getattr(fin, 'status', 'Ativo'),
        "instituicao_financeira": getattr(fin, 'instituicao_financeira', None),
        "observacoes": getattr(fin, 'observacoes', None),
        "valor_presente": round(float(getattr(fin, 'valor_presente', 0.0)), 2)  # NOVO: Valor presente do Sheets
    }

def parcela_to_dict(parcela):
    """Converte ParcelaFinanciamento para dict com formatação precisa de decimais"""
    return {
        "id": parcela.id,
        "financiamento_id": parcela.financiamento_id,
        "numero_parcela": parcela.numero_parcela,
        "valor_original": round(float(parcela.valor_original), 2),
        "valor_pago": round(float(parcela.valor_pago), 2),
        "data_vencimento": parcela.data_vencimento.isoformat() if isinstance(parcela.data_vencimento, date) else str(parcela.data_vencimento),
        "data_pagamento": parcela.data_pagamento.isoformat() if parcela.data_pagamento and isinstance(parcela.data_pagamento, date) else None,
        "status": parcela.status,
        "link_boleto": parcela.link_boleto if hasattr(parcela, 'link_boleto') else None,
        "link_comprovante": parcela.link_comprovante if hasattr(parcela, 'link_comprovante') else None,
    }

@app.post("/api/financiamentos", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_financiamento(fin: FinanciamentoCreate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Cria um novo financiamento e gera as parcelas automaticamente"""
    try:
        # Prepara itens_ids (suporta compatibilidade reversa)
        if not fin.itens_ids and fin.item_id:
            # Compatibilidade reversa: se item_id for fornecido
            itens_ids = [fin.item_id]
        elif fin.itens_ids:
            itens_ids = fin.itens_ids
        else:
            raise HTTPException(status_code=400, detail="É necessário fornecer pelo menos um item (itens_ids ou item_id)")
        
        # Validação adicional: valor_entrada não pode ser maior que valor_total
        if fin.valor_entrada and fin.valor_entrada > fin.valor_total:
            raise HTTPException(
                status_code=400,
                detail=f"Valor de entrada ({fin.valor_entrada}) não pode ser maior que valor total ({fin.valor_total})"
            )
        
        # Se parcelas customizadas foram fornecidas, usa elas
        if fin.parcelas_customizadas and len(fin.parcelas_customizadas) > 0:
            # Valida que soma das parcelas = valor_financiado (não valor_total)
            valor_financiado = fin.valor_total - (fin.valor_entrada or 0.0)
            soma_parcelas = sum(p.valor for p in fin.parcelas_customizadas)
            if abs(soma_parcelas - valor_financiado) > 0.01:  # Tolerância de centavos
                raise HTTPException(status_code=400, detail=f"Soma das parcelas ({soma_parcelas}) não confere com valor financiado ({valor_financiado})")
            
            novo_fin = db_module.criar_financiamento(
                itens_ids=itens_ids,
                codigo_contrato=fin.codigo_contrato,
                valor_total=fin.valor_total,
                valor_entrada=fin.valor_entrada or 0.0,
                numero_parcelas=len(fin.parcelas_customizadas),
                taxa_juros=fin.taxa_juros,
                data_inicio=fin.data_inicio,
                instituicao_financeira=fin.instituicao_financeira,
                observacoes=fin.observacoes,
                parcelas_customizadas=[{"numero": p.numero, "valor": p.valor, "data_vencimento": p.data_vencimento} for p in fin.parcelas_customizadas]
            )
        else:
            novo_fin = db_module.criar_financiamento(
                itens_ids=itens_ids,
                codigo_contrato=fin.codigo_contrato,
                valor_total=fin.valor_total,
                valor_entrada=fin.valor_entrada or 0.0,
                numero_parcelas=fin.numero_parcelas,
                taxa_juros=fin.taxa_juros,
                data_inicio=fin.data_inicio,
                instituicao_financeira=fin.instituicao_financeira,
                observacoes=fin.observacoes
            )
        return financiamento_to_dict(novo_fin)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financiamentos", response_model=List[dict])
async def listar_financiamentos(
    status: Optional[str] = None,
    item_id: Optional[int] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Lista financiamentos com filtros opcionais"""
    try:
        print("[DEBUG] listar_financiamentos endpoint chamado")
        financiamentos = db_module.listar_financiamentos(status=status, item_id=item_id)
        print(f"[DEBUG] {len(financiamentos)} financiamentos retornados")
        return [financiamento_to_dict(f) for f in financiamentos]
    except Exception as e:
        print(f"[ERROR] Erro em listar_financiamentos: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financiamentos/{financiamento_id}", response_model=dict)
async def buscar_financiamento(financiamento_id: int, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Busca um financiamento por ID com suas parcelas"""
    try:
        print(f"[DEBUG] Buscando financiamento ID {financiamento_id}")
        fin = db_module.buscar_financiamento_por_id(financiamento_id)
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamento não encontrado")
        
        print(f"[DEBUG] Financiamento encontrado, convertendo para dict")
        resultado = financiamento_to_dict(fin)
        
        print(f"[DEBUG] Buscando parcelas do financiamento {financiamento_id}")
        # Adiciona parcelas
        parcelas = db_module.listar_parcelas_financiamento(financiamento_id=financiamento_id)
        resultado['parcelas'] = [parcela_to_dict(p) for p in parcelas]
        
        print(f"[DEBUG] Retornando financiamento com {len(parcelas)} parcelas")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erro ao buscar financiamento {financiamento_id}: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/financiamentos/{financiamento_id}", response_model=dict)
async def atualizar_financiamento(financiamento_id: int, fin: FinanciamentoUpdate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Atualiza um financiamento"""
    try:
        fin_atualizado = db_module.atualizar_financiamento(
            financiamento_id=financiamento_id,
            valor_total=fin.valor_total,
            taxa_juros=fin.taxa_juros,
            status=fin.status,
            instituicao_financeira=fin.instituicao_financeira,
            observacoes=fin.observacoes
        )
        if fin_atualizado is None:
            raise HTTPException(status_code=404, detail="Financiamento não encontrado")
        return financiamento_to_dict(fin_atualizado)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/financiamentos/{financiamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_financiamento(financiamento_id: int, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Deleta um financiamento"""
    try:
        sucesso = db_module.deletar_financiamento(financiamento_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Financiamento não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financiamentos/{financiamento_id}/parcelas/{parcela_id}/pagar")
async def pagar_parcela_financiamento(
    financiamento_id: int,
    parcela_id: int,
    pagamento: dict = Body(...), 
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    try:
        # Garantimos que os campos cheguem como tipos básicos ao db_module
        parcela_atualizada = db_module.pagar_parcela_financiamento(
            parcela_id=parcela_id,
            valor_pago=float(pagamento.get('valor_pago', 0)),
            data_pagamento=pagamento.get('data_pagamento'),
            link_comprovante=str(pagamento.get('link_comprovante', '')) if pagamento.get('link_comprovante') else None
        )
        if not parcela_atualizada:
            raise HTTPException(status_code=404, detail="Parcela não encontrada")
        return parcela_to_dict(parcela_atualizada)
    except Exception as e:
        # Retorna string para o React não tentar renderizar um objeto de erro
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/financiamentos/{financiamento_id}/parcelas/{parcela_id}", response_model=dict)
async def atualizar_parcela_financiamento(
    financiamento_id: int,
    parcela_id: int,
    parcela_update: ParcelaUpdate,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Atualiza uma parcela de financiamento"""
    try:
        parcela_atualizada = db_module.atualizar_parcela_financiamento(
            parcela_id=parcela_id,
            status=parcela_update.status,
            link_boleto=parcela_update.link_boleto,
            link_comprovante=parcela_update.link_comprovante,
            valor_original=parcela_update.valor_original,
            data_vencimento=parcela_update.data_vencimento
        )
        if parcela_atualizada is None:
            raise HTTPException(status_code=404, detail="Parcela não encontrada")
        return parcela_to_dict(parcela_atualizada)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financiamentos/{financiamento_id}/valor-presente", response_model=ValorPresenteResponse)
async def calcular_valor_presente_financiamento(
    financiamento_id: int,
    usar_cdi: Optional[bool] = False,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Calcula valor presente (NPV) de um financiamento"""
    try:
        import sys
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        from taxa_selic import calcular_valor_presente, obter_taxa_selic, obter_taxa_cdi
        
        fin = db_module.buscar_financiamento_por_id(financiamento_id)
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamento não encontrado")
        
        parcelas = db_module.listar_parcelas_financiamento(financiamento_id=financiamento_id)
        parcelas_restantes = [p for p in parcelas if p.status != 'Paga']
        
        if usar_cdi:
            taxa_desconto = obter_taxa_cdi()
        else:
            taxa_desconto = obter_taxa_selic()
        
        valor_presente = calcular_valor_presente(parcelas_restantes, taxa_desconto=taxa_desconto, usar_cdi=usar_cdi)
        valor_total_restante = sum(p.valor_original + p.juros + p.multa - p.desconto for p in parcelas_restantes)
        
        return ValorPresenteResponse(
            valor_presente=valor_presente,
            taxa_desconto=taxa_desconto,
            parcelas_restantes=len(parcelas_restantes),
            valor_total_restante=valor_total_restante
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financiamentos/dashboard", response_model=dict)
async def obter_dashboard_financiamentos(token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Obtém dashboard de financiamentos"""
    try:
        financiamentos_ativos = db_module.listar_financiamentos(status='Ativo')
        parcelas_pendentes = db_module.listar_parcelas_financiamento(status='Pendente')
        parcelas_atrasadas = db_module.listar_parcelas_financiamento(status='Atrasada')
        
        hoje = date.today()
        proximos_7_dias = hoje + timedelta(days=7)
        parcelas_proximas = [p for p in parcelas_pendentes if p.data_vencimento <= proximos_7_dias]
        
        valor_total_financiado = sum(f.valor_total for f in financiamentos_ativos)
        valor_total_pago = sum(p.valor_pago for p in db_module.listar_parcelas_financiamento())
        valor_total_restante = valor_total_financiado - valor_total_pago
        
        return {
            'total_financiamentos_ativos': len(financiamentos_ativos),
            'parcelas_pendentes': len(parcelas_pendentes),
            'parcelas_atrasadas': len(parcelas_atrasadas),
            'parcelas_proximas_7_dias': len(parcelas_proximas),
            'valor_total_financiado': valor_total_financiado,
            'valor_total_pago': valor_total_pago,
            'valor_total_restante': valor_total_restante
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS PARCELAS (BOLETOS) =============

def _parcela_data_vencimento(p):
    """Retorna data_vencimento da parcela como date para comparação."""
    dv = getattr(p, "data_vencimento", None)
    if dv is None:
        return None
    if isinstance(dv, date):
        return dv
    if isinstance(dv, str):
        try:
            return datetime.strptime(dv[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

@app.get("/api/parcelas", response_model=List[dict])
async def listar_parcelas(
    data_vencimento: Optional[date] = Query(None),
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000, le=2100),
    status: Optional[str] = Query(None),
    incluir_pagas: bool = Query(False),
    token: str = Depends(verify_token),
    db_module = Depends(get_db),
):
    """Lista parcelas do financiamento. Filtros: data_vencimento, mes/ano, status. Retorna codigo_contrato."""
    try:
        parcelas = db_module.listar_parcelas_financiamento(status=status)
        if not incluir_pagas:
            parcelas = [p for p in parcelas if (getattr(p, "status", None) or "") != "Paga"]
        if data_vencimento:
            parcelas = [p for p in parcelas if _parcela_data_vencimento(p) == data_vencimento]
        if mes is not None and ano is not None:
            parcelas = [
                p for p in parcelas
                if (_parcela_data_vencimento(p) and _parcela_data_vencimento(p).month == mes and _parcela_data_vencimento(p).year == ano)
            ]
        # Enriquecer com codigo_contrato
        resultado = []
        fins_cache = {}
        for p in parcelas:
            d = parcela_to_dict(p)
            d["link_boleto"] = getattr(p, "link_boleto", None)
            d["link_comprovante"] = getattr(p, "link_comprovante", None)
            d["valor_pago"] = float(getattr(p, "valor_pago", 0.0))
            fin_id = getattr(p, "financiamento_id", None)
            if fin_id is not None:
                if fin_id not in fins_cache:
                    try:
                        fin = db_module.buscar_financiamento_por_id(fin_id)
                        fins_cache[fin_id] = (getattr(fin, "codigo_contrato", None) or "").strip() if fin else ""
                    except Exception:
                        fins_cache[fin_id] = ""
                d["codigo_contrato"] = fins_cache[fin_id] or f"Financiamento #{fin_id}"
            else:
                d["codigo_contrato"] = ""
            resultado.append(d)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS PEÇAS EM CARROS =============

class PecaCarroCreate(BaseModel):
    peca_id: int
    carro_id: int
    quantidade: int = 1
    data_instalacao: Optional[date] = None
    observacoes: Optional[str] = None

class PecaCarroUpdate(BaseModel):
    quantidade: Optional[int] = None
    data_instalacao: Optional[date] = None
    observacoes: Optional[str] = None

class PecaCarroResponse(BaseModel):
    id: int
    peca_id: int
    carro_id: int
    quantidade: int
    data_instalacao: Optional[date] = None
    observacoes: Optional[str] = None
    peca: Optional[dict] = None
    carro: Optional[dict] = None
    
    class Config:
        from_attributes = True

def peca_carro_to_dict(pc):
    """Converte PecaCarro para dict com suporte a dicionários e objetos"""
    if not pc: return {}
    
    # Helper para extrair dados de dict ou objeto
    def get_val(obj, key, default=None):
        if isinstance(obj, dict): return obj.get(key, default)
        return getattr(obj, key, default)

    # Tratamento da data de instalação
    dt_inst = get_val(pc, 'data_instalacao')
    if dt_inst and hasattr(dt_inst, 'isoformat'):
        dt_inst_str = dt_inst.isoformat()
    else:
        dt_inst_str = str(dt_inst) if dt_inst else None

    result = {
        "id": get_val(pc, 'id'),
        "peca_id": get_val(pc, 'peca_id'),
        "carro_id": get_val(pc, 'carro_id'),
        "quantidade": get_val(pc, 'quantidade', 1),
        "data_instalacao": dt_inst_str,
        "observacoes": get_val(pc, 'observacoes', '')
    }
    
    # Se houver dados aninhados da peça ou do carro (Joins)
    peca_data = get_val(pc, 'peca')
    if peca_data: result["peca"] = item_to_dict(peca_data)
    
    carro_data = get_val(pc, 'carro')
    if carro_data: result["carro"] = item_to_dict(carro_data)
    
    return result
@app.post("/api/pecas-carros", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_peca_carro(peca_carro: PecaCarroCreate, token: str = Depends(verify_token), db_module = Depends(get_db)):
    try:
        nova_associacao = db_module.criar_peca_carro(
            peca_id=peca_carro.peca_id,
            carro_id=peca_carro.carro_id,
            quantidade=peca_carro.quantidade,
            data_instalacao=peca_carro.data_instalacao,
            observacoes=peca_carro.observacoes
        )
        # Retorno blindado
        return JSONResponse(content=jsonable_encoder(peca_carro_to_dict(nova_associacao)))
    except Exception as e:
        print(f"❌ ERRO PEÇAS-CARROS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pecas-carros", response_model=List[dict])
async def listar_pecas_carros(
    carro_id: Optional[int] = None,
    peca_id: Optional[int] = None,
    token: str = Depends(verify_token),
    db_module = Depends(get_db)
):
    """Lista associações de peças em carros com filtros opcionais"""
    try:
        associacoes = db_module.listar_pecas_carros(carro_id=carro_id, peca_id=peca_id)
        return [peca_carro_to_dict(pc) for pc in associacoes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pecas-carros/{associacao_id}", response_model=dict)
async def buscar_peca_carro(associacao_id: int, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Busca uma associação peça-carro por ID"""
    try:
        associacao = db_module.buscar_peca_carro_por_id(associacao_id)
        if not associacao:
            raise HTTPException(status_code=404, detail="Associação não encontrada")
        return peca_carro_to_dict(associacao)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/pecas-carros/{associacao_id}", response_model=dict)
async def atualizar_peca_carro(
    associacao_id: int, 
    peca_carro: PecaCarroUpdate, 
    token: str = Depends(verify_token), 
    db_module = Depends(get_db)
):
    try:
        associacao_atualizada = db_module.atualizar_peca_carro(
            associacao_id=associacao_id,
            quantidade=peca_carro.quantidade,
            data_instalacao=peca_carro.data_instalacao,
            observacoes=peca_carro.observacoes
        )
        
        if not associacao_atualizada:
            raise HTTPException(status_code=404, detail="Associação não encontrada")
        
        # Retorno blindado contra erros de JSON
        return JSONResponse(content=jsonable_encoder(peca_carro_to_dict(associacao_atualizada)))
        
    except Exception as e:
        print(f"❌ ERRO UPDATE PEÇAS-CARROS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/pecas-carros/{associacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_peca_carro(associacao_id: int, token: str = Depends(verify_token), db_module = Depends(get_db)):
    """Remove uma associação peça-carro"""
    try:
        sucesso = db_module.deletar_peca_carro(associacao_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Associação não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
