import streamlit as st
from datetime import date, datetime
import os

# Lista de UFs brasileiras (usada em múltiplos lugares)
UFS_BRASILEIRAS = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

# Lista de marcas de carros brasileiras
MARCAS_CARROS = [
    'Fiat', 'Volkswagen', 'Chevrolet', 'Ford', 'Toyota', 'Honda', 'Hyundai', 
    'Renault', 'Nissan', 'Peugeot', 'Citroën', 'Jeep', 'Mitsubishi', 'Kia',
    'BMW', 'Mercedes-Benz', 'Audi', 'Volvo', 'Land Rover', 'Jaguar', 'Porsche',
    'Subaru', 'Suzuki', 'Chery', 'JAC', 'Troller', 'RAM', 'Dodge', 'Chrysler',
    'Mini', 'Smart', 'BYD', 'GWM', 'Caoa Chery', 'Outra'
]

def obter_campos_agrupamento(categoria, dados_categoria):
    """Determina campos de agrupamento para uma categoria baseado nos dados
    
    Args:
        categoria: Nome da categoria
        dados_categoria: Dicionário com dados da categoria
        
    Returns:
        Lista de nomes de campos para agrupamento, ou None se não houver agrupamento
    """
    if not dados_categoria or not isinstance(dados_categoria, dict):
        return None
    
    # Campos comuns para agrupamento
    campos_agrupamento_comuns = {
        'Carros': ['Marca', 'Modelo'],  # Compatibilidade
        # Adicione outros padrões aqui conforme necessário
    }
    
    # Verifica padrões conhecidos
    if categoria in campos_agrupamento_comuns:
        campos = campos_agrupamento_comuns[categoria]
        # Verifica se todos os campos existem nos dados
        if all(campo in dados_categoria for campo in campos):
            return campos
    
    # Tenta inferir campos de agrupamento comuns
    campos_possiveis = ['Marca', 'Modelo', 'Tipo', 'Categoria', 'Fabricante']
    campos_encontrados = [campo for campo in campos_possiveis if campo in dados_categoria]
    
    return campos_encontrados if campos_encontrados else None

def obter_valor_campo_agrupamento(item, campos_agrupamento):
    """Obtém valor de agrupamento de um item baseado nos campos especificados
    
    Args:
        item: Objeto Item
        campos_agrupamento: Lista de nomes de campos para agrupamento
        
    Returns:
        String com valores concatenados dos campos, ou None
    """
    if not campos_agrupamento:
        return None
    
    dados_cat = getattr(item, 'dados_categoria', None)
    if not dados_cat or not isinstance(dados_cat, dict):
        return None
    
    valores = []
    for campo in campos_agrupamento:
        valor = dados_cat.get(campo)
        if valor:
            valores.append(str(valor))
    
    return ' '.join(valores) if valores else None

# Configuração da página
st.set_page_config(
    page_title="Gestão de Estoque - Aluguel de Itens",
    page_icon="📦",
    layout="wide"
)

# CSS básico apenas para remover cursor piscante e esconder sidebar + Paleta Azul Profissional
st.markdown("""
<style>
    /* Remove cursor piscante de TODOS os elementos não editáveis */
    * {
        caret-color: transparent;
    }
    
    /* Restaura cursor apenas em inputs editáveis */
    input[type="text"],
    input[type="number"],
    input[type="date"],
    input[type="email"],
    input[type="password"],
    input[type="search"],
    textarea,
    select,
    [contenteditable="true"],
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTextArea textarea,
    .stSelectbox select {
        caret-color: auto !important;
    }
    
    /* Remove cursor piscante mas mantém seleção de texto */
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] div,
    .element-container .stMarkdown p,
    .element-container .stMarkdown div,
    .stMarkdown,
    .stText,
    h1, h2, h3, h4, h5, h6,
    p, span, label, div {
        user-select: text;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
        caret-color: transparent !important;
    }
    
    /* Remove outline ao focar em elementos não editáveis */
    .stMarkdown:focus,
    .stText:focus,
    h1:focus, h2:focus, h3:focus, h4:focus, h5:focus, h6:focus,
    p:focus, span:focus, label:focus, div:focus {
        outline: none;
        caret-color: transparent !important;
    }
    
    /* Esconder sidebar */
    #MainMenu {
        visibility: hidden;
    }
    
    header[data-testid="stHeader"] {
        display: none;
    }
    
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* Ajustar largura do conteúdo principal quando sidebar está escondida */
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* ===== PALETA AZUL PROFISSIONAL - CORES APLICADAS ===== */
    /* Fundo geral */
    .stApp {
        background-color: #f8f9fa !important;
    }
    
    .main .block-container {
        background-color: #f8f9fa !important;
    }
    
    /* Botões - FORÇA ABSOLUTA para garantir azul e texto branco */
    /* Remove qualquer cor vermelha padrão do Streamlit */
    button,
    .stButton > button,
    button[data-baseweb="button"],
    button[kind="primary"],
    button[type="button"],
    button[type="submit"],
    [data-testid="baseButton-primary"],
    [data-baseweb="button"],
    div[data-testid="stButton"] > button,
    div[data-testid="stButton"] button,
    form button[type="submit"],
    form button {
        background-color: #2c3e50 !important; /* Azul escuro */
        color: white !important;
        border: 1px solid #2c3e50 !important;
        transition: all 0.2s ease-in-out;
    }
    
    /* Força texto branco em TODOS os botões - MÁXIMA PRIORIDADE */
    button,
    button *,
    button span,
    button p,
    button div,
    button label,
    .stButton > button,
    .stButton > button *,
    .stButton > button span,
    button[type="submit"],
    button[type="submit"] *,
    button[type="submit"] span,
    form button,
    form button *,
    form button span {
        color: white !important;
        opacity: 1 !important;
    }
    
    /* Remove especificamente cores vermelhas */
    button[style*="background-color"],
    button[style*="background"],
    .stButton > button[style*="background-color"],
    .stButton > button[style*="background"] {
        background-color: #2c3e50 !important;
        color: white !important;
    }
    
    /* Garantir que o texto dentro dos botões seja sempre branco - TODOS os elementos filhos */
    .stButton > button *,
    button[data-baseweb="button"] *,
    button[kind="primary"] *,
    [data-testid="baseButton-primary"] *,
    div[data-testid="stButton"] > button * {
        color: white !important;
    }
    
    /* Garantir que spans, divs e textos dentro dos botões sejam brancos */
    button *,
    button span,
    button p,
    button div,
    button label,
    .stButton > button span,
    .stButton > button p,
    .stButton > button div,
    .stButton > button label,
    .stButton > button *,
    button[data-baseweb="button"] span,
    button[data-baseweb="button"] *,
    button[kind="primary"] span,
    button[kind="primary"] p,
    button[kind="primary"] div,
    button[kind="primary"] label,
    button[kind="primary"] *,
    button[type="submit"] *,
    button[type="submit"] span,
    form button[type="submit"] *,
    form button[type="submit"] span {
        color: white !important;
        opacity: 1 !important;
    }
    
    /* Especialmente para botões primary - texto sempre branco */
    button[kind="primary"],
    button[kind="primary"] *,
    button[kind="primary"] span,
    button[kind="primary"] p,
    button[kind="primary"] div {
        color: white !important;
    }
    
    .stButton > button:hover,
    button[data-baseweb="button"]:hover,
    button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-baseweb="button"]:hover,
    div[data-testid="stButton"] > button:hover {
        background-color: #34495e !important; /* Azul escuro mais suave no hover */
        border-color: #34495e !important;
        color: white !important;
    }
    
    .stButton > button:hover *,
    button[data-baseweb="button"]:hover *,
    button[kind="primary"]:hover * {
        color: white !important;
    }
    
    .stButton > button:hover span,
    .stButton > button:hover p,
    .stButton > button:hover div {
        color: white !important;
    }
    
    /* Botão Secundário (se houver) */
    .stButton > button[kind="secondary"],
    button[kind="secondary"],
    [data-testid="baseButton-secondary"] {
        background-color: white !important;
        color: #2c3e50 !important;
        border-color: #2c3e50 !important;
    }
    
    .stButton > button[kind="secondary"] *,
    button[kind="secondary"] * {
        color: #2c3e50 !important;
    }
    
    .stButton > button[kind="secondary"]:hover,
    button[kind="secondary"]:hover,
    [data-testid="baseButton-secondary"]:hover {
        background-color: #ecf0f1 !important; /* Cinza muito claro no hover */
        border-color: #34495e !important;
        color: #2c3e50 !important;
    }
    
    .stButton > button[kind="secondary"]:hover * {
        color: #2c3e50 !important;
    }
    
    /* Inputs - bordas e foco */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-color: #e0e0e0 !important; /* Cinza claro */
        color: #2c3e50 !important; /* Texto principal */
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: #3498db !important; /* Azul médio no foco */
        box-shadow: 0 0 0 0.1rem rgba(52, 152, 219, 0.25) !important; /* Sombra suave */
    }
    
    /* Mensagens de status - cores suaves */
    .stSuccess {
        background-color: #d4edda !important; /* Verde claro */
        border-left: 4px solid #27ae60 !important; /* Verde suave */
        color: #155724 !important; /* Texto verde escuro */
    }
    
    .stWarning {
        background-color: #fff3cd !important; /* Amarelo claro */
        border-left: 4px solid #f39c12 !important; /* Laranja suave */
        color: #856404 !important; /* Texto amarelo escuro */
    }
    
    .stError {
        background-color: #f8d7da !important; /* Vermelho claro */
        border-left: 4px solid #e74c3c !important; /* Vermelho suave */
        color: #721c24 !important; /* Texto vermelho escuro */
    }
    
    .stInfo {
        background-color: #d1ecf1 !important; /* Azul claro */
        border-left: 4px solid #3498db !important; /* Azul */
        color: #0c5460 !important; /* Texto azul escuro */
    }
    
    /* Expanders - bordas */
    .streamlit-expanderHeader {
        border-color: #e0e0e0 !important; /* Cinza claro */
        background-color: white !important;
    }
    
    .streamlit-expanderContent {
        border-color: #e0e0e0 !important;
        background-color: white !important;
    }
    
    /* Dividers */
    hr {
        border-color: #e0e0e0 !important; /* Cinza claro */
    }
    
    /* Tabs - estilo limpo e profissional */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid #e0e0e0 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent !important;
        color: #2c3e50 !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 0.5rem 1rem !important;
        margin-right: 0.5rem !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: transparent !important;
        border-bottom-color: #bdc3c7 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #2c3e50 !important; /* Cor do texto da aba */
        margin: 0 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 2px solid #3498db !important; /* Linha azul na aba ativa */
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #3498db !important; /* Cor do texto da aba ativa */
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="false"] {
        border-bottom: 2px solid transparent !important;
    }
    
    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important; /* Azul escuro */
    }
    
    /* Texto geral */
    p, label, .stMarkdown {
        color: #2c3e50 !important; /* Azul escuro */
    }
    
    /* Métricas */
    [data-testid="stMetric"] label {
        color: #7f8c8d !important; /* Cinza médio */
    }
    [data-testid="stMetric"] div[data-testid="stMarkdownContainer"] p {
        color: #2c3e50 !important; /* Azul escuro */
    }
</style>
""", unsafe_allow_html=True)

