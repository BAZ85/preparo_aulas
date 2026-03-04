import io
import markdown
from htmldocx import HtmlToDocx
from docx import Document

def markdown_to_docx(md_text: str) -> io.BytesIO:
    """
    Converts markdown text to a DOCX bytes stream, 
    so it can be directly downloaded in Streamlit.
    """
    # Convert Markdown to HTML
    # We use some extensions to ensure tables, line breaks, and lists render properly
    html = markdown.markdown(md_text, extensions=['extra', 'nl2br', 'sane_lists'])
    
    # Create an empty Word Document
    document = Document()
    
    # Initialize the converter
    new_parser = HtmlToDocx()
    
    # Parse HTML and append to document
    new_parser.add_html_to_document(html, document)
    
    # Save the document to an in-memory byte buffer
    docx_io = io.BytesIO()
    document.save(docx_io)
    docx_io.seek(0)
    
    return docx_io
