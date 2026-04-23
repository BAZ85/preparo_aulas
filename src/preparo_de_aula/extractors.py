import os
import re
from urllib.parse import urlparse, parse_qs
from pypdf import PdfReader
import docx
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
import time
import requests
from bs4 import BeautifulSoup

def extract_content(sources) -> str:
    """
    Dado o caminho de um arquivo local, uma URL, ou uma lista deles, extrai todo seu conteúdo em texto de forma nativa e rápida.
    """
    if isinstance(sources, str):
        sources = [sources]
        
    all_content = []
    for source in sources:
        if "Nenhum material de referência fornecido" in source:
            all_content.append(source)
            continue

        if source.startswith("http"):
            all_content.append(_extract_from_url(source))
        else:
            all_content.append(_extract_from_file(source))
            
    return "\n\n=== PRÓXIMO MATERIAL ===\n\n".join(all_content)

def _extract_from_url(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return _extract_youtube_transcript(url)
    
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return f"Erro ao acessar a URL {url}: {str(e)}"

def _extract_youtube_transcript(url: str) -> str:
    try:
        parsed = urlparse(url)
        video_id = ""
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path[1:]
        elif "youtube.com" in parsed.netloc:
            qs = parse_qs(parsed.query)
            video_id = qs.get("v", [""])[0]
        
        if not video_id:
            return "ID do vídeo do YouTube não encontrado."
            
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        return " ".join([t['text'] for t in transcript])
    except Exception as e:
        return f"Erro ao extrair transcrição do YouTube: {str(e)}"

def _extract_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"Arquivo '{file_path}' não encontrado. O analista pesquisará do zero."
        
    ext = file_path.lower().split('.')[-1]
    
    try:
        if ext == 'pdf':
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['doc', 'docx']:
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in ['mp4', 'mkv', 'avi', 'mov']:
            return _analyze_video_with_gemini(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"Erro ao extrair conteúdo do arquivo {file_path}: {str(e)}"

def _analyze_video_with_gemini(video_path: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Erro: GEMINI_API_KEY não encontrada."
        
    try:
        client = genai.Client(api_key=api_key)
        uploaded_file = client.files.upload(file=video_path)
        
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(5)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            return "Erro ao processar o vídeo na API do Gemini."
            
        response = client.models.generate_content(
             model='gemini-1.5-pro',
             contents=[uploaded_file, "Faça uma transcrição e extraia todos os temas, princípios e conceitos fundamentais do vídeo."]
        )
        
        client.files.delete(name=uploaded_file.name)
        return response.text
    except Exception as e:
        return f"Erro na análise do vídeo: {str(e)}"
