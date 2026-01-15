import streamlit as st
from datetime import date, datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Gestão de Estoque - Aluguel de Itens",
    page_icon="📦",
    layout="wide"
)

# Sistema de autenticação simples
from auth_simples import verificar_autenticacao, mostrar_tela_login, mostrar_botao_logout

if not verificar_autenticacao():
    mostrar_tela_login()
    st.stop()

mostrar_botao_logout()

# Escolhe qual banco de dados usar baseado em variável de ambiente
USE_GOOGLE_SHEETS = os.getenv('USE_GOOGLE_SHEETS', 'true').lower() == 'true'

if USE_GOOGLE_SHEETS:
    try:
        import sheets_database as db
        # Inicializa Google Sheets
        sheets = db.get_sheets()
        st.sidebar.success(f"✅ Conectado ao Google Sheets\n[Ver Planilha]({sheets['spreadsheet_url']})")
        st.sidebar.info(f"📊 Planilha ID: `{sheets['spreadsheet_id']}`")
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
        elif "storage quota" in error_msg.lower() or "quota" in error_msg.lower():
            st.warning("""
            **Cota de Armazenamento Excedida:**
            O sistema está configurado para usar sua planilha existente.
            Verifique se o ID da planilha está configurado corretamente.
            """)
        elif "credentials" in error_msg.lower() or "credenciais" in error_msg.lower():
            st.info("💡 Configure as credenciais do Google Sheets. Veja GOOGLE_SHEETS_SETUP.md")
        else:
            st.info("💡 Veja GOOGLE_SHEETS_SETUP.md para instruções de configuração")
        
        st.stop()
else:
    from models import init_db
    import database as db
    # Inicializar banco de dados SQLite
    init_db()

# Título principal
st.title("📦 Sistema de Gestão de Estoque")
st.markdown("---")

# Menu lateral
menu = st.sidebar.selectbox(
    "Menu",
    ["🏠 Início", "➕ Registrar Item", "📅 Registrar Compromisso", "🔍 Verificar Disponibilidade", "📊 Visualizar Dados"]
)

# Página Início
if menu == "🏠 Início":
    st.header("Bem-vindo ao Sistema de Gestão de Estoque")
    st.markdown("""
    Este sistema permite gerenciar o estoque de itens para aluguel em eventos e licitações.
    
    **Funcionalidades:**
    - ➕ Registrar novos itens no estoque
    - 📅 Registrar compromissos (aluguéis) dos itens
    - 🔍 Verificar disponibilidade em datas específicas
    - 📊 Visualizar todos os itens e compromissos
    
    Use o menu lateral para navegar entre as funcionalidades.
    """)
    
    # Estatísticas rápidas
    st.subheader("📊 Estatísticas Rápidas")
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
elif menu == "➕ Registrar Item":
    st.header("Registrar Novo Item")
    
    with st.form("form_item"):
        nome = st.text_input("Nome do Item *", placeholder="Ex: Alambrado, Mesa, Cadeira...")
        quantidade = st.number_input("Quantidade Total *", min_value=1, value=1, step=1)
        descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Mesa retangular de madeira, tamanho 3x2 metros...")
        localizacao = st.text_input("Localização (opcional)", placeholder="Ex: Galpão A, Prateleira 3...")
        
        submitted = st.form_submit_button("Registrar Item", type="primary")
        
        if submitted:
            if nome.strip():
                try:
                    item = db.criar_item(nome.strip(), quantidade, descricao.strip() if descricao else None, localizacao.strip() if localizacao else None)
                    st.success(f"✅ Item '{item.nome}' registrado com sucesso! Quantidade: {item.quantidade_total}")
                except Exception as e:
                    st.error(f"❌ Erro ao registrar item: {str(e)}")
            else:
                st.warning("⚠️ Por favor, preencha o nome do item.")

# Página Registrar Compromisso
elif menu == "📅 Registrar Compromisso":
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
        
        with st.form("form_compromisso"):
            # Seleção do item
            item_options = {f"{item.nome} (Estoque: {item.quantidade_total})": item.id for item in itens}
            item_selecionado = st.selectbox("Selecione o Item *", options=list(item_options.keys()))
            item_id = item_options[item_selecionado]
            
            quantidade = st.number_input("Quantidade *", min_value=1, value=1, step=1)
            
            descricao = st.text_area("Descrição (opcional)", placeholder="Ex: Evento corporativo, Licitação pública...")
            
            submitted = st.form_submit_button("Registrar Compromisso", type="primary")
            
            if submitted:
                if data_fim < data_inicio:
                    st.error("❌ A data de fim deve ser posterior ou igual à data de início.")
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
                                descricao=descricao.strip() if descricao else None
                            )
                            st.success(f"✅ Compromisso registrado com sucesso!")
                            # Limpa os valores do session_state após sucesso
                            if 'data_inicio_compromisso' in st.session_state:
                                del st.session_state['data_inicio_compromisso']
                            if 'data_fim_compromisso' in st.session_state:
                                del st.session_state['data_fim_compromisso']
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar compromisso: {str(e)}")