# JavaScript adicional para garantir que botões sejam azuis (força bruta)
st.markdown("""
<script>
    function aplicarCoresBotoes() {
        // Aplica cores azuis em TODOS os botões do Streamlit, removendo vermelho
        document.querySelectorAll('button').forEach(btn => {
            // Verifica se é botão do Streamlit (incluindo botões de formulário)
            // MAS NÃO aplica em botões de tabs
            const isTabButton = btn.closest('[data-baseweb="tab-list"]');
            if (isTabButton) {
                return; // Não modifica botões de tabs
            }
            
            const isStreamlitButton = btn.closest('[data-testid="stButton"]') || 
                                     btn.closest('form') ||
                                     btn.hasAttribute('data-baseweb') ||
                                     btn.getAttribute('kind') === 'primary' ||
                                     btn.getAttribute('kind') === 'secondary' ||
                                     btn.type === 'submit';
            
            if (isStreamlitButton) {
                // Remove qualquer estilo inline vermelho
                const bgColor = window.getComputedStyle(btn).backgroundColor;
                const isRed = bgColor.includes('rgb(255') || bgColor.includes('rgb(239') || bgColor.includes('#ff') || bgColor.includes('#ef');
                
                // Se for botão primary, submit ou tiver cor vermelha, força azul
                if (btn.getAttribute('kind') === 'primary' || btn.type === 'submit' || isRed || btn.closest('form')) {
                    btn.style.setProperty('background-color', '#2c3e50', 'important');
                    btn.style.setProperty('color', 'white', 'important');
                    btn.style.setProperty('border-color', '#2c3e50', 'important');
                    
                    // MODIFICA O HTML DIRETAMENTE para garantir texto branco
                    const btnText = btn.textContent || btn.innerText;
                    if (btnText && btnText.trim() && !btn.hasAttribute('data-text-fixed')) {
                        // Marca o botão para não modificar novamente
                        btn.setAttribute('data-text-fixed', 'true');
                        // Remove todos os elementos filhos e cria um novo span com texto branco
                        btn.innerHTML = `<span style="color: white !important; opacity: 1 !important; display: inline-block;">${btnText}</span>`;
                    }
                    
                    // Força texto branco DIRETAMENTE no botão
                    btn.style.color = 'white';
                    btn.style.setProperty('color', 'white', 'important');
                    
                    // Garante que texto dentro seja branco - força em TODOS os elementos
                    const allElements = btn.querySelectorAll('*');
                    allElements.forEach(el => {
                        el.style.color = 'white';
                        el.style.setProperty('color', 'white', 'important');
                        el.style.setProperty('opacity', '1', 'important');
                        // Também força em elementos filhos aninhados
                        el.querySelectorAll('*').forEach(child => {
                            child.style.color = 'white';
                            child.style.setProperty('color', 'white', 'important');
                            child.style.setProperty('opacity', '1', 'important');
                        });
                    });
                    
                    // Se o botão tem texto direto, força branco
                    if (btn.textContent || btn.innerText) {
                        const text = btn.textContent || btn.innerText;
                        if (text.trim()) {
                            btn.style.color = 'white';
                            btn.style.setProperty('color', 'white', 'important');
                        }
                    }
                } else if (btn.getAttribute('kind') === 'secondary') {
                    // Botão secundário mantém estilo branco
                    btn.style.setProperty('background-color', 'white', 'important');
                    btn.style.setProperty('color', '#2c3e50', 'important');
                    btn.style.setProperty('border-color', '#2c3e50', 'important');
                }
            }
        });
    }
    
    // Executa várias vezes para garantir
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', aplicarCoresBotoes);
    } else {
        aplicarCoresBotoes();
    }
    
    // Executa várias vezes para garantir
    setTimeout(aplicarCoresBotoes, 50);
    setTimeout(aplicarCoresBotoes, 100);
    setTimeout(aplicarCoresBotoes, 200);
    setTimeout(aplicarCoresBotoes, 500);
    setTimeout(aplicarCoresBotoes, 1000);
    setTimeout(aplicarCoresBotoes, 2000);
    setTimeout(aplicarCoresBotoes, 3000);
    
    // Executa continuamente a cada 500ms por 10 segundos
    let count = 0;
    const interval = setInterval(() => {
        aplicarCoresBotoes();
        count++;
        if (count >= 20) {
            clearInterval(interval);
        }
    }, 500);
    
    // Observa mudanças no DOM de forma mais agressiva
    const observer = new MutationObserver(() => {
        aplicarCoresBotoes();
    });
    observer.observe(document.body, { 
        childList: true, 
        subtree: true, 
        attributes: true,
        attributeFilter: ['style', 'class']
    });
    
    // Também observa quando elementos são adicionados
    document.addEventListener('DOMNodeInserted', aplicarCoresBotoes);
    document.addEventListener('DOMSubtreeModified', aplicarCoresBotoes);
</script>
""", unsafe_allow_html=True)

# Sistema de autenticação simples
from auth_simples import verificar_autenticacao, mostrar_tela_login, mostrar_botao_logout

if not verificar_autenticacao():
    mostrar_tela_login()
    st.stop()

# Escolhe qual banco de dados usar baseado em variável de ambiente
USE_GOOGLE_SHEETS = os.getenv('USE_GOOGLE_SHEETS', 'true').lower() == 'true'

# Inicializa Google Sheets primeiro
sheets = None
if USE_GOOGLE_SHEETS:
    try:
        import sheets_database as db
        sheets = db.get_sheets()
    except Exception as e:
        error_msg = str(e)

# Barra superior simétrica com informações do usuário, Google Sheets e logout
if st.session_state.get('authenticated'):
    col_left, col_center, col_right = st.columns([3, 1, 3])
    
    with col_left:
        st.write(f"👤 {st.session_state.get('usuario', '')}")
    
    with col_center:
        if sheets:
            st.markdown(f"[📊 Google Sheets]({sheets['spreadsheet_url']})")
    
    with col_right:
        col_logout_space, col_logout_btn = st.columns([3, 1])
        with col_logout_btn:
            if st.button("Sair", use_container_width=True, key="logout_button"):
                st.session_state['authenticated'] = False
                st.session_state['usuario'] = None
                st.rerun()

if USE_GOOGLE_SHEETS:
    try:
        if not sheets:
            import sheets_database as db
            sheets = db.get_sheets()
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Erro ao conectar ao Google Sheets")
        st.error(f"**Detalhes:** {error_msg}")
        
        # Mensagens de ajuda específicas
        if "403" in error_msg or "permissão" in error_msg.lower() or "permission" in error_msg.lower():
            st.warning("""
            **Problema de Permissão:**
            1. Verifique se a planilha foi compartilhada com o email da conta de serviço
            2. O email da conta de serviço está no arquivo `credentials.json` (campo `client_email`)
            3. A permissão deve ser **Editor**
            4. Verifique se o ID da planilha está correto
            """)
        elif "No module named 'gspread'" in error_msg:
            st.warning("""
            **Dependências faltando:**
            Execute `make install` ou `pip install -r requirements.txt` para instalar as bibliotecas do Google Sheets.
            """)
        elif "Invalid control character" in error_msg or "JSON" in error_msg:
            st.warning("""
            **Erro nas credenciais JSON:**
            Verifique o formato do seu `GOOGLE_CREDENTIALS` nos secrets.
            Ele deve ser um JSON minificado e com `\\n` escapado para a `private_key`.
            Use o script `gerar_secrets.bat` para gerar o formato correto.
            """)
        elif "Invalid requests[0].addSheet" in error_msg or "already exists" in error_msg:
            st.warning("""
            **Erro ao criar aba:**
            A aba já existe na planilha. Isso pode ser um erro temporário.
            Tente recarregar a aplicação. Se persistir, verifique a planilha.
            """)
        elif "ID da planilha não fornecido" in error_msg:
            st.warning("""
            **ID da Planilha faltando:**
            Configure a variável de ambiente `GOOGLE_SHEET_ID` ou use o script `configurar_id.bat`.
            """)
        elif "429" in error_msg or "Quota exceeded" in error_msg or "RATE_LIMIT_EXCEEDED" in error_msg:
            st.error("""
            **⚠️ Limite de Requisições do Google Sheets Excedido!**
            
            O Google Sheets tem um limite de **60 requisições de leitura por minuto**.
            
            **Soluções:**
            1. **Aguarde 1-2 minutos** antes de tentar novamente
            2. **Reduza operações** que fazem muitas leituras (como visualizar muitos dados)
            3. **Use SQLite local** em vez do Google Sheets para desenvolvimento/testes
            4. **Solicite aumento de quota** no Google Cloud Console se necessário
            
            **Para usar SQLite local:**
            - Configure `USE_GOOGLE_SHEETS=false` nas variáveis de ambiente
            - Ou remova a variável `USE_GOOGLE_SHEETS` do Streamlit Cloud Secrets
            """)
        else:
            st.info("💡 Configure as credenciais do Google Sheets. Veja GOOGLE_SHEETS_SETUP.md para instruções.")
        st.stop()
else:
    from models import init_db
    import database as db
    # Inicializar banco de dados SQLite
    init_db()

# Título principal
st.title("Sistema de Gestão de Estoque")

# Menu horizontal
menu_opcoes = ["Início", "Registrar Item", "Registrar Compromisso", "Verificar Disponibilidade", "Visualizar Dados"]

# Define menu padrão se não houver seleção
if 'menu_selecionado' not in st.session_state:
    st.session_state['menu_selecionado'] = "Início"

# Criando botões de navegação horizontal
col1, col2, col3, col4, col5 = st.columns(5)

menu_atual = st.session_state['menu_selecionado']

with col1:
    button_type = "primary" if menu_atual == "Início" else "secondary"
    if st.button("Início", use_container_width=True, key="menu_inicio", type=button_type):
        st.session_state['menu_selecionado'] = "Início"
        st.rerun()
with col2:
    button_type = "primary" if menu_atual == "Registrar Item" else "secondary"
    if st.button("Registrar Item", use_container_width=True, key="menu_registrar_item", type=button_type):
        st.session_state['menu_selecionado'] = "Registrar Item"
        st.rerun()
with col3:
    button_type = "primary" if menu_atual == "Registrar Compromisso" else "secondary"
    if st.button("Registrar Compromisso", use_container_width=True, key="menu_registrar_compromisso", type=button_type):
        st.session_state['menu_selecionado'] = "Registrar Compromisso"
        st.rerun()
with col4:
    button_type = "primary" if menu_atual == "Verificar Disponibilidade" else "secondary"
    if st.button("Verificar Disponibilidade", use_container_width=True, key="menu_verificar", type=button_type):
        st.session_state['menu_selecionado'] = "Verificar Disponibilidade"
        st.rerun()
with col5:
    button_type = "primary" if menu_atual == "Visualizar Dados" else "secondary"
    if st.button("Visualizar Dados", use_container_width=True, key="menu_visualizar", type=button_type):
        st.session_state['menu_selecionado'] = "Visualizar Dados"
        st.rerun()

menu = st.session_state['menu_selecionado']

# Página Início
if menu == "Início":
    st.header("Bem-vindo ao Sistema de Gestão de Estoque")
    st.markdown("""
    Este sistema permite gerenciar o estoque de itens para aluguel em eventos e licitações.

    **Funcionalidades:**
    - Registrar novos itens no estoque
    - Registrar compromissos (aluguéis) dos itens
    - Verificar disponibilidade em datas específicas
    - Visualizar todos os itens e compromissos

    Use o menu acima para navegar entre as funcionalidades.
    """)

    # Estatísticas rápidas
    st.subheader("Estatísticas Rápidas")
    col1, col2, col3 = st.columns(3)
    
    itens = db.listar_itens()
    compromissos = db.listar_compromissos()
    hoje = date.today()
    
    with col1:
        st.metric("Total de Itens", len(itens))
    
    with col2:
        st.metric("Total de Compromissos", len(compromissos))
    
    with col3:
        compromissos_hoje = [c for c in compromissos if c.data_inicio <= hoje <= c.data_fim]
        st.metric("Compromissos Ativos Hoje", len(compromissos_hoje))

