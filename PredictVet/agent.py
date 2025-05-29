from google.adk.agents import LlmAgent
from PredictVet.tools import (
    load_dataframes,
    ListarCategorias,
    ListarQueixasPorCategoria,
    GerarPerguntaEspecifica,
    ProcessarRespostaPergunta,
    GerarAnaliseFinal
)

# Load dataframes when the module is loaded
load_dataframes()

root_agent = LlmAgent(
    model="gemini-2.0-flash-exp", # Assuming this is the correct model name
    name="PredictVet",
    description="PredictVet é um assistente veterinário que ajuda os tutores de animais com dúvidas relacionadas à saúde de seus pets. Ele fornece informações sobre sintomas, tratamentos e cuidados gerais para diversos animais.",
    instruction="""Você é um assistente veterinário especializado em ajudar médicos veterinários no momento do atendimento de cães e gatos. Você deve fornecer informações precisas e úteis sobre sintomas, tratamentos e cuidados gerais para diferentes tipos de raças, quando for informado o diagnóstico pelo usuário. Seja carinhoso, atencioso e profissional em suas respostas. Sempre que possível, forneça informações adicionais sobre perguntas sugeridas ao tutor após o relato dos sintomas do animal. Lembrar que o usuário é um Médico Veterinário e não um tutor de animal de estimação, por isso não é necessário mencionar que é necessário levar o animal ao veterinário, pois o usuário já é um profissional da área. Foque em fornecer informações técnicas e relevantes para o diagnóstico e tratamento do animal.""",
    tools=[ListarCategorias, ListarQueixasPorCategoria, GerarPerguntaEspecifica, ProcessarRespostaPergunta, GerarAnaliseFinal]
)

