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

# Handler explícito para OPTIONS (preflight requests)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handler para requisições OPTIONS (preflight)"""
    return {"message": "OK"}

# CORS - permite requisições do frontend
# Em desenvolvimento, permite qualquer origem localhost
is_dev = not os.getenv('RENDER')
if is_dev:
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
else:
    # Produção: permite o frontend do Render
    # Lista explícita (FastAPI não suporta wildcards)
    allow_origins = [
        "https://crm-frontend-nbrm.onrender.com",
        "https://crm-frontend-wtcf.onrender.com",  # Nova URL do frontend
        "http://crm-frontend-nbrm.onrender.com",
        "http://crm-frontend-wtcf.onrender.com",
    ]
    # Se tiver FRONTEND_URL configurado, adiciona também
    frontend_url = os.getenv('FRONTEND_URL')
    if frontend_url:
        if frontend_url not in allow_origins:
            allow_origins.append(frontend_url)
        # Adiciona versão HTTP também
        http_url = frontend_url.replace('https://', 'http://')
        if http_url not in allow_origins:
            allow_origins.append(http_url)
    
    print(f"[CORS] Origens permitidas em produção: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
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

class FinanciamentoUpdate(BaseModel):
    valor_total: Optional[float] = None
    taxa_juros: Optional[float] = None
    status: Optional[str] = None
    instituicao_financeira: Optional[str] = None
    observacoes: Optional[str] = None

class FinanciamentoResponse(BaseModel):
    id: int
    item_id: int
    valor_total: float
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

# ============= MODELOS FINANCIAMENTO =============

class ParcelaCustomizada(BaseModel):
    numero: int
    valor: float
    data_vencimento: date

class ParcelaUpdate(BaseModel):
    status: Optional[str] = None
    link_boleto: Optional[str] = None
    valor_original: Optional[float] = None
    data_vencimento: Optional[date] = None

class FinanciamentoCreate(BaseModel):
    item_id: int
    valor_total: float  # Valor financiado (principal)
    numero_parcelas: int
    taxa_juros: float  # Taxa de juros mensal (ex: 0.01 para 1% ao mês)
    data_inicio: date
    instituicao_financeira: Optional[str] = None
    observacoes: Optional[str] = None
    parcelas_customizadas: Optional[List[ParcelaCustomizada]] = None

class FinanciamentoUpdate(BaseModel):
    valor_total: Optional[float] = None
    taxa_juros: Optional[float] = None
    status: Optional[str] = None
    instituicao_financeira: Optional[str] = None
    observacoes: Optional[str] = None

class FinanciamentoResponse(BaseModel):
    id: int
    item_id: int
    valor_total: float
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
    os.getenv('RENDER_EXTERNAL_URL') is not None
)

if is_production:
    # Em produção, EXIGE que as variáveis estejam configuradas
    if not app_usuario_raw or not app_senha_raw:
        raise ValueError(
            "ERRO CRÍTICO: APP_USUARIO e APP_SENHA devem estar configuradas no Render!\n"
            "Configure em: Settings → Environment → Add Environment Variable"
        )
    # Remove espaços extras e caracteres invisíveis
    APP_USUARIO = app_usuario_raw.strip() if app_usuario_raw else ""
    APP_SENHA = app_senha_raw.strip() if app_senha_raw else ""
    
    # Debug: mostra exatamente o que foi lido (sem mostrar senha completa)
    print(f"[DEBUG] APP_USUARIO lido: {repr(APP_USUARIO)} (len={len(APP_USUARIO)})")
    if APP_SENHA:
        print(f"[DEBUG] APP_SENHA lido: len={len(APP_SENHA)}, primeiro_char={repr(APP_SENHA[0])}, ultimo_char={repr(APP_SENHA[-1])}")
    else:
        print(f"[DEBUG] APP_SENHA lido: None")
else:
    # Em desenvolvimento local, permite valores padrão apenas para facilitar
    # Mas ainda recomenda usar .env
    if not app_usuario_raw or not app_senha_raw:
        print("⚠️ AVISO: APP_USUARIO e APP_SENHA não configuradas!")
        print("   Configure no arquivo .env na raiz do projeto:")
        print("   APP_USUARIO=seu_usuario")
        print("   APP_SENHA=sua_senha")
        print("   O servidor não iniciará sem essas variáveis configuradas.")
        raise ValueError(
            "APP_USUARIO e APP_SENHA devem estar configuradas no arquivo .env "
            "ou como variáveis de ambiente."
        )
    APP_USUARIO = app_usuario_raw.strip()
    APP_SENHA = app_senha_raw.strip()