# Página Registrar Item
elif menu == "Registrar Item":
    st.header("Registrar Novo Item")
    
    # Inicializa flag de sucesso se não existir
    if 'item_registrado_sucesso' not in st.session_state:
        st.session_state['item_registrado_sucesso'] = False
    
    # Se houve sucesso anterior, mostra mensagem e reseta flag
    if st.session_state['item_registrado_sucesso']:
        st.success("✅ Item registrado com sucesso!")
        st.session_state['item_registrado_sucesso'] = False
    
    # Gera uma key única baseada no timestamp para forçar reset dos campos
    form_key = f"form_item_{st.session_state.get('form_item_counter', 0)}"
    
    # Lista de UFs brasileiras
    ufs_brasileiras = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    
    # Obtém categorias dinamicamente do Google Sheets
    try:
        if USE_GOOGLE_SHEETS:
            categorias_disponiveis = db.obter_categorias()
        else:
            # Para SQLite, obtém categorias dos itens existentes
            itens_existentes = db.listar_itens()
            categorias_disponiveis = sorted(set([getattr(item, 'categoria', '') or '' for item in itens_existentes if getattr(item, 'categoria', '')]))
    except Exception:
        categorias_disponiveis = []
    
    # Se não houver categorias, mostra aviso
    if not categorias_disponiveis:
        st.warning("⚠️ Não há categorias cadastradas. Por favor, adicione pelo menos uma categoria no Google Sheets.")
        st.stop()
    
    # Inicializa categoria no session_state se não existir (usa primeira categoria disponível)
    categoria_key = f'categoria_form_{form_key}'
    if categoria_key not in st.session_state:
        st.session_state[categoria_key] = categorias_disponiveis[0] if categorias_disponiveis else ""
    
    # Selectbox de categoria FORA do form para permitir mudança dinâmica
    categoria_index = 0
    if st.session_state[categoria_key] in categorias_disponiveis:
        categoria_index = categorias_disponiveis.index(st.session_state[categoria_key])
    
    categoria = st.selectbox(
        "Categoria *", 
        options=categorias_disponiveis, 
        index=categoria_index,
        key=f"select_categoria_{form_key}"
    )
    
    # Atualiza session_state quando categoria mudar e força rerun
    if st.session_state[categoria_key] != categoria:
        st.session_state[categoria_key] = categoria
        st.rerun()
    
    categoria_atual = st.session_state[categoria_key]
    
    # Obtém campos específicos da categoria
    campos_categoria = []
    try:
        if USE_GOOGLE_SHEETS:
            campos_categoria = db.obter_campos_categoria(categoria_atual)
    except Exception:
        campos_categoria = []
    
    with st.form(form_key):
        
        # Campos que mudam baseado na categoria
        # Mantém compatibilidade com código antigo para "Carros"
        campos_dinamicos = {}
        
        # Se há campos específicos da categoria (incluindo Carros se tiver aba), usa lógica dinâmica
        if campos_categoria:
            # Renderiza campos dinamicamente baseado nos cabeçalhos da aba da categoria
            st.markdown(f"**Informações Específicas de {categoria_atual}**")
            
            # Para Carros, quantidade é sempre 1 e nome é gerado automaticamente
            if categoria_atual == "Carros":
                quantidade = 1
                # Renderiza campos específicos da categoria
                marca = None
                modelo = None
                placa = None
                ano = None
                
                for campo in campos_categoria:
                    campo_key = f"{campo}_{form_key}"
                    campo_lower = campo.lower()
                    
                    # Tratamento especial para campos conhecidos de Carros
                    if campo == 'Marca':
                        marca = st.selectbox(f"{campo} *", options=MARCAS_CARROS, index=0, key=campo_key)
                        campos_dinamicos[campo] = marca
                    elif campo == 'Modelo':
                        modelo = st.text_input(f"{campo} *", placeholder="Ex: Uno, Gol, Celta, Corolla...", value="", key=campo_key)
                        campos_dinamicos[campo] = modelo
                    elif campo == 'Placa':
                        placa = st.text_input(f"{campo} *", placeholder="ABC-1234", value="", max_chars=10, key=campo_key)
                        campos_dinamicos[campo] = placa
                    elif campo == 'Ano' or 'ano' in campo_lower or 'year' in campo_lower:
                        ano = st.number_input(f"{campo} *", min_value=1900, max_value=2100, value=2020, step=1, key=campo_key)
                        campos_dinamicos[campo] = ano
                    else:
                        # Outros campos como texto
                        campos_dinamicos[campo] = st.text_input(f"{campo} *", placeholder=f"Digite {campo.lower()}...", value="", key=campo_key)
                
                # Gera nome automaticamente como "Marca Modelo" se ambos existirem
                if marca and modelo:
                    nome = f"{marca} {modelo}".strip()
                else:
                    nome = ""
                
                descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Carro em bom estado, revisado recentemente...", value="", key=f"descricao_{form_key}")
            else:
                # Para outras categorias com campos específicos
                nome = st.text_input("Nome do Item *", placeholder="Ex: Nome do item...", value="", key=f"nome_{form_key}")
                quantidade = st.number_input("Quantidade Total *", min_value=1, value=1, step=1, key=f"quantidade_{form_key}")
                
                # Renderiza campos específicos da categoria
                for campo in campos_categoria:
                    campo_key = f"{campo}_{form_key}"
                    # Tenta inferir o tipo de campo pelo nome
                    campo_lower = campo.lower()
                    if 'ano' in campo_lower or 'year' in campo_lower:
                        campos_dinamicos[campo] = st.number_input(f"{campo} *", min_value=1900, max_value=2100, value=2020, step=1, key=campo_key)
                    elif 'quantidade' in campo_lower or 'qtd' in campo_lower or 'amount' in campo_lower:
                        campos_dinamicos[campo] = st.number_input(f"{campo} *", min_value=1, value=1, step=1, key=campo_key)
                    elif 'data' in campo_lower or 'date' in campo_lower:
                        campos_dinamicos[campo] = st.date_input(f"{campo} *", value=date.today(), key=campo_key)
                    else:
                        # Campo de texto por padrão
                        campos_dinamicos[campo] = st.text_input(f"{campo} *", placeholder=f"Digite {campo.lower()}...", value="", key=campo_key)
                
                descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Descrição do item...", value="", key=f"descricao_{form_key}")
                marca = None
                placa = None
                modelo = None
                ano = None
        elif categoria_atual == "Carros":
            # Lógica hardcoded para Carros quando não há aba específica (compatibilidade)
            st.markdown("**Informações do Veículo**")
            # Para carros, quantidade é sempre 1 (cada veículo é único)
            quantidade = 1
            
            col_marca, col_modelo = st.columns(2)
            with col_marca:
                marca = st.selectbox("Marca *", options=MARCAS_CARROS, index=0, key=f"marca_{form_key}")
            with col_modelo:
                modelo = st.text_input("Modelo *", placeholder="Ex: Uno, Gol, Celta, Corolla...", value="", key=f"modelo_{form_key}")
            
            col_placa, col_ano = st.columns(2)
            with col_placa:
                placa = st.text_input("Placa *", placeholder="ABC-1234", value="", max_chars=10, key=f"placa_{form_key}")
            with col_ano:
                ano = st.number_input("Ano *", min_value=1900, max_value=2100, value=2020, step=1, key=f"ano_{form_key}")
            
            descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Carro em bom estado, revisado recentemente...", value="", key=f"descricao_{form_key}")
            
            # Gera nome automaticamente como "Marca Modelo"
            nome = f"{marca} {modelo}".strip() if modelo else ""
            
            # Preenche campos dinâmicos para compatibilidade
            campos_dinamicos = {'Placa': placa, 'Marca': marca, 'Modelo': modelo, 'Ano': ano}
        else:
            # Categoria sem campos específicos (padrão)
            nome = st.text_input("Nome do Item *", placeholder="Ex: Alambrado, Mesa, Cadeira...", value="", key=f"nome_{form_key}")
            quantidade = st.number_input("Quantidade Total *", min_value=1, value=1, step=1, key=f"quantidade_{form_key}")
            descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Mesa retangular de madeira, tamanho 3x2 metros...", value="", key=f"descricao_{form_key}")
            marca = None
            placa = None
            modelo = None
            ano = None
        
        st.markdown("**Localização do Item**")
        col1, col2 = st.columns(2)
        with col1:
            cidade = st.text_input("Cidade *", placeholder="Ex: São Paulo, Rio de Janeiro...", value="", key=f"cidade_{form_key}")
        with col2:
            uf = st.selectbox("UF *", options=UFS_BRASILEIRAS, index=24, key=f"uf_{form_key}")  # SP como padrão
        endereco = st.text_input("Endereço (opcional)", placeholder="Ex: Rua das Flores, 123 - Centro...", value="", key=f"endereco_{form_key}")
        
        submitted = st.form_submit_button("Registrar Item", type="primary")
        
        if submitted:
            # Validação básica
            campos_ok = nome.strip() and cidade.strip() and uf
            
            if campos_categoria:
                # Valida campos dinâmicos (incluindo Carros se tiver campos_categoria)
                for campo in campos_categoria:
                    valor = campos_dinamicos.get(campo)
                    if valor is None or (isinstance(valor, str) and not valor.strip()) or valor == '':
                        campos_ok = False
                        break
            elif categoria == "Carros":
                # Validação hardcoded para Carros sem aba específica
                campos_ok = campos_ok and marca and placa and modelo and ano
            
            if campos_ok:
                try:
                    # Prepara campos_categoria para passar para criar_item
                    campos_cat_dict = None
                    if campos_categoria and campos_dinamicos:
                        campos_cat_dict = {}
                        for campo in campos_categoria:
                            valor = campos_dinamicos.get(campo)
                            # Converte valores de data para string se necessário
                            if isinstance(valor, date):
                                campos_cat_dict[campo] = valor.strftime('%Y-%m-%d')
                            elif isinstance(valor, (int, float)):
                                campos_cat_dict[campo] = valor
                            else:
                                campos_cat_dict[campo] = str(valor).strip() if valor is not None else ''
                    
                    # Para Carros com campos_categoria, usa campos dinâmicos
                    # Para Carros sem campos_categoria (hardcoded), usa parâmetros antigos
                    if categoria == "Carros" and campos_categoria:
                        # Usa campos dinâmicos
                        item = db.criar_item(
                            nome.strip(), 
                            quantidade, 
                            categoria,
                            descricao.strip() if descricao else None, 
                            cidade.strip(), 
                            uf, 
                            endereco.strip() if endereco else None,
                            None,  # placa vem de campos_categoria
                            None,  # marca vem de campos_categoria
                            None,  # modelo vem de campos_categoria
                            None,  # ano vem de campos_categoria
                            campos_categoria=campos_cat_dict
                        )
                    elif categoria == "Carros":
                        # Usa parâmetros hardcoded (compatibilidade)
                        item = db.criar_item(
                            nome.strip(), 
                            quantidade, 
                            categoria,
                            descricao.strip() if descricao else None, 
                            cidade.strip(), 
                            uf, 
                            endereco.strip() if endereco else None,
                            placa.strip() if placa else None,
                            marca.strip() if marca else None,
                            modelo.strip() if modelo else None,
                            int(ano) if ano else None,
                            campos_categoria=None
                        )
                    else:
                        # Outras categorias
                        item = db.criar_item(
                            nome.strip(), 
                            quantidade, 
                            categoria,
                            descricao.strip() if descricao else None, 
                            cidade.strip(), 
                            uf, 
                            endereco.strip() if endereco else None,
                            None,
                            None,
                            None,
                            None,
                            campos_categoria=campos_cat_dict
                        )
                    # Incrementa contador para gerar nova key no próximo render
                    st.session_state['form_item_counter'] = st.session_state.get('form_item_counter', 0) + 1
                    st.session_state['item_registrado_sucesso'] = True
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "Quota exceeded" in error_msg or "RATE_LIMIT_EXCEEDED" in error_msg:
                        st.error("""
                        **⚠️ Limite de Requisições do Google Sheets Excedido!**
                        
                        O Google Sheets tem um limite de **60 requisições de leitura por minuto**.
                        
                        **Soluções:**
                        1. **Aguarde 1-2 minutos** antes de tentar novamente
                        2. **Evite fazer muitas operações** em sequência
                        3. **Use SQLite local** para desenvolvimento/testes
                        
                        Aguarde alguns segundos e tente novamente.
                        """)
                    else:
                        st.error(f"❌ Erro ao registrar item: {error_msg}")
            else:
                st.warning("⚠️ Por favor, preencha os campos obrigatórios.")

