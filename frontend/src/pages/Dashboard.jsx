import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { statsAPI, compromissosAPI, infoAPI, itensAPI } from '../services/api'
import { 
  TrendingUp, 
  Package, 
  Calendar, 
  AlertCircle, 
  ExternalLink,
  Database,
  CheckCircle2,
  Clock,
  XCircle,
  Activity,
  DollarSign,
  Users,
  MapPin,
  BarChart3,
  Filter,
  X
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import toast from 'react-hot-toast'

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316']

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [info, setInfo] = useState(null)
  const [compromissos, setCompromissos] = useState([])
  const [itens, setItens] = useState([])
  const [compromissosAtivos, setCompromissosAtivos] = useState([])
  const [compromissosProximos, setCompromissosProximos] = useState([])
  const [ocupacaoData, setOcupacaoData] = useState([])
  const [categoriasData, setCategoriasData] = useState([])
  const [localizacoesData, setLocalizacoesData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtroDataInicio, setFiltroDataInicio] = useState('')
  const [filtroDataFim, setFiltroDataFim] = useState('')
  const [mostrarFiltros, setMostrarFiltros] = useState(false)

  useEffect(() => {
    loadData()
  }, [filtroDataInicio, filtroDataFim])

  const loadData = async () => {
    try {
      const [statsRes, compRes, infoRes, itensRes] = await Promise.all([
        statsAPI.obter(),
        compromissosAPI.listar(),
        infoAPI.obter(),
        itensAPI.listar()
      ])
      
      setStats(statsRes.data)
      setInfo(infoRes.data)
      setCompromissos(compRes.data)
      setItens(itensRes.data)
      
      const hoje = new Date()
      hoje.setHours(0, 0, 0, 0)
      
      // Aplica filtros de data se existirem
      let compromissosFiltrados = compRes.data
      if (filtroDataInicio || filtroDataFim) {
        compromissosFiltrados = compRes.data.filter(comp => {
          const dataInicio = new Date(comp.data_inicio)
          dataInicio.setHours(0, 0, 0, 0)
          const dataFim = new Date(comp.data_fim)
          dataFim.setHours(23, 59, 59, 999)
          
          if (filtroDataInicio && filtroDataFim) {
            const inicioFiltro = new Date(filtroDataInicio)
            inicioFiltro.setHours(0, 0, 0, 0)
            const fimFiltro = new Date(filtroDataFim)
            fimFiltro.setHours(23, 59, 59, 999)
            // Compromisso está dentro do período se sobrepõe ao filtro
            return (dataInicio <= fimFiltro && dataFim >= inicioFiltro)
          } else if (filtroDataInicio) {
            const inicioFiltro = new Date(filtroDataInicio)
            inicioFiltro.setHours(0, 0, 0, 0)
            return dataFim >= inicioFiltro
          } else if (filtroDataFim) {
            const fimFiltro = new Date(filtroDataFim)
            fimFiltro.setHours(23, 59, 59, 999)
            return dataInicio <= fimFiltro
          }
          return true
        })
      }
      
      // Compromissos ativos (data_inicio <= hoje <= data_fim)
      const ativos = compromissosFiltrados.filter(comp => {
        const inicio = new Date(comp.data_inicio)
        inicio.setHours(0, 0, 0, 0)
        const fim = new Date(comp.data_fim)
        fim.setHours(23, 59, 59, 999)
        return inicio <= hoje && hoje <= fim
      })
      setCompromissosAtivos(ativos)
      
      // Compromissos próximos (início nos próximos 7 dias)
      const proximos7Dias = new Date(hoje)
      proximos7Dias.setDate(hoje.getDate() + 7)
      
      const proximos = compromissosFiltrados
        .filter(comp => {
          const dataInicio = new Date(comp.data_inicio)
          dataInicio.setHours(0, 0, 0, 0)
          return dataInicio >= hoje && dataInicio <= proximos7Dias
        })
        .sort((a, b) => new Date(a.data_inicio) - new Date(b.data_inicio))
        .slice(0, 10)
      
      setCompromissosProximos(proximos)
      
      // Gráfico de ocupação (últimos 30 dias ou período filtrado)
      const ocupacao = []
      let dataInicioGrafico, dataFimGrafico
      
      if (filtroDataInicio && filtroDataFim) {
        // Usa período filtrado
        dataInicioGrafico = new Date(filtroDataInicio)
        dataFimGrafico = new Date(filtroDataFim)
      } else {
        // Últimos 30 dias
        dataFimGrafico = new Date(hoje)
        dataInicioGrafico = new Date(hoje)
        dataInicioGrafico.setDate(dataFimGrafico.getDate() - 29) // 30 dias incluindo hoje
      }
      
      dataInicioGrafico.setHours(0, 0, 0, 0)
      dataFimGrafico.setHours(23, 59, 59, 999)
      
      // Calcula dias entre início e fim
      const diasDiff = Math.ceil((dataFimGrafico - dataInicioGrafico) / (1000 * 60 * 60 * 24)) + 1
      const diasParaMostrar = Math.min(diasDiff, 90) // Limita a 90 dias para não sobrecarregar
      
      // Loop crescente (de 0 até diasParaMostrar - 1) para ordem cronológica correta
      for (let i = 0; i < diasParaMostrar; i++) {
        const data = new Date(dataInicioGrafico)
        data.setDate(dataInicioGrafico.getDate() + i)
        data.setHours(0, 0, 0, 0)
        
        // Filtra compromissos que estão ativos neste dia específico
        const compromissosNoDia = compromissosFiltrados.filter(comp => {
          const inicio = new Date(comp.data_inicio)
          inicio.setHours(0, 0, 0, 0)
          const fim = new Date(comp.data_fim)
          fim.setHours(23, 59, 59, 999)
          // Compromisso está ativo se a data está entre início e fim
          return inicio <= data && data <= fim
        })
        
        const quantidadeComprometida = compromissosNoDia.reduce((sum, c) => sum + (c.quantidade || 0), 0)
        const totalQuantidade = itensRes.data.reduce((sum, item) => sum + (item.quantidade_total || 0), 0)
        const taxaOcupacao = totalQuantidade > 0 ? (quantidadeComprometida / totalQuantidade * 100) : 0
        
        ocupacao.push({
          date: data.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }),
          ocupacao: Math.round(taxaOcupacao * 10) / 10,
          compromissos: compromissosNoDia.length
        })
      }
      setOcupacaoData(ocupacao)
      
      // Dados de categorias
      if (statsRes.data.categorias) {
        const cats = Object.entries(statsRes.data.categorias)
          .map(([nome, dados]) => ({
            name: nome,
            total: dados.total,
            quantidade: dados.quantidade
          }))
          .sort((a, b) => b.quantidade - a.quantidade)
        setCategoriasData(cats)
      }
      
      // Distribuição por localização
      const locs = {}
      compromissosFiltrados.forEach(comp => {
        if (comp.cidade && comp.uf) {
          const key = `${comp.cidade} - ${comp.uf}`
          if (!locs[key]) {
            locs[key] = 0
          }
          locs[key]++
        }
      })
      
      const locsArray = Object.entries(locs)
        .map(([nome, total]) => ({ name: nome, value: total }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5)
      
      setLocalizacoesData(locsArray)
      
    } catch (error) {
      toast.error('Erro ao carregar dados do dashboard')
      console.error('Erro ao carregar dados:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 mb-2">Dashboard Executivo</h1>
          <p className="text-dark-400">Visão geral completa do seu negócio</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className="flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-lg transition-colors"
          >
            <Filter size={18} />
            <span>Filtros</span>
          </button>
          {info?.spreadsheet_url && (
            <a
              href={info.spreadsheet_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <ExternalLink size={18} />
              <span>Abrir Google Sheets</span>
            </a>
          )}
        </div>
      </div>

      {/* Filtros de Data */}
      {mostrarFiltros && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark-50">Filtros de Período</h3>
            <button
              onClick={() => {
                setFiltroDataInicio('')
                setFiltroDataFim('')
              }}
              className="text-sm text-dark-400 hover:text-dark-200 flex items-center gap-1"
            >
              <X size={16} />
              Limpar
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-dark-400 mb-2">Data Início</label>
              <input
                type="date"
                value={filtroDataInicio}
                onChange={(e) => setFiltroDataInicio(e.target.value)}
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-400 mb-2">Data Fim</label>
              <input
                type="date"
                value={filtroDataFim}
                onChange={(e) => setFiltroDataFim(e.target.value)}
                className="input w-full"
              />
            </div>
            <div className="flex items-end">
              {(filtroDataInicio || filtroDataFim) && (
                <div className="text-sm text-dark-400">
                  {filtroDataInicio && filtroDataFim ? (
                    <span>Período: {new Date(filtroDataInicio).toLocaleDateString('pt-BR')} até {new Date(filtroDataFim).toLocaleDateString('pt-BR')}</span>
                  ) : filtroDataInicio ? (
                    <span>A partir de: {new Date(filtroDataInicio).toLocaleDateString('pt-BR')}</span>
                  ) : (
                    <span>Até: {new Date(filtroDataFim).toLocaleDateString('pt-BR')}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Status do Banco */}
      {info && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-gradient-to-r from-primary-600/20 to-primary-600/5 border-primary-600/30"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-600/20 rounded-lg">
                <Database className="text-primary-400" size={20} />
              </div>
              <div>
                <p className="text-sm text-dark-400">Banco de Dados</p>
                <p className="font-semibold text-dark-50">{info.database}</p>
              </div>
            </div>
            {info.use_google_sheets && info.spreadsheet_url ? (
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle2 size={18} />
                <span className="text-sm font-medium">Conectado</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-dark-400">
                <Database size={18} />
                <span className="text-sm">SQLite Local</span>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Package className="text-primary-500" size={24} />}
          title="Total de Itens"
          value={stats?.total_itens || 0}
          subtitle={`${stats?.total_quantidade_itens || 0} unidades no estoque`}
          color="primary"
        />
        <StatCard
          icon={<Activity className="text-green-500" size={24} />}
          title="Compromissos Ativos"
          value={compromissosAtivos.length}
          subtitle={`${compromissosAtivos.reduce((sum, c) => sum + (c.quantidade || 0), 0)} unidades em uso`}
          color="green"
        />
        <StatCard
          icon={<TrendingUp className="text-yellow-500" size={24} />}
          title="Taxa de Ocupação"
          value={`${stats?.taxa_ocupacao || 0}%`}
          subtitle={`${stats?.quantidade_disponivel || 0} unidades disponíveis`}
          color="yellow"
          progress={stats?.taxa_ocupacao || 0}
        />
        <StatCard
          icon={<Clock className="text-blue-500" size={24} />}
          title="Próximos 7 Dias"
          value={compromissosProximos.length}
          subtitle={`${stats?.total_compromissos || 0} compromissos totais`}
          color="blue"
        />
      </div>

      {/* Gráfico Principal */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-dark-50">
            Taxa de Ocupação ao Longo do Tempo
            {filtroDataInicio && filtroDataFim && (
              <span className="text-sm font-normal text-dark-400 ml-2">
                ({new Date(filtroDataInicio).toLocaleDateString('pt-BR')} - {new Date(filtroDataFim).toLocaleDateString('pt-BR')})
              </span>
            )}
            {!filtroDataInicio && !filtroDataFim && (
              <span className="text-sm font-normal text-dark-400 ml-2">(Últimos 30 dias)</span>
            )}
          </h3>
          <BarChart3 className="text-dark-400" size={20} />
        </div>
        {ocupacaoData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={ocupacaoData}>
              <defs>
                <linearGradient id="colorOcupacao" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="date" 
                stroke="#64748b" 
                fontSize={ocupacaoData.length > 30 ? 10 : 11}
                angle={ocupacaoData.length > 15 ? -45 : 0}
                textAnchor={ocupacaoData.length > 15 ? "end" : "middle"}
                height={ocupacaoData.length > 15 ? 80 : 40}
                interval={ocupacaoData.length > 30 ? Math.floor(ocupacaoData.length / 15) : 0}
              />
              <YAxis 
                stroke="#64748b" 
                fontSize={12}
                domain={[0, 100]}
                label={{ value: '%', angle: -90, position: 'insideLeft', style: { fill: '#64748b' } }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#f8fafc' }}
                formatter={(value, name) => {
                  if (name === 'ocupacao') {
                    return [`${value}%`, 'Ocupação']
                  }
                  return [value, name]
                }}
              />
              <Area 
                type="monotone" 
                dataKey="ocupacao" 
                stroke="#f59e0b" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorOcupacao)" 
                dot={ocupacaoData.length <= 30}
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[400px] text-dark-400">
            <p>Nenhum dado disponível para o período selecionado</p>
          </div>
        )}
      </motion.div>

      {/* Distribuições */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Itens por Categoria */}
        {categoriasData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card"
          >
            <h3 className="text-lg font-semibold text-dark-50 mb-4">Itens por Categoria</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={categoriasData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="total"
                >
                  {categoriasData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {categoriasData.slice(0, 3).map((cat, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                    />
                    <span className="text-dark-400">{cat.name}</span>
                  </div>
                  <span className="text-dark-50 font-medium">{cat.quantidade} unidades</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Status dos Compromissos */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-dark-50 mb-4">Status dos Compromissos</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Ativos', value: compromissosAtivos.length },
                  { name: 'Agendados', value: stats?.compromissos_proximos || 0 },
                  { name: 'Finalizados', value: stats?.compromissos_vencidos || 0 },
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => percent > 0.05 ? `${name} ${(percent * 100).toFixed(0)}%` : ''}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {[0, 1, 2].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#6366f1]" />
                <span className="text-dark-400">Ativos</span>
              </div>
              <span className="text-dark-50 font-medium">{compromissosAtivos.length}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#8b5cf6]" />
                <span className="text-dark-400">Agendados</span>
              </div>
              <span className="text-dark-50 font-medium">{stats?.compromissos_proximos || 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#ec4899]" />
                <span className="text-dark-400">Finalizados</span>
              </div>
              <span className="text-dark-50 font-medium">{stats?.compromissos_vencidos || 0}</span>
            </div>
          </div>
        </motion.div>

        {/* Top Localizações */}
        {localizacoesData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="card"
          >
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="text-dark-400" size={20} />
              <h3 className="text-lg font-semibold text-dark-50">Top Localizações</h3>
            </div>
            <div className="space-y-3">
              {localizacoesData.map((loc, idx) => {
                const maxValue = Math.max(...localizacoesData.map(l => l.value))
                const percentage = (loc.value / maxValue) * 100
                return (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-dark-400">{loc.name}</span>
                      <span className="text-sm font-medium text-dark-50">{loc.value}</span>
                    </div>
                    <div className="w-full bg-dark-700 rounded-full h-2">
                      <div
                        className="bg-primary-500 h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>
        )}
      </div>

      {/* Compromissos Ativos e Próximos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compromissos Ativos */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Activity className="text-green-500" size={20} />
              <h3 className="text-lg font-semibold text-dark-50">Compromissos Ativos</h3>
            </div>
            <span className="px-3 py-1 bg-green-600/20 text-green-400 rounded-full text-sm font-medium">
              {compromissosAtivos.length}
            </span>
          </div>
          
          {compromissosAtivos.length > 0 ? (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {compromissosAtivos.map((comp, index) => (
                <motion.div
                  key={comp.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + index * 0.05 }}
                  className="p-4 bg-dark-700/50 rounded-lg border border-dark-700 hover:border-green-500/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-dark-50 mb-1">{formatItemName(comp.item) || 'Item Deletado'}</h4>
                      <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-dark-400">
                        <span className="flex items-center gap-1">
                          <Calendar size={14} />
                          {new Date(comp.data_inicio).toLocaleDateString('pt-BR')} - {new Date(comp.data_fim).toLocaleDateString('pt-BR')}
                        </span>
                        {comp.contratante && (
                          <span className="flex items-center gap-1">
                            <Users size={14} />
                            {comp.contratante}
                          </span>
                        )}
                        {comp.cidade && comp.uf && (
                          <span className="flex items-center gap-1">
                            <MapPin size={14} />
                            {comp.cidade} - {comp.uf}
                          </span>
                        )}
                      </div>
                      {comp.descricao && (
                        <p className="text-sm text-dark-500 mt-2">{comp.descricao}</p>
                      )}
                    </div>
                    <div className="ml-4">
                      <span className="px-3 py-1 bg-green-600/20 text-green-400 rounded-full text-sm font-medium">
                        {comp.quantidade} unid.
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-dark-400">
              <Activity className="mx-auto mb-3 opacity-50" size={48} />
              <p>Nenhum compromisso ativo no momento</p>
            </div>
          )}
        </motion.div>

        {/* Compromissos Próximos */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Clock className="text-blue-500" size={20} />
              <h3 className="text-lg font-semibold text-dark-50">Próximos 7 Dias</h3>
            </div>
            <span className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full text-sm font-medium">
              {compromissosProximos.length}
            </span>
          </div>
          
          {compromissosProximos.length > 0 ? (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {compromissosProximos.map((comp, index) => {
                const dataInicio = new Date(comp.data_inicio)
                const hoje = new Date()
                hoje.setHours(0, 0, 0, 0)
                dataInicio.setHours(0, 0, 0, 0)
                const diasRestantes = Math.ceil((dataInicio - hoje) / (1000 * 60 * 60 * 24))
                
                return (
                  <motion.div
                    key={comp.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + index * 0.05 }}
                    className="p-4 bg-dark-700/50 rounded-lg border border-dark-700 hover:border-blue-500/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-dark-50">{formatItemName(comp.item) || 'Item Deletado'}</h4>
                          {diasRestantes === 0 && (
                            <span className="px-2 py-0.5 bg-yellow-600/20 text-yellow-400 rounded text-xs font-medium">
                              Hoje
                            </span>
                          )}
                          {diasRestantes === 1 && (
                            <span className="px-2 py-0.5 bg-orange-600/20 text-orange-400 rounded text-xs font-medium">
                              Amanhã
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-dark-400">
                          <span className="flex items-center gap-1">
                            <Calendar size={14} />
                            {new Date(comp.data_inicio).toLocaleDateString('pt-BR')} - {new Date(comp.data_fim).toLocaleDateString('pt-BR')}
                          </span>
                          {comp.contratante && (
                            <span className="flex items-center gap-1">
                              <Users size={14} />
                              {comp.contratante}
                            </span>
                          )}
                          {comp.cidade && comp.uf && (
                            <span className="flex items-center gap-1">
                              <MapPin size={14} />
                              {comp.cidade} - {comp.uf}
                            </span>
                          )}
                        </div>
                        {comp.descricao && (
                          <p className="text-sm text-dark-500 mt-2">{comp.descricao}</p>
                        )}
                      </div>
                      <div className="ml-4 flex flex-col items-end gap-2">
                        <span className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full text-sm font-medium">
                          {comp.quantidade} unid.
                        </span>
                        {diasRestantes > 1 && (
                          <span className="text-xs text-dark-500">
                            Em {diasRestantes} dias
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-dark-400">
              <Clock className="mx-auto mb-3 opacity-50" size={48} />
              <p>Nenhum compromisso nos próximos 7 dias</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle, color, progress }) {
  const colorClasses = {
    primary: 'from-primary-600/20 to-primary-600/5 border-primary-600/20',
    green: 'from-green-600/20 to-green-600/5 border-green-600/20',
    yellow: 'from-yellow-600/20 to-yellow-600/5 border-yellow-600/20',
    blue: 'from-blue-600/20 to-blue-600/5 border-blue-600/20',
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`card bg-gradient-to-br ${colorClasses[color]} border-2 hover:scale-105 transition-transform`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-sm text-dark-400 mb-2">{title}</p>
          <p className="text-3xl font-bold text-dark-50 mb-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-dark-500">{subtitle}</p>
          )}
        </div>
        <div className="p-3 bg-dark-700/50 rounded-lg">
          {icon}
        </div>
      </div>
      {progress !== undefined && (
        <div className="mt-3">
          <div className="w-full bg-dark-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                color === 'yellow' ? 'bg-yellow-500' :
                color === 'green' ? 'bg-green-500' :
                color === 'blue' ? 'bg-blue-500' :
                'bg-primary-500'
              }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}
