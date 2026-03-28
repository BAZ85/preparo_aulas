import streamlit as st
import os
import tempfile
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Disable OpenTelemetry from CrewAI to prevent threading errors in Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"

# Ensure the src directory is in the path so we can import preparo_de_aula
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from preparo_de_aula.main import run_crew
from preparo_de_aula.export_utils import markdown_to_docx
from preparo_de_aula.extractors import extract_content
from preparo_de_aula.slides_pipeline import generate_reveal_markdown
from preparo_de_aula.reveal_renderer import generate_reveal_html
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Preparo de Aula com IA", page_icon="📚", layout="wide")

st.title("📚 Mestre: Seu Assistente de Plano de Aula e Slides")
st.markdown("Crie roteiros de aula detalhados ou gere slides automaticamente usando Inteligência Artificial.")

modo = st.radio("O que você deseja fazer?", ["Gerar Roteiro de Aula", "Gerar Slides"], horizontal=True)
st.markdown("---")

def save_uploaded_template(uploaded_file):
    if not uploaded_file:
        return None
    temp_dir = tempfile.gettempdir()
    t_path = os.path.join(temp_dir, f"template_{uploaded_file.name}")
    with open(t_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return t_path

if modo == "Gerar Roteiro de Aula":
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

    if submit:
        if not materia or not assunto:
            st.error("Por favor, preencha a Matéria e o Assunto.")
            st.stop()
            
        with st.spinner("🚀 Analisando materiais, pesquisando na internet e montando o roteiro... Isso pode levar alguns minutos."):
            file_path = ""
            if uploaded_file is not None:
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            elif reference_url:
                file_path = reference_url

            inputs = {
                'nivel_escolaridade': nivel,
                'materia': materia,
                'assunto': assunto,
                'duracao': str(duracao),
                'arquivo_ou_url': file_path or "(Nenhum material de referência fornecido. O agente deverá pesquisar do zero.)"
            }
            
            try:
                result = run_crew(inputs)
                if os.path.exists('roteiro_de_aula.md'):
                    with open('roteiro_de_aula.md', 'r', encoding='utf-8') as f:
                        final_markdown = f.read()
                else:
                    final_markdown = str(result)
                    
                st.session_state['last_roteiro'] = final_markdown
                st.session_state['last_inputs'] = inputs
                # Limpa eventuais slides anteriores caso regenere o roteiro
                if 'last_html' in st.session_state:
                    del st.session_state['last_html']
                    
                st.success("✨ Roteiro gerado com sucesso!")
            except Exception as e:
                st.error(f"Ocorreu um erro durante a execução: {str(e)}")

    if st.session_state.get('last_roteiro'):
        st.markdown("---")
        st.header("3. Resultado: Roteiro de Aula")
        result_container = st.container()
        
        with result_container:
            st.markdown(st.session_state['last_roteiro'])
            st.markdown("---")
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                st.download_button(
                    label="📄 Baixar Roteiro (.md)",
                    data=st.session_state['last_roteiro'],
                    file_name=f"roteiro_{st.session_state['last_inputs'].get('assunto', 'aula').replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with col_btn2:
                try:
                    docx_file = markdown_to_docx(st.session_state['last_roteiro'])
                    st.download_button(
                        label="📄 Baixar Roteiro (.docx)",
                        data=docx_file,
                        file_name=f"roteiro_{st.session_state['last_inputs'].get('assunto', 'aula').replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as docx_err:
                    st.error(f"Erro ao gerar DOCX: {docx_err}")
            with col_btn3:
                tpl_html_r = st.file_uploader("Template Visual HTML (Opcional)", type=['html'], key='tpl_r')
                if st.button("🎬 Criar Rascunho da Apresentação Web", type="primary", use_container_width=True):
                    with st.spinner("🚀 Estruturando os tópicos base dos slides..."):
                        try:
                            custom_html_r = None
                            if tpl_html_r:
                                custom_html_r = tpl_html_r.getvalue().decode('utf-8', errors='ignore')
                                
                            markdown_slides = asyncio.run(generate_reveal_markdown(
                                st.session_state['last_roteiro'], 
                                st.session_state['last_inputs']
                            ))
                            st.session_state['draft_markdown_r'] = markdown_slides
                            st.session_state['custom_html_r'] = custom_html_r
                            st.success("Rascunho criado! Revise abaixo:")
                        except Exception as e:
                            st.error(f"Erro ao criar rascunho: {e}")
                            
            if 'draft_markdown_r' in st.session_state:
                st.markdown("---")
                st.subheader("📝 Editor de Rascunho (Copiloto)")
                st.markdown("Ajuste os textos abaixo. Se o slide estiver muito grande, aperte `Enter` e digite `---` em uma linha em branco para criar um novo slide.")
                edited_md = st.text_area("Markdown dos Slides", value=st.session_state['draft_markdown_r'], height=400, key="editor_r")
                
                if st.button("✨ Confirmar e Renderizar Design", type="primary", use_container_width=True):
                    html_content = generate_reveal_html(edited_md, custom_template_html=st.session_state.get('custom_html_r'))
                    st.session_state['last_html'] = html_content
                    
            if st.session_state.get('last_html'):
                st.download_button(
                    label="⬇️ Baixar Apresentação Web (.html)",
                    data=st.session_state['last_html'],
                    file_name=f"slides_{st.session_state['last_inputs'].get('assunto', 'aula').replace(' ', '_')}.html",
                    mime="text/html",
                    use_container_width=True
                )
                st.markdown("### 🎬 Preview Interativo")
                st.info("💡 Dica de Apresentação: Após baixar e abrir o arquivo `.html` no Chrome, pressione **'F'** para preencher a Tela Cheia, e pressione **'S'** para abrir o Monitor Especial do Orador na outra tela (revelando as anotações do professor).")
                components.html(st.session_state['last_html'], height=600, scrolling=True)

elif modo == "Gerar Slides":
    st.header("Geração de Slides")
    st.markdown("Faça upload de um arquivo de texto, PDF ou DOCX para gerar os slides baseados no conteúdo.")
    
    col1, col2 = st.columns(2)
    with col1:
        nivel_s = st.selectbox("Nível de Escolaridade", ["Ensino Médio", "Graduação", "Pós-Graduação"], index=1, key='n_s')
        materia_s = st.text_input("Matéria", key='m_s')
        assunto_s = st.text_input("Assunto Principal", key='a_s')
    with col2:
        uploaded_s = st.file_uploader("Arquivo Base (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])
        tpl_html_s = st.file_uploader("Template Visual HTML (Opcional)", type=['html'], key='tpl_s')
        
    submit_s = st.button("🎬 Criar Rascunho da Apresentação", type="primary")
    
    if submit_s:
        if not materia_s or not assunto_s:
            st.error("Preencha matéria e assunto!")
            st.stop()
        if not uploaded_s:
            st.error("Forneça um arquivo como base para os slides.")
            st.stop()
            
        with st.spinner("🚀 Lendo documento e estruturando rascunho base..."):
            try:
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, uploaded_s.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_s.getbuffer())
                    
                content = extract_content(file_path)
                
                if not content or len(content) < 50:
                    st.error("Não foi possível extrair conteúdo suficiente do arquivo indicado.")
                    st.stop()
                    
                inputs_s = {
                    'nivel_escolaridade': nivel_s,
                    'materia': materia_s,
                    'assunto': assunto_s
                }
                
                custom_html_s = None
                if tpl_html_s:
                    custom_html_s = tpl_html_s.getvalue().decode('utf-8', errors='ignore')
                
                markdown_slides = asyncio.run(generate_reveal_markdown(content, inputs_s))
                
                st.session_state['draft_markdown_s'] = markdown_slides
                st.session_state['custom_html_s'] = custom_html_s
                st.session_state['assunto_s_cache'] = assunto_s
                st.success("✨ Rascunho concebido! Revise o texto abaixo.")
            except Exception as e:
                st.error(f"Erro na geração do rascunho: {e}")

    if 'draft_markdown_s' in st.session_state:
        st.markdown("---")
        st.subheader("📝 Editor de Rascunho (Copiloto)")
        st.markdown("Ajuste os textos abaixo. Se o slide estiver muito grande, aperte `Enter` e digite `---` em uma linha em branco para criar um novo slide.")
        edited_md_s = st.text_area("Markdown dos Slides", value=st.session_state['draft_markdown_s'], height=400, key="editor_s")
        
        if st.button("✨ Confirmar e Renderizar Design", type="primary", use_container_width=True):
            html_content = generate_reveal_html(edited_md_s, custom_template_html=st.session_state.get('custom_html_s'))
            st.session_state['final_html_s'] = html_content
            
    if st.session_state.get('final_html_s'):
        st.download_button(
            label="🎬 Baixar Apresentação Web (.html)",
            data=st.session_state['final_html_s'],
            file_name=f"slides_{st.session_state.get('assunto_s_cache', 'aula').replace(' ', '_')}.html",
            mime="text/html",
            use_container_width=True
        )
        st.markdown("### 🎬 Preview Interativo")
        st.info("💡 Dica de Apresentação: Após baixar e abrir o arquivo `.html` no Chrome, pressione **'F'** para preencher a Tela Cheia, e pressione **'S'** para abrir o Monitor Especial do Orador na outra tela (revelando as anotações do professor).")
        components.html(st.session_state['final_html_s'], height=600, scrolling=True)