# Página Verificar Disponibilidade
elif menu == "🔍 Verificar Disponibilidade":
    st.header("Verificar Disponibilidade")
    
    itens = db.listar_itens()
    
    if not itens:
        st.warning("⚠️ Não há itens cadastrados.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            modo_consulta = st.radio(
                "Tipo de Consulta",
                ["📋 Todos os Itens", "🎯 Item Específico"],
                horizontal=True
            )
        
        with col2:
            data_consulta = st.date_input("Data de Consulta", value=date.today())
        
        if modo_consulta == "🎯 Item Específico":
            item_options = {f"{item.nome}": item.id for item in itens}
            item_selecionado = st.selectbox("Selecione o Item", options=list(item_options.keys()))
            item_id = item_options[item_selecionado]
            
            if st.button("Verificar Disponibilidade", type="primary"):
                disponibilidade = db.verificar_disponibilidade(item_id, data_consulta)
                
                if disponibilidade:
                    st.subheader(f"📊 Disponibilidade: {disponibilidade['item'].nome}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Quantidade Total", disponibilidade['quantidade_total'])
                    with col2:
                        st.metric("Quantidade Comprometida", disponibilidade['quantidade_comprometida'])
                    with col3:
                        cor = "normal" if disponibilidade['quantidade_disponivel'] > 0 else "inverse"
                        st.metric("Quantidade Disponível", disponibilidade['quantidade_disponivel'], delta=None)
                    
                    if disponibilidade['compromissos_ativos']:
                        st.subheader("📅 Compromissos Ativos nesta Data")
                        for comp in disponibilidade['compromissos_ativos']:
                            with st.expander(f"Compromisso #{comp.id} - {comp.quantidade} unidades ({comp.data_inicio} a {comp.data_fim})"):
                                if hasattr(comp, 'descricao') and comp.descricao:
                                    st.write(f"**Descrição:** {comp.descricao}")
                                if hasattr(comp, 'localizacao') and comp.localizacao:
                                    st.write(f"**Localização:** {comp.localizacao}")
                                if hasattr(comp, 'contratante') and comp.contratante:
                                    st.write(f"**Contratante:** {comp.contratante}")
                    else:
                        st.info("ℹ️ Nenhum compromisso ativo nesta data.")
        else:
            if st.button("Verificar Disponibilidade de Todos os Itens", type="primary"):
                resultados = db.verificar_disponibilidade_todos_itens(data_consulta)
                
                st.subheader(f"📊 Disponibilidade em {data_consulta.strftime('%d/%m/%Y')}")
                
                if resultados:
                    for resultado in resultados:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                            with col1:
                                st.write(f"**{resultado['item'].nome}**")
                            with col2:
                                st.write(f"Total: {resultado['quantidade_total']}")
                            with col3:
                                st.write(f"Comprometido: {resultado['quantidade_comprometida']}")
                            with col4:
                                disponivel = resultado['quantidade_disponivel']
                                if disponivel < 0:
                                    st.error(f"⚠️ {disponivel}")
                                elif disponivel == 0:
                                    st.warning(f"{disponivel}")
                                else:
                                    st.success(f"✅ {disponivel}")
                            st.divider()

