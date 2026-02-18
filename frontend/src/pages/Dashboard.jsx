import React from 'react'
import { motion } from 'framer-motion'
import { Activity } from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center text-center space-y-4"
      >
        <div className="p-6 bg-primary-600/10 rounded-full border border-primary-500/20 shadow-2xl shadow-primary-500/10">
          <Activity className="text-primary-500 animate-pulse" size={48} />
        </div>
        
        <div className="space-y-2">
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase italic">
            Dashboard em Construção
          </h1>
          <p className="text-dark-400 font-medium tracking-widest uppercase text-[10px]">
            Novas métricas executivas em breve
          </p>
        </div>
      </motion.div>

      <div className="w-64 h-1 bg-dark-800 rounded-full overflow-hidden">
        <motion.div 
          initial={{ x: "-100%" }}
          animate={{ x: "100%" }}
          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
          className="w-full h-full bg-gradient-to-r from-transparent via-primary-500 to-transparent"
        />
      </div>
    </div>
  )
}