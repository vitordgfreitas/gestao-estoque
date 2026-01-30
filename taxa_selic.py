"""
Módulo para buscar taxa SELIC/CDI da API do Banco Central
"""
import requests
import os
from datetime import date, datetime, timedelta
import time

# Cache de taxa
_taxa_cache = {
    'selic': None,
    'cdi': None,
    'cache_time': None,
    'cache_ttl': 86400  # 24 horas em segundos
}

def _is_cache_valid():
    """Verifica se o cache ainda é válido"""
    if _taxa_cache['cache_time'] is None:
        return False
    return (time.time() - _taxa_cache['cache_time']) < _taxa_cache['cache_ttl']

def obter_taxa_selic():
    """Obtém taxa SELIC anual da API do Banco Central"""
    global _taxa_cache
    
    # Verifica cache
    if _is_cache_valid() and _taxa_cache['selic'] is not None:
        return _taxa_cache['selic']
    
    try:
        # API do Banco Central - SELIC (código 11)
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            taxa_anual = float(data[0]['valor']) / 100  # Converte de % para decimal
            taxa_mensal = (1 + taxa_anual) ** (1/12) - 1  # Converte anual para mensal
            
            # Atualiza cache
            _taxa_cache['selic'] = taxa_mensal
            _taxa_cache['cache_time'] = time.time()
            
            return taxa_mensal
    except Exception as e:
        print(f"Erro ao buscar taxa SELIC: {e}")
        # Fallback para taxa padrão configurável
        taxa_fallback = float(os.getenv('TAXA_SELIC_FALLBACK', '0.01'))  # 1% ao mês padrão
        return taxa_fallback
    
    # Fallback padrão
    return 0.01  # 1% ao mês

def obter_taxa_cdi():
    """Obtém taxa CDI anual da API do Banco Central"""
    global _taxa_cache
    
    # Verifica cache
    if _is_cache_valid() and _taxa_cache['cdi'] is not None:
        return _taxa_cache['cdi']
    
    try:
        # API do Banco Central - CDI (código 12)
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            taxa_anual = float(data[0]['valor']) / 100  # Converte de % para decimal
            taxa_mensal = (1 + taxa_anual) ** (1/12) - 1  # Converte anual para mensal
            
            # Atualiza cache
            _taxa_cache['cdi'] = taxa_mensal
            _taxa_cache['cache_time'] = time.time()
            
            return taxa_mensal
    except Exception as e:
        print(f"Erro ao buscar taxa CDI: {e}")
        # Fallback para taxa padrão configurável
        taxa_fallback = float(os.getenv('TAXA_CDI_FALLBACK', '0.01'))  # 1% ao mês padrão
        return taxa_fallback
    
    # Fallback padrão
    return 0.01  # 1% ao mês

def calcular_valor_presente(parcelas, taxa_desconto=None, usar_cdi=False):
    """
    Calcula valor presente (NPV) de parcelas futuras
    
    Args:
        parcelas: Lista de parcelas com data_vencimento e valor_original
        taxa_desconto: Taxa de desconto mensal (opcional, usa SELIC/CDI se não fornecido)
        usar_cdi: Se True, usa CDI ao invés de SELIC
    
    Returns:
        Valor presente total
    """
    if taxa_desconto is None:
        if usar_cdi:
            taxa_desconto = obter_taxa_cdi()
        else:
            taxa_desconto = obter_taxa_selic()
    
    hoje = date.today()
    valor_presente = 0.0
    
    for parcela in parcelas:
        if parcela.status == 'Paga':
            continue  # Parcelas pagas não entram no cálculo
        
        # Calcula número de meses até vencimento
        meses_ate_vencimento = (parcela.data_vencimento.year - hoje.year) * 12 + (parcela.data_vencimento.month - hoje.month)
        if meses_ate_vencimento < 0:
            meses_ate_vencimento = 0
        
        # Calcula valor presente da parcela
        valor_parcela = parcela.valor_original + parcela.juros + parcela.multa - parcela.desconto
        if meses_ate_vencimento == 0:
            valor_presente += valor_parcela
        else:
            valor_presente += valor_parcela / ((1 + taxa_desconto) ** meses_ate_vencimento)
    
    return valor_presente
