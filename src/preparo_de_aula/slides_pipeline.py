import json
import io
import litellm
import asyncio
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

async def generate_reveal_markdown(content: str, inputs: dict) -> str:
    """Gera o Markdown puro, estilizado para uso no ecossistema web Reveal.js"""
    sys_prompt = f"""Você é um Especialista em Apresentações e Professor de {inputs.get('materia')}.
Sua tarefa é criar uma estrutura de slides a partir do conteúdo fornecido.
Os slides serão voltados para alunos do nível: {inputs.get('nivel_escolaridade')}.
Assunto da Apresentação: {inputs.get('assunto')}

Regras ESTRITAS para os slides em Markdown (Reveal.js):
1. Separe cada slide com exatamente TRÊS hifens "---", garantindo pular uma linha antes e depois de "---".
2. Use "## Titulo" sempre com um Emoji legal no cabeçalho do slide.
3. REGRA CRÍTICA DE TAMANHO (ANTI-OVERFLOW): O slide visual deve ser EXTREMAMENTE minimalista, apenas palavras-chave (máximo Absoluto de 3 a 5 bullet points curtíssimos). Se o tema do slide render muito assunto, É OBRIGATÓRIO quebrar o conteúdo em múltiplos slides, repetindo o título e adicionando " (Cont.)". NUNCA escreva parágrafos densos no bloco visual.
4. Todo o roteiro pesado e detalhado que o professor irá Falar deve ir APENAS para as anotações secretas do orador. Coloque-se no final do slide, usando estritamente a palavra mágica 'Note:'.

Exemplo RIGOROSO:
## 📜 Origens Históricas

- Ocorreu na Roma Antiga
- Separação entre poderes
- Influência até os dias de hoje

Note:
O professor deve explicar aqui as nuances do direito romano...

---

## 🏛️ Tribunais Modernos
...
"""
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-6",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Conteúdo Base:\n\n{content}"}
        ],
        max_tokens=8192,
        temperature=0.4
    )
    
    return response.choices[0].message.content.strip()

async def generate_slides_from_content(content: str, inputs: dict) -> list[dict]:
    sys_prompt = f"""Você é um Especialista em Apresentações e Professor de {inputs.get('materia')}.
Sua tarefa é criar uma estrutura de slides a partir do conteúdo fornecido.
Os slides serão voltados para alunos do nível: {inputs.get('nivel_escolaridade')}.
Assunto da Apresentação: {inputs.get('assunto')}

Regras para os slides:
1. Resuma o conteúdo do roteiro de forma didática, distribuindo em quantos slides forem necessários para não amontoar texto.
2. Cada slide deve ter um título claro e curto.
3. REGRA CRÍTICA PARA O CONTEÚDO: O conteúdo principal no slide deve ser EXTREMAMENTE minimalista. Use no máximo 3 a 4 tópicos por slide e JAMAIS ultrapasse 15 palavras por tópico. NUNCA escreva parágrafos longos no bloco CONTEUDO.
4. Coloque toda a explicação densa, detalhes técnicos e exemplos na sessão NOTAS_DO_ORADOR. O slide visual serve apenas de âncora invisível.
5. Retorne os slides ESTRITAMENTE no formato Markdown abaixo. Separe cada slide com exatamente três hifens "---".

Formato Exigido:
---
TITULO: Título do Slide 1
CONTEUDO:
- Ponto 1
- Ponto 2
NOTAS_DO_ORADOR:
O professor deve enfatizar aqui que...
---
TITULO: Título do Slide 2
...
"""
    
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-6",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Conteúdo Base:\n\n{content}"}
        ],
        max_tokens=8192,
        temperature=0.3
    )
    
    text_response = response.choices[0].message.content.strip()
    
    slides_data = []
    blocks = text_response.split('---')
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        titulo = "Slide"
        conteudos = []
        notas = ""
        
        lines = block.split('\n')
        current_section = None
        for line in lines:
            if line.startswith('TITULO:'):
                titulo = line.replace('TITULO:', '').strip()
            elif line.startswith('CONTEUDO:'):
                current_section = 'conteudo'
            elif line.startswith('NOTAS_DO_ORADOR:'):
                current_section = 'notas'
            else:
                if current_section == 'conteudo' and line.strip().startswith('-'):
                    conteudos.append(line.strip()[1:].strip())
                elif current_section == 'notas':
                    notas += line + "\n"
                    
        if conteudos or titulo != "Slide":
            slides_data.append({
                "titulo": titulo,
                "conteudo": conteudos,
                "notas_do_orador": notas.strip()
            })
            
    if not slides_data:
        raise Exception("Nenhum slide pôde ser gerado. O Claude não retornou o formato esperado.")
        
    return slides_data

