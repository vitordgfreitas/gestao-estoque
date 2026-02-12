-- ============================================================
-- Schema Supabase para GestaoCarro (STAR Locação)
-- Execute este SQL no Supabase: SQL Editor → New query → Cole e Run
-- ============================================================

-- Extensão para UUID (opcional, podemos usar SERIAL para IDs)
-- Os IDs são inteiros (SERIAL) para compatibilidade com o app

-- 1. Categorias de itens (lista de categorias disponíveis)
CREATE TABLE IF NOT EXISTS categorias_itens (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL,
    data_criacao DATE DEFAULT CURRENT_DATE
);

-- 2. Itens (estoque)
CREATE TABLE IF NOT EXISTS itens (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    quantidade_total INTEGER NOT NULL DEFAULT 1,
    categoria TEXT NOT NULL DEFAULT 'Estrutura de Evento',
    descricao TEXT,
    cidade TEXT NOT NULL,
    uf VARCHAR(2) NOT NULL,
    endereco TEXT,
    dados_categoria JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_itens_categoria ON itens(categoria);
CREATE INDEX IF NOT EXISTS idx_itens_cidade_uf ON itens(cidade, uf);

-- 3. Carros (dados específicos quando categoria = 'Carros')
CREATE TABLE IF NOT EXISTS carros (
    id SERIAL PRIMARY KEY,
    item_id INTEGER UNIQUE NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
    placa VARCHAR(10) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_carros_placa ON carros(placa);

-- 4. Compromissos (aluguéis/reservas)
CREATE TABLE IF NOT EXISTS compromissos (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
    quantidade INTEGER NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    descricao TEXT,
    cidade TEXT NOT NULL,
    uf VARCHAR(2) NOT NULL,
    endereco TEXT,
    contratante TEXT
);

CREATE INDEX IF NOT EXISTS idx_compromissos_item ON compromissos(item_id);
CREATE INDEX IF NOT EXISTS idx_compromissos_datas ON compromissos(data_inicio, data_fim);

-- 5. Contas a receber
CREATE TABLE IF NOT EXISTS contas_receber (
    id SERIAL PRIMARY KEY,
    compromisso_id INTEGER NOT NULL REFERENCES compromissos(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    valor DECIMAL(12,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pendente',
    forma_pagamento VARCHAR(50),
    observacoes TEXT
);

-- 6. Contas a pagar
CREATE TABLE IF NOT EXISTS contas_pagar (
    id SERIAL PRIMARY KEY,
    descricao TEXT NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    valor DECIMAL(12,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pendente',
    fornecedor TEXT,
    item_id INTEGER REFERENCES itens(id) ON DELETE SET NULL,
    forma_pagamento VARCHAR(50),
    observacoes TEXT
);

-- 7. Financiamentos (item_id = primeiro item, para compatibilidade)
CREATE TABLE IF NOT EXISTS financiamentos (
    id SERIAL PRIMARY KEY,
    codigo_contrato TEXT DEFAULT '',
    item_id INTEGER REFERENCES itens(id) ON DELETE SET NULL,
    valor_total DECIMAL(12,2) NOT NULL,
    valor_entrada DECIMAL(12,2) NOT NULL DEFAULT 0,
    numero_parcelas INTEGER NOT NULL,
    valor_parcela DECIMAL(12,2) NOT NULL,
    taxa_juros DECIMAL(10,6) NOT NULL DEFAULT 0,
    data_inicio DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    instituicao_financeira TEXT,
    observacoes TEXT
);

-- 8. Relação N:N Financiamento ↔ Itens
CREATE TABLE IF NOT EXISTS financiamentos_itens (
    id SERIAL PRIMARY KEY,
    financiamento_id INTEGER NOT NULL REFERENCES financiamentos(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
    valor_proporcional DECIMAL(12,2) DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fin_itens_unique ON financiamentos_itens(financiamento_id, item_id);

-- 9. Parcelas do financiamento
CREATE TABLE IF NOT EXISTS parcelas_financiamento (
    id SERIAL PRIMARY KEY,
    financiamento_id INTEGER NOT NULL REFERENCES financiamentos(id) ON DELETE CASCADE,
    numero_parcela INTEGER NOT NULL,
    valor_original DECIMAL(12,2) NOT NULL,
    valor_pago DECIMAL(12,2) NOT NULL DEFAULT 0,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pendente',
    link_boleto TEXT,
    link_comprovante TEXT
);

CREATE INDEX IF NOT EXISTS idx_parcelas_fin ON parcelas_financiamento(financiamento_id);

-- 10. Peças instaladas em carros (afeta disponibilidade)
CREATE TABLE IF NOT EXISTS pecas_carros (
    id SERIAL PRIMARY KEY,
    peca_id INTEGER NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
    carro_id INTEGER NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
    quantidade INTEGER NOT NULL DEFAULT 1,
    data_instalacao DATE,
    observacoes TEXT
);

-- Função para criar tabela da categoria ao cadastrar nova categoria (chamada pelo backend)
CREATE OR REPLACE FUNCTION criar_tabela_categoria(nome_tabela text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- nome_tabela deve conter apenas letras minúsculas, números e underscore (validado no backend)
  EXECUTE format(
    'CREATE TABLE IF NOT EXISTS %I (
      id SERIAL PRIMARY KEY,
      item_id INTEGER UNIQUE NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
      dados_categoria JSONB DEFAULT ''{}''
    )',
    nome_tabela
  );
END;
$$;

-- Inserir categorias padrão
INSERT INTO categorias_itens (nome, data_criacao)
VALUES 
    ('Estrutura de Evento', CURRENT_DATE),
    ('Carros', CURRENT_DATE)
ON CONFLICT (nome) DO NOTHING;

-- Habilitar RLS (Row Level Security) - opcional
-- Se quiser que apenas o backend (service_role) acesse, pode deixar RLS desabilitado
-- ou criar políticas que permitam tudo para service_role:
-- ALTER TABLE itens ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Service role full access" ON itens FOR ALL USING (true);
