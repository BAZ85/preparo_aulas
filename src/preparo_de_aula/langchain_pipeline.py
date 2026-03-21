import os
import re
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_tool_calling_agent

def get_gemini_llm(temperature=0.7):
    # Usando o modelo Pro sugerido, ajuste se precisar de outro
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
    Passo 2 individual: Expande e pesquisa um único tópico usando AgentTools.
    """
    llm = get_gemini_llm(temperature=0.3)
    tools = [DuckDuckGoSearchRun(name="pesquisa_duckduckgo", description="Busca online informações complementares teóricas e práticas sobre um tópico de aula.")]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um Professor de nível {nivel_escolaridade} especialista em {materia} e Pesquisador Acadêmico experiente.
Seu trabalho é expandir profundamente o tópico recebido incorporando (se necessário) a internet para referências-chave (doutrina, leis, etc).
Seja muito didático e objetivo. Não gere textos enciclopédicos. Adapte a fala aos alunos de {nivel_escolaridade}.

OBRIGATÓRIO: 
- Você DEVE iniciar todo o seu texto OBRIGATORIAMENTE com a string literal "===NOVO_TOPICO===" no início exato da resposta.
- Logo abaixo, insira o Título do Tópico preservando sua tag de '(Tempo Estimado: X min)'.
- Em seguida, expanda a explicação teórica do tópico e liste suas doutrinas, autores ou leis aplicáveis.
"""),
        ("human", "Expanda o seguinte bloco de tópico do mapa estrutural, pesquisando detalhes e exemplos pertinentes: \n\n{topic_chunk}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=3)
    
    try:
        response = await agent_executor.ainvoke({
            "topic_chunk": topic_chunk,
            "nivel_escolaridade": inputs.get("nivel_escolaridade"),
            "materia": inputs.get("materia")
        })
        return response["output"]
    except Exception as e:
        return f"===NOVO_TOPICO===\nErro ao pesquisar tópico: {topic_chunk}\nErro: {str(e)}"

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
            # Qualquer linha como "  - Assunto (Tempo..." inicia um tópico principal
            if re.match(r'^\s*-\s+.*Tempo Estimado', line) or line.strip().startswith("- ") and "Tempo Estimado" in line:
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
