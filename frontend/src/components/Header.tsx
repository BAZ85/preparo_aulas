import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

export function Header() {
  return (
    <header className="mb-10 text-center md:text-left flex flex-col md:flex-row items-center gap-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
        className="shrink-0"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/Syllabus-canva.svg" alt="Syllabus Logo" className="h-28 md:h-36 w-auto" />
      </motion.div>
      
      <div className="flex flex-col items-center md:items-start">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel text-indigo-400 font-medium text-xs mb-4 shadow-inner"
        >
          <Sparkles size={14} /> V1 Plataforma de Ensino
        </motion.div>
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500 pb-1"
        >
          Syllabus
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="mt-2 text-slate-400 text-base max-w-2xl font-light"
        >
          Planos de Ensino e Apresentações Inteligentes via IA
        </motion.p>
      </div>
    </header>
  );
}
