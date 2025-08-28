# Importa as bibliotecas necessárias
import streamlit as st
import google.generativeai as genai
import requests
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- ATENÇÃO: Configuração de API Keys para Teste ---
# Apenas o GA_MEASUREMENT_ID está definido diretamente para o teste.
# As outras chaves continuarão a ser lidas a partir dos Segredos do Streamlit.

GA_MEASUREMENT_ID = "G-SQNHZX78S0" # Ex: "G-XXXXXXXXXX"


# --- Configuração da Página ---
st.set_page_config(
    page_title="CoachAI Espiritual",
    page_icon="🌌",
    layout="wide"
)

# --- Estilos CSS Customizados ---
css = """
/* Estilos da aplicação... (mantidos como na versão anterior) */
.stApp {
    background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://i.imgur.com/B1m7gaE.jpeg");
    background-size: contain;
    background-position: center top;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-color: #0c0c14;
}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stAppViewContainer"] > .main {
    background: none;
}
h1, h2, h3, h4, h5, h6, p, .stRadio, .stTextArea, .stSelectbox, .stTextInput, .stMarkdown {
    color: #28a745 !important;
}
[data-testid="stCaptionContainer"] {
    color: #E0E0E0 !important;
    text-shadow: 1px 1px 6px rgba(0, 0, 0, 0.8);
}
.content-card {
    background-color: rgba(15, 23, 42, 0.7);
    border-radius: 15px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
}
.title { display: none; }
.subtitle {
    text-align: center;
    font-size: 1.2em;
    color: #E0E0E0;
    margin-bottom: 20px;
    padding-top: 250px;
}
#action-buttons-marker { display: none; }
#action-buttons-marker + [data-testid="stHorizontalBlock"] button {
    background-color: transparent !important;
    background-image: none !important;
    color: #28a745 !important;
    border: 2px solid #28a745 !important;
    border-radius: 25px !important;
    padding: 12px 30px !important;
    font-size: 1.1em !important;
    font-weight: bold !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
}
#action-buttons-marker + [data-testid="stHorizontalBlock"] button:hover {
    background-color: #28a745 !important;
    color: #FFFFFF !important;
    border-color: #28a745 !important;
    transform: translateY(-2px) !important;
}
.suggestion-buttons button {
    background-color: transparent !important;
    background-image: none !important;
    color: #E0E0E0 !important;
    border: 1px solid #3498db !important;
    font-weight: normal !important;
    font-size: 0.9em !important;
    padding: 8px 10px !important;
    border-radius: 15px !important;
    transition: all 0.3s ease !important;
}
.suggestion-buttons button:hover {
    background-color: rgba(52, 152, 219, 0.2) !important;
    border-color: #FFFFFF !important;
}
.feedback-form input, .feedback-form select, .feedback-form textarea {
    width: 100%;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 5px;
    border: 1px solid #ccc;
    color: #000000;
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

# --- Configuração das API Keys e Firebase (lendo dos Secrets) ---
def get_api_keys_from_secrets():
    keys = {}
    try:
        keys['google'] = st.secrets["GOOGLE_API_KEY"]
        keys['unsplash'] = st.secrets["UNSPLASH_API_KEY"]
        keys['formspree'] = st.secrets["FORMSPREE_ENDPOINT"]
        keys['firebase_credentials'] = st.secrets["firebase"]["credentials"]
        keys['firebase_database_url'] = st.secrets["firebase"]["databaseURL"]
    except (FileNotFoundError, KeyError):
        st.sidebar.header("🔑 Configuração de API Keys")
        st.sidebar.warning("Uma ou mais chaves não foram encontradas nos Segredos do Streamlit.")
    return keys

api_keys = get_api_keys_from_secrets()
google_api_key = api_keys.get('google')
unsplash_api_key = api_keys.get('unsplash')
formspree_endpoint = api_keys.get('formspree')
firebase_creds = api_keys.get('firebase_credentials')
firebase_url = api_keys.get('firebase_database_url')


# --- Injetar Google Analytics ---
def inject_ga(measurement_id):
    if measurement_id and measurement_id != "COLE_O_SEU_ID_DE_METRICA_GA_AQUI":
        ga_script = f"""
            <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){{dataLayer.push(arguments);}}
              gtag('js', new Date());
              gtag('config', '{measurement_id}');
            </script>
        """
        st.html(ga_script)

inject_ga(GA_MEASUREMENT_ID)


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
            ref = db.reference('stats/visits')
            return ref.transaction(lambda current_value: (current_value or 0) + 1)
    except Exception as e:
        print(f"Erro ao aceder ao contador de visitas: {e}")
        return None

def increment_message_count():
    """Incrementa o contador de mensagens geradas."""
    try:
        if firebase_admin._apps:
            ref = db.reference('stats/message_count')
            ref.transaction(lambda current_value: (current_value or 0) + 1)
    except Exception as e:
        print(f"Erro ao incrementar contador de mensagens: {e}")

def handle_rating(rating_type, user_input=None, response_data=None):
    """Processa as avaliações 'like' e 'dislike'."""
    try:
        if firebase_admin._apps:
            counter_ref = db.reference(f'ratings/{rating_type}_count')
            counter_ref.transaction(lambda current_value: (current_value or 0) + 1)

            if rating_type == 'dislike':
                details_ref = db.reference('ratings/dislike_details')
                details_ref.push({
                    'user_input': user_input,
                    'response': response_data,
                    'timestamp': datetime.now().isoformat()
                })
    except Exception as e:
        print(f"Erro ao guardar a avaliação '{rating_type}': {e}")

@st.cache_data(ttl=30)
def get_app_stats():
    """Busca todas as estatísticas da aplicação."""
    try:
        if firebase_admin._apps:
            stats_ref = db.reference('stats')
            ratings_ref = db.reference('ratings')
            stats = stats_ref.get() or {}
            ratings = ratings_ref.get() or {}
            return {
                "visits": stats.get('visits', 0),
                "messages": stats.get('message_count', 0),
                "likes": ratings.get('like_count', 0),
                "dislikes": ratings.get('dislike_count', 0)
            }
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
    return {"visits": 0, "messages": 0, "likes": 0, "dislikes": 0}

# Inicializa o Firebase e gere o estado da conexão
firebase_status = "Não Configurado"
if firebase_creds and firebase_url:
    firebase_status = init_firebase_app(firebase_creds, firebase_url)

app_stats = {}
if firebase_status == "Conectado":
    if 'visitor_counted' not in st.session_state:
        st.session_state.total_visits = increment_and_get_visitor_count()
        st.session_state.visitor_counted = True
    app_stats = get_app_stats()


# --- Lógica do Modelo de Texto (Gemini) ---
def gerar_conteudo_espiritual(api_key, sentimento_usuario, tom_escolhido):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")
        mapa_tons = {
            "amigo": "amigo(a) e acolhedor(a)",
            "sábio": "sábio(a) e reflexivo(a)",
            "direto": "direto(a) e conciso(a)",
            "encorajador": "encorajador(a) e motivacional, como um treinador",
            "calmo": "calmo(a) e sereno(a), com foco em paz interior e tranquilidade",
            "poético": "poético(a) e contemplativo(a), usando metáforas e linguagem figurativa",
            "descontraído": "descontraído(a) e bem-humorado(a), como uma conversa leve e otimista"
        }
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
st.markdown('<p class="title"></p>', unsafe_allow_html=True) 
st.markdown('<p class="subtitle">Seu assistente pessoal para bem-estar interior e reflexão.</p>', unsafe_allow_html=True)

if 'sentimento_input' not in st.session_state:
    st.session_state.sentimento_input = ""

def set_text_conforto():
    st.session_state.sentimento_input = "Estou a passar por um momento difícil e sinto-me um pouco triste."
def set_text_inspiracao():
    st.session_state.sentimento_input = "Gostaria de uma mensagem de motivação para começar bem o meu dia."
def set_text_perspectiva():
    st.session_state.sentimento_input = "Estou a enfrentar uma decisão importante e sinto-me um pouco perdido(a)."

_, col_controles, _ = st.columns([1, 2, 1])
with col_controles:
    st.subheader("1. Escolha o tom do seu guia")
    tom = st.selectbox(
        label="Tom do Guia",
        options=["amigo", "sábio", "direto", "encorajador", "calmo", "poético", "descontraído"],
        format_func=lambda x: x.capitalize(),
        label_visibility="collapsed"
    )
    
    st.subheader("2. Descreva sua necessidade")
    
    st.write("Precisa de ajuda para começar? Escolha um ponto de partida:")
    st.markdown('<div class="suggestion-buttons">', unsafe_allow_html=True)
    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        st.button("Preciso de Conforto", on_click=set_text_conforto, use_container_width=True)
    with b_col2:
        st.button("Busco Inspiração", on_click=set_text_inspiracao, use_container_width=True)
    with b_col3:
        st.button("Quero uma Perspectiva", on_click=set_text_perspectiva, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    sentimento_input = st.text_area(
        "Necessidade",
        placeholder="Ou escreva livremente como se sente...",
        height=130,
        key="sentimento_input",
        label_visibility="collapsed"
    )


_, col_botoes_acao, _ = st.columns([1, 2, 1])
with col_botoes_acao:
    st.markdown('<div id="action-buttons-marker"></div>', unsafe_allow_html=True)
    b_acao1, b_acao2 = st.columns(2)
    with b_acao1:
        if st.button("Receber Mensagem", use_container_width=True, key="main_button"):
            if not st.session_state.sentimento_input:
                st.warning("Por favor, descreva como você está se sentindo.")
            else:
                st.session_state.acao = ("gerar", st.session_state.sentimento_input)
    
    with b_acao2:
        if st.button("✨ Me Surpreenda", use_container_width=True, key="surprise_button"):
            st.session_state.acao = ("gerar", "Preciso de uma mensagem de sabedoria e inspiração para o meu dia")

if 'acao' in st.session_state:
    acao_tipo, texto_para_ia = st.session_state.acao
    del st.session_state.acao

    conteudo_gerado = None
    with st.spinner("Conectando-se com a sabedoria do universo..."):
        conteudo_gerado = gerar_conteudo_espiritual(GOOGLE_API_KEY, texto_para_ia, tom)
    
    if conteudo_gerado:
        increment_message_count()
        get_app_stats.clear()
        st.session_state.last_response = conteudo_gerado
        st.session_state.last_input = texto_para_ia
        st.session_state.rated = False

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
            image_url = buscar_imagem_no_unsplash(UNSPLASH_API_KEY, conteudo_gerado["keywords"])
        if image_url:
            st.markdown(f"""<div class="content-card">
                <img src="{image_url}" style="border-radius: 10px; width: 100%;">
                <p style="text-align: center; font-style: italic; margin-top: 10px;">Uma imagem para sua reflexão.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.warning("Não foi possível encontrar uma imagem reflexiva no momento.")

    if not st.session_state.get('rated', False):
        st.write("A resposta foi útil?")
        r_col1, r_col2, r_col3 = st.columns([1,1,5])
        if r_col1.button("👍 Gostei"):
            handle_rating("like")
            st.session_state.rated = True
            get_app_stats.clear()
            st.rerun()
        if r_col2.button("👎 Não Gostei"):
            handle_rating("dislike", st.session_state.last_input, st.session_state.last_response)
            st.session_state.rated = True
            get_app_stats.clear()
            st.rerun()
    else:
        st.info("Obrigado pelo seu feedback sobre esta mensagem!")


