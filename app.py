import streamlit as st
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.main_agent import create_main_agent
from agent.chat_history import ChatHistoryManager
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


# ════════════════════════════════════════════════════
# CONFIGURATION DE LA PAGE
# ════════════════════════════════════════════════════
st.set_page_config(
    page_title="Smartovate — Agent Autonome",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)


def charger_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

charger_css()


# ════════════════════════════════════════════════════
# RESSOURCES MISES EN CACHE
# ════════════════════════════════════════════════════
@st.cache_resource
def get_agent():
    return create_main_agent()


@st.cache_resource
def get_history_manager():
    return ChatHistoryManager()


agent = get_agent()
history_manager = get_history_manager()


# ════════════════════════════════════════════════════
# INITIALISATION DE LA SESSION
# ════════════════════════════════════════════════════
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "premiere_visite" not in st.session_state:
    st.session_state.premiere_visite = True


def charger_conversation(session_id: str):
    st.session_state.session_id = session_id
    st.session_state.messages = history_manager.recuperer_messages(session_id)
    st.session_state.premiere_visite = False


def nouvelle_conversation():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.premiere_visite = True


# ════════════════════════════════════════════════════
# SIDEBAR — Marque + historique des conversations
# ════════════════════════════════════════════════════
with st.sidebar:
    col1, col2 = st.columns([1, 4])

    with col1:
        st.image("images/agent.png", width=200)

    with col2:
        st.markdown("""
            <div class="smv-brand-text">Smartovate</div>
            <div class="smv-brand-sub">Agent Autonome</div>
        """, unsafe_allow_html=True)

    if st.button("＋  Nouvelle conversation", use_container_width=True, type="primary"):
        nouvelle_conversation()
        st.rerun()

    st.markdown('<div class="smv-section-label">Conversations récentes</div>', unsafe_allow_html=True)

    sessions = history_manager.lister_sessions()

    if not sessions:
        st.caption("Aucune conversation pour le moment.")
    else:
        for session in sessions[:20]:
            titre = session["premier_message"] or "Nouvelle conversation"
            titre_court = titre[:32] + "…" if len(titre) > 32 else titre
            est_active = session["session_id"] == st.session_state.session_id

            col1, col2 = st.columns([5, 1])
            with col1:
                prefixe = "● " if est_active else ""
                if st.button(f"{prefixe}{titre_court}", key=f"sess_{session['session_id']}", use_container_width=True):
                    charger_conversation(session["session_id"])
                    st.rerun()
            with col2:
                if st.button("✕", key=f"del_{session['session_id']}"):
                    history_manager.supprimer_session(session["session_id"])
                    if session["session_id"] == st.session_state.session_id:
                        nouvelle_conversation()
                    st.rerun()

    st.markdown('<div class="smv-section-label">Outils connectés</div>', unsafe_allow_html=True)
    st.markdown("""
        <span class="smv-tool-pill"><span class="smv-dot"></span>Recherche web</span>
        <span class="smv-tool-pill"><span class="smv-dot"></span>Base SQL</span>
        <span class="smv-tool-pill"><span class="smv-dot"></span>Météo</span>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# EN-TÊTE PRINCIPAL
# ════════════════════════════════════════════════════
titre_page = "Nouvelle conversation"
if st.session_state.messages:
    premier_msg_user = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), None)
    if premier_msg_user:
        titre_page = premier_msg_user[:55] + ("…" if len(premier_msg_user) > 55 else "")

st.markdown(f'<p class="smv-topbar-title">{titre_page}</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="smv-topbar-sub">Propulsé par AWS Bedrock · Claude · LangGraph</p>',
    unsafe_allow_html=True
)


# ════════════════════════════════════════════════════
# MESSAGE D'ACCUEIL
# ════════════════════════════════════════════════════
if len(st.session_state.messages) == 0 and st.session_state.premiere_visite:
    with st.chat_message("assistant", avatar="images/bot.png"):
        st.markdown("**Bonjour, je suis l'agent de Smartovate.**")
        st.markdown(
            "Je peux interroger le web, vos données internes et les services météo "
            "pour vous répondre avec des informations vérifiées plutôt que des suppositions."
        )
        st.markdown("""
            <div class="smv-welcome-grid">
                <div class="smv-welcome-card"><span class="smv-cc-title">Recherche web</span>Actualités et données récentes</div>
                <div class="smv-welcome-card"><span class="smv-cc-title">Données internes</span>Employés, projets, ventes</div>
                <div class="smv-welcome-card"><span class="smv-cc-title">Météo</span>Conditions et prévisions à 7 jours</div>
            </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# HISTORIQUE DE LA CONVERSATION
# ════════════════════════════════════════════════════
for idx, message in enumerate(st.session_state.messages):

    if message["role"] == "user":
        with st.container(key=f"msg_user_{idx}"):
            with st.chat_message("user", avatar="images/user.png"):
                st.markdown(message["content"])

    else:
        # 🔥 assistant en pleine largeur (IMPORTANT)
        with st.chat_message("assistant", avatar="images/bot.png"):
            st.markdown(message["content"])

        if message.get("etapes_outils"):
            with st.expander("Étapes de raisonnement"):
                for etape in message["etapes_outils"]:
                    st.markdown(etape)


# ════════════════════════════════════════════════════
# ZONE DE SAISIE
# ════════════════════════════════════════════════════
question = st.chat_input("Écrivez votre message à l'agent…")

if question:
    st.session_state.premiere_visite = False

    with st.container(key="msg_user_live"):
        with st.chat_message("user", avatar="images/user.png"):
            st.markdown(question)

    st.session_state.messages.append({"role": "user", "content": question, "etapes_outils": []})
    history_manager.sauvegarder_message(st.session_state.session_id, "user", question)

    with st.chat_message("assistant", avatar="images/bot.png"):
        with st.spinner("L'agent consulte ses outils…"):

            config = {
                "configurable": {"thread_id": st.session_state.session_id},
                "recursion_limit": 21
            }

            try:
                resultat = agent.invoke(
                    {"messages": [HumanMessage(content=question)]},
                    config=config
                )
                messages = resultat["messages"]
                reponse_finale = messages[-1].content

                etapes_outils = []
                for msg in messages:
                    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            etapes_outils.append(
                                f"**Action — {tool_call['name']}**  \n"
                                f"Paramètres : `{tool_call['args']}`"
                            )
                    elif isinstance(msg, ToolMessage):
                        etapes_outils.append(f"**Observation**  \n{msg.content}")

            except Exception as e:
                reponse_finale = f"Une erreur s'est produite : {str(e)}"
                etapes_outils = []

        st.markdown(reponse_finale)

        if etapes_outils:
            with st.expander("Étapes de raisonnement"):
                for etape in etapes_outils:
                    st.markdown(etape)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reponse_finale,
        "etapes_outils": etapes_outils
    })
    history_manager.sauvegarder_message(
        st.session_state.session_id, "assistant", reponse_finale, etapes_outils
    )

    st.rerun()