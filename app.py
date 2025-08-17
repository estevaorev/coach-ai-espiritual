# Importa as bibliotecas necessárias
import streamlit as st
import google.generativeai as genai
import requests
import base64
import time

# --- Configuração da Página ---
# Define o título da página, ícone e layout.
st.set_page_config(
    page_title="CoachAI Espiritual",
    page_icon="✨",
    layout="centered"
)

# --- Configuração da API Key ---
# Esta função tenta obter a chave de API dos segredos do Streamlit (para deploy)
# Se não encontrar, mostra um campo na barra lateral (para desenvolvimento local).
def get_api_key():
    try:
        # Tenta obter a chave do secrets.toml (quando em produção no Streamlit Cloud)
        return st.secrets["GOOGLE_API_KEY"]
    except (FileNotFoundError, KeyError):
        # Se não encontrar, mostra o campo na barra lateral para uso local
        st.sidebar.header("Configuração")
        return st.sidebar.text_input(
            "Sua Google API Key",
            type="password",
            help="Obtenha sua chave no Google AI Studio."
        )

google_api_key = get_api_key()


# --- Lógica do Modelo de Texto (Gemini) ---

def gerar_mensagem_espiritual(api_key, sentimento_usuario, tom_escolhido):
    """
    Gera uma mensagem, um versículo e uma oração usando a API do Google Gemini.
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
            Você é um Coach Espiritual. Seu propósito é gerar uma mensagem personalizada para um usuário.
            Contexto do Usuário: Ele descreveu o seguinte estado/necessidade: "{sentimento_usuario}"
            Sua Tarefa (siga esta ordem exata):
            1.  **Mensagem Principal:** Gere uma mensagem de conforto, inspiração ou perspectiva. Use um tom {tom_formatado}.
            2.  **Versículo de Apoio:** Inclua um versículo bíblico de apoio. Apresente-o sob o título "**📖 Versículo de Apoio:**".
            3.  **Oração Guiada:** Crie uma oração em primeira pessoa. Apresente-a sob o título "**🙏 Oração Guiada:**".
            Regras de Estilo: Linguagem inclusiva, resposta direta, sem conselhos não solicitados.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Ocorreu um erro no Gemini: {e}")
        return "Desculpe, não consegui gerar a mensagem de texto no momento."

# --- Lógica do Modelo de Imagem (Imagen) ---

def gerar_imagem_reflexiva(api_key, sentimento_usuario):
    """
    Gera uma imagem simbólica e reflexiva usando a API do Imagen 3.
    """
    try:
        # 1. Cria um prompt descritivo e artístico para o modelo de imagem
        prompt_para_imagem = f"Uma pintura digital bela e simbólica que captura a essência do sentimento de '{sentimento_usuario}'. A imagem deve ser etérea, abstrata e transmitir uma sensação de esperança, paz e reflexão interior. Estilo de arte: fantasia conceitual, cores suaves e luz brilhante."

        # 2. Faz a chamada de API para o Imagen 3 com a URL e payload corrigidos
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
        payload = {
            "instances": [{"prompt": prompt_para_imagem}],
            "parameters": {"sampleCount": 1}
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Lança um erro para respostas ruins (4xx ou 5xx)
        result = response.json()

        # 3. Decodifica a imagem recebida em base64
        if "predictions" in result and len(result["predictions"]) > 0 and "bytesBase64Encoded" in result["predictions"][0]:
            base64_image = result["predictions"][0]["bytesBase64Encoded"]
            image_bytes = base64.b64decode(base64_image)
            return image_bytes
        else:
            print("Resposta da API de imagem inesperada:", result)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar a API de imagem: {e}")
        if e.response:
            print(f"Detalhes do erro da API: {e.response.text}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro na geração da imagem: {e}")
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
    if not google_api_key:
        st.error("Por favor, insira sua Google API Key na barra lateral ou configure-a nos segredos da aplicação.")
    elif not sentimento_input:
        st.warning("Por favor, descreva como você está se sentindo.")
    else:
        # Gerar e exibir conteúdo de texto
        with st.spinner("Conectando-se com a sabedoria do universo..."):
            mensagem = gerar_mensagem_espiritual(google_api_key, sentimento_input, tom)
        st.success("Aqui está uma mensagem para você:")
        st.markdown(mensagem)
        st.markdown("---")

        # Gerar e exibir conteúdo de imagem
        with st.spinner("Criando uma imagem para sua reflexão..."):
            imagem_bytes = gerar_imagem_reflexiva(google_api_key, sentimento_input)

        if imagem_bytes:
            st.image(imagem_bytes, caption="Uma imagem para sua reflexão.")
        else:
            st.warning("Não foi possível gerar a imagem reflexiva no momento.")

# --- Rodapé ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 0.8em;'>"
    "Lembre-se: O CoachAI Espiritual é uma ferramenta de apoio e não substitui aconselhamento profissional."
    "</div>",
    unsafe_allow_html=True
)
