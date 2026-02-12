-- ============================================================
-- Migração: função para criar tabela ao cadastrar nova categoria
-- Execute no Supabase: SQL Editor → New query → Cole e Run
-- (Quem já rodou supabase_schema.sql após a atualização não precisa rodar isto)
-- ============================================================

CREATE OR REPLACE FUNCTION criar_tabela_categoria(nome_tabela text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
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
