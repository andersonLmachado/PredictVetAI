import streamlit as st
import requests
import json
import uuid

# Application Title
st.title("PredictVet")

# Constants
ADK_BASE_URL = "http://localhost:8000"
APP_NAME = "PredictVet"
USER_ID = "streamlit_user"
# API_URL = "http://localhost:8000/run" # Old API URL, commented out

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize ADK session ID if it doesn't exist
if "adk_session_id" not in st.session_state:
    st.session_state.adk_session_id = str(uuid.uuid4())

# Initialize other session state variables for dialog flow
if "current_interaction_type" not in st.session_state:
    st.session_state.current_interaction_type = "show_categories" # Initial state
if "available_options" not in st.session_state:
    st.session_state.available_options = []
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

# Function to communicate with the ADK agent
def call_agent_api(message_text):
    try:
        RUN_API_URL = f"{ADK_BASE_URL}/run"
        payload = {
            "app_name": APP_NAME,
            "user_id": USER_ID,
            "session_id": st.session_state.adk_session_id,
            "new_message": {
                "parts": [{"text": message_text}],
                "role": "user"
            },
            "streaming": False # Keep as False for simpler response handling
        }
        response = requests.post(RUN_API_URL, json=payload)
        response.raise_for_status()
        
        api_response_list = response.json()
        assistant_response_text = None
        
        for event in api_response_list:
            if "content" in event and event["content"].get("role") == "model":
                for part in event["content"].get("parts", []):
                    if "text" in part:
                        assistant_response_text = part["text"]
                        break
                if assistant_response_text:
                    break
        
        return assistant_response_text

    except requests.exceptions.RequestException as e:
        error_message = f"Erro ao conectar com o agente: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        return None
    except json.JSONDecodeError:
        error_message = "Erro ao decodificar a resposta do agente. A API retornou um JSON inválido."
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        return None
    except Exception as e:
        error_message = f"Ocorreu um erro inesperado: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        return None

# One-time session creation/activation with ADK
if "session_initialized" not in st.session_state:
    try:
        session_creation_url = f"{ADK_BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{st.session_state.adk_session_id}"
        response = requests.post(session_creation_url, json={}) # Empty JSON body
        response.raise_for_status()
        st.session_state.session_initialized = True
        
        # Trigger initial message to get categories if no messages exist
        if not st.session_state.messages:
            with st.spinner("Carregando categorias..."):
                initial_response = call_agent_api("INICIAR_FLUXO") # Or any other predefined initial message
                if initial_response:
                    st.session_state.messages.append({"role": "assistant", "content": initial_response})
                    # The agent's response will guide the user, e.g., list categories.
                    # Based on agent's response, you might update current_interaction_type, etc.
                    # For now, the agent's text is the primary guide.
                    if "Olá! Para começarmos, por favor, escolha uma categoria de sintomas abaixo:" in initial_response:
                        st.session_state.current_interaction_type = "show_categories"
                else:
                    st.error("Não foi possível obter a lista inicial de categorias do agente.")
                    st.session_state.messages.append({"role": "assistant", "content": "Não foi possível obter a lista inicial de categorias."})

    except requests.exceptions.RequestException as e:
        error_msg = f"Falha ao inicializar a sessão com o agente ADK: {e}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    except Exception as e:
        error_msg = f"Ocorreu um erro inesperado durante a inicialização da sessão: {e}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Qual é a sua pergunta?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            assistant_response_text = call_agent_api(prompt)
            if assistant_response_text:
                st.markdown(assistant_response_text)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response_text})
                
                # Update interaction type based on keywords in response (simplified)
                # This is a basic way to infer state; agent could send structured state if needed.
                if "Olá! Para começarmos, por favor, escolha uma categoria de sintomas abaixo:" in assistant_response_text or \
                   "Por favor, escolha uma categoria novamente." in assistant_response_text or \
                   "Vamos recomeçar. Por favor, escolha uma categoria." in assistant_response_text:
                    st.session_state.current_interaction_type = "show_categories"
                elif "Entendido. Queixas comuns para" in assistant_response_text and "Por favor, selecione uma queixa." in assistant_response_text:
                    st.session_state.current_interaction_type = "show_complaints"
                elif "No specific question found for queixa:" not in assistant_response_text and \
                     "Error:" not in assistant_response_text and \
                     ("?" in assistant_response_text and not assistant_response_text.startswith("Entendido. Queixas comuns para")): # Heuristic for a question
                    st.session_state.current_interaction_type = "show_question"
                    st.session_state.current_question = assistant_response_text # Store the question
                else: # Could be final analysis or an error message from the agent not fitting other categories.
                    st.session_state.current_interaction_type = "show_analysis" 
                    # If it's an analysis, the agent should have reset its internal state.
                    # If the user types again, it should trigger the "awaiting_category" stage in the agent.

            else:
                # Error messages are already handled and added to chat by call_agent_api
                # but ensure something is displayed if null response for other reasons.
                if not any(msg["content"].startswith("Erro") or msg["content"].startswith("Falha") for msg in st.session_state.messages[-2:]): # Avoid double error
                    err_msg = "O agente não retornou uma resposta."
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
