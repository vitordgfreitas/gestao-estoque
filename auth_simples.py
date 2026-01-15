"""
Sistema de autenticação simples com usuário e senha
"""
import streamlit as st
import os

def obter_usuario():
    """Obtém usuário dos secrets ou variável de ambiente"""
    try:
        return st.secrets.get('APP_USUARIO')
    except:
        pass
    
    usuario_env = os.getenv('APP_USUARIO')
    if usuario_env:
        return usuario_env
    
    return None

def obter_senha():
    """Obtém senha dos secrets ou variável de ambiente"""
    try:
        return st.secrets.get('APP_SENHA')
    except:
        pass
    
    senha_env = os.getenv('APP_SENHA')
    if senha_env:
        return senha_env
    
    return None

def verificar_autenticacao():
    """Verifica se o usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    return st.session_state['authenticated']

def mostrar_tela_login():
    """Mostra tela de login"""
    usuario_config = obter_usuario()
    senha_config = obter_senha()
    
    # Verifica se as credenciais estão configuradas
    if not usuario_config or not senha_config:
        st.error("⚠️ Sistema não configurado!")
        st.warning("""
        **Credenciais não encontradas!**
        
        Configure no Streamlit Cloud Secrets:
        ```toml
        APP_USUARIO = "seu_usuario"
        APP_SENHA = "sua_senha"
        ```
        """)
        st.stop()
    
    # CSS para tela de login - Paleta Azul Profissional
    st.markdown("""
    <style>
        /* Fundo */
        .stApp {
            background-color: #f8f9fa !important;
        }
        
        .main .block-container {
            background-color: #f8f9fa !important;
        }
        
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* TODOS os botões - aplicar cor azul profissional */
        .stButton > button {
            background-color: #2c3e50 !important;
            color: white !important;
            border: 1px solid #2c3e50 !important;
        }
        
        .stButton > button:hover {
            background-color: #34495e !important;
        }
        
        /* Botão Primário específico */
        .stButton > button[kind="primary"] {
            background-color: #2c3e50 !important;
            color: white !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #34495e !important;
        }
        
        /* Inputs */
        .stTextInput > div > div > input {
            border-color: #e0e0e0 !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3498db !important;
        }
        
        /* Mensagens */
        .stSuccess {
            background-color: #d4edda !important;
            border-left: 4px solid #27ae60 !important;
            color: #155724 !important;
        }
        
        .stError {
            background-color: #f8d7da !important;
            border-left: 4px solid #e74c3c !important;
            color: #721c24 !important;
        }
        
        .stWarning {
            background-color: #fff3cd !important;
            border-left: 4px solid #f39c12 !important;
            color: #856404 !important;
        }
        
        .stInfo {
            background-color: #d1ecf1 !important;
            border-left: 4px solid #3498db !important;
            color: #0c5460 !important;
        }
        
        /* Títulos */
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50 !important;
        }
        
        /* Texto geral */
        p, label, .stMarkdown {
            color: #2c3e50 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Centraliza o formulário
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #2c3e50; font-size: 2rem; margin-bottom: 0.5rem;">🔐 Acesso ao Sistema</h1>
            <p style="color: #7f8c8d;">Faça login para continuar</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuário", placeholder="Digite o usuário")
            senha = st.text_input("🔒 Senha", type="password", placeholder="Digite a senha")
            submitted = st.form_submit_button("🚀 Entrar", type="primary", use_container_width=True)
            
            if submitted:
                if usuario == usuario_config and senha == senha_config:
                    st.session_state['authenticated'] = True
                    st.session_state['usuario'] = usuario
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")

def fazer_logout():
    """Faz logout do usuário"""
    st.session_state['authenticated'] = False
    st.session_state['usuario'] = None
    st.rerun()

def mostrar_botao_logout():
    """Função mantida para compatibilidade, mas o logout agora é gerenciado no app.py"""
    pass
