-- ============================================================
-- Migração: categoria "Pecas" e tabela pecas (no Supabase não se usa "Peças de Carro")
-- Execute no Supabase: SQL Editor → New query → Cole e Run
-- ============================================================

-- Inserir categoria Pecas (se ainda não existir)
INSERT INTO categorias_itens (nome, data_criacao)
VALUES ('Pecas', CURRENT_DATE)
ON CONFLICT (nome) DO NOTHING;

-- Criar tabela pecas (itens da categoria Pecas)
SELECT criar_tabela_categoria('pecas');
