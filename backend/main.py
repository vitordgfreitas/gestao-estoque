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
try:
    from dotenv import load_dotenv
    # Só carrega .env se não estiver no Render (onde variáveis vêm do painel)
    if not os.getenv('RENDER'):
        # Tenta carregar .env da raiz do projeto
        env_path = os.path.join(root_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print(f"✅ Carregado .env da raiz: {env_path}")
        else:
            print(f"⚠️ Arquivo .env não encontrado em: {env_path}")
        
        # Também tenta carregar .env do backend
        backend_env = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(backend_env):
            load_dotenv(backend_env, override=True)
            print(f"✅ Carregado .env do backend: {backend_env}")
except ImportError:
    print("⚠️ python-dotenv não instalado. Instale com: pip install python-dotenv")
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
        "http://crm-frontend-nbrm.onrender.com",  # Caso use HTTP
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

# Debug detalhado
print(f"\n{'='*60}")
print(f"🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO")
print(f"{'='*60}")
print(f"Ambiente: {'PRODUÇÃO (Render)' if is_production else 'DESENVOLVIMENTO'}")
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
    # Remove espaços extras e normaliza
    usuario_recebido = credentials.usuario.strip() if credentials.usuario else ""
    senha_recebida = credentials.senha.strip() if credentials.senha else ""
    usuario_esperado = APP_USUARIO.strip() if APP_USUARIO else ""
    senha_esperada = APP_SENHA.strip() if APP_SENHA else ""
    
    # Debug detalhado (sem mostrar senha completa, mas mostra primeiros/last chars para debug)
    print(f"\n[LOGIN] ========== TENTATIVA DE LOGIN ==========")
    print(f"  Usuario recebido: '{usuario_recebido}' (len={len(usuario_recebido)}, repr={repr(usuario_recebido)})")
    print(f"  Usuario esperado: '{usuario_esperado}' (len={len(usuario_esperado)}, repr={repr(usuario_esperado)})")
    print(f"  Senha recebida: len={len(senha_recebida)}, primeiro_char={repr(senha_recebida[0]) if senha_recebida else 'None'}, ultimo_char={repr(senha_recebida[-1]) if senha_recebida else 'None'}")
    print(f"  Senha esperada: len={len(senha_esperada)}, primeiro_char={repr(senha_esperada[0]) if senha_esperada else 'None'}, ultimo_char={repr(senha_esperada[-1]) if senha_esperada else 'None'}")
    print(f"  Match usuario: {usuario_recebido == usuario_esperado}")
    print(f"  Match senha: {senha_recebida == senha_esperada}")
    print(f"  APP_USUARIO original: {repr(APP_USUARIO)}")
    print(f"  APP_SENHA original (primeiros 2 chars): {repr(APP_SENHA[:2]) if APP_SENHA else 'None'}...")
    print(f"[LOGIN] =========================================\n")
    
    if usuario_recebido == usuario_esperado and senha_recebida == senha_esperada:
        token = generate_token()
        active_tokens[token] = {
            "usuario": credentials.usuario,
            "created_at": datetime.now()
        }
        print(f"[LOGIN] Login bem-sucedido para usuario: {usuario_recebido}")
        return {
            "success": True,
            "token": token,
            "usuario": credentials.usuario
        }
    else:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
