"""
Módulo de validações robustas para o sistema de gestão de estoque
"""
import re
from datetime import date, datetime
from typing import Optional, Dict, List

# UFs válidas do Brasil
UFS_VALIDAS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]


def validar_uf(uf: str) -> tuple[bool, Optional[str]]:
    """
    Valida se a UF é válida
    
    Args:
        uf: UF a validar
        
    Returns:
        (é_válida, mensagem_erro)
    """
    if not uf:
        return False, "UF é obrigatória"
    
    uf_upper = uf.upper().strip()[:2]
    
    if uf_upper not in UFS_VALIDAS:
        return False, f"UF inválida: {uf}. UFs válidas: {', '.join(UFS_VALIDAS)}"
    
    return True, None


def validar_placa(placa: str) -> tuple[bool, Optional[str]]:
    """
    Valida formato de placa brasileira (antiga ABC-1234 ou nova ABC1D23)
    
    Args:
        placa: Placa a validar
        
    Returns:
        (é_válida, mensagem_erro)
    """
    if not placa:
        return False, "Placa é obrigatória"
    
    placa_limpa = placa.upper().strip().replace('-', '').replace(' ', '')
    
    # Formato antigo: ABC1234 (3 letras + 4 números)
    padrao_antigo = re.compile(r'^[A-Z]{3}[0-9]{4}$')
    # Formato novo: ABC1D23 (3 letras + 1 número + 1 letra + 2 números)
    padrao_novo = re.compile(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$')
    
    if not (padrao_antigo.match(placa_limpa) or padrao_novo.match(placa_limpa)):
        return False, f"Formato de placa inválido: {placa}. Use formato ABC-1234 ou ABC1D23"
    
    return True, None


def validar_quantidade(quantidade: int, permitir_zero: bool = False) -> tuple[bool, Optional[str]]:
    """
    Valida quantidade
    
    Args:
        quantidade: Quantidade a validar
        permitir_zero: Se True, permite quantidade zero
        
    Returns:
        (é_válida, mensagem_erro)
    """
    if quantidade is None:
        return False, "Quantidade é obrigatória"
    
    try:
        qtd_int = int(quantidade)
    except (ValueError, TypeError):
        return False, f"Quantidade deve ser um número inteiro: {quantidade}"
    
    if qtd_int < 0:
        return False, f"Quantidade não pode ser negativa: {qtd_int}"
    
    if not permitir_zero and qtd_int == 0:
        return False, "Quantidade deve ser maior que zero"
    
    return True, None


def validar_datas(data_inicio: date, data_fim: date, permitir_passado: bool = True) -> tuple[bool, Optional[str]]:
    """
    Valida intervalo de datas
    
    Args:
        data_inicio: Data de início
        data_fim: Data de fim
        permitir_passado: Se False, não permite datas no passado
        
    Returns:
        (é_válida, mensagem_erro)
    """
    if not data_inicio:
        return False, "Data de início é obrigatória"
    
    if not data_fim:
        return False, "Data de fim é obrigatória"
    
    # Converte strings para date se necessário
    if isinstance(data_inicio, str):
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        except ValueError:
            return False, f"Formato de data de início inválido: {data_inicio}"
    
    if isinstance(data_fim, str):
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            return False, f"Formato de data de fim inválido: {data_fim}"
    
    hoje = date.today()
    
    if not permitir_passado:
        if data_inicio < hoje:
            return False, f"Data de início não pode ser no passado: {data_inicio}"
    
    if data_fim < data_inicio:
        return False, f"Data de fim ({data_fim}) deve ser posterior ou igual à data de início ({data_inicio})"
    
    return True, None


def validar_ano(ano: int, ano_minimo: int = 1900, ano_maximo: Optional[int] = None) -> tuple[bool, Optional[str]]:
    """
    Valida ano
    
    Args:
        ano: Ano a validar
        ano_minimo: Ano mínimo permitido
        ano_maximo: Ano máximo permitido (None = ano atual + 1)
        
    Returns:
        (é_válida, mensagem_erro)
    """
    if ano is None:
        return False, "Ano é obrigatório"
    
    try:
        ano_int = int(ano)
    except (ValueError, TypeError):
        return False, f"Ano deve ser um número inteiro: {ano}"
    
    if ano_maximo is None:
        ano_maximo = date.today().year + 1
    
    if ano_int < ano_minimo:
        return False, f"Ano muito antigo: {ano_int}. Mínimo: {ano_minimo}"
    
    if ano_int > ano_maximo:
        return False, f"Ano muito futuro: {ano_int}. Máximo: {ano_maximo}"
    
    return True, None


def validar_campos_obrigatorios(dados: Dict, campos_obrigatorios: List[str], contexto: str = "") -> tuple[bool, Optional[str]]:
    """
    Valida se campos obrigatórios estão preenchidos
    
    Args:
        dados: Dicionário com os dados
        campos_obrigatorios: Lista de nomes de campos obrigatórios
        contexto: Contexto para mensagem de erro (ex: "Item", "Compromisso")
        
    Returns:
        (é_válida, mensagem_erro)
    """
    campos_faltando = []
    
    for campo in campos_obrigatorios:
        valor = dados.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            campos_faltando.append(campo)
    
    if campos_faltando:
        contexto_str = f"{contexto}: " if contexto else ""
        return False, f"{contexto_str}Campos obrigatórios não preenchidos: {', '.join(campos_faltando)}"
    
    return True, None


def validar_item_completo(
    nome: str,
    categoria: str,
    cidade: str,
    uf: str,
    quantidade_total: int,
    placa: Optional[str] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    ano: Optional[int] = None,
    campos_categoria: Optional[Dict] = None
) -> tuple[bool, Optional[str]]:
    """
    Valida um item completo antes de criar/atualizar
    
    Args:
        nome: Nome do item
        categoria: Categoria do item
        cidade: Cidade
        uf: UF
        quantidade_total: Quantidade total
        placa: Placa (se categoria='Carros')
        marca: Marca (se categoria='Carros')
        modelo: Modelo (se categoria='Carros')
        ano: Ano (se categoria='Carros')
        campos_categoria: Campos específicos da categoria
        
    Returns:
        (é_válida, mensagem_erro)
    """
    erros = []
    
    # Valida campos básicos obrigatórios
    if not nome or not nome.strip():
        erros.append("Nome é obrigatório")
    
    if not categoria or not categoria.strip():
        erros.append("Categoria é obrigatória")
    
    if not cidade or not cidade.strip():
        erros.append("Cidade é obrigatória")
    
    # Valida UF
    uf_valida, msg_uf = validar_uf(uf)
    if not uf_valida:
        erros.append(msg_uf)
    
    # Valida quantidade
    qtd_valida, msg_qtd = validar_quantidade(quantidade_total, permitir_zero=False)
    if not qtd_valida:
        erros.append(msg_qtd)
    
    # Validações específicas para Carros
    if categoria == 'Carros':
        if not placa or not placa.strip():
            erros.append("Placa é obrigatória para carros")
        else:
            placa_valida, msg_placa = validar_placa(placa)
            if not placa_valida:
                erros.append(msg_placa)
        
        if not marca or not marca.strip():
            erros.append("Marca é obrigatória para carros")
        
        if not modelo or not modelo.strip():
            erros.append("Modelo é obrigatório para carros")
        
        if ano is None:
            erros.append("Ano é obrigatório para carros")
        else:
            ano_valido, msg_ano = validar_ano(ano)
            if not ano_valido:
                erros.append(msg_ano)
    
    if erros:
        return False, "; ".join(erros)
    
    return True, None


def validar_compromisso_completo(
    item_id: int,
    quantidade: int,
    data_inicio: date,
    data_fim: date,
    cidade: str,
    uf: str,
    quantidade_disponivel: int = 0
) -> tuple[bool, Optional[str]]:
    """
    Valida um compromisso completo antes de criar/atualizar
    
    Args:
        item_id: ID do item
        quantidade: Quantidade do compromisso
        data_inicio: Data de início
        data_fim: Data de fim
        cidade: Cidade
        uf: UF
        quantidade_disponivel: Quantidade disponível do item
        
    Returns:
        (é_válida, mensagem_erro)
    """
    erros = []
    
    # Valida quantidade
    qtd_valida, msg_qtd = validar_quantidade(quantidade, permitir_zero=False)
    if not qtd_valida:
        erros.append(msg_qtd)
    
    # Valida disponibilidade
    if quantidade > quantidade_disponivel:
        erros.append(f"Quantidade solicitada ({quantidade}) excede a disponível ({quantidade_disponivel})")
    
    # Valida datas
    datas_validas, msg_datas = validar_datas(data_inicio, data_fim, permitir_passado=True)
    if not datas_validas:
        erros.append(msg_datas)
    
    # Valida cidade
    if not cidade or not cidade.strip():
        erros.append("Cidade é obrigatória")
    
    # Valida UF
    uf_valida, msg_uf = validar_uf(uf)
    if not uf_valida:
        erros.append(msg_uf)
    
    if erros:
        return False, "; ".join(erros)
    
    return True, None
