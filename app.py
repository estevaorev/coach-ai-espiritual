# Importa as bibliotecas necessárias
import streamlit as st
import google.generativeai as genai
import requests
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

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

/* Estilos para o formulário HTML */
.feedback-form input, .feedback-form select, .feedback-form textarea {
    width: 100%;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 5px;
    border: 1px solid #ccc;
}
.feedback-form button {
    width: 100%;
    padding: 10px;
    border-radius: 5px;
    border: none;
    background-color: #28a745;
    color: white;
    font-weight: bold;
    cursor: pointer;
}
"""
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# --- Configuração das API Keys e Firebase ---
def get_api_keys():
    keys = {}
    try:
        keys['google'] = st.secrets["GOOGLE_API_KEY"]
        keys['unsplash'] = st.secrets["UNSPLASH_API_KEY"]
        keys['formspree'] = st.secrets["FORMSPREE_ENDPOINT"]
        keys['firebase_credentials'] = st.secrets["firebase"]["credentials"]
        keys['firebase_database_url'] = st.secrets["firebase"]["databaseURL"]
    except (FileNotFoundError, KeyError):
        st.sidebar.header("🔑 Configuração de API Keys")
        keys['google'] = st.sidebar.text_input("Sua Google API Key", type="password")
        keys['unsplash'] = st.sidebar.text_input("Sua Unsplash API Key", type="password")
        keys['formspree'] = st.sidebar.text_input("Seu Endpoint do Formspree", type="password")
        st.sidebar.warning("A configuração do Firebase (contador e avaliações) só funciona em produção.")
    return keys

api_keys = get_api_keys()
google_api_key = api_keys.get('google')
unsplash_api_key = api_keys.get('unsplash')
formspree_endpoint = api_keys.get('formspree')

# --- Lógica do Firebase (Contador e Avaliações) ---
def init_firebase_app(credentials_info, database_url):
    """Inicializa a aplicação Firebase se ainda não foi inicializada."""
    if not firebase_admin._apps:
        try:
            creds_dict = dict(credentials_info)
            creds_dict["private_key"] = creds_dict["private_key"].replace('\\n', '\n')
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': database_url})
            return "Conectado"
        except Exception as e:
            return f"Falha: {e}"
    return "Conectado"

def increment_and_get_visitor_count():
    """Incrementa o contador de visitas e retorna o valor atual."""
    try:
        if firebase_admin._apps:
            ref = db.reference('visits')
            return ref.transaction(lambda current_value: (current_value or 0) + 1)
    except Exception as e:
        print(f"Erro ao aceder ao contador: {e}")
        return None

def save_rating_to_firebase(user_input, response_data, rating):
    """Guarda a avaliação da resposta na base de dados."""
    try:
        if firebase_admin._apps:
            ref = db.reference('ratings')
            ref.push({
                'user_input': user_input,
                'response': response_data,
                'rating': rating,
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"Erro ao guardar a avaliação: {e}")

# Inicializa o Firebase e gere o estado da conexão
firebase_status = "Não Configurado"
total_visits = None
firebase_creds = api_keys.get('firebase_credentials')
firebase_url = api_keys.get('firebase_database_url')

if firebase_creds and firebase_url:
    firebase_status = init_firebase_app(firebase_creds, firebase_url)
    if firebase_status == "Conectado":
        if 'visitor_counted' not in st.session_state:
            st.session_state.total_visits = increment_and_get_visitor_count()
            st.session_state.visitor_counted = True
        total_visits = st.session_state.get('total_visits')

# Adiciona o indicador de estado na barra lateral
if firebase_creds and firebase_url:
    if firebase_status == "Conectado":
        st.sidebar.success("✅ Base de Dados: Ativa")
    else:
        st.sidebar.error("❌ Base de Dados: Falhou")
        st.sidebar.caption(f"Detalhe: {firebase_status}")


# --- Lógica do Modelo de Texto (Gemini) ---
def gerar_conteudo_espiritual(api_key, sentimento_usuario, tom_escolhido):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")
        mapa_tons = {"amigo": "amigo(a) e acolhedor(a)", "sábio": "sábio(a) e reflexivo(a)", "direto": "direto(a) e conciso(a)"}
        tom_formatado = mapa_tons.get(tom_escolhido, "acolhedor(a)")
        prompt = f"""Você é um Coach Espiritual. Analise o sentimento do usuário: "{sentimento_usuario}".
            Sua tarefa é retornar um objeto JSON com 4 chaves: "mensagem", "versiculo", "oracao", "keywords".
            1.  **mensagem**: Crie uma mensagem de conforto/inspiração com um tom {tom_formatado}.
            2.  **versiculo**: Forneça o texto completo de um versículo bíblico de apoio, seguido pela referência entre parênteses.
            3.  **oracao**: Escreva uma oração guiada em primeira pessoa.
            4.  **keywords**: Forneça uma string com 3 a 4 palavras-chave em INGLÊS, separadas por vírgula, para a imagem.
            O JSON deve ter exatamente este formato: {{"mensagem": "...", "versiculo": "...", "oracao": "...", "keywords": "..."}}"""
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
        params = {"query": keywords, "page": 1, "per_page": 1, "orientation": "landscape", "client_id": api_key}
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            return data["results"][0]["urls"]["regular"]
        return None
    except Exception as e:
        print(f"Ocorreu um erro na busca do Unsplash: {e}")
        return None

# --- Interface do Usuário (UI) ---
st.markdown('<p class="title">✨ CoachAI Espiritual ✨</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Seu assistente pessoal para bem-estar interior e reflexão.</p>', unsafe_allow_html=True)

_, col_controles, _ = st.columns([1, 2, 1])
with col_controles:
    st.subheader("1. Escolha o tom do seu guia")
    tom = st.radio("Tom do Guia", ["amigo", "sábio", "direto"], horizontal=True, label_visibility="collapsed")
    st.subheader("2. Descreva sua necessidade")
    sentimento_input = st.text_area("Necessidade", placeholder="Ex: 'Estou me sentindo um pouco triste hoje'", height=130, label_visibility="collapsed")

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
            
            # Guarda o resultado na sessão para poder ser avaliado
            if conteudo_gerado:
                st.session_state.last_response = conteudo_gerado
                st.session_state.last_input = sentimento_input
                st.session_state.rated = False # Reseta o estado de avaliação

# --- Exibição do Conteúdo Gerado ---
if 'last_response' in st.session_state:
    conteudo_gerado = st.session_state.last_response
    st.success("Aqui está uma mensagem para você:")
    col_texto, col_imagem = st.columns([1.5, 1])
    with col_texto:
        st.markdown(f"""<div class="content-card">
            <p>{conteudo_gerado["mensagem"]}</p><hr>
            <p><b>📖 Versículo de Apoio:</b> {conteudo_gerado['versiculo']}</p><hr>
            <p><b>🙏 Oração Guiada:</b> {conteudo_gerado['oracao']}</p>
        </div>""", unsafe_allow_html=True)
    with col_imagem:
        image_url = None
        with st.spinner("Buscando uma imagem para sua reflexão..."):
            image_url = buscar_imagem_no_unsplash(unsplash_api_key, conteudo_gerado["keywords"])
        if image_url:
            st.markdown(f"""<div class="content-card">
                <img src="{image_url}" style="border-radius: 10px; width: 100%;">
                <p style="text-align: center; font-style: italic; margin-top: 10px;">Uma imagem para sua reflexão.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.warning("Não foi possível encontrar uma imagem reflexiva no momento.")

    # --- Seção de Avaliação da Resposta (Like/Dislike) ---
    if not st.session_state.get('rated', False):
        st.write("A resposta foi útil?")
        r_col1, r_col2, r_col3 = st.columns([1,1,5])
        if r_col1.button("👍 Gostei"):
            save_rating_to_firebase(st.session_state.last_input, st.session_state.last_response, "like")
            st.session_state.rated = True
            st.rerun()
        if r_col2.button("👎 Não Gostei"):
            save_rating_to_firebase(st.session_state.last_input, st.session_state.last_response, "dislike")
            st.session_state.rated = True
            st.rerun()
    else:
        st.info("Obrigado pelo seu feedback sobre esta mensagem!")