# Página Registrar Compromisso
elif menu == "Registrar Compromisso":
    st.header("Registrar Compromisso (Aluguel)")
    
    itens = db.listar_itens()
    
    if not itens:
        st.warning("⚠️ Não há itens cadastrados. Por favor, registre um item primeiro.")
    else:
        # Inicializa valores no session_state
        if 'data_inicio_compromisso' not in st.session_state:
            st.session_state['data_inicio_compromisso'] = date.today()
        if 'data_fim_compromisso' not in st.session_state:
            st.session_state['data_fim_compromisso'] = date.today()
        
        # Campos de data fora do form para permitir atualização automática
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input(
                "Data de Início *", 
                value=st.session_state['data_inicio_compromisso'],
                key='input_data_inicio'
            )
            # Atualiza session_state quando a data de início mudar
            if data_inicio != st.session_state['data_inicio_compromisso']:
                st.session_state['data_inicio_compromisso'] = data_inicio
                # Se a data de fim for anterior à nova data de início, atualiza
                if st.session_state['data_fim_compromisso'] < data_inicio:
                    st.session_state['data_fim_compromisso'] = data_inicio
                    st.rerun()
        
        with col2:
            # Garante que data de fim seja pelo menos igual à data de início
            data_fim_min = st.session_state['data_inicio_compromisso']
            if st.session_state['data_fim_compromisso'] < data_fim_min:
                st.session_state['data_fim_compromisso'] = data_fim_min
            
            data_fim = st.date_input(
                "Data de Fim *", 
                value=st.session_state['data_fim_compromisso'],
                min_value=data_fim_min,
                key='input_data_fim'
            )
            # Atualiza session_state quando a data de fim mudar
            if data_fim != st.session_state['data_fim_compromisso']:
                st.session_state['data_fim_compromisso'] = data_fim
        
        st.divider()
        
        # Inicializa flag de sucesso se não existir
        if 'compromisso_registrado_sucesso' not in st.session_state:
            st.session_state['compromisso_registrado_sucesso'] = False
        
        # Se houve sucesso anterior, mostra mensagem e reseta flag
        if st.session_state['compromisso_registrado_sucesso']:
            st.success("✅ Compromisso registrado com sucesso!")
            st.session_state['compromisso_registrado_sucesso'] = False
            # Limpa os valores do session_state após sucesso
            if 'data_inicio_compromisso' in st.session_state:
                del st.session_state['data_inicio_compromisso']
            if 'data_fim_compromisso' in st.session_state:
                del st.session_state['data_fim_compromisso']
        
        # Gera uma key única baseada no contador para forçar reset dos campos
        form_key_comp = f"form_compromisso_{st.session_state.get('form_compromisso_counter', 0)}"
        
        # Filtro por categoria FORA do form para permitir atualização dinâmica
        categorias_disponiveis = sorted(set([getattr(item, 'categoria', '') or '' for item in itens if getattr(item, 'categoria', '')]))
        
        # Inicializa categoria no session_state se não existir
        categoria_key_comp = f'categoria_compromisso_{form_key_comp}'
        if categoria_key_comp not in st.session_state:
            st.session_state[categoria_key_comp] = categorias_disponiveis[0] if categorias_disponiveis else ""
        
        if not categorias_disponiveis:
            st.warning("⚠️ Não há categorias cadastradas.")
            categoria_filtro = None
            itens_filtrados = []
        else:
            # Selectbox de categoria FORA do form
            categoria_index_comp = 0
            if st.session_state[categoria_key_comp] in categorias_disponiveis:
                categoria_index_comp = categorias_disponiveis.index(st.session_state[categoria_key_comp])
            
            categoria_filtro = st.selectbox(
                "Categoria *", 
                options=categorias_disponiveis, 
                index=categoria_index_comp,
                key=f"select_categoria_comp_{form_key_comp}"
            )
            
            # Atualiza session_state quando categoria mudar e força rerun
            if st.session_state[categoria_key_comp] != categoria_filtro:
                st.session_state[categoria_key_comp] = categoria_filtro
                st.rerun()
            
            # Usa a categoria do session_state
            categoria_filtro_atual = st.session_state[categoria_key_comp]
            
            # Filtra itens pela categoria selecionada (com normalização de strings)
            itens_filtrados = []
            for item in itens:
                categoria_item = (getattr(item, 'categoria', '') or '').strip()
                categoria_filtro_stripped = categoria_filtro_atual.strip() if categoria_filtro_atual else ''
                if categoria_item == categoria_filtro_stripped:
                    itens_filtrados.append(item)
        
        with st.form(form_key_comp):
            if not itens_filtrados and categoria_filtro_atual:
                st.warning(f"⚠️ Não há itens cadastrados na categoria '{categoria_filtro_atual}'.")
            elif itens_filtrados:
                # Seleção do item - dinâmico baseado na categoria
                item_options = {}
                for item in itens_filtrados:
                    # Verifica se o item realmente pertence à categoria selecionada
                    categoria_item = (getattr(item, 'categoria', '') or '').strip()
                    categoria_filtro_stripped = categoria_filtro_atual.strip() if categoria_filtro_atual else ''
                    
                    # Só adiciona se a categoria corresponder
                    if categoria_item != categoria_filtro_stripped:
                        continue
                    
                    dados_cat = getattr(item, 'dados_categoria', None)
                    
                    # Tenta construir nome descritivo baseado nos dados da categoria
                    nome_display = item.nome
                    
                    if dados_cat and isinstance(dados_cat, dict):
                        # Para categorias com dados específicos, tenta criar nome mais descritivo
                        campos_chave = []
                        # Ordem de prioridade para campos que aparecem no nome
                        campos_prioridade = ['Marca', 'Modelo', 'Placa', 'Serial', 'Código']
                        for campo_prioridade in campos_prioridade:
                            if campo_prioridade in dados_cat and dados_cat[campo_prioridade]:
                                campos_chave.append(str(dados_cat[campo_prioridade]))
                        
                        if campos_chave:
                            nome_display = f"{item.nome} - {' '.join(campos_chave)}"
                    
                    # Compatibilidade: para Carros, usa carro se existir
                    if categoria_item == "Carros":
                        carro = getattr(item, 'carro', None)
                        if carro:
                            marca = getattr(carro, 'marca', 'N/A')
                            modelo = carro.modelo
                            placa = carro.placa
                            nome_display = f"{marca} {modelo} - {placa}"
                    
                    # Adiciona quantidade se não for categoria que sempre tem quantidade 1
                    # Verifica se há campos que indicam item único
                    tem_campo_item_unico = False
                    if dados_cat and isinstance(dados_cat, dict):
                        campos_item_unico = ['Placa', 'Serial', 'Código Único', 'Código', 'ID Único']
                        tem_campo_item_unico = any(campo in dados_cat for campo in campos_item_unico)
                    
                    if categoria_item != "Carros" and not tem_campo_item_unico and hasattr(item, 'quantidade_total'):
                        nome_display += f" (Estoque: {item.quantidade_total})"
                    
                    item_options[nome_display] = item.id
                
                item_selecionado = st.selectbox("Selecione o Item *", options=list(item_options.keys()))
                item_id = item_options[item_selecionado]
                
                # Determina se a categoria tem quantidade fixa em 1 (itens únicos)
                # Verifica se há campos que indicam item único (Placa, Serial, Código Único, etc.)
                item_selecionado_obj = next((item for item in itens_filtrados if item.id == item_id), None)
                quantidade_fixa_1 = False
                
                if item_selecionado_obj:
                    dados_cat = getattr(item_selecionado_obj, 'dados_categoria', None)
                    if dados_cat and isinstance(dados_cat, dict):
                        # Campos que indicam item único
                        campos_item_unico = ['Placa', 'Serial', 'Código Único', 'Código', 'ID Único', 'Número de Série']
                        quantidade_fixa_1 = any(campo in dados_cat for campo in campos_item_unico)
                    
                    # Compatibilidade: Carros sempre quantidade 1
                    if categoria_filtro_atual == "Carros":
                        quantidade_fixa_1 = True
                
                if quantidade_fixa_1:
                    quantidade = 1
                    st.info(f"ℹ️ Para {categoria_filtro_atual}, a quantidade é sempre 1 (cada item é único).")
                else:
                    quantidade = st.number_input("Quantidade *", min_value=1, value=1, step=1)
            
            descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Evento corporativo, Licitação pública...", value="")
            
            st.markdown("**Localização do Compromisso**")
            col1, col2 = st.columns(2)
            with col1:
                cidade_compromisso = st.text_input("Cidade *", placeholder="Ex: São Paulo, Rio de Janeiro...", value="")
            with col2:
                uf_compromisso = st.selectbox("UF *", options=UFS_BRASILEIRAS, index=24, key="uf_compromisso")  # SP como padrão
            endereco_compromisso = st.text_input("Endereço (opcional)", placeholder="Ex: Rua das Flores, 123 - Centro...", value="")
            contratante = st.text_input("Contratante (opcional)", placeholder="Ex: Empresa ABC, Prefeitura de Cidade...", value="")
            
            submitted = st.form_submit_button("Registrar Compromisso", type="primary")
            
            if submitted:
                if data_fim < data_inicio:
                    st.error("❌ A data de fim deve ser posterior ou igual à data de início.")
                elif not cidade_compromisso.strip() or not uf_compromisso:
                    st.warning("⚠️ Por favor, preencha os campos obrigatórios.")
                else:
                    try:
                        # Verificar disponibilidade em todo o período antes de criar
                        disponibilidade = db.verificar_disponibilidade_periodo(item_id, data_inicio, data_fim)
                        if disponibilidade['disponivel_minimo'] < quantidade:
                            st.error(f"❌ Quantidade insuficiente no período! Disponível mínimo: {disponibilidade['disponivel_minimo']}, Solicitado: {quantidade}")
                        else:
                            compromisso = db.criar_compromisso(
                                item_id=item_id,
                                quantidade=quantidade,
                                data_inicio=data_inicio,
                                data_fim=data_fim,
                                descricao=descricao.strip() if descricao else None,
                                cidade=cidade_compromisso.strip(),
                                uf=uf_compromisso,
                                endereco=endereco_compromisso.strip() if endereco_compromisso else None,
                                contratante=contratante.strip() if contratante else None
                            )
                            # Incrementa contador para gerar nova key no próximo render
                            st.session_state['form_compromisso_counter'] = st.session_state.get('form_compromisso_counter', 0) + 1
                            st.session_state['compromisso_registrado_sucesso'] = True
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar compromisso: {str(e)}")

