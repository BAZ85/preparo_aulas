#!/usr/import sys
import sys
import warnings
import asyncio
from datetime import datetime

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

# Import the new Langchain-based pipeline instead of CrewAI
from preparo_de_aula.extractors import extract_content
from preparo_de_aula.langchain_pipeline import generate_structural_map, research_topics_parallel

async def run_crew(inputs: dict):
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
        documento_expandido = await research_topics_parallel(structural_map, inputs)
        
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
Sua tarefa é redigir UMA PARTE de um roteiro de aula (apenas sobre o tópico fornecido) seguindo estas regras:
- Exposição Teórica Completa e Aprofundada
- Referências, Autores e Base Jurídica (se presentes no material, precisam ser abordados na explicação)
- Exemplos Práticos que reforcem o entendimento profundo do aluno

A aula total é sobre o assunto '{inputs.get('assunto')}' ({inputs.get('materia')}) para alunos do {inputs.get('nivel_escolaridade')}. A duração total é de {inputs.get('duracao')} minutos.
O texto que você receberá contém uma indicação de "Tempo Estimado" para o tópico. O seu grande desafio pedagógico é DEIXAR DE LADO RESUMOS SECOS e redigir um volume textualmente denso, rico e explicativo que *corresponda exatamente à quantidade de material falado compatível com esse tempo*. 
- Se o tópico tem 20 minutos, escreva um roteiro teoricamente expansivo e completo correspondente a 20 minutos de exposição oral!
- A linguagem deve ser adequada ao nível {inputs.get('nivel_escolaridade')}.
Inicie a sua resposta destacando esse tempo estimado logo abaixo do subtítulo (ex: ## Tópico\n**Tempo Estimado:** X min).
Retorne APENAS o texto Markdown formatado da sua parte, começando sempre com um subtítulo (##). Nunca inclua saudações ou explicações iniciais suas."""
            
            response = await litellm.acompletion(
                model="anthropic/claude-3-5-sonnet-20241022",
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
        results = await process_all_chunks(valid_chunks)
        
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
    asyncio.run(run_crew(inputs))