# --- Seção de Feedback Geral ---
st.markdown("---")
_, col_form, _ = st.columns([1, 2, 1])
with col_form:
    st.subheader("💬 Deixe seu Feedback Geral")
    if formspree_endpoint:
        form_html = f"""
        <div class="feedback-form">
            <form action="{formspree_endpoint}" method="POST">
                <input type="email" name="email" placeholder="Seu e-mail (opcional)">
                <select name="tipo">
                    <option>Elogio</option><option>Crítica Construtiva</option><option>Sugestão de Melhoria</option><option>Relatar um Erro</option>
                </select>
                <textarea name="message" placeholder="Sua mensagem" required></textarea>
                <button type="submit">Enviar Feedback</button>
            </form>
        </div>
        """
        st.markdown(form_html, unsafe_allow_html=True)
    else:
        st.warning("A funcionalidade de feedback não está configurada.")

# --- Rodapé ---
st.markdown("---")
if total_visits is not None:
    st.markdown(f"<div style='text-align: center; font-size: 1em; color: #34495e;'>👁️ Visitas Totais: <strong>{total_visits}</strong></div>", unsafe_allow_html=True)

st.markdown(
    "<div style='text-align: center; font-size: 0.9em; color: #34495e; padding: 20px;'>"
    "Lembre-se: O CoachAI Espiritual é uma ferramenta de apoio e não substitui aconselhamento profissional."
    "</div>",
    unsafe_allow_html=True
)