# Debug condicional - apenas se DEBUG ou DEBUG_AUTH estiver habilitado
DEBUG_AUTH_INIT = os.getenv('DEBUG_AUTH', 'false').lower() == 'true' or DEBUG_MODE

if DEBUG_AUTH_INIT:
    print(f"\n{'='*60}")
    print(f"🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO")
    print(f"{'='*60}")
    print(f"Ambiente: {'PRODUÇÃO (Render)' if is_production else 'DESENVOLVIMENTO'}")
    if DEBUG_MODE:
        print(f"Variáveis Render detectadas:")
        print(f"  RENDER: {os.getenv('RENDER')}")
        print(f"  RENDER_SERVICE_NAME: {os.getenv('RENDER_SERVICE_NAME')}")
        print(f"  RENDER_EXTERNAL_URL: {os.getenv('RENDER_EXTERNAL_URL')}")
        print(f"APP_USUARIO (os.getenv): {repr(app_usuario_raw)}")
        print(f"APP_SENHA (os.getenv): {'DEFINIDA' if app_senha_raw else 'NÃO DEFINIDA'}")
        if app_usuario_raw:
            print(f"Usuário final: {repr(APP_USUARIO)} (len={len(APP_USUARIO)})")
        if app_senha_raw:
            print(f"Senha final: DEFINIDA (len={len(APP_SENHA)})")
        else:
            print(f"Senha final: NÃO DEFINIDA")
    
    # Sempre mostra status crítico (sucesso ou erro)
    if is_production:
        if app_usuario_raw and app_senha_raw:
            print("✅ Usando credenciais do Render (produção)")
        else:
            print("❌ ERRO CRÍTICO: Variáveis não configuradas no Render!")
            print("   Configure em: Settings → Environment → Add Environment Variable")
            print("   Variáveis necessárias: APP_USUARIO e APP_SENHA")
    else:
        if app_usuario_raw and app_senha_raw:
            print("✅ Usando credenciais do .env (desenvolvimento)")
        else:
            print("❌ ERRO: Variáveis não configuradas!")
            print("   Configure no arquivo .env na raiz do projeto")
    print(f"{'='*60}\n")
elif not (app_usuario_raw and app_senha_raw):
    # Sempre mostra erro crítico mesmo sem debug
    if is_production:
        print("❌ ERRO CRÍTICO: APP_USUARIO e APP_SENHA não configuradas no Render!")
        print("   Configure em: Settings → Environment → Add Environment Variable")
    else:
        print("❌ ERRO: APP_USUARIO e APP_SENHA não configuradas!")
        print("   Configure no arquivo .env na raiz do projeto")

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
    # Debug condicional - apenas se DEBUG_AUTH estiver habilitado
    DEBUG_AUTH = os.getenv('DEBUG_AUTH', 'false').lower() == 'true'
    
    # Remove espaços extras e normaliza
    usuario_recebido = credentials.usuario.strip() if credentials.usuario else ""
    senha_recebida = credentials.senha.strip() if credentials.senha else ""
    usuario_esperado = APP_USUARIO.strip() if APP_USUARIO else ""
    senha_esperada = APP_SENHA.strip() if APP_SENHA else ""
    
    # Debug detalhado apenas se habilitado
    if DEBUG_AUTH:
        print(f"\n[LOGIN] ========== TENTATIVA DE LOGIN ==========")
        print(f"  Usuario recebido: '{usuario_recebido}' (len={len(usuario_recebido)})")
        print(f"  Usuario esperado: '{usuario_esperado}' (len={len(usuario_esperado)})")
        print(f"  Match usuario: {usuario_recebido == usuario_esperado}")
        print(f"[LOGIN] =========================================\n")
    
    if usuario_recebido == usuario_esperado and senha_recebida == senha_esperada:
        token = generate_token()
        active_tokens[token] = {
            "usuario": credentials.usuario,
            "created_at": datetime.now()
        }
        # Log simples de sucesso (sempre)
        print(f"[LOGIN] Login bem-sucedido para usuario: {usuario_recebido}")
        return {
            "success": True,
            "token": token,
            "usuario": credentials.usuario
        }
    else:
        # Log simples de falha (sempre)
        print(f"[LOGIN] Login FALHOU - Credenciais incorretas")
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

