-- ============================================================
-- Migração: tabela container + colunas chassi e renavam em carros
-- Execute no Supabase: SQL Editor → New query → Cole e Run
-- ============================================================

-- 1. Adicionar chassi e renavam na tabela carros
ALTER TABLE carros
ADD COLUMN IF NOT EXISTS chassi VARCHAR(50),
ADD COLUMN IF NOT EXISTS renavam VARCHAR(20);

COMMENT ON COLUMN carros.chassi IS 'Número do chassi do veículo';
COMMENT ON COLUMN carros.renavam IS 'Registro Nacional de Veículos Automotores';

-- 2. Criar tabela container (dados específicos quando categoria = Container ou similar)
CREATE TABLE IF NOT EXISTS container (
    id SERIAL PRIMARY KEY,
    item_id INTEGER UNIQUE NOT NULL REFERENCES itens(id) ON DELETE CASCADE,
    tara DECIMAL(12,2),
    carga_maxima DECIMAL(12,2),
    comprimento DECIMAL(10,2),
    largura DECIMAL(10,2),
    altura DECIMAL(10,2),
    capacidade DECIMAL(12,2),
    cor VARCHAR(50),
    modelo VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_container_item ON container(item_id);

COMMENT ON TABLE container IS 'Containers vinculados a itens (item_id)';
COMMENT ON COLUMN container.tara IS 'Peso vazio (kg)';
COMMENT ON COLUMN container.carga_maxima IS 'Carga máxima (kg)';
COMMENT ON COLUMN container.comprimento IS 'Comprimento (m ou cm, conforme uso)';
COMMENT ON COLUMN container.largura IS 'Largura (m ou cm)';
COMMENT ON COLUMN container.altura IS 'Altura (m ou cm)';
COMMENT ON COLUMN container.capacidade IS 'Capacidade (m³ ou conforme uso)';
