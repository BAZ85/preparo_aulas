import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Presentation, Download, Loader2, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface PreviewPanelProps {
  mode: "Roteiro" | "Slides";
  loading: boolean;
  isConvertingSlides: boolean;
  isExporting: boolean;
  generatedMarkdown: string;
  setGeneratedMarkdown: (val: string) => void;
  convertToSlides: () => void;
  downloadDocx: () => void;
  downloadHtml: () => void;
}

export function PreviewPanel({
  mode,
  loading,
  isConvertingSlides,
  isExporting,
  generatedMarkdown,
  setGeneratedMarkdown,
  convertToSlides,
  downloadDocx,
  downloadHtml
}: PreviewPanelProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="lg:col-span-8 flex flex-col h-[820px] relative"
    >
      {generatedMarkdown ? (
        <div className="glass-panel rounded-3xl flex flex-col h-full shadow-2xl overflow-hidden border-slate-700/40 relative">
            <div className={`absolute top-0 w-full h-[4px] bg-gradient-to-r ${mode === 'Roteiro' ? 'from-indigo-500 to-blue-500' : 'from-purple-500 to-indigo-500'}`} />
            
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between p-4 px-6 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md z-10">
              <h3 className="font-semibold text-slate-300 flex items-center gap-2 text-sm w-full sm:w-auto">
                 <CheckCircle2 className="text-emerald-400" size={16}/> Copiloto Ativado
              </h3>
              
              <div className="flex gap-3 w-full sm:w-auto justify-end flex-wrap items-center">
                {mode === "Roteiro" && (
                   <button 
                     onClick={convertToSlides} disabled={isConvertingSlides} title="Criar os bullets de slides derivados do roteiro atual" 
                     className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-purple-300 text-xs font-semibold tracking-wide uppercase rounded-lg transition-colors border border-purple-500/30 shadow-md disabled:opacity-70 disabled:cursor-progress"
                   >
                      {isConvertingSlides ? (<><Loader2 size={14} className="animate-spin text-purple-400" /> Sintetizando...</>) : ("Fazer Slides")}
                   </button>
                )}
                
                {mode === "Roteiro" ? (
                   <button onClick={downloadDocx} disabled={isExporting} className="flex items-center gap-1.5 px-4 py-2 bg-slate-200 hover:bg-white text-slate-900 disabled:opacity-50 text-xs font-bold tracking-wide uppercase rounded-lg transition-colors shadow-lg">
                     {isExporting ? <Loader2 size={14} className="animate-spin"/> : <Download size={14}/>} DOCX
                   </button>
                ) : (
                   <button onClick={downloadHtml} disabled={isExporting} className="flex items-center gap-1.5 px-6 py-2 bg-slate-200 hover:bg-white text-slate-900 disabled:opacity-50 text-xs font-extrabold tracking-widest uppercase rounded-lg transition-all shadow-[0_0_20px_rgba(255,255,255,0.15)] hover:shadow-[0_0_25px_rgba(255,255,255,0.3)]">
                     {isExporting ? <Loader2 size={15} className="animate-spin"/> : <Presentation size={15}/>} Baixar .HTML Pronto!
                   </button>
                )}
              </div>
            </div>

            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 min-h-0 bg-[#0B0E14]/80 relative">
               <AnimatePresence>
                  {isConvertingSlides && (
                     <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-50 bg-slate-950/70 backdrop-blur-[3px] flex flex-col items-center justify-center border-t border-purple-500/30">
                        <div className="bg-slate-900 p-8 rounded-3xl shadow-2xl border border-slate-700/50 flex flex-col items-center gap-5">
                          <Loader2 size={42} className="animate-spin text-purple-400" />
                          <span className="font-semibold text-slate-200 text-lg">Formatando Balas e Páginas...</span>
                          <span className="text-sm text-slate-400">A Inteligência está escaneando a semântica para o palanque.</span>
                        </div>
                     </motion.div>
                  )}
               </AnimatePresence>

               <textarea 
                  value={generatedMarkdown} onChange={(e) => setGeneratedMarkdown(e.target.value)} spellCheck="false"
                  className="p-6 bg-transparent text-slate-300 font-mono text-[13px] leading-relaxed outline-none resize-none hide-scrollbar placeholder:text-slate-700 w-full h-full border-r border-slate-800/80"
               />
               <div className="p-6 prose prose-invert prose-indigo prose-h2:text-purple-400 prose-h3:text-slate-300 prose-p:text-slate-300 prose-li:text-slate-300 max-w-none overflow-y-auto h-full hidden md:block">
                  <ReactMarkdown>{generatedMarkdown}</ReactMarkdown>
               </div>
            </div>
        </div>
       ) : (
          <div className="flex-1 glass-panel rounded-3xl flex flex-col items-center justify-center text-slate-500 p-12 text-center h-full relative overflow-hidden">
             <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]" />
             {loading ? (
               <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center z-10">
                  <div className="relative mb-5">
                       <div className="absolute inset-0 bg-indigo-500 blur-2xl opacity-20 rounded-full" />
                       <Loader2 size={46} className="animate-spin text-indigo-400 relative z-10" />
                  </div>
                  <h3 className="text-xl font-medium text-slate-200 mb-2">Engenharia Cerebral em Progresso...</h3>
                  <p className="max-w-sm text-slate-400 text-[13px] leading-relaxed">
                    A API Claude/Gemini está minerando e articulando o conteúdo da matéria solicitada contra o banco de dados.
                  </p>
               </motion.div>
             ) : (
               <div className="flex flex-col items-center z-10 opacity-70">
                  <div className="w-20 h-20 rounded-full bg-slate-800/80 flex items-center justify-center mb-6 border border-slate-700 relative overflow-hidden">
                    <BookOpen size={28} className={`${mode === 'Slides' ? 'text-purple-500' : 'text-indigo-500'} opacity-80`} />
                  </div>
                  <h3 className="text-2xl font-medium text-slate-300 mb-3">O Copiloto Aguarda</h3>
                  <p className="max-w-md text-slate-500 text-sm">
                    {mode === "Roteiro" 
                      ? "Neste espaço habitam os Textuais brutos da Aula. Preencha seus parâmetros construtivos e referências lá no primeiro painel."
                      : "Preencha o Mestre de Conteúdo. Copie seu Markdown pronto e receba os dados mastigados para o Reveal JS."}
                  </p>
               </div>
             )}
          </div>
       )}
    </motion.div>
  );
}
