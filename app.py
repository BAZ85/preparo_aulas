import streamlit as st
import os
import tempfile
import sys
from pathlib import Path
from dotenv import load_dotenv

# Disable OpenTelemetry from CrewAI to prevent threading errors in Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"

# Ensure the src directory is in the path so we can import preparo_de_aula
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from preparo_de_aula.main import run_crew
from preparo_de_aula.export_utils import markdown_to_docx

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Preparo de Aula com IA", page_icon="📚", layout="wide")

st.title("📚 Mestre: Seu Assistente de Plano de Aula")
st.markdown("Preencha o formulário abaixo e receba um Roteiro de Aula detalhado criado por uma equipe de Agentes de IA!")

# 2 columns for inputs side-by-side
col1, col2 = st.columns(2)

with col1:
    st.header("1. Informações da Aula")
    nivel = st.selectbox("Nível de Escolaridade", [
        "Ensino Médio", "Graduação", "Pós-Graduação"
    ], index=None, placeholder="Selecione")
    materia = st.text_input("Matéria (ex: Direito Tributário, História)", placeholder="Ex: Direito Tributário")
    assunto = st.text_input("Assunto da Aula", placeholder="Ex: Tributos Diretos")
    duracao = st.number_input("Duração da Aula (minutos)", min_value=10, max_value=300, value=50, step=5)
    
with col2:
    st.header("2. Material de Referência")
    st.markdown("Carregue um arquivo para basear o conteúdo ou defina uma URL.")
    uploaded_file = st.file_uploader("Arquivo (PDF, DOCX, MP4, etc)", type=['pdf', 'docx', 'mp4', 'mkv', 'txt'])
    reference_url = st.text_input("Ou URL de Referência (Artigo, YouTube, etc)", placeholder="https://...")

    submit = st.button("Gerar Roteiro de Aula", type="primary", use_container_width=True)

st.markdown("---")
st.header("3. Resultado: Roteiro de Aula")
result_container = st.container()
    
if submit:
    if not materia or not assunto:
        st.error("Por favor, preencha a Matéria e o Assunto.")
        st.stop()
        
    with st.spinner("🚀 Analisando materiais, pesquisando na internet e montando o roteiro... Isso pode levar alguns minutos."):
        file_path = ""
        
        # Save uploaded file to a temporary location
        if uploaded_file is not None:
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        elif reference_url:
            file_path = reference_url

        # Prepare inputs for Crew
        inputs = {
            'nivel_escolaridade': nivel,
            'materia': materia,
            'assunto': assunto,
            'duracao': str(duracao),
            'arquivo_ou_url': file_path or "(Nenhum material de referência fornecido. O agente deverá pesquisar do zero.)"
        }
        
        try:
            # Run the crew
            result = run_crew(inputs)
            
            # Check if file was saved correctly
            if os.path.exists('roteiro_de_aula.md'):
                with open('roteiro_de_aula.md', 'r', encoding='utf-8') as f:
                    final_markdown = f.read()
            else:
                final_markdown = str(result)
                
            st.success("✨ Roteiro gerado com sucesso!")
            
            with result_container:
                st.markdown("---")
                st.markdown(final_markdown)
                st.markdown("---")
                # Create two adjacent buttons
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    st.download_button(
                        label="📄 Baixar Roteiro (.md)",
                        data=final_markdown,
                        file_name=f"roteiro_{assunto.replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col_btn2:
                    try:
                        docx_file = markdown_to_docx(final_markdown)
                        st.download_button(
                            label="📄 Baixar Roteiro (.docx)",
                            data=docx_file,
                            file_name=f"roteiro_{assunto.replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                    except Exception as docx_err:
                        st.error(f"Erro ao gerar DOCX: {docx_err}")
                
        except Exception as e:
            st.error(f"Ocorreu um erro durante a execução: {str(e)}")
