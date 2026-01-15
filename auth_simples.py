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
    
    # Centraliza o formulário
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔐 Acesso ao Sistema")
        st.markdown("---")
        
        with st.form("login_form"):
            usuario = st.text_input("Usuário", placeholder="Digite o usuário")
            senha = st.text_input("Senha", type="password", placeholder="Digite a senha")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
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
    """Mostra botão de logout na sidebar"""
    if st.session_state.get('authenticated'):
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Usuário:** {st.session_state.get('usuario', '')}")
        if st.sidebar.button("🚪 Sair", use_container_width=True):
            fazer_logout()