# Página Verificar Disponibilidade
elif menu == "Verificar Disponibilidade":
    st.header("Verificar Disponibilidade")
    
    itens = db.listar_itens()
    
    if not itens:
        st.warning("⚠️ Não há itens cadastrados.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            modo_consulta = st.radio(
                "Tipo de Consulta",
                ["Todos os Itens", "Item Específico"],
                horizontal=True
            )
        
        with col2:
            data_consulta = st.date_input("Data de Consulta", value=date.today())
        
        # Filtro por categoria
        categorias_disponiveis = sorted(set([getattr(item, 'categoria', '') or '' for item in itens if getattr(item, 'categoria', '')]))
        categoria_filtro = st.selectbox("Filtrar por Categoria (opcional)", options=["Todas as Categorias"] + categorias_disponiveis, index=0)
        
        # Filtra itens pela categoria se selecionada
        if categoria_filtro != "Todas as Categorias":
            itens = [item for item in itens if (getattr(item, 'categoria', '') or '') == categoria_filtro]
        
        # Filtro por localização (Cidade - UF)
        localizacoes_disponiveis = set()
        for item in itens:
            if hasattr(item, 'cidade') and hasattr(item, 'uf') and item.cidade and item.uf:
                localizacoes_disponiveis.add(f"{item.cidade} - {item.uf}")
        
        # Também adiciona localizações dos compromissos
        compromissos = db.listar_compromissos()
        for comp in compromissos:
            if hasattr(comp, 'cidade') and hasattr(comp, 'uf') and comp.cidade and comp.uf:
                localizacoes_disponiveis.add(f"{comp.cidade} - {comp.uf}")
        
        localizacoes_disponiveis = sorted(list(localizacoes_disponiveis))
        
        if localizacoes_disponiveis:
            filtro_localizacao = st.selectbox(
                "📍 Filtrar por Localização (opcional)",
                options=["Todas as Localizações"] + localizacoes_disponiveis
            )
        else:
            filtro_localizacao = "Todas as Localizações"
            st.info("ℹ️ Nenhum item ou compromisso possui localização cadastrada.")
        
        if modo_consulta == "Item Específico":
            # Determina campos de agrupamento para a categoria selecionada
            campos_agrupamento = None
            if categoria_filtro != "Todas as Categorias" and itens:
                primeiro_item = itens[0]
                dados_cat = getattr(primeiro_item, 'dados_categoria', None)
                if dados_cat:
                    campos_agrupamento = obter_campos_agrupamento(categoria_filtro, dados_cat)
            
            # Constrói opções de itens dinamicamente
            item_options = {}
            if campos_agrupamento:
                # Agrupa por campos de agrupamento
                grupos = {}
                for item in itens:
                    chave_agrupamento = obter_valor_campo_agrupamento(item, campos_agrupamento)
                    if chave_agrupamento:
                        if chave_agrupamento not in grupos:
                            grupos[chave_agrupamento] = []
                        grupos[chave_agrupamento].append(item)
                    else:
                        # Se não tem campos de agrupamento, mostra individualmente
                        item_options[f"{item.nome}"] = item.id
                
                # Adiciona grupos ao item_options
                for chave, items_grupo in grupos.items():
                    item_options[chave] = items_grupo[0].id  # Usa o primeiro item do grupo como representante
            else:
                # Sem agrupamento, mostra todos os itens individualmente
                for item in itens:
                    nome_display = item.nome
                    dados_cat = getattr(item, 'dados_categoria', None)
                    if dados_cat and isinstance(dados_cat, dict):
                        # Adiciona campos identificadores se existirem
                        campos_id = ['Placa', 'Serial', 'Código']
                        valores_id = [str(dados_cat.get(c)) for c in campos_id if dados_cat.get(c)]
                        if valores_id:
                            nome_display += f" - {' '.join(valores_id)}"
                    item_options[nome_display] = item.id
            
            item_selecionado = st.selectbox("Selecione o Item", options=list(item_options.keys()))
            item_id = item_options[item_selecionado]
            
            if st.button("Verificar Disponibilidade", type="primary"):
                # Se há campos de agrupamento, busca todos os itens do mesmo grupo
                if campos_agrupamento:
                    # Busca o item selecionado para obter valores de agrupamento
                    item_selecionado_obj = next((item for item in itens if item.id == item_id), None)
                    if item_selecionado_obj:
                        chave_agrupamento_selecionada = obter_valor_campo_agrupamento(item_selecionado_obj, campos_agrupamento)
                        
                        # Busca todos os itens com a mesma chave de agrupamento
                        itens_mesmo_grupo = []
                        for item in itens:
                            chave_item = obter_valor_campo_agrupamento(item, campos_agrupamento)
                            if chave_item == chave_agrupamento_selecionada:
                                itens_mesmo_grupo.append(item)
                        
                        # Verifica disponibilidade de todos os itens do mesmo grupo
                        resultados_grupo = []
                        for item_grupo in itens_mesmo_grupo:
                            # Se há filtro de localização, verifica se o item está na localização
                            if filtro_localizacao and filtro_localizacao != "Todas as Localizações":
                                cidade_uf = filtro_localizacao.split(" - ")
                                if len(cidade_uf) == 2:
                                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                                    item_na_localizacao = (hasattr(item_grupo, 'cidade') and hasattr(item_grupo, 'uf')
                                                           and item_grupo.cidade == cidade_filtro 
                                                           and item_grupo.uf == uf_filtro.upper())
                                    if not item_na_localizacao:
                                        continue  # Pula itens que não estão na localização filtrada
                            
                            disponibilidade_item = db.verificar_disponibilidade(
                                item_grupo.id,
                                data_consulta,
                                filtro_localizacao if filtro_localizacao != "Todas as Localizações" else None
                            )
                            if disponibilidade_item:
                                resultados_grupo.append(disponibilidade_item)
                        
                        if resultados_grupo:
                            st.subheader(f"Disponibilidade para '{chave_agrupamento_selecionada}' em {data_consulta.strftime('%d/%m/%Y')}")
                            
                            if filtro_localizacao and filtro_localizacao != "Todas as Localizações":
                                st.info(f"📍 **Filtro aplicado:** Localização '{filtro_localizacao}'")
                            
                            # Calcula totais
                            total_disponivel = sum(r['quantidade_disponivel'] for r in resultados_grupo)
                            total_comprometido = sum(r['quantidade_comprometida'] for r in resultados_grupo)
                            total_itens = len(resultados_grupo)
                            
                            # Determina ícone baseado na categoria
                            categoria_item = getattr(resultados_grupo[0]['item'], 'categoria', '') or ''
                            icone = "🚗" if categoria_item == "Carros" else "📦"
                            
                            with st.expander(f"{icone} **{chave_agrupamento_selecionada}** - {total_disponivel} disponível(is) de {total_itens} total"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total de Itens", total_itens)
                                with col2:
                                    st.metric("Comprometidos", total_comprometido)
                                with col3:
                                    st.metric("Disponíveis", total_disponivel)
                                
                                st.divider()
                                
                                # Determina campo identificador principal (Placa, Serial, etc.)
                                campo_id_principal = None
                                campos_id_possiveis = ['Placa', 'Serial', 'Código', 'Código Único', 'Número de Série']
                                
                                # Mostra detalhes de cada item do grupo
                                for resultado in resultados_grupo:
                                    item_resultado = resultado['item']
                                    dados_cat = getattr(item_resultado, 'dados_categoria', None)
                                    
                                    # Determina campo identificador
                                    if dados_cat and isinstance(dados_cat, dict):
                                        for campo_id in campos_id_possiveis:
                                            if campo_id in dados_cat and dados_cat[campo_id]:
                                                campo_id_principal = campo_id
                                                break
                                    
                                    disponivel = resultado['quantidade_disponivel']
                                    comprometido = resultado['quantidade_comprometida']
                                    status = "✅ Disponível" if disponivel > 0 else "❌ Indisponível"
                                    
                                    # Constrói informação do item
                                    if campo_id_principal and dados_cat:
                                        valor_id = dados_cat.get(campo_id_principal, '')
                                        info_item = f"- **{campo_id_principal}: {valor_id}**"
                                        
                                        # Adiciona outros campos relevantes
                                        campos_adicionais = ['Ano', 'Modelo']
                                        for campo_add in campos_adicionais:
                                            if campo_add in dados_cat and dados_cat[campo_add]:
                                                info_item += f" ({campo_add}: {dados_cat[campo_add]})"
                                        
                                        info_item += f" - {status}"
                                    else:
                                        info_item = f"- **{item_resultado.nome}** - {status}"
                                    
                                    # Adiciona localização
                                    if hasattr(item_resultado, 'cidade') and hasattr(item_resultado, 'uf') and item_resultado.cidade and item_resultado.uf:
                                        localizacao_item = f"{item_resultado.cidade} - {item_resultado.uf}"
                                        if hasattr(item_resultado, 'endereco') and item_resultado.endereco:
                                            localizacao_item += f" ({item_resultado.endereco})"
                                        info_item += f" | 📍 {localizacao_item}"
                                    
                                    st.write(info_item)
                                    if comprometido > 0:
                                        st.caption(f"  Comprometido: {comprometido}")
                                
                                # Mostra compromissos ativos
                                todos_compromissos = []
                                for resultado in resultados_grupo:
                                    todos_compromissos.extend(resultado.get('compromissos_ativos', []))
                                
                                if todos_compromissos:
                                    st.divider()
                                    st.subheader("Compromissos Ativos nesta Data")
                                    for comp in todos_compromissos:
                                        with st.expander(f"Compromisso #{comp.id} - {comp.quantidade} unidades ({comp.data_inicio} a {comp.data_fim})"):
                                            st.write(f"**Item:** {comp.item.nome}")
                                            
                                            # Mostra campos identificadores se existirem
                                            dados_cat_comp = getattr(comp.item, 'dados_categoria', None)
                                            if dados_cat_comp and isinstance(dados_cat_comp, dict):
                                                for campo_id in campos_id_possiveis:
                                                    if campo_id in dados_cat_comp and dados_cat_comp[campo_id]:
                                                        st.write(f"**{campo_id}:** {dados_cat_comp[campo_id]}")
                                            
                                            st.write(f"**Quantidade:** {comp.quantidade}")
                                            st.write(f"**Período:** {comp.data_inicio.strftime('%d/%m/%Y')} a {comp.data_fim.strftime('%d/%m/%Y')}")
                                            if hasattr(comp, 'descricao') and comp.descricao:
                                                st.write(f"**Descrição:** {comp.descricao}")
                                            if hasattr(comp, 'cidade') and hasattr(comp, 'uf') and comp.cidade and comp.uf:
                                                localizacao_str = f"{comp.cidade} - {comp.uf}"
                                                if hasattr(comp, 'endereco') and comp.endereco:
                                                    localizacao_str += f" ({comp.endereco})"
                                                st.write(f"**Localização:** {localizacao_str}")
                                            if hasattr(comp, 'contratante') and comp.contratante:
                                                st.write(f"**Contratante:** {comp.contratante}")
                                else:
                                    st.info("ℹ️ Nenhum compromisso ativo nesta data.")
                        else:
                            st.error(f"❌ Nenhum item encontrado para '{chave_agrupamento_selecionada}'.")
                    else:
                        st.error("❌ Item não encontrado.")
                else:
                    # Para itens sem agrupamento, comportamento normal
                    disponibilidade = db.verificar_disponibilidade(
                        item_id, 
                        data_consulta, 
                        filtro_localizacao if filtro_localizacao != "Todas as Localizações" else None
                    )
                    
                    if disponibilidade:
                        st.subheader(f"Disponibilidade para '{disponibilidade['item'].nome}' em {data_consulta.strftime('%d/%m/%Y')}")
                        
                        # Mostra filtro de localização se aplicado
                        if filtro_localizacao and filtro_localizacao != "Todas as Localizações":
                            st.info(f"📍 **Filtro aplicado:** Localização '{filtro_localizacao}'")
                            # Verifica se o item está na localização selecionada
                            cidade_uf = filtro_localizacao.split(" - ")
                            if len(cidade_uf) == 2:
                                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                                item_na_localizacao = (hasattr(disponibilidade['item'], 'cidade') and hasattr(disponibilidade['item'], 'uf') and 
                                                      disponibilidade['item'].cidade == cidade_filtro and disponibilidade['item'].uf == uf_filtro.upper())
                                if not item_na_localizacao:
                                    st.warning(f"⚠️ Este item não está na localização '{filtro_localizacao}'. Mostrando disponibilidade considerando apenas compromissos nesta localização.")
                        
                        # Mostra localização do item se disponível
                        if hasattr(disponibilidade['item'], 'cidade') and hasattr(disponibilidade['item'], 'uf') and disponibilidade['item'].cidade and disponibilidade['item'].uf:
                            localizacao_str = f"{disponibilidade['item'].cidade} - {disponibilidade['item'].uf}"
                            if hasattr(disponibilidade['item'], 'endereco') and disponibilidade['item'].endereco:
                                localizacao_str += f" ({disponibilidade['item'].endereco})"
                            st.caption(f"📍 **Localização do Item:** {localizacao_str}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Quantidade Total", disponibilidade['quantidade_total'])
                        with col2:
                            st.metric("Quantidade Comprometida", disponibilidade['quantidade_comprometida'])
                        with col3:
                            cor = "normal" if disponibilidade['quantidade_disponivel'] > 0 else "inverse"
                            st.metric("Quantidade Disponível", disponibilidade['quantidade_disponivel'], delta=None)
                        
                        if disponibilidade['compromissos_ativos']:
                            st.subheader("Compromissos Ativos nesta Data")
                            for comp in disponibilidade['compromissos_ativos']:
                                with st.expander(f"Compromisso #{comp.id} - {comp.quantidade} unidades ({comp.data_inicio} a {comp.data_fim})"):
                                    st.write(f"**Item:** {comp.item.nome}")
                                    st.write(f"**Quantidade:** {comp.quantidade}")
                                    st.write(f"**Período:** {comp.data_inicio.strftime('%d/%m/%Y')} a {comp.data_fim.strftime('%d/%m/%Y')}")
                                    if hasattr(comp, 'descricao') and comp.descricao:
                                        st.write(f"**Descrição:** {comp.descricao}")
                                    if hasattr(comp, 'cidade') and hasattr(comp, 'uf') and comp.cidade and comp.uf:
                                        localizacao_str = f"{comp.cidade} - {comp.uf}"
                                        if hasattr(comp, 'endereco') and comp.endereco:
                                            localizacao_str += f" ({comp.endereco})"
                                        st.write(f"**Localização:** {localizacao_str}")
                                    if hasattr(comp, 'contratante') and comp.contratante:
                                        st.write(f"**Contratante:** {comp.contratante}")
                        else:
                            st.info("ℹ️ Nenhum compromisso ativo nesta data.")
                    else:
                        st.error("❌ Item não encontrado.")
        else: # Todos os Itens
            if st.button("Verificar Disponibilidade de Todos os Itens", type="primary"):
                # Passa o filtro de localização para a função
                resultados = db.verificar_disponibilidade_todos_itens(data_consulta, filtro_localizacao if filtro_localizacao != "Todas as Localizações" else None)
                    
                st.subheader(f"Disponibilidade em {data_consulta.strftime('%d/%m/%Y')}")
                if categoria_filtro != "Todas as Categorias":
                    st.info(f"📦 **Filtro aplicado:** Categoria '{categoria_filtro}'")
                if filtro_localizacao and filtro_localizacao != "Todas as Localizações":
                    st.info(f"📍 **Filtro aplicado:** Localização '{filtro_localizacao}'")
                
                if resultados:
                    # Agrupa resultados por categoria e depois por campos de agrupamento
                    resultados_por_categoria = {}
                    
                    for resultado in resultados:
                        item = resultado['item']
                        categoria_item = getattr(item, 'categoria', '') or ''
                        
                        if categoria_item not in resultados_por_categoria:
                            resultados_por_categoria[categoria_item] = []
                        resultados_por_categoria[categoria_item].append(resultado)
                    
                    # Processa cada categoria
                    for categoria_nome, resultados_categoria in resultados_por_categoria.items():
                        # Aplica filtro de localização se necessário
                        if filtro_localizacao and filtro_localizacao != "Todas as Localizações":
                            cidade_uf = filtro_localizacao.split(" - ")
                            if len(cidade_uf) == 2:
                                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                                resultados_categoria = [r for r in resultados_categoria 
                                                       if hasattr(r['item'], 'cidade') and hasattr(r['item'], 'uf')
                                                       and r['item'].cidade == cidade_filtro 
                                                       and r['item'].uf == uf_filtro.upper()]
                        
                        if not resultados_categoria:
                            continue
                        
                        # Determina campos de agrupamento para esta categoria
                        primeiro_item = resultados_categoria[0]['item']
                        dados_cat = getattr(primeiro_item, 'dados_categoria', None)
                        campos_agrupamento = obter_campos_agrupamento(categoria_nome, dados_cat) if dados_cat else None
                        
                        # Determina ícone baseado na categoria
                        icone = "🚗" if categoria_nome == "Carros" else "📦"
                        
                        if campos_agrupamento:
                            # Agrupa por campos de agrupamento
                            grupos_agrupados = {}
                            for resultado in resultados_categoria:
                                item = resultado['item']
                                chave_agrupamento = obter_valor_campo_agrupamento(item, campos_agrupamento)
                                
                                if not chave_agrupamento:
                                    chave_agrupamento = item.nome  # Fallback para nome do item
                                
                                if chave_agrupamento not in grupos_agrupados:
                                    grupos_agrupados[chave_agrupamento] = {
                                        'itens': [],
                                        'total_disponivel': 0,
                                        'total_comprometido': 0
                                    }
                                
                                grupos_agrupados[chave_agrupamento]['itens'].append({
                                    'item': item,
                                    'dados_categoria': getattr(item, 'dados_categoria', None),
                                    'disponivel': resultado['quantidade_disponivel'],
                                    'comprometido': resultado['quantidade_comprometida']
                                })
                                grupos_agrupados[chave_agrupamento]['total_disponivel'] += resultado['quantidade_disponivel']
                                grupos_agrupados[chave_agrupamento]['total_comprometido'] += resultado['quantidade_comprometida']
                            
                            # Mostra grupos agrupados
                            for chave, grupo in sorted(grupos_agrupados.items()):
                                with st.expander(f"{icone} **{chave}** - {grupo['total_disponivel']} disponível(is) de {len(grupo['itens'])} total"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total de Itens", len(grupo['itens']))
                                    with col2:
                                        st.metric("Comprometidos", grupo['total_comprometido'])
                                    with col3:
                                        st.metric("Disponíveis", grupo['total_disponivel'])
                                    
                                    st.divider()
                                    
                                    # Determina campo identificador principal
                                    campo_id_principal = None
                                    campos_id_possiveis = ['Placa', 'Serial', 'Código', 'Código Único', 'Número de Série']
                                    
                                    # Mostra detalhes de cada item do grupo
                                    for item_info in grupo['itens']:
                                        item_grupo = item_info['item']
                                        dados_cat_item = item_info['dados_categoria']
                                        
                                        # Determina campo identificador
                                        if dados_cat_item and isinstance(dados_cat_item, dict):
                                            for campo_id in campos_id_possiveis:
                                                if campo_id in dados_cat_item and dados_cat_item[campo_id]:
                                                    campo_id_principal = campo_id
                                                    break
                                        
                                        disponivel = item_info['disponivel']
                                        comprometido = item_info['comprometido']
                                        status = "✅ Disponível" if disponivel > 0 else "❌ Indisponível"
                                        
                                        # Constrói informação do item
                                        if campo_id_principal and dados_cat_item:
                                            valor_id = dados_cat_item.get(campo_id_principal, '')
                                            info_item = f"- **{campo_id_principal}: {valor_id}**"
                                            
                                            # Adiciona outros campos relevantes
                                            campos_adicionais = ['Ano', 'Modelo']
                                            for campo_add in campos_adicionais:
                                                if campo_add in dados_cat_item and dados_cat_item[campo_add]:
                                                    info_item += f" ({campo_add}: {dados_cat_item[campo_add]})"
                                            
                                            info_item += f" - {status}"
                                        else:
                                            info_item = f"- **{item_grupo.nome}** - {status}"
                                        
                                        # Adiciona localização
                                        if hasattr(item_grupo, 'cidade') and hasattr(item_grupo, 'uf') and item_grupo.cidade and item_grupo.uf:
                                            localizacao_item = f"{item_grupo.cidade} - {item_grupo.uf}"
                                            if hasattr(item_grupo, 'endereco') and item_grupo.endereco:
                                                localizacao_item += f" ({item_grupo.endereco})"
                                            info_item += f" | 📍 {localizacao_item}"
                                        
                                        st.write(info_item)
                                        if comprometido > 0:
                                            st.caption(f"  Comprometido: {comprometido}")
                        else:
                            # Sem agrupamento, mostra individualmente
                            for resultado in resultados_categoria:
                                item_resultado = resultado['item']
                                item_nome = item_resultado.nome
                                disponivel = resultado['quantidade_disponivel']
                                total = resultado['quantidade_total']
                                comprometido = resultado['quantidade_comprometida']
                                
                                with st.expander(f"{icone} **{item_nome}** - {disponivel} disponível(is) de {total} total"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Quantidade Total", total)
                                    with col2:
                                        st.metric("Comprometidos", comprometido)
                                    with col3:
                                        st.metric("Disponíveis", disponivel)
                                    
                                    st.divider()
                                    
                                    # Mostra dados específicos da categoria se existirem
                                    dados_cat = getattr(item_resultado, 'dados_categoria', None)
                                    if dados_cat and isinstance(dados_cat, dict):
                                        st.write(f"**Detalhes de {categoria_nome}:**")
                                        for campo, valor in dados_cat.items():
                                            if campo not in ['ID', 'Item ID', ''] and valor:
                                                st.write(f"**{campo}:** {valor}")
                                        st.divider()
                                    
                                    # Mostra localização do item se disponível
                                    if hasattr(item_resultado, 'cidade') and hasattr(item_resultado, 'uf') and item_resultado.cidade and item_resultado.uf:
                                        localizacao_str = f"{item_resultado.cidade} - {item_resultado.uf}"
                                        if hasattr(item_resultado, 'endereco') and item_resultado.endereco:
                                            localizacao_str += f" ({item_resultado.endereco})"
                                        st.write(f"**Localização:** {localizacao_str}")
                                    
                                    # Mostra aviso se item não está na localização filtrada
                                    if filtro_localizacao and filtro_localizacao != "Todas as Localizações":
                                        cidade_uf = filtro_localizacao.split(" - ")
                                        if len(cidade_uf) == 2:
                                            cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                                            item_na_localizacao = (hasattr(item_resultado, 'cidade') and hasattr(item_resultado, 'uf') and 
                                                                  item_resultado.cidade == cidade_filtro and item_resultado.uf == uf_filtro.upper())
                                            if not item_na_localizacao:
                                                st.warning("⚠️ Este item não está na localização filtrada.")
                                    
                                    # Mostra descrição se disponível
                                    if hasattr(item_resultado, 'descricao') and item_resultado.descricao:
                                        st.divider()
                                        st.write(f"**Descrição:** {item_resultado.descricao}")
                else:
                    st.info("ℹ️ Nenhum item cadastrado ou disponível.")

# Página Visualizar Dados
elif menu == "Visualizar Dados":
    st.header("Visualizar Dados")
    
    # Filtro por categoria
    itens = db.listar_itens()
    categorias_disponiveis = sorted(set([getattr(item, 'categoria', '') or '' for item in itens if getattr(item, 'categoria', '')]))
    categoria_filtro_viz = st.selectbox("Filtrar por Categoria (opcional)", options=["Todas as Categorias"] + categorias_disponiveis, index=0, key="filtro_categoria_viz")
    
    tab1, tab2 = st.tabs(["Itens", "Compromissos"])
    
    with tab1:
        st.subheader("Itens Cadastrados")
        
        # Campo de busca
        col_search, col_space = st.columns([3, 1])
        with col_search:
            busca_item = st.text_input("🔍 Buscar item", placeholder="Digite o nome do item para filtrar...", key="busca_item")
        
        itens = db.listar_itens()
        
        # Filtra por categoria se selecionada
        if categoria_filtro_viz != "Todas as Categorias":
            itens = [item for item in itens if (getattr(item, 'categoria', '') or '') == categoria_filtro_viz]
        
        # Carrega compromissos UMA vez para evitar múltiplas chamadas à API
        compromissos_todos = db.listar_compromissos()
        # Cria dicionário para contar compromissos por item_id
        compromissos_por_item = {}
        for comp in compromissos_todos:
            item_id = comp.item_id
            compromissos_por_item[item_id] = compromissos_por_item.get(item_id, 0) + 1
        
        # Filtra itens pela busca
        itens_originais = itens.copy() if itens else []
        if busca_item:
            busca_lower = busca_item.lower().strip()
            itens = [item for item in itens if busca_lower in item.nome.lower()]
            if itens:
                st.info(f"🔍 Mostrando {len(itens)} item(ns) encontrado(s) para '{busca_item}'")
            elif itens_originais:
                st.warning(f"🔍 Nenhum item encontrado para '{busca_item}'")
        
        if itens:
            for item in itens:
                categoria_item = getattr(item, 'categoria', '') or ''
                # Título do expander muda baseado na categoria
                # Determina ícone baseado na categoria (🚗 para Carros, 📦 para outros)
                icone = "🚗" if categoria_item == 'Carros' else "📦"
                
                # Para categorias com dados específicos, tenta adicionar identificador
                dados_cat = getattr(item, 'dados_categoria', None)
                identificador = ""
                if dados_cat and isinstance(dados_cat, dict):
                    campos_id = ['Placa', 'Serial', 'Código']
                    for campo_id in campos_id:
                        if campo_id in dados_cat and dados_cat[campo_id]:
                            identificador = f" - {dados_cat[campo_id]}"
                            break
                
                if categoria_item == 'Carros' and identificador:
                    titulo_expander = f"{icone} {item.nome}{identificador}"
                elif categoria_item and categoria_item != 'Carros':
                    titulo_expander = f"{icone} {item.nome} - Estoque Total: {item.quantidade_total}"
                else:
                    titulo_expander = f"{icone} {item.nome}"
                
                with st.expander(titulo_expander):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**ID:** {item.id}")
                        categoria_item = getattr(item, 'categoria', '') or ''
                        st.write(f"**Categoria:** {categoria_item}")
                        st.write(f"**Nome:** {item.nome}")
                        # Quantidade só aparece se não for categoria que sempre tem quantidade 1
                        # Verifica se há campos que indicam item único
                        dados_cat_viz = getattr(item, 'dados_categoria', None)
                        tem_campo_item_unico_viz = False
                        if dados_cat_viz and isinstance(dados_cat_viz, dict):
                            campos_item_unico = ['Placa', 'Serial', 'Código Único', 'Código', 'ID Único']
                            tem_campo_item_unico_viz = any(campo in dados_cat_viz for campo in campos_item_unico)
                        
                        if categoria_item != 'Carros' and not tem_campo_item_unico_viz:
                            st.write(f"**Quantidade Total:** {item.quantidade_total}")
                        
                        # Mostra campos específicos da categoria se aplicável
                        dados_cat = getattr(item, 'dados_categoria', None)
                        if dados_cat and isinstance(dados_cat, dict):
                            # Exibe todos os campos da categoria dinamicamente
                            st.divider()
                            st.write(f"**Detalhes de {categoria_item}:**")
                            for campo, valor in dados_cat.items():
                                # Pula campos padrão que não são específicos da categoria
                                if campo not in ['ID', 'Item ID', '']:
                                    if valor:  # Só mostra se tiver valor
                                        st.write(f"**{campo}:** {valor}")
                        
                        # Compatibilidade: mostra campos de carro se existir (para código antigo)
                        if categoria_item == 'Carros':
                            carro = getattr(item, 'carro', None)
                            if carro:
                                # Só mostra se não foi mostrado acima via dados_categoria
                                if not dados_cat or not isinstance(dados_cat, dict) or not dados_cat.get('Marca'):
                                    st.write(f"**Marca:** {getattr(carro, 'marca', 'N/A')}")
                                    st.write(f"**Modelo:** {carro.modelo}")
                                    st.write(f"**Placa:** {carro.placa}")
                                    st.write(f"**Ano:** {carro.ano}")
                        
                        if hasattr(item, 'descricao') and item.descricao:
                            st.write(f"**Descrição:** {item.descricao}")
                        if hasattr(item, 'cidade') and hasattr(item, 'uf') and item.cidade and item.uf:
                            localizacao_str = f"{item.cidade} - {item.uf}"
                            if hasattr(item, 'endereco') and item.endereco:
                                localizacao_str += f" ({item.endereco})"
                            st.write(f"**Localização:** {localizacao_str}")
                        # Usa o dicionário pré-calculado em vez de chamar a API novamente
                        compromissos_count = compromissos_por_item.get(item.id, 0)
                        st.write(f"**Total de Compromissos:** {compromissos_count}")
                    with col2:
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button(f"✏️ Editar", key=f"edit_item_{item.id}"):
                                st.session_state[f'editing_item_{item.id}'] = True
                                st.session_state[f'edit_nome_{item.id}'] = item.nome
                                st.session_state[f'edit_quantidade_{item.id}'] = item.quantidade_total
                                st.session_state[f'edit_descricao_{item.id}'] = getattr(item, 'descricao', '') or ''
                                st.session_state[f'edit_cidade_{item.id}'] = getattr(item, 'cidade', '') or ''
                                st.session_state[f'edit_uf_{item.id}'] = getattr(item, 'uf', 'SP') or 'SP'
                                st.session_state[f'edit_endereco_{item.id}'] = getattr(item, 'endereco', '') or ''
                                # Inicializa campos de carro se existir
                                carro = getattr(item, 'carro', None)
                                if carro:
                                    st.session_state[f'edit_marca_{item.id}'] = getattr(carro, 'marca', '')
                                    st.session_state[f'edit_placa_{item.id}'] = carro.placa
                                    st.session_state[f'edit_modelo_{item.id}'] = carro.modelo
                                    st.session_state[f'edit_ano_{item.id}'] = carro.ano
                        with col_del:
                            if st.button(f"🗑️ Deletar", key=f"del_item_{item.id}"):
                                try:
                                    db.deletar_item(item.id)
                                    st.success("Item deletado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao deletar: {str(e)}")
                    
                    # Formulário de edição
                    if st.session_state.get(f'editing_item_{item.id}', False):
                        st.divider()
                        st.write("**Editar Item**")
                        with st.form(f"form_edit_item_{item.id}"):
                            # Determina categoria atual e obtém todas as categorias disponíveis
                            categoria_atual = getattr(item, 'categoria', '') or ''
                            todas_categorias = db.obter_categorias() if USE_GOOGLE_SHEETS else sorted(set([getattr(i, 'categoria', '') or '' for i in db.listar_itens() if getattr(i, 'categoria', '')]))
                            
                            if not todas_categorias:
                                st.warning("⚠️ Não há categorias cadastradas.")
                            else:
                                categoria_index = todas_categorias.index(categoria_atual) if categoria_atual in todas_categorias else 0
                                edit_categoria = st.selectbox("Categoria *", options=todas_categorias, index=categoria_index, key=f"input_categoria_{item.id}")
                            
                            edit_nome = st.text_input("Nome do Item", value=st.session_state.get(f'edit_nome_{item.id}', item.nome), key=f"input_nome_{item.id}")
                            
                            # Determina se a categoria tem quantidade fixa em 1 (itens únicos)
                            campos_categoria_edit = []
                            try:
                                if USE_GOOGLE_SHEETS:
                                    campos_categoria_edit = db.obter_campos_categoria(edit_categoria)
                            except Exception:
                                pass
                            
                            tem_campo_item_unico_edit = False
                            if campos_categoria_edit:
                                campos_item_unico = ['Placa', 'Serial', 'Código Único', 'Código', 'ID Único']
                                tem_campo_item_unico_edit = any(campo in campos_categoria_edit for campo in campos_item_unico)
                            
                            if edit_categoria == "Carros" or tem_campo_item_unico_edit:
                                # Para categorias com itens únicos, quantidade é sempre 1
                                edit_quantidade = 1
                            else:
                                edit_quantidade = st.number_input("Quantidade Total", min_value=1, value=st.session_state.get(f'edit_quantidade_{item.id}', item.quantidade_total), key=f"input_quantidade_{item.id}")
                            
                            edit_descricao = st.text_area("Descrição (opcional)", value=st.session_state.get(f'edit_descricao_{item.id}', getattr(item, 'descricao', '') or ''), key=f"input_descricao_{item.id}")
                            
                            # Campos específicos para carros
                            if edit_categoria == "Carros":
                                carro_atual = getattr(item, 'carro', None)
                                marca_atual = getattr(carro_atual, 'marca', '') if carro_atual else ''
                                placa_atual = carro_atual.placa if carro_atual else ''
                                modelo_atual = carro_atual.modelo if carro_atual else ''
                                ano_atual = carro_atual.ano if carro_atual else 2020
                                
                                # Busca índice da marca atual
                                marca_index = 0
                                if marca_atual and marca_atual in MARCAS_CARROS:
                                    marca_index = MARCAS_CARROS.index(marca_atual)
                                
                                col_marca, col_modelo = st.columns(2)
                                with col_marca:
                                    edit_marca = st.selectbox("Marca *", options=MARCAS_CARROS, index=marca_index, key=f"input_marca_{item.id}")
                                with col_modelo:
                                    edit_modelo = st.text_input("Modelo *", value=st.session_state.get(f'edit_modelo_{item.id}', modelo_atual), key=f"input_modelo_{item.id}")
                                
                                col_placa, col_ano = st.columns(2)
                                with col_placa:
                                    edit_placa = st.text_input("Placa *", value=st.session_state.get(f'edit_placa_{item.id}', placa_atual), key=f"input_placa_{item.id}", max_chars=10)
                                with col_ano:
                                    edit_ano = st.number_input("Ano *", min_value=1900, max_value=2100, value=st.session_state.get(f'edit_ano_{item.id}', ano_atual), key=f"input_ano_{item.id}", step=1)
                                
                                # Atualiza nome automaticamente
                                edit_nome = f"{edit_marca} {edit_modelo}".strip() if edit_modelo else edit_nome
                            else:
                                edit_marca = None
                                edit_placa = None
                                edit_modelo = None
                                edit_ano = None
                            
                            st.markdown("**Localização do Item**")
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_cidade = st.text_input("Cidade *", value=st.session_state.get(f'edit_cidade_{item.id}', getattr(item, 'cidade', '') or ''), key=f"input_cidade_{item.id}")
                            with col2:
                                uf_atual = st.session_state.get(f'edit_uf_{item.id}', getattr(item, 'uf', 'SP') or 'SP')
                                uf_index = UFS_BRASILEIRAS.index(uf_atual) if uf_atual in UFS_BRASILEIRAS else 24
                                edit_uf = st.selectbox("UF *", options=UFS_BRASILEIRAS, index=uf_index, key=f"input_uf_{item.id}")
                            edit_endereco = st.text_input("Endereço (opcional)", value=st.session_state.get(f'edit_endereco_{item.id}', getattr(item, 'endereco', '') or ''), key=f"input_endereco_{item.id}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
                            with col_cancel:
                                cancel = st.form_submit_button("❌ Cancelar")
                            
                            if submitted:
                                # Validação básica
                                campos_ok = edit_nome.strip() and edit_cidade.strip() and edit_uf
                                if edit_categoria == "Carros":
                                    campos_ok = campos_ok and edit_marca and edit_placa and edit_modelo and edit_ano
                                
                                if campos_ok:
                                    try:
                                        item_atualizado = db.atualizar_item(
                                            item.id, 
                                            edit_nome.strip(), 
                                            edit_quantidade, 
                                            edit_categoria,
                                            edit_descricao.strip() if edit_descricao else None, 
                                            edit_cidade.strip(), 
                                            edit_uf, 
                                            edit_endereco.strip() if edit_endereco else None,
                                            edit_placa.strip() if edit_placa else None,
                                            edit_marca.strip() if edit_marca else None,
                                            edit_modelo.strip() if edit_modelo else None,
                                            int(edit_ano) if edit_ano else None
                                        )
                                        if item_atualizado:
                                            st.success("✅ Item atualizado com sucesso!")
                                            st.session_state[f'editing_item_{item.id}'] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao atualizar item. Item não encontrado.")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao atualizar item: {str(e)}")
                                else:
                                    st.warning("⚠️ Por favor, preencha os campos obrigatórios.")
                            
                            if cancel:
                                st.session_state[f'editing_item_{item.id}'] = False
                                st.rerun()
        else:
            st.info("ℹ️ Nenhum item cadastrado ainda.")
    
    with tab2:
        st.subheader("Compromissos Registrados")
        
        # Campo de busca
        col_search, col_space = st.columns([3, 1])
        with col_search:
            busca_compromisso = st.text_input("🔍 Buscar compromisso", placeholder="Digite o nome do item ou contratante para filtrar...", key="busca_compromisso")
        
        compromissos = db.listar_compromissos()
        
        # Filtra compromissos pela busca
        if busca_compromisso:
            busca_lower = busca_compromisso.lower().strip()
            compromissos_originais = compromissos.copy()
            compromissos_filtrados = []
            for comp in compromissos:
                # Busca no nome do item, descrição, cidade, UF, endereço ou contratante
                if (busca_lower in comp.item.nome.lower() or
                    (hasattr(comp, 'descricao') and comp.descricao and busca_lower in comp.descricao.lower()) or
                    (hasattr(comp, 'cidade') and comp.cidade and busca_lower in comp.cidade.lower()) or
                    (hasattr(comp, 'uf') and comp.uf and busca_lower in comp.uf.lower()) or
                    (hasattr(comp, 'endereco') and comp.endereco and busca_lower in comp.endereco.lower()) or
                    (hasattr(comp, 'contratante') and comp.contratante and busca_lower in comp.contratante.lower())):
                    compromissos_filtrados.append(comp)
            compromissos = compromissos_filtrados
            if compromissos:
                st.info(f"🔍 Mostrando {len(compromissos)} compromisso(s) encontrado(s) para '{busca_compromisso}'")
            elif compromissos_originais:
                st.warning(f"🔍 Nenhum compromisso encontrado para '{busca_compromisso}'")
        
        if compromissos:
            # Ordenar por data de início (mais recentes primeiro)
            compromissos_ordenados = sorted(compromissos, key=lambda x: x.data_inicio, reverse=True)
            
            for comp in compromissos_ordenados:
                status = "🟢 Ativo" if comp.data_inicio <= date.today() <= comp.data_fim else "⚪ Inativo"
                with st.expander(f"📅 {comp.item.nome if comp.item else 'Item Deletado'} - {comp.quantidade} unidades ({comp.data_inicio} a {comp.data_fim}) - {status}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**ID:** {comp.id}")
                        if comp.item:
                            categoria_item_comp = getattr(comp.item, 'categoria', '') or ''
                            st.write(f"**Categoria:** {categoria_item_comp}")
                        st.write(f"**Item:** {comp.item.nome if comp.item else 'Item Deletado (ID: ' + str(comp.item_id) + ')'}")
                        st.write(f"**Quantidade:** {comp.quantidade}")
                        st.write(f"**Período:** {comp.data_inicio.strftime('%d/%m/%Y')} a {comp.data_fim.strftime('%d/%m/%Y')}")
                        if hasattr(comp, 'descricao') and comp.descricao:
                            st.write(f"**Descrição:** {comp.descricao}")
                        if hasattr(comp, 'cidade') and hasattr(comp, 'uf') and comp.cidade and comp.uf:
                            localizacao_str = f"{comp.cidade} - {comp.uf}"
                            if hasattr(comp, 'endereco') and comp.endereco:
                                localizacao_str += f" ({comp.endereco})"
                            st.write(f"**Localização:** {localizacao_str}")
                        if hasattr(comp, 'contratante') and comp.contratante:
                            st.write(f"**Contratante:** {comp.contratante}")
                    with col2:
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button(f"✏️ Editar", key=f"edit_comp_{comp.id}"):
                                st.session_state[f'editing_comp_{comp.id}'] = True
                                st.session_state[f'edit_item_id_{comp.id}'] = comp.item_id
                                st.session_state[f'edit_quantidade_{comp.id}'] = comp.quantidade
                                st.session_state[f'edit_data_inicio_{comp.id}'] = comp.data_inicio
                                st.session_state[f'edit_data_fim_{comp.id}'] = comp.data_fim
                                st.session_state[f'edit_descricao_{comp.id}'] = getattr(comp, 'descricao', '') or ''
                                st.session_state[f'edit_cidade_{comp.id}'] = getattr(comp, 'cidade', '') or ''
                                st.session_state[f'edit_uf_{comp.id}'] = getattr(comp, 'uf', 'SP') or 'SP'
                                st.session_state[f'edit_endereco_{comp.id}'] = getattr(comp, 'endereco', '') or ''
                                st.session_state[f'edit_contratante_{comp.id}'] = getattr(comp, 'contratante', '') or ''
                        with col_del:
                            if st.button(f"🗑️ Deletar", key=f"del_comp_{comp.id}"):
                                try:
                                    db.deletar_compromisso(comp.id)
                                    st.success("Compromisso deletado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao deletar: {str(e)}")
                    
                    # Formulário de edição
                    if st.session_state.get(f'editing_comp_{comp.id}', False):
                        st.divider()
                        st.write("**Editar Compromisso**")
                        with st.form(f"form_edit_comp_{comp.id}"):
                            # Lista de itens para seleção
                            itens = db.listar_itens()
                            itens_dict = {item.id: item.nome for item in itens}
                            item_selecionado = st.selectbox(
                                "Item",
                                options=list(itens_dict.keys()),
                                format_func=lambda x: itens_dict[x],
                                index=list(itens_dict.keys()).index(comp.item_id) if comp.item_id in itens_dict.keys() else 0,
                                key=f"select_item_{comp.id}"
                            )
                            
                            edit_quantidade = st.number_input("Quantidade", min_value=1, value=st.session_state.get(f'edit_quantidade_{comp.id}', comp.quantidade), key=f"input_quantidade_{comp.id}")
                            
                            col_data1, col_data2 = st.columns(2)
                            with col_data1:
                                edit_data_inicio = st.date_input(
                                    "Data Início",
                                    value=st.session_state.get(f'edit_data_inicio_{comp.id}', comp.data_inicio),
                                    key=f"input_data_inicio_{comp.id}"
                                )
                            with col_data2:
                                # Data fim deve ser >= data início
                                min_date = edit_data_inicio
                                edit_data_fim = st.date_input(
                                    "Data Fim",
                                    value=st.session_state.get(f'edit_data_fim_{comp.id}', comp.data_fim),
                                    min_value=min_date,
                                    key=f"input_data_fim_{comp.id}"
                                )
                            
                            edit_descricao = st.text_area("Descrição (opcional)", value=st.session_state.get(f'edit_descricao_{comp.id}', getattr(comp, 'descricao', '') or ''), key=f"input_descricao_{comp.id}")
                            
                            st.markdown("**Localização do Compromisso**")
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_cidade = st.text_input("Cidade *", value=st.session_state.get(f'edit_cidade_{comp.id}', getattr(comp, 'cidade', '') or ''), key=f"input_cidade_{comp.id}")
                            with col2:
                                uf_atual = st.session_state.get(f'edit_uf_{comp.id}', getattr(comp, 'uf', 'SP') or 'SP')
                                uf_index = UFS_BRASILEIRAS.index(uf_atual) if uf_atual in UFS_BRASILEIRAS else 24
                                edit_uf = st.selectbox("UF *", options=UFS_BRASILEIRAS, index=uf_index, key=f"input_uf_{comp.id}")
                            edit_endereco = st.text_input("Endereço (opcional)", value=st.session_state.get(f'edit_endereco_{comp.id}', getattr(comp, 'endereco', '') or ''), key=f"input_endereco_{comp.id}")
                            edit_contratante = st.text_input("Contratante (opcional)", value=st.session_state.get(f'edit_contratante_{comp.id}', getattr(comp, 'contratante', '') or ''), key=f"input_contratante_{comp.id}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
                            with col_cancel:
                                cancel = st.form_submit_button("❌ Cancelar")
                            
                            if submitted:
                                if edit_data_fim < edit_data_inicio:
                                    st.error("❌ Data fim deve ser igual ou posterior à data início!")
                                elif not edit_cidade.strip() or not edit_uf:
                                    st.warning("⚠️ Por favor, preencha os campos obrigatórios.")
                                else:
                                    try:
                                        compromisso_atualizado = db.atualizar_compromisso(
                                            comp.id,
                                            item_selecionado,
                                            edit_quantidade,
                                            edit_data_inicio,
                                            edit_data_fim,
                                            edit_descricao.strip() if edit_descricao else None,
                                            edit_cidade.strip(),
                                            edit_uf,
                                            edit_endereco.strip() if edit_endereco else None,
                                            edit_contratante.strip() if edit_contratante else None
                                        )
                                        if compromisso_atualizado:
                                            st.success("✅ Compromisso atualizado com sucesso!")
                                            st.session_state[f'editing_comp_{comp.id}'] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao atualizar compromisso. Compromisso não encontrado.")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao atualizar compromisso: {str(e)}")
                            
                            if cancel:
                                st.session_state[f'editing_comp_{comp.id}'] = False
                                st.rerun()
        else:
            st.info("ℹ️ Nenhum compromisso registrado ainda.")
