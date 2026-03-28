import os
import re
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from duckduckgo_search import DDGS

def get_gemini_llm(temperature=0.7):
    return ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=temperature, max_output_tokens=8192)

def generate_structural_map(content: str, inputs: dict) -> str:
    """
    Passo 1: Lê todo o texto extraído e gera o Mapa Estrutural via LCEL (muito rápido).
    """
    llm = get_gemini_llm(temperature=0.4)
    
    prompt_text = """Você é um Professor de nível {nivel_escolaridade} especialista em {materia} e Analista de Conteúdo Acadêmico.
Seu objetivo é construir um Mapa Estrutural do material que seja exaustivamente focado no assunto "{assunto}".

Material Integral:
-----------------------------
{content}
-----------------------------

Instruções vitais:
1. O nível de detalhamento deve ser focado no essencial para não alongar excessivamente a aula, compatível com o nível {nivel_escolaridade}.
2. MENSURAÇÃO DE TEMPO OBRIGATÓRIA: Atribua uma estimativa de tempo realista (em minutos) para cada tópico principal identificado. 
   A soma dos tempos de TODOS os tópicos listados DEVE resultar EXATAMENTE em {duracao} minutos.

Formato e Saída Exigida:
Tema principal: [Nome do Tema]

Tópicos identificados
  - [Nome do Tópico] (Tempo Estimado: X min)
    - Subtópicos vinculados
    - Conceitos teóricos base
    - Exemplos
    - Base jurídica ou doutrinária (se houver no texto)

Referências identificadas (se houver)
  - Leis / Doutrina / Súmulas
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm | StrOutputParser()
    
    print("Gerando o Mapa Estrutural via Gemini...")
    result = chain.invoke({
        "nivel_escolaridade": inputs.get("nivel_escolaridade"),
        "materia": inputs.get("materia"),
        "assunto": inputs.get("assunto"),
        "duracao": inputs.get("duracao"),
        "content": content
    })
    return result

async def research_single_topic(topic_chunk: str, inputs: dict) -> str:
    """
    Passo 2 individual: Expande e pesquisa um único tópico de forma direta (Sem Agent Loops).
    """
    llm = get_gemini_llm(temperature=0.3)
    
    try:
        topic_name = topic_chunk.split("(Tempo Estimado")[0].replace("-", "").strip()
        query = f"{inputs.get('materia')} {topic_name}"
        
        # Pesquisa nativa com DDGS focada em coletar expansão teórica
        results = DDGS().text(query, max_results=4)
        res_list = list(results)
        if res_list:
            web_context = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')}" for r in res_list])
        else:
            web_context = "Sem resultados adicionais relevantes na web."
    except Exception as e:
        web_context = "Pesquisa falhou."

    system_prompt = f"""Você é um Professor de nível {inputs.get('nivel_escolaridade')} especialista em {inputs.get('materia')} e Pesquisador Acadêmico experiente.
Sua missão é **AMPLIAR E APROFUNDAR** a explicação do tópico recebido. Não faça apenas um resumo!
Use o Contexto da Web fornecido para incorporar ativamente fundamentação teórica robusta, doutrina, exemplos práticos e, se cabível, referências jurídicas. O objetivo é enriquecer o conteúdo de forma profunda, indo além do texto cruzado original.

OBRIGATÓRIO: 
- Inicie todo o seu texto OBRIGATORIAMENTE com a string literal "===NOVO_TOPICO===" no início exato da resposta.
- Logo abaixo, insira o Título do Tópico preservando fielmente sua tag de '(Tempo Estimado: X min)'.
- Em seguida, redija a explicação teórica rica e expandida."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Expanda o seguinte bloco de tópico do mapa estrutural:\n\n{topic_chunk}\n\nResultados da Pesquisa Web:\n{web_context}"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        return await chain.ainvoke({
            "topic_chunk": topic_chunk,
            "web_context": web_context
        })
    except Exception as e:
        return f"===NOVO_TOPICO===\nErro ao expandir tópico: {topic_chunk}\nErro: {str(e)}"

async def research_topics_parallel(structural_map: str, inputs: dict) -> str:
    """
    Passo 2 Paralelo: Extrai do mapa os blocos de cada tópico e roda a pesquisa (Step 2) simultaneamente.
    """
    topics_list = []
    lines = structural_map.split('\n')
    in_topics = False
    current_topic = ""
    
    for line in lines:
        if "Tópicos identificados" in line:
            in_topics = True
            continue
        if in_topics and ("Referências identificadas" in line or "Referências jurídicas" in line):
            if current_topic:
                topics_list.append(current_topic.strip())
            break
            
        if in_topics:
            # Qualquer linha que contenha a tag "Tempo Estimado" inicia um tópico principal
            if "Tempo Estimado" in line:
                if current_topic:
                    topics_list.append(current_topic.strip())
                current_topic = line.strip() + "\n"
            elif current_topic:
                current_topic += line + "\n"
                
    if not topics_list:
        # Fallback de segurança se o Regex falhar
        print("Aviso: Regex de particionamento falhou. Pesquisando tudo em batch único...")
        topics_list = [structural_map]
        
    print(f"Descobertos {len(topics_list)} tópicos para expansão de pesquisa em Paralelo (Async)!")
    
    # Roda as tarefas assincronamente (Langchain paralelo via asyncio)
    tasks = [research_single_topic(t, inputs) for t in topics_list]
    results = await asyncio.gather(*tasks)
    
    return "\n\n".join(results)
