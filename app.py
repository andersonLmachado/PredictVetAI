import streamlit as st
import requests
import json
import uuid

# Application Title
st.title("Assistente Veterinário PredictVet")

# API Endpoint
API_URL = "http://localhost:8000/run"
USER_ID = "streamlit_user"

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize sessionId if it doesn't exist
if "sessionId" not in st.session_state:
    st.session_state.sessionId = str(uuid.uuid4())

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
                payload = {
                    "appName": "PredictVet",
                    "userId": USER_ID,  # This uses the existing USER_ID = "streamlit_user"
                    "sessionId": st.session_state.sessionId,
                    "newMessage": {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ],
                        "role": "user"
                    },
                    "streaming": False
                }
                response = requests.post(API_URL, json=payload)
                response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
                
                api_response = response.json()
                assistant_response = api_response.get("output")

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
