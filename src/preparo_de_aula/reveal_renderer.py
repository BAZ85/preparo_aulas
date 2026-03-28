import io

def generate_reveal_html(markdown_content: str, custom_template_html: str = None) -> str:
    """
    Injeta o markdown dentro do template padrão do Reveal.js (ou em um template HTML customizado).
    Procura pela tag {{SLIDES_AQUI}} no template customizado para aplicar o bloco de slides.
    """
    reveal_head = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reset.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/theme/simple.min.css" id="theme">
    <style>
        .reveal h1, .reveal h2, .reveal h3 { text-transform: none !important; }
        .reveal h1 { font-size: 2.5em; margin-bottom: 20px; }
        .reveal h2 { font-size: 1.8em; margin-bottom: 20px; }
        .reveal p, .reveal li { font-size: 1.1em; line-height: 1.4; color: #111; }
        .reveal img { max-height: 400px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .reveal-viewport { background: transparent !important; }
        .reveal .slides section { background: transparent; padding: 20px; box-sizing: border-box; }
    </style>
    """

    reveal_body = f"""
    <div class="reveal" style="width: 100%; height: 100%;">
        <div class="slides">
            <section data-markdown data-separator="^---$" data-separator-notes="^Note:">
                <textarea data-template>
{markdown_content}
                </textarea>
            </section>
        </div>
    </div>
    """

    reveal_scripts = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/markdown/markdown.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/notes/notes.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            slideNumber: true,
            center: true,
            width: 1024,
            height: 768,
            margin: 0.1,
            minScale: 0.2,
            maxScale: 1.2,
            backgroundTransition: 'none',
            plugins: [ RevealMarkdown, RevealNotes ]
        });
    </script>
    """

    if custom_template_html:
        tpl = custom_template_html
        
        # Inject head before </head>
        if "</head>" in tpl:
            tpl = tpl.replace("</head>", reveal_head + "\n</head>")
        else:
            tpl = reveal_head + "\n" + tpl
            
        # Inject slide body in placeholder
        if "{{SLIDES_AQUI}}" in tpl:
            tpl = tpl.replace("{{SLIDES_AQUI}}", reveal_body)
        elif "</body>" in tpl:
            tpl = tpl.replace("</body>", reveal_body + "\n</body>")
        else:
            tpl += "\n" + reveal_body
            
        # Inject scripts before </body>
        if "</body>" in tpl:
            tpl = tpl.replace("</body>", reveal_scripts + "\n</body>")
        else:
            tpl += "\n" + reveal_scripts
            
        return tpl
    else:
        # Fallback padrão (Fundo branco simples)
        return f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Apresentação de Aula</title>
    {reveal_head}
    <style>
        .reveal .slides section {{
            background: #ffffff;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    {reveal_body}
    {reveal_scripts}
</body>
</html>
"""
