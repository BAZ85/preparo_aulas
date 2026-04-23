import os
import tempfile
import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from preparo_de_aula.main import run_crew
from preparo_de_aula.slides_pipeline import generate_reveal_markdown
from preparo_de_aula.reveal_renderer import generate_reveal_html
from preparo_de_aula.extractors import extract_content
from preparo_de_aula.export_utils import markdown_to_docx

app = FastAPI(title="Preparo de Aula API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # No deploy, alteramos para a exata URL da Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "FastAPI rodando a todo vapor!"}

@app.post("/api/roteiro/gerar")
async def gerar_roteiro_api(
    materia: str = Form(...),
    assunto: str = Form(...),
    nivel_escolaridade: str = Form(...),
    duracao: int = Form(...),
    reference_url: Optional[str] = Form(None),
    arquivos: Optional[List[UploadFile]] = File(None)
):
    """Gera o Roteiro via LangChain Pipeline."""
    try:
        file_paths = []
        if arquivos:
            temp_dir = tempfile.gettempdir()
            for uf in arquivos:
                if uf.filename:
                    unique_filename = f"{uuid.uuid4()}_{uf.filename}"
                    path = os.path.join(temp_dir, unique_filename)
                    with open(path, "wb") as f:
                        f.write(await uf.read())
                    file_paths.append(path)
        elif reference_url:
            file_paths.append(reference_url)

        inputs = {
            'nivel_escolaridade': nivel_escolaridade,
            'materia': materia,
            'assunto': assunto,
            'duracao': str(duracao),
            'arquivo_ou_url': file_paths if file_paths else "(Nenhum)"
        }
        
        resultado = await run_crew(inputs)
        
        return {"status": "success", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/slides/rascunho")
async def gerar_slides_rascunho_api(
    materia: str = Form(...),
    assunto: str = Form(...),
    nivel_escolaridade: str = Form(...),
    arquivos: Optional[List[UploadFile]] = File(None),
    roteiro_markdown: Optional[str] = Form(None)
):
    """Cria os Slides Base a partir do Roteiro Gerado ou de Arquivos externos."""
    try:
        inputs = {
            'nivel_escolaridade': nivel_escolaridade,
            'materia': materia,
            'assunto': assunto
        }
        
        content = ""
        if roteiro_markdown:
            content = roteiro_markdown
        elif arquivos:
            temp_dir = tempfile.gettempdir()
            file_paths = []
            for uf in arquivos:
                if uf.filename:
                    unique_filename = f"{uuid.uuid4()}_{uf.filename}"
                    path = os.path.join(temp_dir, unique_filename)
                    with open(path, "wb") as f:
                        f.write(await uf.read())
                    file_paths.append(path)
            content = extract_content(file_paths)
            if not content:
                raise HTTPException(status_code=400, detail="Sem conteúdo.")
        else:
            raise HTTPException(status_code=400, detail="Forneça arquivos ou texto markdown.")

        # A chamada de generate_reveal_markdown já é assíncrona, então damos await direto
        markdown_slides = await generate_reveal_markdown(content, inputs)
        
        return {"status": "success", "markdown_slides": markdown_slides}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarkdownPayload(BaseModel):
    edited_markdown: str

@app.post("/api/export/html")
async def export_html_api(
    edited_markdown: str = Form(...),
    template_arquivo: Optional[UploadFile] = File(None)
):
    """Exporta o HTML de Slides com Template Personalizado via Upload."""
    try:
        custom_html = None
        if template_arquivo and template_arquivo.filename:
            custom_html = (await template_arquivo.read()).decode("utf-8")
            
        html_content = generate_reveal_html(edited_markdown, custom_template_html=custom_html)
        return {"status": "success", "html_content": html_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/docx")
async def export_docx_api(payload: MarkdownPayload):
    """Cria o documento Word baixável com o roteiro de aula finalizado."""
    try:
        docx_io = markdown_to_docx(payload.edited_markdown)
        path = os.path.join(tempfile.gettempdir(), "roteiro_export.docx")
        with open(path, "wb") as f:
            f.write(docx_io.getvalue())
        return FileResponse(path, filename="roteiro_de_aula.docx", 
                            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
