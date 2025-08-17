# Importa as bibliotecas necessárias
import streamlit as st
import google.generativeai as genai
import requests
import base64
import time
import json

# --- Configuração da Página ---
st.set_page_config(
    page_title="CoachAI Espiritual",
    page_icon="✨",
    layout="centered"
)

# --- Configuração das API Keys ---
def get_api_keys():
    """
    Obtém as chaves de API dos segredos do Streamlit ou da barra lateral.
    Retorna um dicionário com as chaves.
    """
    keys = {}
    try:
        # Tenta obter as chaves do secrets.toml (quando em produção)
        keys['google'] = st.secrets["GOOGLE_API_KEY"]
        keys['unsplash'] = st.secrets["UNSPLASH_API_KEY"]
    except (FileNotFoundError, KeyError):
        # Se não encontrar, mostra os campos na barra lateral (para uso local)
        st.sidebar.header("Configuração de API Keys")
        keys['google'] = st.sidebar.text_input(
            "Sua Google API Key", type="password", help="Obtenha no Google AI Studio."
        )
        keys['unsplash'] = st.sidebar.text_input(
            "Sua Unsplash API Key", type="password", help="Obtenha no Unsplash for Developers."
        )
    return keys

api_keys = get_api_keys()
google_api_key = api_keys.get('google')
unsplash_api_key = api_keys.get('unsplash')


# --- Lógica do Modelo de Texto (Gemini) ---

def gerar_conteudo_espiritual(api_key, sentimento_usuario, tom_escolhido):
    """
    Usa o Gemini para gerar a mensagem, versículo, oração E palavras-chave para a imagem.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
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
            2.  **versiculo**: Forneça um versículo bíblico de apoio (livro, capítulo, número).
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
        # Limpa a resposta para garantir que seja um JSON válido
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)

    except Exception as e:
        print(f"Ocorreu um erro no Gemini: {e}")
        return None

# --- Lógica de Busca de Imagem (Unsplash) ---

def buscar_imagem_no_unsplash(api_key, keywords):
    """
    Busca uma imagem no Unsplash com base nas palavras-chave.
    """
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
        else:
            return None
    except Exception as e:
        print(f"Ocorreu um erro na busca do Unsplash: {e}")
        return None

# --- Interface do Usuário (UI) ---

st.title("✨ CoachAI Espiritual ✨")
st.markdown("Seu assistente pessoal para bem-estar interior e reflexão.")
st.markdown("---")

st.subheader("1. Escolha o tom do seu guia")
tom = st.radio(
    "Que tipo de guia você prefere hoje?",
    ["amigo", "sábio", "direto"],
    captions=["Uma conversa calorosa e empática.", "Uma reflexão profunda e calma.", "Uma mensagem clara e objetiva."],
    horizontal=True
)

st.subheader("2. Descreva sua necessidade")
sentimento_input = st.text_area(
    "Como você está se sentindo ou o que você busca?",
    placeholder="Ex: 'Estou me sentindo um pouco triste hoje' ou 'Preciso de inspiração para começar o dia'",
    height=100
)

if st.button("Receber Mensagem"):
    if not google_api_key or not unsplash_api_key:
        st.error("Por favor, configure ambas as chaves de API na barra lateral.")
    elif not sentimento_input:
        st.warning("Por favor, descreva como você está se sentindo.")
    else:
        conteudo_gerado = None
        with st.spinner("Conectando-se com a sabedoria do universo..."):
            conteudo_gerado = gerar_conteudo_espiritual(google_api_key, sentimento_input, tom)

        if conteudo_gerado:
            st.success("Aqui está uma mensagem para você:")
            st.markdown(conteudo_gerado["mensagem"])
            st.markdown(f"**📖 Versículo de Apoio:** {conteudo_gerado['versiculo']}")
            st.markdown(f"**🙏 Oração Guiada:** {conteudo_gerado['oracao']}")
            st.markdown("---")

            image_url = None
            with st.spinner("Buscando uma imagem para sua reflexão..."):
                image_url = buscar_imagem_no_unsplash(unsplash_api_key, conteudo_gerado["keywords"])

            if image_url:
                st.image(image_url, caption="Uma imagem para sua reflexão.")
            else:
                st.warning("Não foi possível encontrar uma imagem reflexiva no momento.")
        else:
            st.error("Não foi possível gerar o conteúdo. Tente novamente.")

# --- Rodapé ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 0.8em;'>"
    "Lembre-se: O CoachAI Espiritual é uma ferramenta de apoio e não substitui aconselhamento profissional."
    "</div>",
    unsafe_allow_html=True
)
