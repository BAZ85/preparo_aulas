import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import PDFSearchTool, DOCXSearchTool, ScrapeWebsiteTool, YoutubeVideoSearchTool
from google import genai
import time
from duckduckgo_search import DDGS

# --- Setup Custom Tools ---

@tool("Pesquisa na Internet")
def duckduckgo_search(query: str) -> str:
    """Busca informações atuais na internet para o termo pesquisado."""
    try:
        results = DDGS().text(query, max_results=5)
        res_list = list(results)
        if not res_list:
            return "Nenhum resultado encontrado."
        return "\\n".join([f"- {r.get('title', '')}: {r.get('body', '')} ({r.get('href', '')})" for r in res_list])
    except Exception as e:
        return f"Erro na pesquisa: {str(e)}"

@tool("Analisar Arquivo de Video")
def analyze_video_tool(video_path: str, prompt: str = "Extraia os temas, conceitos teóricos e informações cruciais deste vídeo para base de uma aula.") -> str:
    """
    Ferramenta para analisar e extrair texto de arquivos de vídeo locais (MP4, etc) enviados.
    O 'video_path' deve ser o caminho absoluto do arquivo no disco.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Erro: GEMINI_API_KEY não encontrada."
    
    try:
        client = genai.Client(api_key=api_key)
        # Uploading video to GenAI API
        uploaded_file = client.files.upload(file=video_path)
        
        # Wait until processing is complete
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(5)
            uploaded_file = client.files.get(name=uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            return "Erro ao processar o vídeo na API do Gemini."
            
        print(f"Vídeo processado. Gerando conteúdo via Gemini 1.5 Pro...")
        response = client.models.generate_content(
             model='gemini-1.5-pro',
             contents=[uploaded_file, prompt]
        )
        
        # Opcional: deletar arquivo após o uso
        client.files.delete(name=uploaded_file.name)
        return response.text
    except Exception as e:
        return f"Erro na análise do vídeo: {str(e)}"

# --- Define Crew ---
@CrewBase
class PreparoDeAula():
    """PreparoDeAula crew"""

    @agent
    def document_analyst(self) -> Agent:
        # GPT-4o-mini is fine for NLP, but since Document Analyst needs large context, we can use Gemini 1.5 Pro here as well. Let's use gpt-4o-mini as requested for NLP, except for video which uses the custom Gemini tool.
        # However, to process large PDFs, Gemini 1.5 Pro or GPT-4o-mini can be used. We'll use GPT-4o-mini for the agent.
        llm = LLM(model="gpt-4o-mini")
        return Agent(
            config=self.agents_config['document_analyst'],
            verbose=True,
            llm=llm,
            tools=[PDFSearchTool(), DOCXSearchTool(), ScrapeWebsiteTool(), YoutubeVideoSearchTool(), analyze_video_tool]
        )

    @agent
    def researcher(self) -> Agent:
        llm = LLM(model="gpt-4o-mini")
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            llm=llm,
            tools=[duckduckgo_search]
        )

    @agent
    def lesson_planner(self) -> Agent:
        llm = LLM(model="gpt-4o-mini")
        return Agent(
            config=self.agents_config['lesson_planner'],
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

    @task
    def analyze_documents_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_documents_task']
        )

    @task
    def research_topic_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_topic_task']
        )

    @task
    def create_lesson_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_lesson_plan_task'],
            output_file='roteiro_de_aula.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
