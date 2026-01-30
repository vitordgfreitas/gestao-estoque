from models import get_session, Item, Compromisso, Carro, ContaReceber, ContaPagar, Financiamento, ParcelaFinanciamento
from datetime import date, datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
import validacoes
import auditoria

def criar_item(nome, quantidade_total, categoria='Estrutura de Evento', descricao=None, cidade=None, uf=None, endereco=None, placa=None, marca=None, modelo=None, ano=None):
    """Cria um novo item no estoque
    
    Args:
        nome: Nome do item
        quantidade_total: Quantidade total dispon├¡vel
        categoria: Categoria do item ('Estrutura de Evento' ou 'Carros')
        descricao: Descri├º├úo opcional do item
        cidade: Cidade onde o item est├í localizado (obrigat├│rio)
        uf: UF onde o item est├í localizado (obrigat├│rio)
        endereco: Endere├ºo opcional do item
        placa: Placa do carro (obrigat├│rio se categoria='Carros')
        marca: Marca do carro (obrigat├│rio se categoria='Carros')
        modelo: Modelo do carro (obrigat├│rio se categoria='Carros')
        ano: Ano do carro (obrigat├│rio se categoria='Carros')
    """
    session = get_session()
    try:
        # Valida├º├Áes robustas
        valido, msg_erro = validacoes.validar_item_completo(
            nome=nome,
            categoria=categoria or '',
            cidade=cidade or '',
            uf=uf or '',
            quantidade_total=quantidade_total,
            placa=placa,
            marca=marca,
            modelo=modelo,
            ano=ano
        )
        
        if not valido:
            raise ValueError(msg_erro)
        
        # Valida├º├úo de duplicatas
        # Verifica nome + categoria ├║nico
        item_existente = session.query(Item).filter(
            and_(
                Item.nome == nome,
                Item.categoria == categoria
            )
        ).first()
        
        if item_existente:
            raise ValueError(f"Item '{nome}' j├í existe na categoria '{categoria}'")
        
        # Valida├º├úo de placa ├║nica para carros
        if categoria == 'Carros' and placa:
            carro_existente = session.query(Carro).filter(Carro.placa == placa.upper().strip()).first()
            if carro_existente:
                raise ValueError(f"Placa {placa} j├í cadastrada")
        
        item = Item(
            nome=nome, 
            quantidade_total=quantidade_total,
            categoria=categoria,
            descricao=descricao,
            cidade=cidade,
            uf=uf.upper()[:2],  # Garante que UF tenha no m├íximo 2 caracteres e seja mai├║scula
            endereco=endereco
        )
        session.add(item)
        session.flush()  # Para obter o ID do item
        
        # Se for carro, cria registro na tabela carros
        if categoria == 'Carros':
            carro = Carro(
                item_id=item.id,
                placa=placa.upper().strip(),
                marca=marca.strip(),
                modelo=modelo.strip(),
                ano=int(ano)
            )
            session.add(carro)
        
        session.commit()
        session.refresh(item)
        if categoria == 'Carros' and item.carro:
            session.refresh(item.carro)
            session.expunge(item.carro)
        session.expunge(item)
        
        # Registra auditoria
        valores_novos = {
            'id': item.id,
            'nome': nome,
            'quantidade_total': quantidade_total,
            'categoria': categoria,
            'descricao': descricao,
            'cidade': cidade,
            'uf': uf,
            'endereco': endereco
        }
        if categoria == 'Carros':
            valores_novos.update({
                'placa': placa,
                'marca': marca,
                'modelo': modelo,
                'ano': ano
            })
        auditoria.registrar_auditoria('CREATE', 'Itens', item.id, valores_novos=valores_novos)
        
        return item
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_itens():
    """Lista todos os itens do estoque"""
    session = get_session()
    try:
        # Carrega os relacionamentos antes de desanexar
        itens = session.query(Item).options(joinedload(Item.compromissos), joinedload(Item.carro)).all()
        # Desanexa todos os objetos da sess├úo
        for item in itens:
            if item.carro:
                session.expunge(item.carro)
            session.expunge(item)
        return itens
    finally:
        session.close()


def buscar_item_por_id(item_id):
    """Busca um item pelo ID"""
    session = get_session()
    try:
        item = session.query(Item).options(joinedload(Item.carro)).filter(Item.id == item_id).first()
        if item:
            if item.carro:
                session.expunge(item.carro)
            session.expunge(item)
        return item
    finally:
        session.close()


