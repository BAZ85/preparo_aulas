#!/usr/import sys
import sys
import warnings
import asyncio
from datetime import datetime

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Import the new Langchain-based pipeline instead of CrewAI
from preparo_de_aula.extractors import extract_content
from preparo_de_aula.langchain_pipeline import generate_structural_map, research_topics_parallel

def run_crew(inputs: dict):
    """
    Orquestra o novo Pipeline baseado em Langchain e Paralelismo Assíncrono.
    """
    try:
        import litellm
        
        arquivo_ou_url = inputs.get('arquivo_ou_url', '')
        
        print("Iniciando Fase 0 (Extração de Conteúdo Base Nativo)...")
        conteudo_base = extract_content(arquivo_ou_url)
        
        print("Iniciando Fase 1 (Construção do Mapa Estrutural via LCEL)...")
        structural_map = generate_structural_map(conteudo_base, inputs)
        
        print("Iniciando Fase 2 (Pesquisa Direcionada Paralela no Langchain)...")
        # Roda o AgentExecutor paralelamente
        documento_expandido = asyncio.run(research_topics_parallel(structural_map, inputs))
        
        print("Iniciando Fase 3 (Map-Reduce Simultâneo do Roteiro via Claude 3.5 Sonnet)...")
        chunks = documento_expandido.split("===NOVO_TOPICO===")
        
        roteiro_final = f"# Roteiro de Aula: {inputs.get('assunto', '')} - {inputs.get('materia', '')}\n\n"
        roteiro_final += f"**Nível:** {inputs.get('nivel_escolaridade', '')}\n"
        roteiro_final += f"**Duração Total:** {inputs.get('duracao', '')} minutos\n\n"
        
        valid_chunks = [c.strip() for c in chunks if len(c.strip()) > 50]
        
        if not valid_chunks:
            # Fallback seguro caso não haja quebras por algum motivo de geração
            valid_chunks = [documento_expandido]
            
        async def fetch_claude_chunk(chunk, i, total):
            print(f"  -> Disparando thread {i+1}/{total} do Claude...")
            sys_prompt = f"""Você é um Coordenador Pedagógico altamente qualificado.
Sua tarefa é escrever UMA PARTE de um roteiro de aula (apenas sobre o tópico fornecido) seguindo estas regras:
- Conteúdo Teórico Objetivo e Focado
- Referências e Autores Essenciais
- Exemplos Práticos
- Base Jurídica (se houver no texto, incorporar na explicação de forma concisa)

A aula total é sobre o assunto '{inputs.get('assunto')}' ({inputs.get('materia')}) e os alunos são especificamente do nível {inputs.get('nivel_escolaridade')}. A duração total é de {inputs.get('duracao')} minutos.
O texto que você receberá contém uma indicação de "Tempo Estimado" para o tópico. Você DEVE adequar rigorosamente o volume de texto e a densidade da explicação para que correspondam de forma realista a esse tempo de exposição oral.
A sua resposta DEVE estar em formato de aula expositiva, possuir linguagem totalmente adaptada ao linguajar esperado de alunos do nível {inputs.get('nivel_escolaridade')}. Seja sucinto, evite floreios, repetições, ou longas divagações. Vá direto ao ponto!
Inicie a sua resposta destacando esse tempo estimado logo abaixo do subtítulo (ex: ## Tópico\n**Tempo Estimado:** X min).
Retorne APENAS o texto Markdown formatado da sua parte, começando sempre com um subtítulo (##). Nunca inclua saudações ou introduções suas."""
            
            response = await litellm.acompletion(
                model="anthropic/claude-sonnet-4-6", # Fallback for Sonnet
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"Escreva a seção do plano de aula EXCLUSIVAMENTE para o seguinte conteúdo mapeado abaixo:\n\n{chunk}"}
                ],
                max_tokens=8192
            )
            return response.choices[0].message.content + "\n\n---\n\n"

        async def process_all_chunks(chunk_list):
            tasks = [fetch_claude_chunk(c, i, len(chunk_list)) for i, c in enumerate(chunk_list)]
            return await asyncio.gather(*tasks)
            
        print(f"Injetando {len(valid_chunks)} blocos paralelamente no Anthropic API...")
        results = asyncio.run(process_all_chunks(valid_chunks))
        
        for r in results:
            roteiro_final += r

        with open('roteiro_de_aula.md', 'w', encoding='utf-8') as f:
            f.write(roteiro_final)
            
        return roteiro_final
    except Exception as e:
        raise Exception(f"An error occurred while running the Langchain pipeline: {e}")

def run():
    inputs = {
        'nivel_escolaridade': 'Ensino Médio',
        'materia': 'História',
        'assunto': 'Revolução Francesa',
        'duracao': '50',
    }
    run_crew(inputs)

def train():
    pass

def replay():
    pass

def test():
    pass

def run_with_trigger():
    pass
