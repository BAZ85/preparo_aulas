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
Sua tarefa é criar uma estrutura de slides a partir do conteúdo fornecido. Construa slides balanceados que sirvam de guia claro para a aula.
Os slides serão voltados para alunos do nível: {inputs.get('nivel_escolaridade')}.
Assunto da Apresentação: {inputs.get('assunto')}

Regras ESTRITAS para os slides em Markdown (Reveal.js):

1. ESTRUTURA GERAL: O primeiro slide deve obrigatoriamente ser uma 'capa', contendo apenas a matéria e o assunto da aula. O último slide deve ser de agradecimento e conter explicitamente a frase "Até a próxima aula!".
2. Separe cada slide com exatamente TRÊS hifens "---", garantindo pular uma linha antes e depois de "---".
3. Use "## Titulo" sempre com um Emoji legal no cabeçalho do slide.
4. QUANTIDADE DE TÓPICOS: Cada slide (exceto capa/encerramento) deve conter NO MÁXIMO 3 tópicos. NUNCA coloque parágrafos densos no bloco visual. Se o tema for extenso, quebre a explicação em múltiplos slides, repetindo o título e adicionando " (Cont.)".
5. SLIDE VISUAL VS NOTAS DO ORADOR: Cada tópico no slide visual deve ter um destaque e uma *breve explicação* direta (máximo de 10 a 15 palavras por tópico), para guiar o apresentador e os alunos. Já as explicações detalhadas, aprofundamentos teóricos e texto pesado devem ir EXCLUSIVAMENTE para as anotações secretas do orador. Coloque as notas no final do slide, usando estritamente a palavra mágica 'Note:'.

Exemplo RIGOROSO:
## 📜 Origens Históricas

- **Roma Antiga:** O modelo teve suas raízes no direito romano estruturado.
- **Separação de Poderes:** Lançou os alicerces básicos da política atual.
- **Legado Moderno:** Princípios fundamentais que ainda regem o código civil.

Note:
O professor deve explicar aqui as nuances do direito romano, destacando a influência de Justiniano. Aprofundar como as antigas leis não-escritas passaram a ser registradas, detalhando as datas e principais pensadores envolvidos.
---

## 🏛️ Tribunais Modernos
...
"""
    response = await litellm.acompletion(
        model="anthropic/claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Conteúdo Base:\n\n{content}"}
        ],
        max_tokens=8192,
        temperature=0.4
    )
    
    return response.choices[0].message.content.strip()

