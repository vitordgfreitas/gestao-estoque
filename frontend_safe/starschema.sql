-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.carros (
  id integer NOT NULL DEFAULT nextval('carros_id_seq'::regclass),
  item_id integer NOT NULL UNIQUE,
  placa character varying NOT NULL,
  marca character varying NOT NULL,
  modelo character varying NOT NULL,
  ano_fabricacao integer NOT NULL,
  chassi character varying,
  renavam character varying,
  Cor text,
  CONSTRAINT carros_pkey PRIMARY KEY (id),
  CONSTRAINT carros_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.categorias_itens (
  id integer NOT NULL DEFAULT nextval('categorias_itens_id_seq'::regclass),
  nome text NOT NULL UNIQUE,
  data_criacao date DEFAULT CURRENT_DATE,
  CONSTRAINT categorias_itens_pkey PRIMARY KEY (id)
);
CREATE TABLE public.compromisso_itens (
  id integer NOT NULL DEFAULT nextval('compromisso_itens_id_seq'::regclass),
  compromisso_id integer,
  item_id integer,
  quantidade integer NOT NULL DEFAULT 1,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT compromisso_itens_pkey PRIMARY KEY (id),
  CONSTRAINT compromisso_itens_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id),
  CONSTRAINT compromisso_itens_compromisso_id_fkey FOREIGN KEY (compromisso_id) REFERENCES public.compromissos(id)
);
CREATE TABLE public.compromissos (
  id integer NOT NULL DEFAULT nextval('compromissos_id_seq'::regclass),
  data_inicio date NOT NULL,
  data_fim date NOT NULL,
  descricao text,
  cidade text NOT NULL,
  uf character varying NOT NULL,
  endereco text,
  contratante text,
  nome_contrato text,
  valor_total_contrato numeric DEFAULT 0,
  CONSTRAINT compromissos_pkey PRIMARY KEY (id)
);
CREATE TABLE public.container (
  id integer NOT NULL DEFAULT nextval('container_id_seq'::regclass),
  item_id integer NOT NULL UNIQUE,
  tara numeric,
  carga_maxima numeric,
  comprimento numeric,
  largura numeric,
  altura numeric,
  capacidade numeric,
  cor character varying,
  modelo character varying,
  CONSTRAINT container_pkey PRIMARY KEY (id),
  CONSTRAINT container_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.contas_pagar (
  id integer NOT NULL DEFAULT nextval('contas_pagar_id_seq'::regclass),
  descricao text NOT NULL,
  categoria character varying NOT NULL,
  valor numeric NOT NULL,
  data_vencimento date NOT NULL,
  data_pagamento date,
  status character varying NOT NULL DEFAULT 'Pendente'::character varying,
  fornecedor text,
  item_id integer,
  forma_pagamento character varying,
  observacoes text,
  CONSTRAINT contas_pagar_pkey PRIMARY KEY (id),
  CONSTRAINT contas_pagar_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.contas_receber (
  id integer NOT NULL DEFAULT nextval('contas_receber_id_seq'::regclass),
  compromisso_id integer NOT NULL,
  descricao text NOT NULL,
  valor numeric NOT NULL,
  data_vencimento date NOT NULL,
  data_pagamento date,
  status character varying NOT NULL DEFAULT 'Pendente'::character varying,
  forma_pagamento character varying,
  observacoes text,
  CONSTRAINT contas_receber_pkey PRIMARY KEY (id),
  CONSTRAINT contas_receber_compromisso_id_fkey FOREIGN KEY (compromisso_id) REFERENCES public.compromissos(id)
);
CREATE TABLE public.estruturas (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  item_id integer NOT NULL UNIQUE,
  CONSTRAINT estruturas_pkey PRIMARY KEY (id),
  CONSTRAINT estruturas_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.financiamentos (
  id integer NOT NULL DEFAULT nextval('financiamentos_id_seq'::regclass),
  codigo_contrato text DEFAULT ''::text,
  item_id integer,
  valor_total numeric NOT NULL,
  valor_entrada numeric NOT NULL DEFAULT 0,
  numero_parcelas integer NOT NULL,
  valor_parcela numeric NOT NULL,
  taxa_juros numeric NOT NULL DEFAULT 0,
  data_inicio date NOT NULL,
  status character varying NOT NULL DEFAULT 'Ativo'::character varying,
  instituicao_financeira text,
  observacoes text,
  CONSTRAINT financiamentos_pkey PRIMARY KEY (id),
  CONSTRAINT financiamentos_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.financiamentos_itens (
  id integer NOT NULL DEFAULT nextval('financiamentos_itens_id_seq'::regclass),
  financiamento_id integer NOT NULL,
  item_id integer NOT NULL,
  valor_proporcional numeric DEFAULT 0,
  CONSTRAINT financiamentos_itens_pkey PRIMARY KEY (id),
  CONSTRAINT financiamentos_itens_financiamento_id_fkey FOREIGN KEY (financiamento_id) REFERENCES public.financiamentos(id),
  CONSTRAINT financiamentos_itens_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.geradores (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  potencia_kva text,
  tipo_combustivel text,
  CONSTRAINT geradores_pkey PRIMARY KEY (id)
);
CREATE TABLE public.itens (
  id integer NOT NULL DEFAULT nextval('itens_id_seq'::regclass),
  nome text NOT NULL,
  quantidade_total integer NOT NULL DEFAULT 1,
  categoria text NOT NULL DEFAULT 'Estrutura de Evento'::text,
  descricao text,
  cidade text NOT NULL,
  uf character varying NOT NULL,
  endereco text,
  dados_categoria jsonb DEFAULT '{}'::jsonb,
  valor_compra numeric DEFAULT 0,
  data_aquisicao date DEFAULT CURRENT_DATE,
  CONSTRAINT itens_pkey PRIMARY KEY (id)
);
CREATE TABLE public.movimentacoes_estoque (
  id integer NOT NULL DEFAULT nextval('movimentacoes_estoque_id_seq'::regclass),
  item_id integer,
  quantidade integer NOT NULL,
  tipo character varying NOT NULL,
  data_movimentacao timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  referencia_id integer,
  descricao text,
  CONSTRAINT movimentacoes_estoque_pkey PRIMARY KEY (id),
  CONSTRAINT movimentacoes_estoque_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.parcelas_financiamento (
  id integer NOT NULL DEFAULT nextval('parcelas_financiamento_id_seq'::regclass),
  financiamento_id integer NOT NULL,
  numero_parcela integer NOT NULL,
  valor_original numeric NOT NULL,
  valor_pago numeric NOT NULL DEFAULT 0,
  data_vencimento date NOT NULL,
  data_pagamento date,
  status character varying NOT NULL DEFAULT 'Pendente'::character varying,
  link_boleto text,
  link_comprovante text,
  CONSTRAINT parcelas_financiamento_pkey PRIMARY KEY (id),
  CONSTRAINT parcelas_financiamento_financiamento_id_fkey FOREIGN KEY (financiamento_id) REFERENCES public.financiamentos(id)
);
CREATE TABLE public.pecas (
  id integer NOT NULL DEFAULT nextval('pecas_id_seq'::regclass),
  item_id integer NOT NULL UNIQUE,
  dados_categoria jsonb DEFAULT '{}'::jsonb,
  marca character varying,
  CONSTRAINT pecas_pkey PRIMARY KEY (id),
  CONSTRAINT pecas_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.itens(id)
);
CREATE TABLE public.pecas_carros (
  id integer NOT NULL DEFAULT nextval('pecas_carros_id_seq'::regclass),
  peca_id integer NOT NULL,
  carro_id integer NOT NULL,
  quantidade integer NOT NULL DEFAULT 1,
  data_instalacao date,
  observacoes text,
  custo_na_data numeric DEFAULT 0,
  CONSTRAINT pecas_carros_pkey PRIMARY KEY (id),
  CONSTRAINT pecas_carros_peca_id_fkey FOREIGN KEY (peca_id) REFERENCES public.itens(id),
  CONSTRAINT pecas_carros_carro_id_fkey FOREIGN KEY (carro_id) REFERENCES public.itens(id)
);