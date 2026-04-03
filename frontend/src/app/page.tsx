"use client";

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Presentation, UploadCloud, Link as LinkIcon, Download, Loader2, Sparkles, CheckCircle2, ChevronRight, Play } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API_BASE = "http://127.0.0.1:8000/api";

export default function Home() {
  const [mode, setMode] = useState<"Roteiro" | "Slides">("Roteiro");
  
  // States - Form
  const [nivel, setNivel] = useState("");
  const [materia, setMateria] = useState("");
  const [assunto, setAssunto] = useState("");
  const [duracao, setDuracao] = useState(50);
  const [referenciaUrl, setReferenciaUrl] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  
  // States - Process
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [generatedMarkdown, setGeneratedMarkdown] = useState("");
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!materia || !assunto || !nivel) {
      setError("Preencha os campos obrigatórios (Nível, Matéria e Assunto).");
      return;
    }
    setError("");
    setLoading(true);
    setGeneratedMarkdown("");

    try {
      const formData = new FormData();
      formData.append("materia", materia);
      formData.append("assunto", assunto);
      formData.append("nivel_escolaridade", nivel);
      formData.append("duracao", duracao.toString());
      if (referenciaUrl) formData.append("reference_url", referenciaUrl);
      
      if (files) {
         Array.from(files).forEach((file) => formData.append("arquivos", file));
      }

      const endpoint = mode === "Roteiro" ? "/roteiro/gerar" : "/slides/rascunho";
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erro inesperado do Servidor");
      }

      const result = await response.json();
      
      if (mode === "Roteiro") {
        setGeneratedMarkdown(result.data);
      } else {
        setGeneratedMarkdown(result.markdown_slides);
      }
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadDocx = async () => {
    if (!generatedMarkdown) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/export/docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited_markdown: generatedMarkdown })
      });
      if (!res.ok) throw new Error("Falha ao exportar DOCX.");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `roteiro_${assunto.replace(/\s+/g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch(err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const convertToSlides = async () => {
    if (!generatedMarkdown) return;
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append("materia", materia);
      formData.append("assunto", assunto);
      formData.append("nivel_escolaridade", nivel);
      formData.append("roteiro_markdown", generatedMarkdown);

      const response = await fetch(`${API_BASE}/slides/rascunho`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("Erro ao converter roteiro para slides.");
      const result = await response.json();
      setGeneratedMarkdown(result.markdown_slides);
      setMode("Slides");
    } catch(err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadHtml = async () => {
    if (!generatedMarkdown) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/export/html`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited_markdown: generatedMarkdown })
      });
      if (!res.ok) throw new Error("Falha ao exportar HTML animado.");
      
      const data = await res.json();
      const blob = new Blob([data.html_content], { type: "text/html" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `slides_${assunto.replace(/\s+/g, '_')}.html`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch(err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0B0E14] text-slate-200 overflow-x-hidden relative selection:bg-indigo-500/30 font-sans">
      
      {/* Background Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-indigo-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[30vw] h-[30vw] rounded-full bg-blue-600/10 blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto p-4 md:p-10 relative z-10 w-full">
        
        {/* Header */}
        <header className="mb-10 text-center md:text-left">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel text-indigo-400 font-medium text-xs mb-5"
          >
            <Sparkles size={14} /> Pré-lançamento PrepAula AI
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500 pb-2"
          >
            Mestre Assíncrono
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="mt-3 text-slate-400 text-lg max-w-2xl"
          >
            Seu assistente universal para orquestrar roteiros densos e slides premium. Construído para ser ágil e inteligente.
          </motion.p>
        </header>

        {/* Action Toggle */}
        <div className="flex gap-3 mb-8 bg-slate-900/50 p-1.5 rounded-2xl w-fit border border-slate-800/80 backdrop-blur-md">
          <button 
            onClick={() => { setMode("Roteiro"); setGeneratedMarkdown(""); }}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 ${mode === "Roteiro" ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm" : "text-slate-400 hover:text-slate-200"}`}
          >
            <BookOpen size={16} />
            Gerar Roteiro
          </button>
          <button 
            onClick={() => { setMode("Slides"); setGeneratedMarkdown(""); }}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 ${mode === "Slides" ? "bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-sm" : "text-slate-400 hover:text-slate-200"}`}
          >
            <Presentation size={16} />
            Gerar Slides Direto
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Panel: Formulário */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-4 space-y-6"
          >
            <form onSubmit={handleSubmit} className="glass-panel rounded-3xl p-6 md:p-8 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
              
              <h2 className="text-lg font-semibold mb-6 flex items-center gap-3">
                <span className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-xs border border-slate-700 text-indigo-300">1</span>
                Infraestrutura da Aula
              </h2>

              <div className="space-y-5">
                 <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Nível</label>
                  <select 
                    value={nivel} onChange={e => setNivel(e.target.value)} required
                    className="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none transition-all"
                  >
                    <option value="" disabled>Selecione o Nível</option>
                    <option>Ensino Médio</option>
                    <option>Graduação</option>
                    <option>Pós-Graduação</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Matéria</label>
                  <input 
                    type="text" value={materia} onChange={e => setMateria(e.target.value)} required placeholder="Ex: História da Arte"
                    className="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Assunto Específico</label>
                  <input 
                    type="text" value={assunto} onChange={e => setAssunto(e.target.value)} required placeholder="Ex: Renascimento"
                    className="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                  />
                </div>

                {mode === "Roteiro" && (
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex justify-between">
                      Duração Estimada <span className="text-indigo-400 font-mono text-xs">{duracao} min</span>
                    </label>
                    <input 
                      type="range" min="10" max="300" step="5" value={duracao} onChange={e => setDuracao(parseInt(e.target.value))}
                      className="w-full accent-indigo-500 bg-slate-800"
                    />
                  </div>
                )}
              </div>

              <div className="my-8 h-px bg-slate-800" />

              <h2 className="text-lg font-semibold mb-6 flex items-center gap-3">
                <span className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-xs border border-slate-700 text-indigo-300">2</span>
                Base de Raciocínio (Opcional)
              </h2>

              <div className="space-y-4">
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-slate-700/80 hover:border-indigo-500/50 hover:bg-indigo-500/5 bg-slate-900/40 rounded-2xl p-5 text-center cursor-pointer transition-all flex flex-col items-center gap-2"
                >
                  <UploadCloud size={24} className="text-slate-500" />
                  <div className="text-sm">
                    {files && files.length > 0 ? (
                      <span className="text-indigo-300 font-medium block mt-1">{files.length} arquivo(s) preparado(s)</span>
                    ) : (
                      <span className="text-slate-400">Clique para enviar <b className="text-slate-300 font-medium">PDF ou DOCX</b></span>
                    )}
                  </div>
                  <input 
                    type="file" multiple ref={fileInputRef} className="hidden" 
                    accept=".pdf,.docx,.txt"
                    onChange={e => setFiles(e.target.files)} 
                  />
                </div>

                <div className="relative">
                  <LinkIcon size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input 
                    type="url" value={referenciaUrl} onChange={e => setReferenciaUrl(e.target.value)} placeholder="Cole uma URL Referência (YouTube, Artigo...)"
                    className="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                  />
                </div>
              </div>

              {error && (
                <div className="mt-6 p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-start gap-2">
                  <span className="mt-0.5">⚠️</span> {error}
                </div>
              )}

              <button 
                type="submit" disabled={loading}
                className="w-full mt-8 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:opacity-50 disabled:grayscale-[0.5] text-white font-medium text-sm py-3.5 px-6 rounded-xl flex justify-center items-center gap-2 transition-all shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/40 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} fill="currentColor" />}
                {loading ? "Inteligência Trabalhando..." : `Executar Missão`}
              </button>
            </form>
          </motion.div>


          {/* Panel: Copiloto / Resultado */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-8 flex flex-col h-full lg:h-[750px]"
          >
             {generatedMarkdown ? (
              <div className="glass-panel rounded-3xl flex flex-col h-full shadow-2xl overflow-hidden border-indigo-500/20 relative">
                  <div className="absolute top-0 w-full h-[3px] bg-gradient-to-r from-indigo-500 via-purple-500 to-blue-500" />
                  
                  <div className="flex items-center justify-between p-4 px-6 border-b border-slate-800/80 bg-slate-900/40">
                    <h3 className="font-semibold text-slate-300 flex items-center gap-2 text-sm">
                       <CheckCircle2 className="text-emerald-400" size={16}/> Copiloto Ativado
                    </h3>
                    <div className="flex gap-2">
                      {mode === "Roteiro" && (
                         <button onClick={convertToSlides} title="Gerar Slides baseados neste Roteiro" className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-indigo-300 text-xs font-semibold tracking-wide uppercase rounded-lg transition-colors border border-slate-700">
                            Fazer Slides
                         </button>
                      )}
                      
                      {mode === "Roteiro" ? (
                         <button onClick={downloadDocx} className="flex items-center gap-1.5 px-4 py-1.5 bg-slate-200 hover:bg-white text-slate-900 text-xs font-bold tracking-wide uppercase rounded-lg transition-colors shadow-lg">
                           <Download size={14}/> Baixar DOCX
                         </button>
                      ) : (
                         <button onClick={downloadHtml} className="flex items-center gap-1.5 px-4 py-1.5 bg-slate-200 hover:bg-white text-slate-900 text-xs font-bold tracking-wide uppercase rounded-lg transition-colors shadow-lg">
                           <Presentation size={14}/> Baixar HTML
                         </button>
                      )}
                    </div>
                  </div>

                  {/* Dual Panel Editor: Left Raw, Right Rendered */}
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-2 min-h-0 bg-[#0B0E14]/80">
                     <textarea 
                        value={generatedMarkdown}
                        onChange={(e) => setGeneratedMarkdown(e.target.value)}
                        className="p-6 bg-transparent text-slate-300 font-mono text-[13px] leading-relaxed outline-none resize-none hide-scrollbar placeholder:text-slate-700 w-full h-full border-r border-slate-800/80"
                        spellCheck="false"
                     />
                     <div className="p-6 prose prose-invert prose-indigo prose-h2:text-indigo-400 prose-h3:text-slate-300 prose-p:text-slate-300 prose-li:text-slate-300 max-w-none overflow-y-auto h-full hidden md:block">
                        <ReactMarkdown>{generatedMarkdown}</ReactMarkdown>
                     </div>
                  </div>
              </div>
             ) : (
                <div className="flex-1 glass-panel rounded-3xl border-dashed border-2 border-slate-800/60 flex flex-col items-center justify-center text-slate-500 p-12 text-center h-[500px] lg:h-full">
                   {loading ? (
                     <motion.div 
                       initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                       className="flex flex-col items-center"
                     >
                        <Loader2 size={42} className="animate-spin text-indigo-500 mb-5 opacity-90" />
                        <h3 className="text-xl font-medium text-slate-200 mb-2">A Mágica está acontecendo...</h3>
                        <p className="max-w-md text-slate-400 text-sm leading-relaxed">
                          Neste exato segundo, a tecnologia da Anthropic está orquestrando a pedagogia da sua aula. Pode demorar de 1 a 3 minutos dependo do nível de detalhamento solicitado.
                        </p>
                     </motion.div>
                   ) : (
                     <div className="flex flex-col items-center">
                        <div className="w-20 h-20 rounded-full bg-slate-800/50 flex items-center justify-center mb-6 border border-slate-700/50 relative overflow-hidden">
                          <Sparkles size={32} className="text-indigo-500 opacity-80" />
                          <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 to-transparent animate-pulse" />
                        </div>
                        <h3 className="text-2xl font-medium text-slate-300 mb-3">Pronto para Ensinar</h3>
                        <p className="max-w-[280px] md:max-w-md text-slate-500 text-sm">
                          Preencha a infraestrutura de tempo e contexto da sua aula ao lado. Nós cuidamos da teoria, do seu roteiro prático e dos Slides Reveal visualmente espetaculares.
                        </p>
                     </div>
                   )}
                </div>
             )}
          </motion.div>
        </div>
      </div>
    </main>
  );
}