def process_message(self: LlmAgent, new_message, agent_session_state: dict, **kwargs) -> str:
    """
    Processes a new message from the user and manages the dialog flow.
    """
    # Ensure agent_session_state is initialized
    if not agent_session_state:
        agent_session_state.update({
            "dialog_stage": "awaiting_category",
            "selected_category": None,
            "selected_complaint": None,
            "collected_answers": {},
            "last_question_asked": None
        })
    
    # Default to "awaiting_category" if dialog_stage is missing
    if "dialog_stage" not in agent_session_state:
        agent_session_state["dialog_stage"] = "awaiting_category"

    user_message_text = ""
    if isinstance(new_message, dict) and "parts" in new_message and new_message["parts"]:
        # Standard ADK message format
        user_message_text = new_message["parts"][-1].get("text", "").strip()
    elif isinstance(new_message, str): 
        # Simple string input (for testing or direct calls)
        user_message_text = new_message.strip()
    else:
        # Fallback or error if message format is unexpected
        return "Formato de mensagem inválido."

    dialog_stage = agent_session_state.get("dialog_stage")

    # Stage: "awaiting_category"
    if dialog_stage == "awaiting_category":
        available_categories = ListarCategorias()
        if "Error:" in available_categories[0] if available_categories else True:
             # Reset state and inform about the error
            agent_session_state.clear() # Clear state to restart
            return f"Desculpe, houve um problema ao carregar as categorias: {available_categories[0] if available_categories else 'Nenhuma categoria disponível.'}. Por favor, tente iniciar a conversa novamente mais tarde."

        if user_message_text and user_message_text in available_categories:
            agent_session_state["selected_category"] = user_message_text
            agent_session_state["dialog_stage"] = "awaiting_complaint"
            queixas = ListarQueixasPorCategoria(categoria=user_message_text)
            if "Error:" in queixas[0] if queixas else True:
                # Handle error, maybe reset or ask for category again
                agent_session_state["dialog_stage"] = "awaiting_category" # Go back
                agent_session_state["selected_category"] = None
                return f"Houve um problema ao listar as queixas para '{user_message_text}': {queixas[0] if queixas else 'Nenhuma queixa disponível.'}. Por favor, escolha uma categoria novamente."
            return f"Entendido. Queixas comuns para '{user_message_text}':\n" + "\n".join([f"- {q}" for q in queixas]) + "\nPor favor, selecione uma queixa."
        else:
            # Initial message or invalid category
            return "Olá! Para começarmos, por favor, escolha uma categoria de sintomas abaixo:\n" + "\n".join([f"- {c}" for c in available_categories])

    # Stage: "awaiting_complaint"
    elif dialog_stage == "awaiting_complaint":
        selected_category = agent_session_state.get("selected_category")
        if not selected_category: # Should not happen if flow is correct
            agent_session_state["dialog_stage"] = "awaiting_category"
            return "Parece que nenhuma categoria foi selecionada. Por favor, escolha uma categoria primeiro."

        queixas_validas = ListarQueixasPorCategoria(categoria=selected_category)
        if "Error:" in queixas_validas[0] if queixas_validas else True:
            agent_session_state["dialog_stage"] = "awaiting_category" # Reset
            agent_session_state["selected_category"] = None
            return f"Desculpe, houve um problema ao carregar as queixas para '{selected_category}': {queixas_validas[0] if queixas_validas else 'Nenhuma queixa disponível.'}. Por favor, tente selecionar a categoria novamente."

        if user_message_text and user_message_text in queixas_validas:
            agent_session_state["selected_complaint"] = user_message_text
            agent_session_state["dialog_stage"] = "awaiting_specific_answer"
            pergunta = GerarPerguntaEspecifica(queixa=user_message_text)
            if "Error:" in pergunta:
                 agent_session_state["dialog_stage"] = "awaiting_complaint" # Go back
                 agent_session_state["selected_complaint"] = None
                 return f"Houve um problema ao gerar a pergunta para '{user_message_text}': {pergunta}. Por favor, selecione a queixa novamente."
            agent_session_state["last_question_asked"] = pergunta
            return pergunta
        else:
            return f"Por favor, selecione uma queixa válida da lista para '{selected_category}':\n" + "\n".join([f"- {q}" for q in queixas_validas])


    # Stage: "awaiting_specific_answer"
    elif dialog_stage == "awaiting_specific_answer":
        selected_complaint = agent_session_state.get("selected_complaint")
        last_question = agent_session_state.get("last_question_asked")

        if not selected_complaint or not last_question: # Should not happen
            agent_session_state["dialog_stage"] = "awaiting_category" # Reset
            return "Ocorreu um erro no fluxo. Vamos recomeçar. Por favor, escolha uma categoria."

        # ProcessarRespostaPergunta is mostly for state tracking by the agent/system
        # For this flow, we directly use the user's answer.
        # processamento_info = ProcessarRespostaPergunta(queixa=selected_complaint, pergunta_feita=last_question, resposta_usuario=user_message_text)
        
        agent_session_state["collected_answers"][last_question] = user_message_text
        agent_session_state["dialog_stage"] = "generating_analysis"
        # Fall through to "generating_analysis"

    # Stage: "generating_analysis"
    if agent_session_state.get("dialog_stage") == "generating_analysis": # Note: using `if` not `elif` to allow fall-through
        selected_complaint = agent_session_state.get("selected_complaint")
        collected_answers = agent_session_state.get("collected_answers")

        if not selected_complaint: # Should not happen
            agent_session_state["dialog_stage"] = "awaiting_category" # Reset
            return "Ocorreu um erro antes de gerar a análise. Vamos recomeçar. Por favor, escolha uma categoria."

        prompt_final_para_llm = GerarAnaliseFinal(queixa_selecionada=selected_complaint, respostas_coletadas=collected_answers)
        
        if "Informação de diagnóstico específica para esta queixa não disponível." in prompt_final_para_llm and "N/A" in prompt_final_para_llm:
             # Check if GerarAnaliseFinal returned a fallback string due to missing diagnostico_df or columns
             # This might indicate an issue with data loading or the CSV files themselves.
             # For now, we proceed, but this is a point for potential improvement in error feedback.
             pass


        try:
            # Use the agent's LLM to process this prompt
            final_analysis_response = self.generate_content(prompt_final_para_llm)
            final_analysis_text = final_analysis_response.text if hasattr(final_analysis_response, 'text') else str(final_analysis_response)

        except Exception as e:
            # Reset state and inform about the error
            agent_session_state.clear()
            agent_session_state["dialog_stage"] = "awaiting_category"
            return f"Desculpe, ocorreu um erro ao gerar a análise final: {e}. Vamos tentar novamente do início. Por favor, escolha uma categoria."

        # Reset for next interaction
        agent_session_state["dialog_stage"] = "awaiting_category"
        agent_session_state["selected_category"] = None
        agent_session_state["selected_complaint"] = None
        agent_session_state["collected_answers"] = {}
        agent_session_state["last_question_asked"] = None
        
        return final_analysis_text
    
    # Fallback if no stage is matched (should ideally not be reached)
    agent_session_state["dialog_stage"] = "awaiting_category" # Reset
    return "Ocorreu um erro inesperado no fluxo da conversa. Vamos recomeçar. Por favor, escolha uma categoria."

# Assign the custom process_message method to the agent instance
root_agent.process_message = process_message.__get__(root_agent, LlmAgent)

