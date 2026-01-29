from models import get_session, Item, Compromisso, Carro
from datetime import date
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
import validacoes
import auditoria
import auditoria

def criar_item(nome, quantidade_total, categoria='Estrutura de Evento', descricao=None, cidade=None, uf=None, endereco=None, placa=None, marca=None, modelo=None, ano=None):
    """Cria um novo item no estoque
    
    Args:
        nome: Nome do item
        quantidade_total: Quantidade total disponível
        categoria: Categoria do item ('Estrutura de Evento' ou 'Carros')
        descricao: Descrição opcional do item
        cidade: Cidade onde o item está localizado (obrigatório)
        uf: UF onde o item está localizado (obrigatório)
        endereco: Endereço opcional do item
        placa: Placa do carro (obrigatório se categoria='Carros')
        marca: Marca do carro (obrigatório se categoria='Carros')
        modelo: Modelo do carro (obrigatório se categoria='Carros')
        ano: Ano do carro (obrigatório se categoria='Carros')
    """
    session = get_session()
    try:
        # Validações robustas
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
        
        # Validação de duplicatas
        # Verifica nome + categoria único
        item_existente = session.query(Item).filter(
            and_(
                Item.nome == nome,
                Item.categoria == categoria
            )
        ).first()
        
        if item_existente:
            raise ValueError(f"Item '{nome}' já existe na categoria '{categoria}'")
        
        # Validação de placa única para carros
        if categoria == 'Carros' and placa:
            carro_existente = session.query(Carro).filter(Carro.placa == placa.upper().strip()).first()
            if carro_existente:
                raise ValueError(f"Placa {placa} já cadastrada")
        
        item = Item(
            nome=nome, 
            quantidade_total=quantidade_total,
            categoria=categoria,
            descricao=descricao,
            cidade=cidade,
            uf=uf.upper()[:2],  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
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
        # Desanexa todos os objetos da sessão
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
        quantidade_total: Quantidade total disponível
        categoria: Categoria do item ('Estrutura de Evento' ou 'Carros')
        descricao: Descrição opcional do item
        cidade: Cidade onde o item está localizado (obrigatório)
        uf: UF onde o item está localizado (obrigatório)
        endereco: Endereço opcional do item
        placa: Placa do carro (obrigatório se categoria='Carros')
        marca: Marca do carro (obrigatório se categoria='Carros')
        modelo: Modelo do carro (obrigatório se categoria='Carros')
        ano: Ano do carro (obrigatório se categoria='Carros')
    """
    session = get_session()
    try:
        item = session.query(Item).options(joinedload(Item.carro)).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Item com ID {item_id} não encontrado")
        
        # Usa valores atuais se não fornecidos
        categoria_final = categoria if categoria is not None else (item.categoria or '')
        cidade_final = cidade if cidade else (item.cidade or '')
        uf_final = uf if uf else (item.uf or '')
        
        # Validações robustas
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
        
        # Validação de duplicatas (excluindo o item atual)
        item_existente = session.query(Item).filter(
            and_(
                Item.nome == nome,
                Item.categoria == categoria_final,
                Item.id != item_id
            )
        ).first()
        
        if item_existente:
            raise ValueError(f"Item '{nome}' já existe na categoria '{categoria_final}'")
        
        # Validação de placa única para carros (excluindo o item atual)
        if categoria_final == 'Carros' and placa:
            carro_existente = session.query(Carro).join(Item).filter(
                and_(
                    Carro.placa == placa.upper().strip(),
                    Carro.item_id != item_id
                )
            ).first()
            if carro_existente:
                raise ValueError(f"Placa {placa} já cadastrada")
        
        # Se categoria mudou ou foi especificada
        if categoria:
            item.categoria = categoria
            
            # Se mudou para Carros, cria registro de carro se não existir
            if categoria == 'Carros':
                if not placa or not marca or not modelo or not ano:
                    raise ValueError("Para carros, placa, marca, modelo e ano são obrigatórios")
                
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
        item.uf = uf_final.upper()[:2]  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
        item.endereco = endereco
        
        # Se já é carro e não mudou categoria, atualiza dados do carro
        if item.categoria == 'Carros' and item.carro and placa and marca and modelo and ano:
            item.carro.placa = placa.upper().strip()
            item.carro.marca = marca.strip()
            item.carro.modelo = modelo.strip()
            item.carro.ano = int(ano)
        
        # Prepara valores antigos para auditoria (antes do commit, mas após atualizar campos)
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
        data_inicio: Data de início do aluguel
        data_fim: Data de fim do aluguel
        descricao: Descrição opcional do compromisso
        cidade: Cidade do compromisso (obrigatório)
        uf: UF do compromisso (obrigatório)
        endereco: Endereço opcional do compromisso
        contratante: Nome do contratante (opcional)
    """
    session = get_session()
    try:
        if not cidade or not uf:
            raise ValueError("Cidade e UF são obrigatórios")
        
        compromisso = Compromisso(
            item_id=item_id,
            quantidade=quantidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            descricao=descricao,
            cidade=cidade,
            uf=uf.upper()[:2],  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
            endereco=endereco,
            contratante=contratante
        )
        session.add(compromisso)
        session.commit()
        session.refresh(compromisso)
        # Carrega o relacionamento com Item antes de desanexar
        compromisso.item  # Força o carregamento do relacionamento
        # Desanexa o objeto da sessão para poder ser usado depois que a sessão fechar
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
        # Desanexa todos os objetos da sessão
        for compromisso in compromissos:
            session.expunge(compromisso)
            # Também desanexa o item relacionado
            if compromisso.item:
                session.expunge(compromisso.item)
        return compromissos
    finally:
        session.close()


def verificar_disponibilidade(item_id, data_consulta, filtro_localizacao=None):
    """Verifica a disponibilidade de um item em uma data específica
    
    Args:
        item_id: ID do item
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localização
    """
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None
        
        # Busca compromissos que estão ativos na data de consulta
        compromissos_ativos_query = session.query(Compromisso).filter(
            and_(
                Compromisso.item_id == item_id,
                Compromisso.data_inicio <= data_consulta,
                Compromisso.data_fim >= data_consulta
            )
        )
        
        # Se há filtro de localização, aplica filtro adicional (formato: "Cidade - UF")
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
        
        # Se há filtro de localização e o item não está nessa localização,
        # considera que não há itens disponíveis naquela localização
        if filtro_localizacao:
            cidade_uf = filtro_localizacao.split(" - ")
            if len(cidade_uf) == 2:
                cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                item_na_localizacao = (item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                if not item_na_localizacao:
                    # Item não está na localização, então disponível = 0 (ou negativo se houver compromissos)
                    quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        else:
            quantidade_disponivel = item.quantidade_total - quantidade_comprometida
        
        # Desanexa objetos da sessão antes de retornar
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
    """Verifica se há disponibilidade suficiente em todo o período para um novo compromisso"""
    from datetime import timedelta
    
    session = get_session()
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None
        
        # Busca compromissos que se sobrepõem com o período solicitado
        # Dois períodos se sobrepõem se: inicio1 <= fim2 AND inicio2 <= fim1
        compromissos_sobrepostos = session.query(Compromisso).filter(
            and_(
                Compromisso.item_id == item_id,
                Compromisso.data_inicio <= data_fim,
                Compromisso.data_fim >= data_inicio
            )
        ).all()
        
        # Exclui o próprio compromisso se estiver editando
        if excluir_compromisso_id:
            compromissos_sobrepostos = [c for c in compromissos_sobrepostos if c.id != excluir_compromisso_id]
        
        # Encontra o dia com maior comprometimento no período
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
        
        # Desanexa objeto da sessão antes de retornar
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
    """Verifica a disponibilidade de todos os itens em uma data específica
    
    Args:
        data_consulta: Data para verificar disponibilidade
        filtro_localizacao: Se fornecido, considera apenas compromissos com esta localização
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
            
            # Se há filtro de localização, aplica filtro adicional (formato: "Cidade - UF")
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
            
            # Se há filtro de localização e o item não está nessa localização,
            # considera que não há itens disponíveis naquela localização
            if filtro_localizacao:
                cidade_uf = filtro_localizacao.split(" - ")
                if len(cidade_uf) == 2:
                    cidade_filtro, uf_filtro = cidade_uf[0], cidade_uf[1]
                    item_na_localizacao = (item.cidade == cidade_filtro and item.uf == uf_filtro.upper())
                    if not item_na_localizacao:
                        # Item não está na localização, então disponível = 0 (ou negativo se houver compromissos)
                        quantidade_disponivel = max(0, -quantidade_comprometida) if quantidade_comprometida > 0 else 0
                    else:
                        quantidade_disponivel = item.quantidade_total - quantidade_comprometida
                else:
                    quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            else:
                quantidade_disponivel = item.quantidade_total - quantidade_comprometida
            
            # Desanexa objeto da sessão
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
            raise ValueError(f"Item com ID {item_id} não encontrado")
        
        # Verifica se há compromissos ativos ou futuros
        hoje = date.today()
        compromissos_futuros = [
            c for c in item.compromissos 
            if isinstance(c.data_fim, date) and c.data_fim >= hoje
        ]
        
            if compromissos_futuros:
                raise ValueError(
                    f"Não é possível deletar o item. Existem {len(compromissos_futuros)} compromisso(s) ativo(s) ou futuro(s). "
                    f"Delete os compromissos primeiro ou aguarde sua conclusão."
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
        data_inicio: Data de início do aluguel
        data_fim: Data de fim do aluguel
        descricao: Descrição opcional do compromisso
        cidade: Cidade do compromisso (obrigatório)
        uf: UF do compromisso (obrigatório)
        endereco: Endereço opcional do compromisso
        contratante: Nome do contratante (opcional)
    """
    session = get_session()
    try:
        compromisso = session.query(Compromisso).filter(Compromisso.id == compromisso_id).first()
        if not compromisso:
            raise ValueError(f"Compromisso com ID {compromisso_id} não encontrado")
        
        # Verifica se o item existe
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Item com ID {item_id} não encontrado")
        
        # Verifica disponibilidade (excluindo o compromisso atual)
        disponibilidade = verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=compromisso_id)
        if not disponibilidade:
            raise ValueError(f"Erro ao verificar disponibilidade do item {item_id}")
        
        quantidade_disponivel = disponibilidade.get('disponivel_minimo', 0)
        
        # Validações robustas
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
            compromisso.uf = uf.upper()[:2]  # Garante que UF tenha no máximo 2 caracteres e seja maiúscula
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
            compromisso.item  # Força o carregamento do relacionamento
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