def atualizar_item(item_id, nome, quantidade_total, categoria=None, descricao=None, cidade=None, uf=None, endereco=None, placa=None, marca=None, modelo=None, ano=None, campos_categoria=None):
    """Atualiza um item existente
    
    Args:
        item_id: ID do item
        nome: Nome do item
        quantidade_total: Quantidade total dispon├¡vel
        categoria: Categoria do item ('Estrutura de Evento' ou 'Carros')
        descricao: Descri├º├úo opcional do item
        cidade: Cidade onde o item est├í localizado (obrigat├│rio)
        uf: UF onde o item est├í localizado (obrigat├│rio)
        endereco: Endere├ºo opcional do item
        placa: Placa do carro (obrigat├│rio se categoria='Carros')
        marca: Marca do carro (obrigat├│rio se categoria='Carros')
        modelo: Modelo do carro (obrigat├│rio se categoria='Carros')
        ano: Ano do carro (obrigat├│rio se categoria='Carros')
    """
    session = get_session()
    try:
        item = session.query(Item).options(joinedload(Item.carro)).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Item com ID {item_id} n├úo encontrado")
        
        # Usa valores atuais se n├úo fornecidos
        categoria_final = categoria if categoria is not None else (item.categoria or '')
        cidade_final = cidade if cidade else (item.cidade or '')
        uf_final = uf if uf else (item.uf or '')
        
        # Valida├º├Áes robustas
        valido, msg_erro = validacoes.validar_item_completo(
            nome=nome,
            categoria=categoria_final,
            cidade=cidade_final,
            uf=uf_final,
            quantidade_total=quantidade_total,
            placa=placa,
            marca=marca,
            modelo=modelo,
            ano=ano,
            campos_categoria=campos_categoria
        )
        
        if not valido:
            raise ValueError(msg_erro)
        
        # Valida├º├úo de duplicatas (excluindo o item atual)
        item_existente = session.query(Item).filter(
            and_(
                Item.nome == nome,
                Item.categoria == categoria_final,
                Item.id != item_id
            )
        ).first()
        
        if item_existente:
            raise ValueError(f"Item '{nome}' j├í existe na categoria '{categoria_final}'")
        
        # Valida├º├úo de placa ├║nica para carros (excluindo o item atual)
        if categoria_final == 'Carros' and placa:
            carro_existente = session.query(Carro).join(Item).filter(
                and_(
                    Carro.placa == placa.upper().strip(),
                    Carro.item_id != item_id
                )
            ).first()
            if carro_existente:
                raise ValueError(f"Placa {placa} j├í cadastrada")
        
        # Se categoria mudou ou foi especificada
        if categoria:
            item.categoria = categoria
            
            # Se mudou para Carros, cria registro de carro se n├úo existir
            if categoria == 'Carros':
                if not placa or not marca or not modelo or not ano:
                    raise ValueError("Para carros, placa, marca, modelo e ano s├úo obrigat├│rios")
                
                if item.carro:
                    # Atualiza carro existente
                    item.carro.placa = placa.upper().strip()
                    item.carro.marca = marca.strip()
                    item.carro.modelo = modelo.strip()
                    item.carro.ano = int(ano)
                else:
                    # Cria novo registro de carro
                    carro = Carro(
                        item_id=item.id,
                        placa=placa.upper().strip(),
                        marca=marca.strip(),
                        modelo=modelo.strip(),
                        ano=int(ano)
                    )
                    session.add(carro)
            elif item.carro:
                # Se mudou de Carros para outra categoria, remove o registro de carro
                session.delete(item.carro)
        
        # Atualiza campos do item
        item.nome = nome
        item.quantidade_total = quantidade_total
        item.descricao = descricao
        item.cidade = cidade_final
        item.uf = uf_final.upper()[:2]  # Garante que UF tenha no m├íximo 2 caracteres e seja mai├║scula
        item.endereco = endereco
        
        # Se j├í ├® carro e n├úo mudou categoria, atualiza dados do carro
        if item.categoria == 'Carros' and item.carro and placa and marca and modelo and ano:
            item.carro.placa = placa.upper().strip()
            item.carro.marca = marca.strip()
            item.carro.modelo = modelo.strip()
            item.carro.ano = int(ano)
        
        # Prepara valores antigos para auditoria (antes do commit, mas ap├│s atualizar campos)
        valores_antigos = {
            'id': item.id,
            'nome': item.nome,
            'quantidade_total': item.quantidade_total,
            'categoria': item.categoria,
            'descricao': item.descricao,
            'cidade': item.cidade,
            'uf': item.uf,
            'endereco': item.endereco
        }
        if item.carro:
            valores_antigos.update({
                'placa': item.carro.placa,
                'marca': item.carro.marca,
                'modelo': item.carro.modelo,
                'ano': item.carro.ano
            })
        
        session.commit()
        session.refresh(item)
        if item.carro:
            session.refresh(item.carro)
            session.expunge(item.carro)
        session.expunge(item)
        
        # Prepara valores novos para auditoria
        valores_novos = {
            'id': item.id,
            'nome': nome,
            'quantidade_total': quantidade_total,
            'categoria': categoria_final,
            'descricao': descricao,
            'cidade': cidade_final,
            'uf': uf_final,
            'endereco': endereco
        }
        if categoria_final == 'Carros' and item.carro:
            valores_novos.update({
                'placa': item.carro.placa,
                'marca': item.carro.marca,
                'modelo': item.carro.modelo,
                'ano': item.carro.ano
            })
        
        # Registra auditoria
        auditoria.registrar_auditoria('UPDATE', 'Itens', item.id, valores_antigos, valores_novos)
        
        return item
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def criar_compromisso(item_id, quantidade, data_inicio, data_fim, descricao=None, cidade=None, uf=None, endereco=None, contratante=None):
    """Cria um novo compromisso (aluguel)
    
    Args:
        item_id: ID do item
        quantidade: Quantidade alugada
        data_inicio: Data de in├¡cio do aluguel
        data_fim: Data de fim do aluguel
        descricao: Descri├º├úo opcional do compromisso
        cidade: Cidade do compromisso (obrigat├│rio)
        uf: UF do compromisso (obrigat├│rio)
        endereco: Endere├ºo opcional do compromisso
        contratante: Nome do contratante (opcional)
    """
    session = get_session()
    try:
        if not cidade or not uf:
            raise ValueError("Cidade e UF s├úo obrigat├│rios")
        
        compromisso = Compromisso(
            item_id=item_id,
            quantidade=quantidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            descricao=descricao,
            cidade=cidade,
            uf=uf.upper()[:2],  # Garante que UF tenha no m├íximo 2 caracteres e seja mai├║scula
            endereco=endereco,
            contratante=contratante
        )
        session.add(compromisso)
        session.commit()
        session.refresh(compromisso)
        # Carrega o relacionamento com Item antes de desanexar
        compromisso.item  # For├ºa o carregamento do relacionamento
        # Desanexa o objeto da sess├úo para poder ser usado depois que a sess├úo fechar
        session.expunge(compromisso)
        if compromisso.item:
            session.expunge(compromisso.item)
        
        # Registra auditoria
        valores_novos = {
            'id': compromisso.id,
            'item_id': item_id,
            'quantidade': quantidade,
            'data_inicio': data_inicio.isoformat() if isinstance(data_inicio, date) else str(data_inicio),
            'data_fim': data_fim.isoformat() if isinstance(data_fim, date) else str(data_fim),
            'descricao': descricao,
            'cidade': cidade,
            'uf': uf,
            'endereco': endereco,
            'contratante': contratante
        }
        auditoria.registrar_auditoria('CREATE', 'Compromissos', compromisso.id, valores_novos=valores_novos)
        
        return compromisso
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_compromissos():
    """Lista todos os compromissos"""
    session = get_session()
    try:
        # Carrega o relacionamento com Item antes de desanexar
        compromissos = session.query(Compromisso).options(joinedload(Compromisso.item)).all()
        # Desanexa todos os objetos da sess├úo
        for compromisso in compromissos:
            session.expunge(compromisso)
            # Tamb├®m desanexa o item relacionado
            if compromisso.item:
                session.expunge(compromisso.item)
        return compromissos
    finally:
        session.close()