def create_pptx_from_data(slides_data: list[dict], subject: str, template_path: str = None) -> io.BytesIO:
    prs = None
    if template_path and os.path.exists(template_path):
        try:
            prs = Presentation(template_path)
            # Fallback if the user uploaded an empty presentation with no layouts
            if len(prs.slide_layouts) == 0:
                prs = Presentation()
        except:
            prs = Presentation()
    else:
        prs = Presentation()
        
    # Limpar slides antigos de forma segura (evita corromper arquivo no PowerPoint)
    if len(prs.slides) > 0:
        xml_slides = prs.slides._sldIdLst
        slides = list(xml_slides)
        for s in slides:
            # Buscar a relação para apagá-la junto com o XML, prevenindo PPTX corrompido
            rId = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            if not rId:
                rId = s.get('id')
            if rId:
                prs.part.drop_rel(rId)
            xml_slides.remove(s)
    
    # Seleção Robusta de Layouts Mestre
    title_slide_layout = prs.slide_layouts[0]
    bullet_slide_layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
    
    # Criar slide de capa
    slide = prs.slides.add_slide(title_slide_layout)
    title_shape = None
    try:
        title_shape = slide.shapes.title
    except KeyError:
        pass
        
    if not title_shape and len(slide.placeholders) > 0:
        # Se não tem shape de título oficial, usa o primeiro placeholder disponível
        for shape in slide.placeholders:
            title_shape = shape
            break
        
    if title_shape and hasattr(title_shape, "text"):
        title_shape.text = subject
    
    # Adicionar o subtítulo no segundo placeholder, caso exista
    if len(slide.placeholders) > 1:
        # Pega qualquer placeholder que não seja o título principal para servir de subtítulo
        for shape in slide.placeholders:
            if shape != title_shape and hasattr(shape, "text"):
                shape.text = "Apresentação de Aula"
                break
                
    from pptx.dml.color import RGBColor
    
    for slide_data in slides_data:
        slide = prs.slides.add_slide(bullet_slide_layout)
        shapes = slide.shapes
        
        # Inserir o Título do Slide
        slide_title_shape = None
        try:
            slide_title_shape = shapes.title
        except KeyError:
            pass
            
        if not slide_title_shape and len(shapes.placeholders) > 0:
            for shape in shapes.placeholders:
                slide_title_shape = shape
                break
            
        if slide_title_shape and hasattr(slide_title_shape, "text"):
            slide_title_shape.text = slide_data.get("titulo", "Slide")
        
        # Encontrar um "Body Placeholder" confiável pra escrever
        body_shape = None
        for shape in shapes.placeholders:
            # Type 2 é PP_PLACEHOLDER.BODY, Type 7 é OBJECT (frequentemente body text)
            if shape != slide_title_shape and hasattr(shape, "placeholder_format") and shape.placeholder_format.type in (2, 7):
                body_shape = shape
                break
                
        # Fallback 1: se não achou pelo Type 2 / 7, pega qualquer placeholder que não seja o título
        if not body_shape:
            for shape in shapes.placeholders:
                if shape != slide_title_shape and hasattr(shape, "text_frame"):
                    body_shape = shape
                    break
        
        conteudos = slide_data.get("conteudo", [])
        if isinstance(conteudos, str):
            conteudos = [conteudos]
                
        # Se encontrou um placeholder válido de conteúdo na formatação Mestre
        if body_shape and hasattr(body_shape, "text_frame"):
            tf = body_shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            for point in conteudos:
                p = tf.add_paragraph()
                p.text = str(point)
                p.level = 0
                p.font.size = Pt(24)
        else:
            # Fallback 2: O slide mestre é 100% em branco. Cria uma caixa de texto "na mão".
            txBox = shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4.5))
            tf = txBox.text_frame
            tf.word_wrap = True
            for point in conteudos:
                p = tf.add_paragraph()
                p.text = str(point)
                p.level = 0
                p.font.size = Pt(24)
                p.font.color.rgb = RGBColor(0, 0, 0)
            
        # Adicionar notas do orador (somente para quem estiver apresentando)
        if slide.has_notes_slide:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = slide_data.get("notas_do_orador", "")
            
    ppt_stream = io.BytesIO()
    prs.save(ppt_stream)
    ppt_stream.seek(0)
    
    return ppt_stream
