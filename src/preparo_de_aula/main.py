#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from preparo_de_aula.crew import PreparoDeAula

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run_crew(inputs: dict):
    """
    Run the crew dynamically with user provided inputs.
    """
    try:
        from litellm import completion
        
        print("Iniciando Fases 1 e 2 (Extração e Pesquisa)...")
        # Roda apenas as tarefas 1 e 2 (pois a 3 foi removida do crew.py)
        research_result = PreparoDeAula().crew().kickoff(inputs=inputs)
        documento_expandido = str(research_result)
        
        print("Iniciando Fase 3 (Map-Reduce do Roteiro)...")
        # Divide o documento gigante usando o delimitador inserido pela Fase 2
        chunks = documento_expandido.split("===NOVO_TOPICO===")
        
        roteiro_final = f"# Roteiro de Aula: {inputs.get('assunto', '')} - {inputs.get('materia', '')}\n\n"
        roteiro_final += f"**Nível:** {inputs.get('nivel_escolaridade', '')}\n"
        roteiro_final += f"**Duração Total:** {inputs.get('duracao', '')} minutos\n\n"
        
        # O primeiro chunk pode ser texto solto ou vazio antes do 1º delimitador
        valid_chunks = [c.strip() for c in chunks if len(c.strip()) > 50]
        
        for i, chunk in enumerate(valid_chunks):
            print(f"Gerando parte {i+1} de {len(valid_chunks)} do roteiro via Claude...")
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
            
            response = completion(
                model="anthropic/claude-sonnet-4-6",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"Escreva a seção do plano de aula EXCLUSIVAMENTE para o seguinte conteúdo mapeado abaixo:\n\n{chunk}"}
                ],
                max_tokens=8192
            )
            roteiro_final += response.choices[0].message.content + "\n\n---\n\n"
        
        # Salvar o arquivo final e devolver para o Streamlit ler (mesmo comportamento anterior)
        with open('roteiro_de_aula.md', 'w', encoding='utf-8') as f:
            f.write(roteiro_final)
            
        return roteiro_final
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def run():
    """
    Run the crew from CLI.
    """
    inputs = {
        'nivel_escolaridade': 'Ensino Médio',
        'materia': 'História',
        'assunto': 'Revolução Francesa',
        'duracao': '50',
    }

    try:
        PreparoDeAula().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        PreparoDeAula().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        PreparoDeAula().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        PreparoDeAula().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = PreparoDeAula().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