def verificar_disponibilidade(item_id, data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de um item em uma data espec├¡fica
    
    Args:
        item_id: ID do item
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localiza├º├úo
    """
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None
        
        # Busca compromissos que est├úo ativos na data de consulta
        compromissos_ativos_query = session.query(Compromisso).filter(
            and_(
                Compromisso.item_id == item_id,
                Compromisso.data_inicio <= data_consulta,
                Compromisso.data_fim >= data_consulta
            )
        )
        
        # Se h├í filtro de localiza├º├úo, aplica filtro adicional (formato: "Cidade - UF")
        if filtro_localizacao:
            cidade_uf = filtro_localizacao.split(" - ")
            if len(cidade_uf) == 2:
                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                compromissos_ativos_query = compromissos_ativos_query.filter(
                    and_(
                        Compromisso.cidade == cidade_filtro,
                        Compromisso.uf == uf_filtro.upper()
                    )
                )
        
        compromissos_ativos = compromissos_ativos_query.all()
        
        quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
        
        # Se h├í filtro de localiza├º├úo e o item n├úo est├í nessa localiza├º├úo,
        # considera que n├úo h├í itens dispon├¡veis naquela localiza├º├úo
        if filtro_localizacao:
            cidade_uf = filtro_localizacao.split(" - ")
            if len(cidade_uf) == 2:
                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                item_na_localizacao = (item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                if not item_na_localizacao:
                    # Item n├úo est├í na localiza├º├úo, ent├úo dispon├¡vel = 0 (ou negativo se houver compromissos)
                    quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        else:
            quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        
        # Desanexa objetos da sess├úo antes de retornar
        session.expunge(item)
        for comp in compromissos_ativos:
            session.expunge(comp)
        
        return {
            'item': item,
            'quantidade_total': item.quantidade_total,
            'quantidade_comprometida': quantidade_comprometida,
            'quantidade_disponivel': quantidade_disponivel,
            'compromissos_ativos': compromissos_ativos
        }
    finally:
        session.close()


def verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=None):
    """Verifica se h├í disponibilidade suficiente em todo o per├¡odo para um novo compromisso"""
    from datetime import timedelta
    
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None
        
        # Busca compromissos que se sobrep├Áem com o per├¡odo solicitado
        # Dois per├¡odos se sobrep├Áem se: inicio1 <= fim2 AND inicio2 <= fim1
        compromissos_sobrepostos = session.query(Compromisso).filter(
            and_(
                Compromisso.item_id == item_id,
                Compromisso.data_inicio <= data_fim,
                Compromisso.data_fim >= data_inicio
            )
        ).all()
        
        # Exclui o pr├│prio compromisso se estiver editando
        if excluir_compromisso_id:
            compromissos_sobrepostos = [c for c in compromissos_sobrepostos if c.id != excluir_compromisso_id]
        
        # Encontra o dia com maior comprometimento no per├¡odo
        max_comprometido = 0
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            compromissos_no_dia = [c for c in compromissos_sobrepostos 
                                  if c.data_inicio <= data_atual <= c.data_fim]
            comprometido_no_dia = sum(c.quantidade for c in compromissos_no_dia)
            max_comprometido = max(max_comprometido, comprometido_no_dia)
            
            # Incrementa a data
            if data_atual >= data_fim:
                break
            data_atual += timedelta(days=1)
        
        # Desanexa objeto da sess├úo antes de retornar
        session.expunge(item)
        
        return {
            'item': item,
            'quantidade_total': item.quantidade_total,
            'max_comprometido': max_comprometido,
            'disponivel_minimo': item.quantidade_total - max_comprometido
        }
    finally:
        session.close()


def verificar_disponibilidade_todos_itens(data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de todos os itens em uma data espec├¡fica
    
    Args:
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localiza├º├úo
    """
    session = get_session()
    try:
        itens = session.query(Item).all()
        resultados = []
        
        for item in itens:
            compromissos_ativos_query = session.query(Compromisso).filter(
                and_(
                    Compromisso.item_id == item.id,
                    Compromisso.data_inicio <= data_consulta,
                    Compromisso.data_fim >= data_consulta
                )
            )
            
            # Se h├í filtro de localiza├º├úo, aplica filtro adicional (formato: "Cidade - UF")
            if filtro_localizacao:
                cidade_uf = filtro_localizacao.split(" - ")
                if len(cidade_uf) == 2:
                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                    compromissos_ativos_query = compromissos_ativos_query.filter(
                        and_(
                            Compromisso.cidade == cidade_filtro,
                            Compromisso.uf == uf_filtro.upper()
                        )
                    )
            
            compromissos_ativos = compromissos_ativos_query.all()
            
            quantidade_comprometida = sum(c.quantidade for c in compromissos_ativos)
            
            # Se h├í filtro de localiza├º├úo e o item n├úo est├í nessa localiza├º├úo,
            # considera que n├úo h├í itens dispon├¡veis naquela localiza├º├úo
            if filtro_localizacao:
                cidade_uf = filtro_localizacao.split(" - ")
                if len(cidade_uf) == 2:
                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                    item_na_localizacao = (item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                    if not item_na_localizacao:
                        # Item n├úo est├í na localiza├º├úo, ent├úo dispon├¡vel = 0 (ou negativo se houver compromissos)
                        quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                    else:
                        quantidade_disponivel = item.quantidade_total - quantidade_comprometida
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            
            # Desanexa objeto da sess├úo
            session.expunge(item)
            
            resultados.append({
                'item': item,
                'quantidade_total': item.quantidade_total,
                'quantidade_comprometida': quantidade_comprometida,
                'quantidade_disponivel': quantidade_disponivel
            })
        
        return resultados
    finally:
        session.close()


def deletar_item(item_id):
    """Deleta um item e todos os seus compromissos"""
    session = get_session()
    try:
        item = session.query(Item).options(joinedload(Item.compromissos)).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Item com ID {item_id} n├úo encontrado")
        
        # Verifica se h├í compromissos ativos ou futuros
        hoje = date.today()
        compromissos_futuros = [
            c for c in item.compromissos 
            if isinstance(c.data_fim, date) and c.data_fim >= hoje
        ]
        
        if compromissos_futuros:
            raise ValueError(
                f"N├úo ├® poss├¡vel deletar o item. Existem {len(compromissos_futuros)} compromisso(s) ativo(s) ou futuro(s). "
                f"Delete os compromissos primeiro ou aguarde sua conclus├úo."
            )
        
        # Prepara valores antigos para auditoria antes de deletar
        valores_antigos = {
            'id': item.id,
            'nome': item.nome,
            'quantidade_total': item.quantidade_total,
            'categoria': item.categoria,
            'descricao': item.descricao,
            'cidade': item.cidade,
            'uf': item.uf,
            'endereco': item.endereco
        }
        if hasattr(item, 'carro') and item.carro:
            valores_antigos.update({
                'placa': item.carro.placa,
                'marca': item.carro.marca,
                'modelo': item.carro.modelo,
                'ano': item.carro.ano
            })
        
        session.delete(item)
        session.commit()
        
        # Registra auditoria
        auditoria.registrar_auditoria('DELETE', 'Itens', item_id, valores_antigos=valores_antigos)
        
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def atualizar_compromisso(compromisso_id, item_id, quantidade, data_inicio, data_fim, descricao=None, cidade=None, uf=None, endereco=None, contratante=None):
    """Atualiza um compromisso existente
    
    Args:
        compromisso_id: ID do compromisso
        item_id: ID do item
        quantidade: Quantidade alugada
        data_inicio: Data de in├¡cio do aluguel
        data_fim: Data de fim do aluguel
        descricao: Descri├º├úo opcional do compromisso
        cidade: Cidade do compromisso (obrigat├│rio)
        uf: UF do compromisso (obrigat├│rio)
        endereco: Endere├ºo opcional do compromisso
        contratante: Nome do contratante (opcional)
    """
    session = get_session()
    try:
        compromisso = session.query(Compromisso).filter(Compromisso.id == compromisso_id).first()
        if not compromisso:
            raise ValueError(f"Compromisso com ID {compromisso_id} n├úo encontrado")
        
        # Verifica se o item existe
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Item com ID {item_id} n├úo encontrado")
        
        # Verifica disponibilidade (excluindo o compromisso atual)
        disponibilidade = verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=compromisso_id)
        if not disponibilidade:
            raise ValueError(f"Erro ao verificar disponibilidade do item {item_id}")
        
        quantidade_disponivel = disponibilidade.get('disponivel_minimo', 0)
        
        # Valida├º├Áes robustas
        valido, msg_erro = validacoes.validar_compromisso_completo(
            item_id=item_id,
            quantidade=quantidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            cidade=cidade or '',
            uf=uf or '',
            quantidade_disponivel=quantidade_disponivel
        )
        
        if not valido:
            raise ValueError(msg_erro)
        
        if compromisso:
            
            compromisso.item_id = item_id
            compromisso.quantidade = quantidade
            compromisso.data_inicio = data_inicio
            compromisso.data_fim = data_fim
            compromisso.descricao = descricao
            compromisso.cidade = cidade
            compromisso.uf = uf.upper()[:2]  # Garante que UF tenha no m├íximo 2 caracteres e seja mai├║scula
            compromisso.endereco = endereco
            compromisso.contratante = contratante
            
            # Prepara valores antigos para auditoria
            valores_antigos = {
                'id': compromisso.id,
                'item_id': compromisso.item_id,
                'quantidade': compromisso.quantidade,
                'data_inicio': compromisso.data_inicio.isoformat() if isinstance(compromisso.data_inicio, date) else str(compromisso.data_inicio),
                'data_fim': compromisso.data_fim.isoformat() if isinstance(compromisso.data_fim, date) else str(compromisso.data_fim),
                'descricao': compromisso.descricao,
                'cidade': compromisso.cidade,
                'uf': compromisso.uf,
                'endereco': compromisso.endereco,
                'contratante': compromisso.contratante
            }
            
            session.commit()
            session.refresh(compromisso)
            compromisso.item  # For├ºa o carregamento do relacionamento
            session.expunge(compromisso)
            if compromisso.item:
                session.expunge(compromisso.item)
            
            # Prepara valores novos para auditoria
            valores_novos = {
                'id': compromisso.id,
                'item_id': item_id,
                'quantidade': quantidade,
                'data_inicio': data_inicio.isoformat() if isinstance(data_inicio, date) else str(data_inicio),
                'data_fim': data_fim.isoformat() if isinstance(data_fim, date) else str(data_fim),
                'descricao': descricao,
                'cidade': cidade,
                'uf': uf,
                'endereco': endereco,
                'contratante': contratante
            }
            
            # Registra auditoria
            auditoria.registrar_auditoria('UPDATE', 'Compromissos', compromisso_id, valores_antigos, valores_novos)
            
            return compromisso
        return None
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def deletar_compromisso(compromisso_id):
    """Deleta um compromisso"""
    session = get_session()
    try:
        compromisso = session.query(Compromisso).filter(Compromisso.id == compromisso_id).first()
        if compromisso:
            # Prepara valores antigos para auditoria antes de deletar
            valores_antigos = {
                'id': compromisso.id,
                'item_id': compromisso.item_id,
                'quantidade': compromisso.quantidade,
                'data_inicio': compromisso.data_inicio.isoformat() if isinstance(compromisso.data_inicio, date) else str(compromisso.data_inicio),
                'data_fim': compromisso.data_fim.isoformat() if isinstance(compromisso.data_fim, date) else str(compromisso.data_fim),
                'descricao': compromisso.descricao,
                'cidade': compromisso.cidade,
                'uf': compromisso.uf,
                'endereco': compromisso.endereco,
                'contratante': compromisso.contratante
            }
            
            session.delete(compromisso)
            session.commit()
            
            # Registra auditoria
            auditoria.registrar_auditoria('DELETE', 'Compromissos', compromisso_id, valores_antigos=valores_antigos)
            
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ============= CONTAS A RECEBER =============

def criar_conta_receber(compromisso_id, descricao, valor, data_vencimento, forma_pagamento=None, observacoes=None):
    """Cria uma nova conta a receber vinculada a um compromisso"""
    session = get_session()
    try:
        # Verifica se compromisso existe
        compromisso = session.query(Compromisso).filter(Compromisso.id == compromisso_id).first()
        if not compromisso:
            raise ValueError(f"Compromisso {compromisso_id} n├úo encontrado")
        
        # Calcula status inicial
        hoje = date.today()
        status = 'Vencido' if data_vencimento < hoje else 'Pendente'
        
        nova_conta = ContaReceber(
            compromisso_id=compromisso_id,
            descricao=descricao,
            valor=float(valor),
            data_vencimento=data_vencimento,
            data_pagamento=None,
            status=status,
            forma_pagamento=forma_pagamento,
            observacoes=observacoes
        )
        
        session.add(nova_conta)
        session.commit()
        session.refresh(nova_conta)
        
        auditoria.registrar_auditoria('CREATE', 'Contas a Receber', nova_conta.id, valores_novos={
            'compromisso_id': compromisso_id,
            'descricao': descricao,
            'valor': valor,
            'data_vencimento': str(data_vencimento)
        })
        
        return nova_conta
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_contas_receber(status=None, data_inicio=None, data_fim=None, compromisso_id=None):
    """Lista contas a receber com filtros opcionais"""
    session = get_session()
    try:
        query = session.query(ContaReceber)
        
        if status:
            query = query.filter(ContaReceber.status == status)
        if compromisso_id:
            query = query.filter(ContaReceber.compromisso_id == compromisso_id)
        if data_inicio:
            query = query.filter(ContaReceber.data_vencimento >= data_inicio)
        if data_fim:
            query = query.filter(ContaReceber.data_vencimento <= data_fim)
        
        contas = query.all()
        
        # Recalcula status para garantir consist├¬ncia
        hoje = date.today()
        for conta in contas:
            if conta.data_pagamento:
                conta.status = 'Pago'
            elif conta.data_vencimento < hoje:
                conta.status = 'Vencido'
            else:
                conta.status = 'Pendente'
        
        return contas
    except Exception as e:
        raise e
    finally:
        session.close()


def atualizar_conta_receber(conta_id, descricao=None, valor=None, data_vencimento=None, data_pagamento=None, status=None, forma_pagamento=None, observacoes=None):
    """Atualiza uma conta a receber"""
    session = get_session()
    try:
        conta = session.query(ContaReceber).filter(ContaReceber.id == conta_id).first()
        if not conta:
            return None
        
        valores_antigos = {
            'descricao': conta.descricao,
            'valor': conta.valor,
            'data_vencimento': str(conta.data_vencimento),
            'data_pagamento': str(conta.data_pagamento) if conta.data_pagamento else None,
            'status': conta.status
        }
        
        if descricao is not None:
            conta.descricao = descricao
        if valor is not None:
            conta.valor = float(valor)
        if data_vencimento is not None:
            conta.data_vencimento = data_vencimento
        if data_pagamento is not None:
            conta.data_pagamento = data_pagamento
            if data_pagamento:
                conta.status = 'Pago'
        if status is not None:
            conta.status = status
        if forma_pagamento is not None:
            conta.forma_pagamento = forma_pagamento
        if observacoes is not None:
            conta.observacoes = observacoes
        
        # Recalcula status se necess├írio
        hoje = date.today()
        if conta.data_pagamento:
            conta.status = 'Pago'
        elif conta.data_vencimento < hoje:
            conta.status = 'Vencido'
        else:
            conta.status = 'Pendente'
        
        session.commit()
        session.refresh(conta)
        
        auditoria.registrar_auditoria('UPDATE', 'Contas a Receber', conta_id, valores_antigos=valores_antigos, valores_novos={
            'descricao': conta.descricao,
            'valor': conta.valor,
            'data_vencimento': str(conta.data_vencimento),
            'data_pagamento': str(conta.data_pagamento) if conta.data_pagamento else None,
            'status': conta.status
        })
        
        return conta
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def marcar_conta_receber_paga(conta_id, data_pagamento=None, forma_pagamento=None):
    """Marca uma conta a receber como paga"""
    if data_pagamento is None:
        data_pagamento = date.today()
    return atualizar_conta_receber(conta_id, data_pagamento=data_pagamento, status='Pago', forma_pagamento=forma_pagamento)


def deletar_conta_receber(conta_id):
    """Deleta uma conta a receber"""
    session = get_session()
    try:
        conta = session.query(ContaReceber).filter(ContaReceber.id == conta_id).first()
        if not conta:
            return False
        
        valores_antigos = {
            'compromisso_id': conta.compromisso_id,
            'descricao': conta.descricao,
            'valor': conta.valor
        }
        
        session.delete(conta)
        session.commit()
        
        auditoria.registrar_auditoria('DELETE', 'Contas a Receber', conta_id, valores_antigos=valores_antigos)
        
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ============= CONTAS A PAGAR =============

def criar_conta_pagar(descricao, categoria, valor, data_vencimento, fornecedor=None, item_id=None, forma_pagamento=None, observacoes=None):
    """Cria uma nova conta a pagar"""
    session = get_session()
    try:
        # Verifica se item existe (se fornecido)
        if item_id:
            item = session.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise ValueError(f"Item {item_id} n├úo encontrado")
        
        # Calcula status inicial
        hoje = date.today()
        status = 'Vencido' if data_vencimento < hoje else 'Pendente'
        
        nova_conta = ContaPagar(
            descricao=descricao,
            categoria=categoria,
            valor=float(valor),
            data_vencimento=data_vencimento,
            data_pagamento=None,
            status=status,
            fornecedor=fornecedor,
            item_id=item_id,
            forma_pagamento=forma_pagamento,
            observacoes=observacoes
        )
        
        session.add(nova_conta)
        session.commit()
        session.refresh(nova_conta)
        
        auditoria.registrar_auditoria('CREATE', 'Contas a Pagar', nova_conta.id, valores_novos={
            'descricao': descricao,
            'categoria': categoria,
            'valor': valor,
            'data_vencimento': str(data_vencimento)
        })
        
        return nova_conta
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_contas_pagar(status=None, data_inicio=None, data_fim=None, categoria=None):
    """Lista contas a pagar com filtros opcionais"""
    session = get_session()
    try:
        query = session.query(ContaPagar)
        
        if status:
            query = query.filter(ContaPagar.status == status)
        if categoria:
            query = query.filter(ContaPagar.categoria == categoria)
        if data_inicio:
            query = query.filter(ContaPagar.data_vencimento >= data_inicio)
        if data_fim:
            query = query.filter(ContaPagar.data_vencimento <= data_fim)
        
        contas = query.all()
        
        # Recalcula status para garantir consist├¬ncia
        hoje = date.today()
        for conta in contas:
            if conta.data_pagamento:
                conta.status = 'Pago'
            elif conta.data_vencimento < hoje:
                conta.status = 'Vencido'
            else:
                conta.status = 'Pendente'
        
        return contas
    except Exception as e:
        raise e
    finally:
        session.close()


def atualizar_conta_pagar(conta_id, descricao=None, categoria=None, valor=None, data_vencimento=None, data_pagamento=None, status=None, fornecedor=None, item_id=None, forma_pagamento=None, observacoes=None):
    """Atualiza uma conta a pagar"""
    session = get_session()
    try:
        conta = session.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
        if not conta:
            return None
        
        valores_antigos = {
            'descricao': conta.descricao,
            'categoria': conta.categoria,
            'valor': conta.valor,
            'data_vencimento': str(conta.data_vencimento),
            'data_pagamento': str(conta.data_pagamento) if conta.data_pagamento else None,
            'status': conta.status
        }
        
        if descricao is not None:
            conta.descricao = descricao
        if categoria is not None:
            conta.categoria = categoria
        if valor is not None:
            conta.valor = float(valor)
        if data_vencimento is not None:
            conta.data_vencimento = data_vencimento
        if data_pagamento is not None:
            conta.data_pagamento = data_pagamento
            if data_pagamento:
                conta.status = 'Pago'
        if status is not None:
            conta.status = status
        if fornecedor is not None:
            conta.fornecedor = fornecedor
        if item_id is not None:
            conta.item_id = item_id
        if forma_pagamento is not None:
            conta.forma_pagamento = forma_pagamento
        if observacoes is not None:
            conta.observacoes = observacoes
        
        # Recalcula status se necess├írio
        hoje = date.today()
        if conta.data_pagamento:
            conta.status = 'Pago'
        elif conta.data_vencimento < hoje:
            conta.status = 'Vencido'
        else:
            conta.status = 'Pendente'
        
        session.commit()
        session.refresh(conta)
        
        auditoria.registrar_auditoria('UPDATE', 'Contas a Pagar', conta_id, valores_antigos=valores_antigos, valores_novos={
            'descricao': conta.descricao,
            'categoria': conta.categoria,
            'valor': conta.valor,
            'data_vencimento': str(conta.data_vencimento),
            'data_pagamento': str(conta.data_pagamento) if conta.data_pagamento else None,
            'status': conta.status
        })
        
        return conta
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def marcar_conta_pagar_paga(conta_id, data_pagamento=None, forma_pagamento=None):
    """Marca uma conta a pagar como paga"""
    if data_pagamento is None:
        data_pagamento = date.today()
    return atualizar_conta_pagar(conta_id, data_pagamento=data_pagamento, status='Pago', forma_pagamento=forma_pagamento)


def deletar_conta_pagar(conta_id):
    """Deleta uma conta a pagar"""
    session = get_session()
    try:
        conta = session.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
        if not conta:
            return False
        
        valores_antigos = {
            'descricao': conta.descricao,
            'categoria': conta.categoria,
            'valor': conta.valor
        }
        
        session.delete(conta)
        session.commit()
        
        auditoria.registrar_auditoria('DELETE', 'Contas a Pagar', conta_id, valores_antigos=valores_antigos)
        
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ============= FUN├ç├òES DE C├üLCULO FINANCEIRO =============

def calcular_saldo_periodo(data_inicio, data_fim):
    """Calcula saldo (receitas - despesas) em um per├¡odo"""
    receitas = listar_contas_receber(data_inicio=data_inicio, data_fim=data_fim)
    despesas = listar_contas_pagar(data_inicio=data_inicio, data_fim=data_fim)
    
    receitas_pagas = sum(c.valor for c in receitas if c.status == 'Pago')
    despesas_pagas = sum(c.valor for c in despesas if c.status == 'Pago')
    
    return {
        'receitas': receitas_pagas,
        'despesas': despesas_pagas,
        'saldo': receitas_pagas - despesas_pagas,
        'total_receitas': len(receitas),
        'total_despesas': len(despesas)
    }


def obter_fluxo_caixa(data_inicio, data_fim):
    """Retorna fluxo de caixa por per├¡odo (agrupado por m├¬s)"""
    receitas = listar_contas_receber(data_inicio=data_inicio, data_fim=data_fim)
    despesas = listar_contas_pagar(data_inicio=data_inicio, data_fim=data_fim)
    
    fluxo = {}
    
    for conta in receitas:
        if conta.status == 'Pago':
            mes = conta.data_pagamento.strftime('%Y-%m') if conta.data_pagamento else conta.data_vencimento.strftime('%Y-%m')
            if mes not in fluxo:
                fluxo[mes] = {'receitas': 0, 'despesas': 0}
            fluxo[mes]['receitas'] += conta.valor
    
    for conta in despesas:
        if conta.status == 'Pago':
            mes = conta.data_pagamento.strftime('%Y-%m') if conta.data_pagamento else conta.data_vencimento.strftime('%Y-%m')
            if mes not in fluxo:
                fluxo[mes] = {'receitas': 0, 'despesas': 0}
            fluxo[mes]['despesas'] += conta.valor
    
    # Converte para lista ordenada
    resultado = []
    for mes in sorted(fluxo.keys()):
        resultado.append({
            'mes': mes,
            'receitas': fluxo[mes]['receitas'],
            'despesas': fluxo[mes]['despesas'],
            'saldo': fluxo[mes]['receitas'] - fluxo[mes]['despesas']
        })
    
    return resultado


# ============= FINANCIAMENTOS =============

def criar_financiamento(item_id, valor_total, numero_parcelas, taxa_juros, data_inicio, instituicao_financeira=None, observacoes=None, parcelas_customizadas=None):
    """Cria um novo financiamento e gera as parcelas automaticamente"""
    from datetime import timedelta
    import calendar
    
    session = get_session()
    try:
        # Verifica se item existe
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Item {item_id} n├úo encontrado")
        
        # Calcula valor da parcela com juros (Sistema Price - parcelas fixas)
        # PMT = PV * (i * (1+i)^n) / ((1+i)^n - 1)
        # onde: PMT = valor da parcela, PV = valor financiado, i = taxa mensal, n = número de parcelas
        if not parcelas_customizadas and taxa_juros > 0:
            i = float(taxa_juros)  # Taxa mensal (ex: 0.01 para 1%)
            n = numero_parcelas
            if i > 0:
                # Sistema Price (parcelas fixas com juros compostos)
                valor_parcela = valor_total * (i * ((1 + i) ** n)) / (((1 + i) ** n) - 1)
            else:
                valor_parcela = valor_total / numero_parcelas
        else:
            valor_parcela = valor_total / numero_parcelas if not parcelas_customizadas else 0
        
        # Calcula valor total a pagar (com juros)
        valor_total_a_pagar = valor_parcela * numero_parcelas if not parcelas_customizadas else valor_total
        
        # Cria financiamento
        # valor_total armazena o valor financiado (principal)
        # valor_parcela já inclui os juros calculados acima
        financiamento = Financiamento(
            item_id=item_id,
            valor_total=float(valor_total),  # Valor financiado (principal)
            numero_parcelas=numero_parcelas,
            valor_parcela=float(valor_parcela),  # Valor da parcela com juros
            taxa_juros=float(taxa_juros),
            data_inicio=data_inicio,
            status='Ativo',
            instituicao_financeira=instituicao_financeira,
            observacoes=observacoes
        )
        
        session.add(financiamento)
        session.flush()  # Para obter o ID
        
        # Gera parcelas
        if parcelas_customizadas:
            # Usa parcelas customizadas
            for parcela_custom in parcelas_customizadas:
                parcela = ParcelaFinanciamento(
                    financiamento_id=financiamento.id,
                    numero_parcela=parcela_custom['numero'],
                    valor_original=float(parcela_custom['valor']),
                    valor_pago=0.0,
                    data_vencimento=parcela_custom['data_vencimento'] if isinstance(parcela_custom['data_vencimento'], date) else datetime.strptime(parcela_custom['data_vencimento'], '%Y-%m-%d').date(),
                    data_pagamento=None,
                    status='Pendente',
                    juros=0.0,
                    multa=0.0,
                    desconto=0.0,
                    link_boleto=None
                )
                session.add(parcela)
        else:
            # Gera parcelas automaticamente (fixas)
            data_venc = data_inicio
            for i in range(1, numero_parcelas + 1):
                # Calcula data de vencimento
                if i == 1:
                    data_vencimento = data_venc
                else:
                    meses_adicionar = i - 1
                    ano = data_venc.year
                    mes = data_venc.month + meses_adicionar
                    while mes > 12:
                        mes -= 12
                        ano += 1
                    try:
                        data_vencimento = date(ano, mes, data_venc.day)
                    except ValueError:
                        ultimo_dia = calendar.monthrange(ano, mes)[1]
                        data_vencimento = date(ano, mes, ultimo_dia)
                
                parcela = ParcelaFinanciamento(
                    financiamento_id=financiamento.id,
                    numero_parcela=i,
                    valor_original=float(valor_parcela),
                    valor_pago=0.0,
                    data_vencimento=data_vencimento,
                    data_pagamento=None,
                    status='Pendente',
                    juros=0.0,
                    multa=0.0,
                    desconto=0.0,
                    link_boleto=None
                )
                session.add(parcela)
        
        session.commit()
        session.refresh(financiamento)
        
        auditoria.registrar_auditoria('CREATE', 'Financiamentos', financiamento.id, valores_novos={
            'item_id': item_id,
            'valor_total': valor_total,
            'numero_parcelas': numero_parcelas
        })
        
        return financiamento
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_financiamentos(status=None, item_id=None):
    """Lista financiamentos com filtros opcionais"""
    session = get_session()
    try:
        query = session.query(Financiamento)
        
        if status:
            query = query.filter(Financiamento.status == status)
        if item_id:
            query = query.filter(Financiamento.item_id == item_id)
        
        return query.all()
    except Exception as e:
        raise e
    finally:
        session.close()


def buscar_financiamento_por_id(financiamento_id):
    """Busca um financiamento por ID"""
    session = get_session()
    try:
        return session.query(Financiamento).filter(Financiamento.id == financiamento_id).first()
    except Exception as e:
        raise e
    finally:
        session.close()


def atualizar_financiamento(financiamento_id, valor_total=None, taxa_juros=None, status=None, instituicao_financeira=None, observacoes=None):
    """Atualiza um financiamento"""
    session = get_session()
    try:
        financiamento = session.query(Financiamento).filter(Financiamento.id == financiamento_id).first()
        if not financiamento:
            return None
        
        valores_antigos = {
            'valor_total': financiamento.valor_total,
            'taxa_juros': financiamento.taxa_juros,
            'status': financiamento.status
        }
        
        if valor_total is not None:
            financiamento.valor_total = float(valor_total)
        if taxa_juros is not None:
            financiamento.taxa_juros = float(taxa_juros)
        if status is not None:
            financiamento.status = status
        if instituicao_financeira is not None:
            financiamento.instituicao_financeira = instituicao_financeira
        if observacoes is not None:
            financiamento.observacoes = observacoes
        
        session.commit()
        session.refresh(financiamento)
        
        auditoria.registrar_auditoria('UPDATE', 'Financiamentos', financiamento_id, valores_antigos=valores_antigos, valores_novos={
            'valor_total': financiamento.valor_total,
            'taxa_juros': financiamento.taxa_juros,
            'status': financiamento.status
        })
        
        return financiamento
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def deletar_financiamento(financiamento_id):
    """Deleta um financiamento e suas parcelas"""
    session = get_session()
    try:
        financiamento = session.query(Financiamento).filter(Financiamento.id == financiamento_id).first()
        if not financiamento:
            return False
        
        valores_antigos = {
            'item_id': financiamento.item_id,
            'valor_total': financiamento.valor_total
        }
        
        session.delete(financiamento)  # Cascade deleta parcelas automaticamente
        session.commit()
        
        auditoria.registrar_auditoria('DELETE', 'Financiamentos', financiamento_id, valores_antigos=valores_antigos)
        
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_parcelas_financiamento(financiamento_id=None, status=None):
    """Lista parcelas de financiamento com filtros opcionais"""
    session = get_session()
    try:
        query = session.query(ParcelaFinanciamento)
        
        if financiamento_id:
            query = query.filter(ParcelaFinanciamento.financiamento_id == financiamento_id)
        if status:
            query = query.filter(ParcelaFinanciamento.status == status)
        
        parcelas = query.all()
        
        # Recalcula status para garantir consist├¬ncia
        hoje = date.today()
        for parcela in parcelas:
            if parcela.valor_pago >= parcela.valor_original:
                parcela.status = 'Paga'
            elif parcela.data_vencimento < hoje:
                parcela.status = 'Atrasada'
            else:
                parcela.status = 'Pendente'
        
        return parcelas
    except Exception as e:
        raise e
    finally:
        session.close()


def pagar_parcela_financiamento(parcela_id, valor_pago, data_pagamento=None, juros=0.0, multa=0.0, desconto=0.0):
    """Registra pagamento de uma parcela"""
    if data_pagamento is None:
        data_pagamento = date.today()
    
    session = get_session()
    try:
        parcela = session.query(ParcelaFinanciamento).filter(ParcelaFinanciamento.id == parcela_id).first()
        if not parcela:
            return None
        
        valores_antigos = {
            'valor_pago': parcela.valor_pago,
            'data_pagamento': str(parcela.data_pagamento) if parcela.data_pagamento else None
        }
        
        valor_pago_total = float(valor_pago) + float(juros) + float(multa) - float(desconto)
        parcela.valor_pago = valor_pago_total
        parcela.data_pagamento = data_pagamento
        parcela.juros = float(juros)
        parcela.multa = float(multa)
        parcela.desconto = float(desconto)
        
        # Atualiza status
        if valor_pago_total >= parcela.valor_original:
            parcela.status = 'Paga'
        else:
            parcela.status = 'Pendente'
        
        session.commit()
        session.refresh(parcela)
        
        # Verifica se financiamento foi quitado
        parcelas = listar_parcelas_financiamento(financiamento_id=parcela.financiamento_id)
        todas_pagas = all(p.status == 'Paga' for p in parcelas)
        if todas_pagas:
            atualizar_financiamento(parcela.financiamento_id, status='Quitado')
        
        auditoria.registrar_auditoria('UPDATE', 'Parcelas Financiamento', parcela_id, valores_antigos=valores_antigos, valores_novos={
            'valor_pago': valor_pago_total,
            'data_pagamento': str(data_pagamento)
        })
        
        return parcela
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def atualizar_parcela_financiamento(parcela_id, status=None, link_boleto=None, valor_original=None, data_vencimento=None):
    """Atualiza uma parcela de financiamento"""
    session = get_session()
    try:
        parcela = session.query(ParcelaFinanciamento).filter(ParcelaFinanciamento.id == parcela_id).first()
        if not parcela:
            return None
        
        valores_antigos = {
            'status': parcela.status,
            'link_boleto': parcela.link_boleto if hasattr(parcela, 'link_boleto') else None,
            'valor_original': parcela.valor_original,
            'data_vencimento': str(parcela.data_vencimento)
        }
        
        if status is not None:
            parcela.status = status
        if link_boleto is not None:
            parcela.link_boleto = link_boleto
        if valor_original is not None:
            parcela.valor_original = float(valor_original)
        if data_vencimento is not None:
            parcela.data_vencimento = data_vencimento
        
        session.commit()
        session.refresh(parcela)
        
        auditoria.registrar_auditoria('UPDATE', 'Parcelas Financiamento', parcela_id, valores_antigos=valores_antigos, valores_novos={
            'status': parcela.status,
            'link_boleto': parcela.link_boleto if hasattr(parcela, 'link_boleto') else None,
            'valor_original': parcela.valor_original,
            'data_vencimento': str(parcela.data_vencimento)
        })
        
        return parcela
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