@app.get("/api/itens/buscar", response_model=dict)
async def buscar_itens(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    cidade: Optional[str] = None,
    uf: Optional[str] = None,
    ordenar_por: Optional[str] = "nome",
    ordem: Optional[str] = "asc",
    pagina: Optional[int] = 1,
    por_pagina: Optional[int] = 50
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
    por_pagina: Optional[int] = 50
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

@app.get("/api/auditoria/{tabela}/{registro_id}", response_model=dict)
async def obter_historico_auditoria(tabela: str, registro_id: int):
    """Obtém histórico de mudanças de um registro"""
    try:
        historico = auditoria.obter_historico(tabela, registro_id)
        return {"historico": historico}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup/criar", response_model=dict)
async def criar_backup():
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
async def listar_backups(max_backups: Optional[int] = 50):
    """Lista backups disponíveis"""
    try:
        if backup is None:
            return {"backups": [], "total": 0}
        backups = backup.listar_backups(max_backups=max_backups)
        return {"backups": backups, "total": len(backups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup/restaurar/{backup_id}", response_model=dict)
async def restaurar_backup_endpoint(backup_id: str):
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
async def exportar_backup_json():
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
async def limpar_backups_antigos_endpoint(dias_manter: Optional[int] = 30):
    """Remove backups mais antigos que o número de dias especificado"""
    try:
        if backup is None:
            return {"removidos": 0, "dias_manter": dias_manter}
        removidos = backup.limpar_backups_antigos(dias_manter=dias_manter)
        return {"removidos": removidos, "dias_manter": dias_manter}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/info")
async def obter_info():
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
        return info
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
async def criar_conta_receber(conta: ContaReceberCreate, token: str = Depends(verify_token)):
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
    token: str = Depends(verify_token)
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
async def atualizar_conta_receber(conta_id: int, conta: ContaReceberUpdate, token: str = Depends(verify_token)):
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
    token: str = Depends(verify_token)
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
async def deletar_conta_receber(conta_id: int, token: str = Depends(verify_token)):
    """Deleta uma conta a receber"""
    try:
        sucesso = db_module.deletar_conta_receber(conta_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Conta a receber não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contas-pagar", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_conta_pagar(conta: ContaPagarCreate, token: str = Depends(verify_token)):
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
    token: str = Depends(verify_token)
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
async def atualizar_conta_pagar(conta_id: int, conta: ContaPagarUpdate, token: str = Depends(verify_token)):
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
    token: str = Depends(verify_token)
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
async def deletar_conta_pagar(conta_id: int, token: str = Depends(verify_token)):
    """Deleta uma conta a pagar"""
    try:
        sucesso = db_module.deletar_conta_pagar(conta_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Conta a pagar não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/dashboard", response_model=DashboardFinanceiroResponse)
async def obter_dashboard_financeiro(token: str = Depends(verify_token)):
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
    token: str = Depends(verify_token)
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
    """Converte Financiamento para dict"""
    # Garante que fin é um objeto, não um dict ou Response
    if isinstance(fin, dict):
        return fin
    
    return {
        "id": getattr(fin, 'id', None),
        "item_id": getattr(fin, 'item_id', None),
        "valor_total": getattr(fin, 'valor_total', 0.0),
        "numero_parcelas": getattr(fin, 'numero_parcelas', 0),
        "valor_parcela": getattr(fin, 'valor_parcela', 0.0),
        "taxa_juros": getattr(fin, 'taxa_juros', 0.0),
        "data_inicio": fin.data_inicio.isoformat() if hasattr(fin, 'data_inicio') and isinstance(fin.data_inicio, date) else (str(fin.data_inicio) if hasattr(fin, 'data_inicio') else None),
        "status": getattr(fin, 'status', 'Ativo'),
        "instituicao_financeira": getattr(fin, 'instituicao_financeira', None),
        "observacoes": getattr(fin, 'observacoes', None)
    }

def parcela_to_dict(parcela):
    """Converte ParcelaFinanciamento para dict"""
    return {
        "id": parcela.id,
        "financiamento_id": parcela.financiamento_id,
        "numero_parcela": parcela.numero_parcela,
        "valor_original": parcela.valor_original,
        "valor_pago": parcela.valor_pago,
        "data_vencimento": parcela.data_vencimento.isoformat() if isinstance(parcela.data_vencimento, date) else str(parcela.data_vencimento),
        "data_pagamento": parcela.data_pagamento.isoformat() if parcela.data_pagamento and isinstance(parcela.data_pagamento, date) else None,
        "status": parcela.status,
        "juros": parcela.juros,
        "multa": parcela.multa,
        "desconto": parcela.desconto,
        "link_boleto": parcela.link_boleto if hasattr(parcela, 'link_boleto') else None
    }

@app.post("/api/financiamentos", response_model=dict, status_code=status.HTTP_201_CREATED)
async def criar_financiamento(fin: FinanciamentoCreate, token: str = Depends(verify_token)):
    """Cria um novo financiamento e gera as parcelas automaticamente"""
    try:
        # Se parcelas customizadas foram fornecidas, usa elas
        if fin.parcelas_customizadas and len(fin.parcelas_customizadas) > 0:
            # Valida que soma das parcelas = valor_total
            soma_parcelas = sum(p.valor for p in fin.parcelas_customizadas)
            if abs(soma_parcelas - fin.valor_total) > 0.01:  # Tolerância de centavos
                raise HTTPException(status_code=400, detail=f"Soma das parcelas ({soma_parcelas}) não confere com valor total ({fin.valor_total})")
            
            novo_fin = db_module.criar_financiamento(
                item_id=fin.item_id,
                valor_total=fin.valor_total,
                numero_parcelas=len(fin.parcelas_customizadas),
                taxa_juros=fin.taxa_juros,
                data_inicio=fin.data_inicio,
                instituicao_financeira=fin.instituicao_financeira,
                observacoes=fin.observacoes,
                parcelas_customizadas=[{"numero": p.numero, "valor": p.valor, "data_vencimento": p.data_vencimento} for p in fin.parcelas_customizadas]
            )
        else:
            novo_fin = db_module.criar_financiamento(
                item_id=fin.item_id,
                valor_total=fin.valor_total,
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
    token: str = Depends(verify_token)
):
    """Lista financiamentos com filtros opcionais"""
    try:
        financiamentos = db_module.listar_financiamentos(status=status, item_id=item_id)
        return [financiamento_to_dict(f) for f in financiamentos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financiamentos/{financiamento_id}", response_model=dict)
async def buscar_financiamento(financiamento_id: int, token: str = Depends(verify_token)):
    """Busca um financiamento por ID com suas parcelas"""
    try:
        fin = db_module.buscar_financiamento_por_id(financiamento_id)
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamento não encontrado")
        
        resultado = financiamento_to_dict(fin)
        # Adiciona parcelas
        parcelas = db_module.listar_parcelas_financiamento(financiamento_id=financiamento_id)
        resultado['parcelas'] = [parcela_to_dict(p) for p in parcelas]
        
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/financiamentos/{financiamento_id}", response_model=dict)
async def atualizar_financiamento(financiamento_id: int, fin: FinanciamentoUpdate, token: str = Depends(verify_token)):
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
async def deletar_financiamento(financiamento_id: int, token: str = Depends(verify_token)):
    """Deleta um financiamento"""
    try:
        sucesso = db_module.deletar_financiamento(financiamento_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Financiamento não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financiamentos/{financiamento_id}/parcelas/{parcela_id}/pagar", response_model=dict)
async def pagar_parcela_financiamento(
    financiamento_id: int,
    parcela_id: int,
    pagamento: PagarParcelaRequest,
    token: str = Depends(verify_token)
):
    """Registra pagamento de uma parcela"""
    try:
        parcela_atualizada = db_module.pagar_parcela_financiamento(
            parcela_id=parcela_id,
            valor_pago=pagamento.valor_pago,
            data_pagamento=pagamento.data_pagamento,
            juros=pagamento.juros,
            multa=pagamento.multa,
            desconto=pagamento.desconto
        )
        if parcela_atualizada is None:
            raise HTTPException(status_code=404, detail="Parcela não encontrada")
        return parcela_to_dict(parcela_atualizada)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/financiamentos/{financiamento_id}/parcelas/{parcela_id}", response_model=dict)
async def atualizar_parcela_financiamento(
    financiamento_id: int,
    parcela_id: int,
    parcela_update: ParcelaUpdate,
    token: str = Depends(verify_token)
):
    """Atualiza uma parcela de financiamento"""
    try:
        parcela_atualizada = db_module.atualizar_parcela_financiamento(
            parcela_id=parcela_id,
            status=parcela_update.status,
            link_boleto=parcela_update.link_boleto,
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
    token: str = Depends(verify_token)
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
async def obter_dashboard_financiamentos(token: str = Depends(verify_token)):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
