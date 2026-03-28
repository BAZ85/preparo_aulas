import io

def generate_reveal_html(markdown_content: str, bg_image_base64: str = None) -> str:
    """
    Injeta o markdown dentro do template padrão do Reveal.js (carregado de CDN)
    Usa tema simples (claro/preto) com opção de imagem de fundo com overlay semi-transparente.
    """
    bg_style = ""
    if bg_image_base64:
        bg_style = f"""
        .reveal {{
            background-image: url('{bg_image_base64}');
            background-size: cover;
            background-position: center;
        }}
        .reveal .slides section {{
            background: rgba(255, 255, 255, 0.88);
            padding: 40px !important;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            color: #000;
        }}
        """

    html_template = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

    <title>Apresentação de Aula</title>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reset.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/theme/simple.min.css" id="theme">

    <style>
        {bg_style}
        .reveal h1, .reveal h2, .reveal h3 {{
            text-transform: none; /* Mantém maiúsculas/minúsculas naturais */
        }}
        .reveal img {{
            max-height: 400px; /* Limita altura para não estourar o slide */
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}
        .reveal ul {{
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <section data-markdown data-separator="^---$" data-separator-notes="^Note:">
                <textarea data-template>
{markdown_content}
                </textarea>
            </section>
        </div>
    </div>

    <!-- Bibliotecas JS do Reveal -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/markdown/markdown.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/notes/notes.js"></script>

    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: true,
            center: true,
            margin: 0.1,
            minScale: 0.2,
            maxScale: 1.5,
            plugins: [ RevealMarkdown, RevealNotes ]
        }});
    </script>
</body>
</html>
"""
    return html_template
