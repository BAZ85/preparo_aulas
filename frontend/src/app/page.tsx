"use client";

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Presentation, UploadCloud, Link as LinkIcon, Download, Loader2, Sparkles, CheckCircle2, ChevronRight, Play, FileCode2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function Home() {
  const [mode, setMode] = useState<"Roteiro" | "Slides">("Roteiro");
  
  // States - Form Gerais
  const [nivel, setNivel] = useState("");
  const [materia, setMateria] = useState("");
  const [assunto, setAssunto] = useState("");
  const [duracao, setDuracao] = useState(50);
  const [files, setFiles] = useState<FileList | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // Especializados: Roteiro (Apenas em Roteiro)
  const [referenciaUrl, setReferenciaUrl] = useState("");
  
  // Especializados: Slides (Apenas em Slides via C+B)
  const [pastedRoteiro, setPastedRoteiro] = useState("");
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const templateFileInputRef = useRef<HTMLInputElement>(null);

  // States - Status do Processo
  const [loading, setLoading] = useState(false);
  const [isConvertingSlides, setIsConvertingSlides] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");
  const [generatedMarkdown, setGeneratedMarkdown] = useState("");
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) setFiles(e.dataTransfer.files);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!materia || !assunto || !nivel) {
      setError("Preencha os campos vitais (Nível, Matéria e Assunto).");
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
      
      if (mode === "Roteiro") {
        formData.append("duracao", duracao.toString());
        if (referenciaUrl) formData.append("reference_url", referenciaUrl);
      } else {
        if (pastedRoteiro) formData.append("roteiro_markdown", pastedRoteiro);
      }
      
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
        throw new Error(err.detail || "Erro engasgou a IA no Backend :(");
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
      setIsExporting(true);
      const res = await fetch(`${API_BASE}/export/docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited_markdown: generatedMarkdown })
      });
      if (!res.ok) throw new Error("A exportação de DOCX tropeçou no processo.");
      
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
      setIsExporting(false);
    }
  };

  const convertToSlides = async () => {
    if (!generatedMarkdown) return;
    try {
      setIsConvertingSlides(true);
      const formData = new FormData();
      formData.append("materia", materia);
      formData.append("assunto", assunto);
      formData.append("nivel_escolaridade", nivel);
      formData.append("roteiro_markdown", generatedMarkdown);

      const response = await fetch(`${API_BASE}/slides/rascunho`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("Geração bloqueada na montagem de slides.");
      const result = await response.json();
      setGeneratedMarkdown(result.markdown_slides);
      setMode("Slides");
    } catch(err: any) {
      setError(err.message);
    } finally {
      setIsConvertingSlides(false);
    }
  };

  const downloadHtml = async () => {
    if (!generatedMarkdown) return;
    try {
      setIsExporting(true);
      const formData = new FormData();
      formData.append("edited_markdown", generatedMarkdown);
      if (templateFile) formData.append("template_arquivo", templateFile);

      const res = await fetch(`${API_BASE}/export/html`, {
        method: 'POST',
        body: formData
      });
      
      if (!res.ok) throw new Error("Servidor perdeu o fôlego compactando seu pacote HTML.");
      
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
      setIsExporting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0B0E14] text-slate-200 overflow-x-hidden relative selection:bg-purple-500/30 font-sans">
      <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-indigo-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[30vw] h-[30vw] rounded-full bg-blue-600/10 blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto p-4 md:p-10 relative z-10 w-full">
        
        {/* Superior da Plataforma */}
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

        {/* TabSwitcher Aprimorado */}
        <div className="flex gap-3 mb-8 bg-slate-900/50 p-1.5 rounded-2xl w-fit border border-slate-800/80 backdrop-blur-md">
          <button 
            type="button"
            onClick={() => { setMode("Roteiro"); setGeneratedMarkdown(""); setPastedRoteiro(""); setFiles(null); }}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 ${mode === "Roteiro" ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-md shadow-indigo-600/10" : "text-slate-400 hover:text-slate-200"}`}
          >
            <BookOpen size={16} />
            Gerar Roteiro
          </button>
          <button 
            type="button"
            onClick={() => { setMode("Slides"); setGeneratedMarkdown(""); setPastedRoteiro(""); setFiles(null); }}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 ${mode === "Slides" ? "bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-md shadow-purple-600/10" : "text-slate-400 hover:text-slate-200"}`}
          >
            <Presentation size={16} />
            Gerar Slides Direto
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* PAINEL DINÂMICO DE ENTRADA (O SEGREDO DA OPÇÃO B + C) */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-4 space-y-6"
          >
            <form onSubmit={handleSubmit} className="glass-panel rounded-3xl p-6 md:p-8 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
              
              <h2 className="text-lg font-semibold mb-6 flex items-center gap-3">
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs border ${mode === 'Roteiro' ? 'bg-slate-800 border-slate-700 text-indigo-300' : 'bg-slate-800/80 border-slate-700/80 text-purple-300'}`}>1</span>
                Infraestrutura da Aula
              </h2>

              <div className="space-y-4">
                 <div className="flex gap-4">
                   <div className="w-1/2">
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5 pl-1">Nível</label>
                    <select 
                      value={nivel} onChange={e => setNivel(e.target.value)} required
                      className="w-full bg-slate-900 border border-slate-700/80 focus:border-indigo-500 rounded-xl px-3 py-2.5 text-sm text-slate-200 outline-none transition-all"
                    >
                      <option value="" disabled>Selecione</option>
                      <option>Médio</option>
                      <option>Graduação</option>
                      <option>Pós</option>
                    </select>
                  </div>
                  <div className="w-1/2 flex flex-col justify-end">
                     {mode === "Roteiro" && (
                      <>
                        <label className="flex justify-between w-full text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5 pl-1">
                          Minutos <span className="text-indigo-400 font-mono text-[10px] bg-indigo-500/10 px-1.5 rounded">{duracao}m</span>
                        </label>
                        <input type="range" min="10" max="300" step="5" value={duracao} onChange={e => setDuracao(parseInt(e.target.value))} className="w-full accent-indigo-500 bg-slate-800 h-2 mt-1" />
                      </>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5 pl-1">Matéria</label>
                  <input type="text" value={materia} onChange={e => setMateria(e.target.value)} required placeholder="Ex: Direito Tributário"
                    className="w-full bg-slate-900 border border-slate-700/80 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600" />
                </div>
                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5 pl-1">Assunto</label>
                  <input type="text" value={assunto} onChange={e => setAssunto(e.target.value)} required placeholder="Ex: Extinção do Crédito Tributário"
                    className="w-full bg-slate-900 border border-slate-700/80 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600" />
                </div>
              </div>

              <div className="my-6 h-px bg-slate-800" />

              <h2 className="text-lg font-semibold mb-6 flex items-center gap-3">
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs border ${mode === 'Roteiro' ? 'bg-slate-800 border-slate-700 text-indigo-300' : 'bg-slate-800/80 border-slate-700/80 text-purple-300'}`}>2</span>
                {mode === "Roteiro" ? "Base de Raciocínio" : "Receita Bruta do Seu Roteiro"}
              </h2>

              <div className="space-y-4">
                {mode === "Roteiro" ? (
                  /* --- TÚNEL: ROTEIRO --- */
                  <AnimatePresence mode="popLayout">
                    <motion.div initial={{ opacity: 0}} animate={{ opacity: 1}} exit={{ opacity: 0}} className="space-y-4">
                      
                      <div 
                        onClick={() => fileInputRef.current?.click()} 
                        onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
                        className={`w-full border-2 border-dashed ${isDragging ? "border-indigo-500 bg-indigo-500/10 scale-[1.02]" : "border-slate-700/80 hover:border-indigo-500/50 hover:bg-slate-900/60 bg-slate-900/30"} rounded-2xl p-5 text-center cursor-pointer transition-all duration-300 flex flex-col items-center gap-2`}
                      >
                        <UploadCloud size={24} className={isDragging ? "text-indigo-400" : "text-slate-500"} />
                        <div className="text-sm pointer-events-none">
                          {files && files.length > 0 ? (
                            <span className="text-indigo-300 font-medium">{files.length} material(is) pronto(s) na agulha!</span>
                          ) : (
                            <span className="text-slate-400">Carregue PDF/Textos de <b className="text-slate-300 font-medium">referência profunda</b></span>
                          )}
                        </div>
                        <input type="file" multiple ref={fileInputRef} className="hidden" accept=".pdf,.docx,.txt" onChange={e => setFiles(e.target.files)} />
                      </div>

                      <div className="relative">
                        <LinkIcon size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                        <input type="url" value={referenciaUrl} onChange={e => setReferenciaUrl(e.target.value)} placeholder="URL Referência (Youtube, Notion, Wikipedia)"
                          className="w-full bg-slate-900 border border-slate-700/80 focus:border-indigo-500 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600" />
                      </div>

                    </motion.div>
                  </AnimatePresence>
                ) : (
                  /* --- TÚNEL: SLIDES DIRETO --- */
                  <AnimatePresence mode="popLayout">
                    <motion.div initial={{ opacity: 0}} animate={{ opacity: 1}} exit={{ opacity: 0}} className="space-y-3">
                      
                      {/* O Colador Expansivo (B) */}
                      <textarea 
                        value={pastedRoteiro} onChange={e => setPastedRoteiro(e.target.value)}
                        placeholder="Dê Ctrl+V no conteúdo integral/Markdown bruto do seu roteiro aqui..."
                        className="w-full h-[140px] bg-slate-900/40 border border-slate-700/80 focus:border-purple-500 rounded-2xl p-4 text-[13px] leading-relaxed text-slate-300 outline-none transition-all placeholder:text-slate-600 resize-none font-mono"
                      />
                      
                      <div className="flex gap-3 items-center w-full px-2 py-1 opacity-60">
                           <div className="flex-1 h-px bg-slate-700" />
                           <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">Ou Suba o Arquivo Físico</span>
                           <div className="flex-1 h-px bg-slate-700" />
                      </div>
                      
                      <button 
                        type="button" 
                        onClick={() => fileInputRef.current?.click()} 
                        onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
                        className={`w-full ${isDragging ? "bg-purple-900/20 border-purple-500 text-purple-300 scale-[1.02]" : "bg-slate-900 border-slate-700 hover:border-purple-500/50 text-slate-400 hover:text-purple-300"} border-2 border-dashed rounded-xl px-4 py-3 text-sm transition-all duration-300 flex items-center justify-center gap-2 shadow-sm`}
                      >
                           <UploadCloud size={16}/> {files && files.length > 0 ? <b className="text-purple-300">{files.length} Roteiro Anexado! (DOCX/MD)</b> : "Arraste / Solte ou Procure o Arquivo (DOCX/MD)"}
                      </button>
                      <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,.docx,.txt,.md" onChange={e => setFiles(e.target.files)} />

                    </motion.div>
                  </AnimatePresence>
                )}

                {/* Seção 3 Global Constante: Identidade Visual */}
                <div className="pt-3">
                   <div 
                      onClick={() => templateFileInputRef.current?.click()}
                      className={`relative overflow-hidden w-full bg-slate-900 border border-slate-700 ${mode === 'Slides' ? 'hover:border-purple-500/50' : 'hover:border-indigo-500/50'} rounded-xl px-4 py-3.5 cursor-pointer transition-all flex items-center justify-between group`}
                    >
                       <div className="flex items-center gap-3">
                           <FileCode2 size={18} className={templateFile ? "text-emerald-400" : "text-slate-500 group-hover:text-slate-400 transition-colors"} />
                           <div className="flex flex-col">
                             <span className={`text-[13px] ${templateFile ? (mode === "Slides" ? "text-purple-300" : "text-indigo-300") : "text-slate-400"} font-medium`}>
                                 {templateFile ? templateFile.name : "Anexar Design (Slides HTML)"}
                             </span>
                           </div>
                       </div>
                       {templateFile && <CheckCircle2 size={16} className="text-emerald-400" />}
                       <input type="file" ref={templateFileInputRef} className="hidden" accept=".html,.htm" onChange={e => { if (e.target.files && e.target.files[0]) setTemplateFile(e.target.files[0]); }} />
                    </div>
                </div>

              </div>

              {error && (
                <div className="mt-6 p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-start gap-2">
                  <span className="mt-0.5">⚠️</span> {error}
                </div>
              )}

              <button 
                type="submit" disabled={loading || isConvertingSlides}
                className={`w-full mt-8 bg-gradient-to-r ${mode === 'Roteiro' ? 'from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 shadow-indigo-600/20 hover:shadow-indigo-600/40' : 'from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-purple-600/20 hover:shadow-purple-600/40'} disabled:opacity-50 disabled:grayscale-[0.5] text-white font-medium text-[15px] py-4 rounded-2xl flex justify-center items-center gap-2 transition-all shadow-lg active:scale-[0.98]`}
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} fill="currentColor" />}
                {loading ? "Inteligência Trabalhando..." : (mode === "Roteiro" ? "Gerar Arquitetura e Roteiro" : "Bater Martelo nos Slides")}
              </button>
            </form>
          </motion.div>


          {/* Copiloto Visualizador (Intacto para o Backend) */}
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
        </div>
      </div>
    </main>
  );
}
