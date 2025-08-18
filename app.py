# Importa as bibliotecas necessárias
import streamlit as st
import google.generativeai as genai
import requests
import json

# --- Configuração da Página ---
st.set_page_config(
    page_title="CoachAI Espiritual",
    page_icon="🌌",
    layout="wide"
)

# --- Estilos CSS Customizados ---
css = """
/* Fundo com gradiente suave */
[data-testid="stAppViewContainer"] > .main {
    background-image: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* Estilo dos cards de conteúdo */
.content-card {
    background-color: rgba(255, 255, 255, 0.6);
    border-radius: 15px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
}

/* Estilo do título principal */
.title {
    text-align: center;
    font-size: 4.5em;
    font-weight: bold;
    color: #2c3e50;
    padding-top: 20px;
}

/* Estilo do subtítulo */
.subtitle {
    text-align: center;
    font-size: 1.2em;
    color: #34495e;
    margin-bottom: 40px;
}

/* Estilo do botão principal */
div[data-testid="stButton"] > button {
    background-color: #3498db;
    color: white;
    border-radius: 25px;
    padding: 12px 30px;
    font-size: 1.1em;
    font-weight: bold;
    border: none;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}

div[data-testid="stButton"] > button:hover {
    background-color: #2980b9;
    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    transform: translateY(-2px);
}

/* Centraliza o botão */
.stButton {
    display: flex;
    justify-content: center;
}
"""
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# --- Configuração das API Keys ---
def get_api_keys():
    keys = {}
    try:
        keys['google'] = st.secrets["GOOGLE_API_KEY"]
        keys['unsplash'] = st.secrets["UNSPLASH_API_KEY"]
        keys['formspree'] = st.secrets["FORMSPREE_ENDPOINT"] # Nova chave
    except (FileNotFoundError, KeyError):
        st.sidebar.header("🔑 Configuração de API Keys")
        keys['google'] = st.sidebar.text_input(
            "Sua Google API Key", type="password", help="Obtenha no Google AI Studio."
        )
        keys['unsplash'] = st.sidebar.text_input(
            "Sua Unsplash API Key", type="password", help="Obtenha no Unsplash for Developers."
        )
        keys['formspree'] = st.sidebar.text_input(
            "Seu Endpoint do Formspree", type="password", help="Obtenha no site do Formspree."
        )
    return keys

api_keys = get_api_keys()
google_api_key = api_keys.get('google')
unsplash_api_key = api_keys.get('unsplash')
formspree_endpoint = api_keys.get('formspree')


# --- Lógica do Modelo de Texto (Gemini) ---
def gerar_conteudo_espiritual(api_key, sentimento_usuario, tom_escolhido):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")
        mapa_tons = {
            "amigo": "amigo(a) e acolhedor(a)",
            "sábio": "sábio(a) e reflexivo(a)",
            "direto": "direto(a) e conciso(a)"
        }
        tom_formatado = mapa_tons.get(tom_escolhido, "acolhedor(a)")

        prompt = f"""
            Você é um Coach Espiritual. Analise o sentimento do usuário: "{sentimento_usuario}".
            Sua tarefa é retornar um objeto JSON com 4 chaves: "mensagem", "versiculo", "oracao", "keywords".

            1.  **mensagem**: Crie uma mensagem de conforto/inspiração com um tom {tom_formatado}.
            2.  **versiculo**: Forneça o texto completo de um versículo bíblico de apoio, seguido pela referência entre parênteses. (Exemplo: "O Senhor é o meu pastor; nada me faltará. (Salmo 23:1)").
            3.  **oracao**: Escreva uma oração guiada em primeira pessoa.
            4.  **keywords**: Forneça uma string com 3 a 4 palavras-chave em INGLÊS, separadas por vírgula, que representem visualmente o sentimento do usuário de forma abstrata e simbólica (ex: hope, light, path, faith, peace).

            O JSON deve ter exatamente este formato:
            {{
              "mensagem": "...",
              "versiculo": "...",
              "oracao": "...",
              "keywords": "..."
            }}
        """
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Ocorreu um erro no Gemini: {e}")
        return None

# --- Lógica de Busca de Imagem (Unsplash) ---
def buscar_imagem_no_unsplash(api_key, keywords):
    try:
        api_url = "https://api.unsplash.com/search/photos"
        params = {
            "query": keywords,
            "page": 1,
            "per_page": 1,
            "orientation": "landscape",
            "client_id": api_key
        }
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            return data["results"][0]["urls"]["regular"]
        return None
    except Exception as e:
        print(f"Ocorreu um erro na busca do Unsplash: {e}")
        return None

