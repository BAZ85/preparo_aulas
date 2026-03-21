import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import PDFSearchTool, DOCXSearchTool, ScrapeWebsiteTool, YoutubeVideoSearchTool
from google import genai
import time
from duckduckgo_search import DDGS

# --- Setup Custom Tools ---
@tool("Ler Arquivo Completo")
def read_full_file_tool(file_path: str) -> str:
    """Ferramenta para extrair TODO o texto de um arquivo local (PDF, DOCX, TXT). Obrigatório passar o caminho do arquivo."""
    try:
        ext = file_path.lower().split('.')[-1]
        if ext == 'pdf':
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext == 'docx':
            import docx
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return "Formato não suportado por esta ferramenta local."
    except Exception as e:
        return f"Erro ao ler o arquivo: {str(e)}"


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
            
        print(f"Vídeo processado. Gerando conteúdo via Gemini 3.1 Pro...")
        response = client.models.generate_content(
             model='gemini-3.1-pro-preview',
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
        llm = LLM(model="gemini/gemini-3.1-pro-preview", max_tokens=8192)
        return Agent(
            config=self.agents_config['document_analyst'],
            verbose=True,
            llm=llm,
            tools=[read_full_file_tool, ScrapeWebsiteTool(), YoutubeVideoSearchTool(), analyze_video_tool]
        )

    @agent
    def researcher(self) -> Agent:
        llm = LLM(model="gemini/gemini-3.1-pro-preview", max_tokens=8192)
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            llm=llm,
            tools=[duckduckgo_search]
        )

    # O lesson_planner foi removido do Crew Sequencial para atuar de forma nativa/direta (Map-Reduce)
    # @agent
    # def lesson_planner(self) -> Agent:
    #     llm = LLM(model="anthropic/claude-sonnet-4-6", max_tokens=8192)
    #     return Agent(

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

    # A tarefa 3 foi removida do Crew Sequencial para atuar nativamente no main.py
    # @task
    # def create_lesson_plan_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['create_lesson_plan_task'],
    #         output_file='roteiro_de_aula.md'
    #     )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
