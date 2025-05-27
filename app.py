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

# One-time session creation/activation with ADK
if "session_initialized" not in st.session_state:
    try:
        session_creation_url = f"{ADK_BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{st.session_state.adk_session_id}"
        response = requests.post(session_creation_url, json={})
        response.raise_for_status()  # Check for HTTP errors
        st.session_state.session_initialized = True
        # Optional: st.toast("Session initialized successfully!") # For debugging
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
            try:
                RUN_API_URL = f"{ADK_BASE_URL}/run"
                payload = {
                    "app_name": APP_NAME,
                    "user_id": USER_ID,
                    "session_id": st.session_state.adk_session_id,
                    "new_message": {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ],
                        "role": "user"
                    },
                    "streaming": False
                }
                response = requests.post(RUN_API_URL, json=payload)
                response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
                
                api_response_list = response.json()
                assistant_response = None
                
                # Itere sobre os eventos na lista
                for event in api_response_list:
                    # O exemplo que você deu mostra "content" com role "model" e "parts"
                    if "content" in event and event["content"].get("role") == "model":
                        for part in event["content"].get("parts", []):
                            if "text" in part:
                                assistant_response = part["text"]
                                break # Encontrou o texto, pode sair do loop de partes
                        if assistant_response:
                            break # Encontrou o texto principal, pode sair do loop de eventos

                if assistant_response:
                    st.markdown(assistant_response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                else:
                    st.error("O agente não retornou uma resposta válida.")
                    st.session_state.messages.append({"role": "assistant", "content": "O agente não retornou uma resposta válida."})

            except requests.exceptions.RequestException as e:
                error_message = f"Erro ao conectar com o agente: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except json.JSONDecodeError:
                error_message = "Erro ao decodificar a resposta do agente. A API retornou um JSON inválido."
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"Ocorreu um erro inesperado: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