# --- Função para Enviar Feedback ---
def enviar_feedback(endpoint, email, tipo, mensagem):
    try:
        headers = {"Content-Type": "application/json"}
        data = {"email": email, "tipo": tipo, "mensagem": mensagem}
        response = requests.post(endpoint, json=data, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao enviar feedback: {e}")
        return False

# --- Interface do Usuário (UI) ---

st.markdown('<p class="title">✨ CoachAI Espiritual ✨</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Seu assistente pessoal para bem-estar interior e reflexão.</p>', unsafe_allow_html=True)

_, col_controles, _ = st.columns([1, 2, 1])
with col_controles:
    st.subheader("1. Escolha o tom do seu guia")
    tom = st.radio(
        "Que tipo de guia você prefere hoje?",
        ["amigo", "sábio", "direto"],
        captions=["Uma conversa calorosa e empática.", "Uma reflexão profunda e calma.", "Uma mensagem clara e objetiva."],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.subheader("2. Descreva sua necessidade")
    sentimento_input = st.text_area(
        "Como você está se sentindo ou o que você busca?",
        placeholder="Ex: 'Estou me sentindo um pouco triste hoje' ou 'Preciso de inspiração para começar o dia'",
        height=130,
        label_visibility="collapsed"
    )

_, col_button, _ = st.columns([1, 2, 1])
with col_button:
    if st.button("Receber Mensagem", use_container_width=True):
        if not google_api_key or not unsplash_api_key:
            st.error("Por favor, configure as chaves de API na barra lateral.")
        elif not sentimento_input:
            st.warning("Por favor, descreva como você está se sentindo.")
        else:
            conteudo_gerado = None
            with st.spinner("Conectando-se com a sabedoria do universo..."):
                conteudo_gerado = gerar_conteudo_espiritual(google_api_key, sentimento_input, tom)

            if conteudo_gerado:
                st.success("Aqui está uma mensagem para você:")
                col_texto, col_imagem = st.columns([1.5, 1])
                with col_texto:
                    st.markdown(f"""
                    <div class="content-card">
                        <p>{conteudo_gerado["mensagem"]}</p><hr>
                        <p><b>📖 Versículo de Apoio:</b> {conteudo_gerado['versiculo']}</p><hr>
                        <p><b>🙏 Oração Guiada:</b> {conteudo_gerado['oracao']}</p>
                    </div>""", unsafe_allow_html=True)
                with col_imagem:
                    image_url = None
                    with st.spinner("Buscando uma imagem para sua reflexão..."):
                        image_url = buscar_imagem_no_unsplash(unsplash_api_key, conteudo_gerado["keywords"])
                    if image_url:
                        st.markdown(f"""
                        <div class="content-card">
                            <img src="{image_url}" style="border-radius: 10px; width: 100%;">
                            <p style="text-align: center; font-style: italic; margin-top: 10px;">Uma imagem para sua reflexão.</p>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.warning("Não foi possível encontrar uma imagem reflexiva no momento.")
            else:
                st.error("Não foi possível gerar o conteúdo. Tente novamente.")

# --- Seção de Feedback ---
st.markdown("---")
_, col_form, _ = st.columns([1, 2, 1])
with col_form:
    st.subheader("💬 Deixe seu Feedback")
    with st.form(key="feedback_form"):
        feedback_email = st.text_input("Seu e-mail (opcional)")
        feedback_tipo = st.selectbox(
            "Tipo de Feedback",
            ["Elogio", "Crítica Construtiva", "Sugestão de Melhoria", "Relatar um Erro"]
        )
        feedback_mensagem = st.text_area("Sua mensagem", height=150)
        submit_button = st.form_submit_button(label="Enviar Feedback")

        if submit_button:
            if not formspree_endpoint:
                st.error("A funcionalidade de feedback não está configurada pelo dono da aplicação.")
            elif not feedback_mensagem:
                st.warning("Por favor, escreva uma mensagem antes de enviar.")
            else:
                if enviar_feedback(formspree_endpoint, feedback_email, feedback_tipo, feedback_mensagem):
                    st.success("Obrigado! Seu feedback foi enviado com sucesso. ❤️")
                else:
                    st.error("Desculpe, houve um erro ao enviar seu feedback. Tente novamente.")


# --- Rodapé ---
st.markdown(
    "<div style='text-align: center; font-size: 0.9em; color: #34495e; padding: 20px;'>"
    "Lembre-se: O CoachAI Espiritual é uma ferramenta de apoio e não substitui aconselhamento profissional."
    "</div>",
    unsafe_allow_html=True
)
