# Importa as bibliotecas necessárias
import streamlit as st
import google.generativeai as genai
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


# --- Lógica do Modelo Gemini ---

def gerar_mensagem_espiritual(api_key, sentimento_usuario, tom_escolhido):
    """
    Gera uma mensagem, um versículo e uma oração usando a API do Google Gemini.

    Args:
        api_key: A chave de API do Google.
        sentimento_usuario: O texto que o usuário inseriu sobre como se sente.
        tom_escolhido: O tom que o chatbot deve usar ('amigo', 'sábio', 'direto').

    Returns:
        A mensagem gerada pelo modelo ou uma mensagem de erro.
    """
    try:
        # Configura a API key
        genai.configure(api_key=api_key)

        # Configurações do modelo
        generation_config = {
            "candidate_count": 1,
            "temperature": 0.9, # Aumentei um pouco para mais criatividade na oração
            "top_p": 0.9,
        }
        safety_settings = {
            "HARASSMENT": "BLOCK_NONE",
            "HATE": "BLOCK_NONE",
            "SEXUAL": "BLOCK_NONE",
            "DANGEROUS": "BLOCK_NONE",
        }

        # Inicializa o modelo
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Mapeia a escolha do tom para uma instrução mais detalhada
        mapa_tons = {
            "amigo": "amigo(a) e acolhedor(a)",
            "sábio": "sábio(a) e reflexivo(a)",
            "direto": "direto(a) e conciso(a)"
        }
        tom_formatado = mapa_tons.get(tom_escolhido, "acolhedor(a)")

        # O prompt que será enviado ao modelo, agora com a instrução para a oração
        prompt = f"""
            Você é um Coach Espiritual. Seu propósito é gerar uma mensagem personalizada para um usuário.

            **Contexto do Usuário:** Ele descreveu o seguinte estado/necessidade: "{sentimento_usuario}"

            **Sua Tarefa (siga esta ordem exata):**
            1.  **Mensagem Principal:** Gere uma mensagem de conforto, inspiração ou perspectiva. **Use um tom {tom_formatado} na sua resposta.**
            2.  **Versículo de Apoio:** Inclua um versículo bíblico de apoio que se relacione com a mensagem. Apresente-o sob o título "**📖 Versículo de Apoio:**".
            3.  **Oração Guiada:** Crie uma oração em primeira pessoa (usando "eu", "meu", "minha") que o usuário possa ler como se fosse sua própria prece, refletindo a necessidade dele. Apresente-a sob o título "**🙏 Oração Guiada:**".

            **Regras de Estilo:**
            - Sua linguagem deve ser inclusiva e respeitosa.
            - Responda de forma direta. Não inclua saudações como "Olá".
            - Evite conselhos não solicitados. O foco é no apoio emocional e espiritual.
        """

        # Gera o conteúdo
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        # Retorna uma mensagem de erro amigável
        print(f"Ocorreu um erro: {e}")
        return "Desculpe, não consegui gerar uma mensagem no momento. Verifique sua chave de API e tente novamente."


# --- Interface do Usuário (UI) ---

# Título principal da aplicação
st.title("✨ CoachAI Espiritual ✨")

# Subtítulo ou descrição
st.markdown("Seu assistente pessoal para bem-estar interior e reflexão.")
st.markdown("---")

# Seleção do Tom
st.subheader("1. Escolha o tom do seu guia")
tom = st.radio(
    "Que tipo de guia você prefere hoje?",
    ["amigo", "sábio", "direto"],
    captions=["Uma conversa calorosa e empática.", "Uma reflexão profunda e calma.", "Uma mensagem clara e objetiva."],
    horizontal=True
)

# Campo para o usuário descrever o sentimento
st.subheader("2. Descreva sua necessidade")
sentimento_input = st.text_area(
    "Como você está se sentindo ou o que você busca?",
    placeholder="Ex: 'Estou me sentindo um pouco triste hoje' ou 'Preciso de inspiração para começar o dia'",
    height=100
)

# Botão para gerar a mensagem
if st.button("Receber Mensagem"):
    # Validações antes de chamar a API
    if not google_api_key:
        st.error("Por favor, insira sua Google API Key na barra lateral ou configure-a nos segredos da aplicação.")
    elif not sentimento_input:
        st.warning("Por favor, descreva como você está se sentindo.")
    else:
        # Mostra uma mensagem de "pensando..."
        with st.spinner("Conectando-se com a sabedoria do universo..."):
            mensagem = gerar_mensagem_espiritual(google_api_key, sentimento_input, tom)

        # Exibe a mensagem gerada
        st.success("Aqui está uma mensagem para você:")
        # O st.markdown interpreta a formatação de negrito e quebras de linha que o modelo enviar
        st.markdown(mensagem)

# --- Rodapé ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 0.8em;'>"
    "Lembre-se: O CoachAI Espiritual é uma ferramenta de apoio e não substitui aconselhamento profissional."
    "</div>",
    unsafe_allow_html=True
)