_, col_form, _ = st.columns([1, 2, 1])
with col_form:
    st.subheader("💬 Deixe seu Feedback Geral")
    if FORMSPREE_ENDPOINT != "COLE_O_SEU_ENDPOINT_DO_FORMSPREE_AQUI":
        form_html = f"""
        <div class="feedback-form">
            <form action="{FORMSPREE_ENDPOINT}" method="POST">
                <input tabindex="-1" type="email" name="email" placeholder="Seu e-mail (opcional)">
                <select tabindex="-1" name="tipo">
                    <option>Elogio</option><option>Crítica Construtiva</option><option>Sugestão de Melhoria</option><option>Relatar um Erro</option>
                </select>
                <textarea tabindex="-1" name="message" placeholder="Sua mensagem" required></textarea>
                <button tabindex="-1" type="submit">Enviar Feedback</button>
            </form>
        </div>
        """
        st.markdown(form_html, unsafe_allow_html=True)
    else:
        st.warning("A funcionalidade de feedback não está configurada.")

st.markdown("---")
if firebase_status == "Conectado":
    stats_html = f"""
    <div style='text-align: center; font-size: 1em; color: #FFFFFF;'>
        👁️ Visitas: <strong>{app_stats.get('visits', 0)}</strong> &nbsp;&nbsp;&nbsp; ✉️ Mensagens Geradas: <strong>{app_stats.get('messages', 0)}</strong>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    total_ratings = app_stats.get('likes', 0) + app_stats.get('dislikes', 0)
    if total_ratings > 0:
        satisfaction_rate = app_stats.get('likes', 0) / total_ratings
        st.markdown(f"""
        <div style='text-align: center; font-size: 1em; color: #FFFFFF; margin-top: 10px;'>
            <strong>Taxa de Satisfação ({total_ratings} avaliações)</strong><br>
            👍 {app_stats.get('likes', 0)} Gostaram &nbsp;&nbsp;&nbsp; 👎 {app_stats.get('dislikes', 0)} Não Gostaram
        </div>
        """, unsafe_allow_html=True)
        st.progress(satisfaction_rate)

st.markdown("---")
_, col_creator, _ = st.columns([1, 2, 1])
with col_creator:
    st.subheader("👨‍💻 Sobre o Criador")
    st.markdown("""
    <div class="content-card">
        <p>Olá! Sou Estevão Gonçalves, Analista de Sistemas e um entusiasta da tecnologia com foco em automação de processos e gestão de TI. Atualmente, estou a aprofundar os meus conhecimentos em Análise e Desenvolvimento de Sistemas.</p>
        <p>Além da minha carreira em tecnologia, sou Presbítero na ICB Vista Linda, amante da teologia e produtor semanal de estudos para células. O CoachAI Espiritual nasceu da união dessas duas paixões: explorar como a Inteligência Artificial pode ser usada para criar ferramentas que oferecem apoio, conforto e inspiração no nosso dia a dia.</p>
        <p>
            Conecte-se comigo no <a href="https://www.linkedin.com/in/estevaorev" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold;">LinkedIn</a> 
            ou acompanhe os meus estudos no meu canal do <a href="https://www.youtube.com/@estevaorev" target="_blank" style="color: #FF0000; text-decoration: none; font-weight: bold;">YouTube</a>.
        </p>
    </div>
    """, unsafe_allow_html=True)


st.markdown(
    "<div style='text-align: center; font-size: 0.9em; color: #E0E0E0; padding: 20px;'>"
    "Lembre-se: O CoachAI Espiritual é uma ferramenta de apoio e não substitui aconselhamento profissional."
    "</div>",
    unsafe_allow_html=True
)
