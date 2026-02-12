import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { itensAPI, categoriasAPI } from '../services/api'
import { Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { getCidadesPorUF, ESTADOS } from '../utils/municipios'

const MARCAS_CARROS = [
  'Fiat', 'Volkswagen', 'Chevrolet', 'Ford', 'Toyota', 'Honda', 'Hyundai', 
  'Renault', 'Nissan', 'Peugeot', 'Citroën', 'Jeep', 'Mitsubishi', 'Kia',
  'BMW', 'Mercedes-Benz', 'Audi', 'Volvo', 'Land Rover', 'Jaguar', 'Porsche',
  'Subaru', 'Suzuki', 'Chery', 'JAC', 'Troller', 'RAM', 'Dodge', 'Chrysler',
  'Mini', 'Smart', 'BYD', 'GWM', 'Caoa Chery', 'Outra'
]

export default function Itens() {
  const [categorias, setCategorias] = useState([])
  const [camposCategoria, setCamposCategoria] = useState([])
  const [loadingCategorias, setLoadingCategorias] = useState(true)
  const [cidadesDisponiveis, setCidadesDisponiveis] = useState([])
  const [mostrarModalNovaCategoria, setMostrarModalNovaCategoria] = useState(false)
  const [novaCategoria, setNovaCategoria] = useState('')
  const [criandoCategoria, setCriandoCategoria] = useState(false)
  const [formData, setFormData] = useState({
    nome: '',
    quantidade_total: 1,
    categoria: '',
    descricao: '',
    cidade: '',
    uf: 'DF',
    endereco: '',
    valor_compra: '0,00', // Iniciado como string para a máscara
    data_aquisicao: new Date().toISOString().split('T')[0],
  })
  const [camposDinamicos, setCamposDinamicos] = useState({})
  const [loading, setLoading] = useState(false)

  // --- HELPERS ---

  const formatarMoeda = (valor) => {
    const apenasNumeros = String(valor).replace(/\D/g, "");
    const valorDecimal = (Number(apenasNumeros) / 100).toFixed(2);
    return new Intl.NumberFormat('pt-BR', {
      style: 'decimal',
      minimumFractionDigits: 2,
    }).format(valorDecimal);
  };

  const converterMoedaParaFloat = (valorStr) => {
    if (!valorStr) return 0;
    return parseFloat(String(valorStr).replace(/\./g, '').replace(',', '.')) || 0;
  };

  // --- EFEITOS ---

  useEffect(() => {
    loadCategorias()
  }, [])

  useEffect(() => {
    if (formData.categoria) {
      loadCamposCategoria(formData.categoria)
    } else {
      setCamposCategoria([])
      setCamposDinamicos({})
    }
  }, [formData.categoria])

  useEffect(() => {
    if (formData.uf) {
      setCidadesDisponiveis(getCidadesPorUF(formData.uf))
    } else {
      setCidadesDisponiveis([])
    }
  }, [formData.uf])

  // --- CARREGAMENTO DE DADOS ---

  const loadCategorias = async () => {
    try {
      const response = await categoriasAPI.listar()
      const cats = response.data
      setCategorias(cats)
      if (cats.length > 0 && !formData.categoria) {
        setFormData(prev => ({ ...prev, categoria: cats[0] }))
      }
    } catch (error) {
      console.error('Erro ao carregar categorias:', error)
      toast.error('Erro ao carregar categorias')
      setCategorias([])
    } finally {
      setLoadingCategorias(false)
    }
  }

  const loadCamposCategoria = async (categoria) => {
    try {
      const response = await categoriasAPI.obterCampos(categoria)
      const campos = response.data || []
      setCamposCategoria(campos)
      const novosCampos = {}
      campos.forEach(campo => { novosCampos[campo] = '' })
      setCamposDinamicos(novosCampos)
    } catch (error) {
      console.error('Erro ao carregar campos da categoria:', error)
      setCamposCategoria([])
    }
  }

  // --- HANDLERS ---

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'valor_compra') {
      setFormData(prev => ({ ...prev, [name]: formatarMoeda(value) }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }

    if (name === 'categoria' && value === 'Carros') {
      setFormData(prev => ({ ...prev, quantidade_total: 1 }));
    }
  };

  const handleCampoDinamicoChange = (campo, value) => {
    setCamposDinamicos(prev => {
      const updated = { ...prev, [campo]: value };
      
      // Auto-geração de nome para Carros
      if (formData.categoria === 'Carros') {
        const marca = campo === 'Marca' ? value : updated['Marca'] || '';
        const modelo = campo === 'Modelo' ? value : updated['Modelo'] || '';
        const placa = campo === 'Placa' ? value : updated['Placa'] || '';
        
        if (marca && modelo) {
          const novoNome = `${marca} ${modelo}${placa ? ' - ' + placa : ''}`.trim();
          setFormData(prevForm => ({ ...prevForm, nome: novoNome }));
        }
      }
      return updated;
    });
  };

  const handleCriarCategoria = async () => {
    if (!novaCategoria.trim()) return toast.error('Digite o nome da categoria');
    if (categorias.includes(novaCategoria.trim())) return toast.error('Categoria já existe');

    setCriandoCategoria(true);
    try {
      await categoriasAPI.criar(novaCategoria.trim());
      toast.success(`Categoria "${novaCategoria}" criada!`);
      await loadCategorias();
      setFormData(prev => ({ ...prev, categoria: novaCategoria.trim() }));
      setMostrarModalNovaCategoria(false);
      setNovaCategoria('');
    } catch (error) {
      toast.error('Erro ao criar categoria');
    } finally {
      setCriandoCategoria(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (!formData.nome.trim() || !formData.cidade.trim()) {
        throw new Error('Preencha os campos obrigatórios');
      }

      // Prepara o payload limpando a moeda e formatando campos
      const payload = {
        ...formData,
        quantidade_total: parseInt(formData.quantidade_total),
        valor_compra: converterMoedaParaFloat(formData.valor_compra),
        campos_categoria: camposDinamicos
      };

      await itensAPI.criar(payload);
      toast.success('Item registrado com sucesso!');
      
      // Limpa o formulário mantendo a categoria
      setFormData({
        ...formData,
        nome: '',
        quantidade_total: formData.categoria === 'Carros' ? 1 : 1,
        descricao: '',
        valor_compra: '0,00',
        endereco: ''
      });
      setCamposDinamicos({});
    } catch (error) {
      toast.error(error.message || 'Erro ao registrar item');
    } finally {
      setLoading(false);
    }
  };

  const inferirTipoCampo = (campoNome) => {
    const c = campoNome.toLowerCase();
    if (c.includes('ano') || c.includes('quantidade') || c.includes('qtd')) return 'number';
    if (c.includes('data') || c.includes('vencimento')) return 'date';
    return 'text';
  };

  const renderCampoDinamico = (campo, opcional = false) => {
    const tipo = inferirTipoCampo(campo);
    const valor = camposDinamicos[campo] || '';
    const req = !opcional;

    if (formData.categoria === 'Carros' && campo === 'Marca') {
      return (
        <select value={valor} onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)} required={req} className="input">
          <option value="">Selecione a marca</option>
          {MARCAS_CARROS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      )
    }

    return (
      <input
        type={tipo}
        value={valor}
        onChange={(e) => handleCampoDinamicoChange(campo, tipo === 'text' && campo === 'Placa' ? e.target.value.toUpperCase() : e.target.value)}
        required={req}
        className="input"
        placeholder={`Digite ${campo.toLowerCase()}...`}
      />
    );
  };

  if (loadingCategorias) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  const quantidadeFixa = formData.categoria === 'Carros' || camposCategoria.some(c => ['Placa', 'Serial', 'Código'].includes(c));

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Registrar Novo Item</h1>
        <p className="text-dark-400">Gestão de Ativos e Centro de Custo</p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="card space-y-6"
      >
        {/* Informações Básicas */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
            <div className="w-1 h-6 bg-primary-500 rounded-full"></div>
            Informações do Item
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Categoria *</label>
              <div className="flex gap-2">
                <select name="categoria" value={formData.categoria} onChange={handleChange} required className="input flex-1">
                  <option value="">Selecione uma categoria</option>
                  {categorias.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                </select>
                <button type="button" onClick={() => setMostrarModalNovaCategoria(true)} className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center gap-2">
                  <Plus size={20} />
                </button>
              </div>
            </div>

            <div>
              <label className="label">Quantidade Total *</label>
              <input
                type="number"
                name="quantidade_total"
                value={formData.quantidade_total}
                onChange={handleChange}
                required
                min="1"
                disabled={quantidadeFixa}
                className={`input ${quantidadeFixa ? 'opacity-50 cursor-not-allowed' : ''}`}
              />
            </div>
          </div>

          {/* Nome do item (Dinâmico para Carros) */}
          <div>
            <label className="label">Nome do Item *</label>
            <input
              type="text"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              required
              className="input"
              placeholder="Ex: Alambrado, Mesa, Cadeira..."
            />
          </div>

          {/* Campos Dinâmicos da Categoria */}
          {camposCategoria.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-dark-700/30 rounded-xl border border-dark-600">
              {camposCategoria.map(campo => (
                <div key={campo}>
                  <label className="label">{campo}</label>
                  {renderCampoDinamico(campo, ['Chassi', 'Renavam'].includes(campo))}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Centro de Custo */}
        <div className="space-y-4 pt-6 border-t border-dark-700">
          <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
            <div className="w-1 h-6 bg-green-500 rounded-full"></div>
            Investimento e Aquisição
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Valor de Compra Unitário (R$)</label>
              <input
                type="text"
                name="valor_compra"
                value={formData.valor_compra}
                onChange={handleChange}
                className="input"
                placeholder="0,00"
              />
            </div>
            <div>
              <label className="label">Data de Aquisição</label>
              <input
                type="date"
                name="data_aquisicao"
                value={formData.data_aquisicao}
                onChange={handleChange}
                className="input"
              />
            </div>
          </div>
        </div>

        {/* Localização */}
        <div className="space-y-4 pt-6 border-t border-dark-700">
          <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
            <div className="w-1 h-6 bg-blue-500 rounded-full"></div>
            Localização
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">UF *</label>
              <select name="uf" value={formData.uf} onChange={handleChange} required className="input">
                {ESTADOS.map(e => <option key={e.sigla} value={e.sigla}>{e.sigla}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Cidade *</label>
              <select name="cidade" value={formData.cidade} onChange={handleChange} required className="input">
                <option value="">Selecione...</option>
                {cidadesDisponiveis.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-4 text-lg">
          {loading ? 'Processando...' : 'Registrar Ativo no Estoque'}
        </button>
      </motion.form>

      {/* Modal Categoria - Simples */}
      {mostrarModalNovaCategoria && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-dark-800 rounded-xl p-6 max-w-sm w-full border border-dark-600 shadow-2xl">
            <h2 className="text-xl font-bold text-dark-50 mb-4">Nova Categoria</h2>
            <input
              type="text"
              value={novaCategoria}
              onChange={(e) => setNovaCategoria(e.target.value)}
              className="input mb-4"
              placeholder="Ex: Geradores"
              autoFocus
            />
            <div className="flex gap-2">
              <button onClick={() => setMostrarModalNovaCategoria(false)} className="btn btn-secondary flex-1">Cancelar</button>
              <button onClick={handleCriarCategoria} disabled={criandoCategoria} className="btn btn-primary flex-1">
                {criandoCategoria ? 'Criando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}