# Página Visualizar Dados
elif menu == "📊 Visualizar Dados":
    st.header("Visualizar Dados")
    
    tab1, tab2 = st.tabs(["📦 Itens", "📅 Compromissos"])
    
    with tab1:
        st.subheader("Itens Cadastrados")
        itens = db.listar_itens()
        
        if itens:
            for item in itens:
                with st.expander(f"📦 {item.nome} - Estoque Total: {item.quantidade_total}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**ID:** {item.id}")
                        st.write(f"**Nome:** {item.nome}")
                        st.write(f"**Quantidade Total:** {item.quantidade_total}")
                        if hasattr(item, 'descricao') and item.descricao:
                            st.write(f"**Descrição:** {item.descricao}")
                        if hasattr(item, 'localizacao') and item.localizacao:
                            st.write(f"**Localização:** {item.localizacao}")
                        # Conta compromissos sem acessar o relacionamento lazy
                        compromissos_count = len([c for c in db.listar_compromissos() if c.item_id == item.id])
                        st.write(f"**Total de Compromissos:** {compromissos_count}")
                    with col2:
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button(f"✏️ Editar", key=f"edit_item_{item.id}"):
                                st.session_state[f'editing_item_{item.id}'] = True
                                st.session_state[f'edit_nome_{item.id}'] = item.nome
                                st.session_state[f'edit_quantidade_{item.id}'] = item.quantidade_total
                                st.session_state[f'edit_descricao_{item.id}'] = getattr(item, 'descricao', '') or ''
                                st.session_state[f'edit_localizacao_{item.id}'] = getattr(item, 'localizacao', '') or ''
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
                            edit_nome = st.text_input("Nome do Item", value=st.session_state.get(f'edit_nome_{item.id}', item.nome), key=f"input_nome_{item.id}")
                            edit_quantidade = st.number_input("Quantidade Total", min_value=1, value=st.session_state.get(f'edit_quantidade_{item.id}', item.quantidade_total), key=f"input_quantidade_{item.id}")
                            edit_descricao = st.text_area("Descrição (opcional)", value=st.session_state.get(f'edit_descricao_{item.id}', getattr(item, 'descricao', '') or ''), key=f"input_descricao_{item.id}")
                            edit_localizacao = st.text_input("Localização (opcional)", value=st.session_state.get(f'edit_localizacao_{item.id}', getattr(item, 'localizacao', '') or ''), key=f"input_localizacao_{item.id}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
                            with col_cancel:
                                cancel = st.form_submit_button("❌ Cancelar")
                            
                            if submitted:
                                if edit_nome.strip():
                                    try:
                                        if db.atualizar_item(item.id, edit_nome.strip(), edit_quantidade, edit_descricao.strip() if edit_descricao else None, edit_localizacao.strip() if edit_localizacao else None):
                                            st.success("✅ Item atualizado com sucesso!")
                                            st.session_state[f'editing_item_{item.id}'] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao atualizar item. Item não encontrado.")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao atualizar item: {str(e)}")
                                else:
                                    st.warning("⚠️ Por favor, preencha o nome do item.")
                            
                            if cancel:
                                st.session_state[f'editing_item_{item.id}'] = False
                                st.rerun()
        else:
            st.info("ℹ️ Nenhum item cadastrado ainda.")
    
    with tab2:
        st.subheader("Compromissos Registrados")
        compromissos = db.listar_compromissos()
        
        if compromissos:
            # Ordenar por data de início (mais recentes primeiro)
            compromissos_ordenados = sorted(compromissos, key=lambda x: x.data_inicio, reverse=True)
            
            for comp in compromissos_ordenados:
                status = "🟢 Ativo" if comp.data_inicio <= date.today() <= comp.data_fim else "⚪ Inativo"
                with st.expander(f"📅 {comp.item.nome} - {comp.quantidade} unidades ({comp.data_inicio} a {comp.data_fim}) - {status}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**ID:** {comp.id}")
                        st.write(f"**Item:** {comp.item.nome}")
                        st.write(f"**Quantidade:** {comp.quantidade}")
                        st.write(f"**Período:** {comp.data_inicio.strftime('%d/%m/%Y')} a {comp.data_fim.strftime('%d/%m/%Y')}")
                        if hasattr(comp, 'descricao') and comp.descricao:
                            st.write(f"**Descrição:** {comp.descricao}")
                        if hasattr(comp, 'localizacao') and comp.localizacao:
                            st.write(f"**Localização:** {comp.localizacao}")
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
                                st.session_state[f'edit_localizacao_{comp.id}'] = getattr(comp, 'localizacao', '') or ''
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
                            edit_localizacao = st.text_input("Localização (opcional)", value=st.session_state.get(f'edit_localizacao_{comp.id}', getattr(comp, 'localizacao', '') or ''), key=f"input_localizacao_{comp.id}")
                            edit_contratante = st.text_input("Contratante (opcional)", value=st.session_state.get(f'edit_contratante_{comp.id}', getattr(comp, 'contratante', '') or ''), key=f"input_contratante_{comp.id}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
                            with col_cancel:
                                cancel = st.form_submit_button("❌ Cancelar")
                            
                            if submitted:
                                if edit_data_fim < edit_data_inicio:
                                    st.error("❌ Data fim deve ser igual ou posterior à data início!")
                                else:
                                    try:
                                        if db.atualizar_compromisso(
                                            comp.id,
                                            item_selecionado,
                                            edit_quantidade,
                                            edit_data_inicio,
                                            edit_data_fim,
                                            edit_descricao.strip() if edit_descricao else None,
                                            edit_localizacao.strip() if edit_localizacao else None,
                                            edit_contratante.strip() if edit_contratante else None
                                        ):
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
