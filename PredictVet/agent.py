from PredictVet.tools import all_tools
from google.adk.agents import LlmAgent
from PredictVet.tools import (
    load_dataframes,
    ListarCategorias,
    ListarQueixasPorCategoria,
    GerarPerguntaEspecifica,
    # ProcessarRespostaPergunta,
    GerarAnaliseFinal
)
# import google.generativeai.types as genai_types # Comente ou remova esta linha

# Opção 1: Importar do google.genai
try:
    from google.genai import types
    Content = types.Content
    Part = types.Part
except ImportError:
    # Opção 2: Usar apenas strings ou dict como fallback
    Content = dict  # Fallback temporário
    Part = dict     # Fallback temporário

# Load dataframes when the module is loaded
load_dataframes()

# 1. Instancie seu LlmAgent como um componente
llm_component = LlmAgent(
    model="gemini-2.0-flash-exp",
    name="PredictVetLLMComponent",
    description="Componente LLM para o PredictVet, responsável pela geração de texto.",
    instruction="Você é um assistente de IA. Responda com base no prompt fornecido.",
    tools=all_tools
)

# 2. Sua função de lógica de diálogo
def handle_predictvet_interaction(
    new_message: Content, # MODIFICADO AQUI: Ou o tipo esperado pela sua aplicação
    agent_session_state: dict,
    **kwargs
) -> str:
    """
    Processa uma nova mensagem do usuário e gerencia o fluxo do diálogo para PredictVet.
    Utiliza o llm_component para geração de texto quando necessário.
    """
    # Ensure agent_session_state is initialized
    if not isinstance(agent_session_state, dict): # ADK might pass None initially
        agent_session_state = {}

    # Initialize state variables if they don't exist
    agent_session_state.setdefault("dialog_stage", "awaiting_category")
    agent_session_state.setdefault("selected_category", None)
    agent_session_state.setdefault("selected_complaint", None)
    agent_session_state.setdefault("collected_answers", {})
    agent_session_state.setdefault("last_question_asked", None)

    user_message_text = ""
    # Correctly parse new_message. Assuming it's a genai.types.Content object
    if hasattr(new_message, 'parts') and new_message.parts:
        part = new_message.parts[0]
        if hasattr(part, 'text'):
            user_message_text = part.text.strip()
    elif isinstance(new_message, str): # Fallback for simple string input
        user_message_text = new_message.strip()
    # Add more robust parsing if new_message can be other types (e.g., dict from JSON)

    dialog_stage = agent_session_state.get("dialog_stage")

    # --- Início da lógica de diálogo (adaptada da sua função process_message) ---

    # Stage: "awaiting_category"
    if dialog_stage == "awaiting_category":
        available_categories = ListarCategorias()
        if not available_categories or (available_categories and "Error:" in available_categories[0]):
            agent_session_state.clear()
            return f"Desculpe, houve um problema ao carregar as categorias: {available_categories[0] if available_categories else 'Nenhuma categoria disponível.'}. Por favor, tente iniciar a conversa novamente mais tarde."

        if user_message_text and user_message_text in available_categories:
            agent_session_state["selected_category"] = user_message_text
            agent_session_state["dialog_stage"] = "awaiting_complaint"
            queixas = ListarQueixasPorCategoria(categoria=user_message_text)
            if not queixas or (queixas and "Error:" in queixas[0]):
                agent_session_state["dialog_stage"] = "awaiting_category"
                agent_session_state["selected_category"] = None
                return f"Houve um problema ao listar as queixas para '{user_message_text}': {queixas[0] if queixas else 'Nenhuma queixa disponível.'}. Por favor, escolha uma categoria novamente."
            return f"Entendido. Queixas comuns para '{user_message_text}':\n" + "\n".join([f"- {q}" for q in queixas]) + "\nPor favor, selecione uma queixa."
        else:
            return "Olá! Para começarmos, por favor, escolha uma categoria de sintomas abaixo:\n" + "\n".join([f"- {c}" for c in available_categories])

    # Stage: "awaiting_complaint"
    elif dialog_stage == "awaiting_complaint":
        selected_category = agent_session_state.get("selected_category")
        if not selected_category:
            agent_session_state["dialog_stage"] = "awaiting_category"
            return "Parece que nenhuma categoria foi selecionada. Por favor, escolha uma categoria primeiro."

        queixas_validas = ListarQueixasPorCategoria(categoria=selected_category)
        if not queixas_validas or (queixas_validas and "Error:" in queixas_validas[0]):
            agent_session_state["dialog_stage"] = "awaiting_category"
            agent_session_state["selected_category"] = None
            return f"Desculpe, houve um problema ao carregar as queixas para '{selected_category}': {queixas_validas[0] if queixas_validas else 'Nenhuma queixa disponível.'}. Por favor, tente selecionar a categoria novamente."

        if user_message_text and user_message_text in queixas_validas:
            agent_session_state["selected_complaint"] = user_message_text
            agent_session_state["dialog_stage"] = "awaiting_specific_answer"
            pergunta = GerarPerguntaEspecifica(queixa=user_message_text)
            if "Error:" in pergunta:
                 agent_session_state["dialog_stage"] = "awaiting_complaint"
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

        if not selected_complaint or not last_question:
            agent_session_state["dialog_stage"] = "awaiting_category"
            return "Ocorreu um erro no fluxo. Vamos recomeçar. Por favor, escolha uma categoria."
        
        agent_session_state["collected_answers"][last_question] = user_message_text
        agent_session_state["dialog_stage"] = "generating_analysis"
        # Fall through to "generating_analysis"

    # Stage: "generating_analysis" (allow fall-through by using 'if' not 'elif')
    if agent_session_state.get("dialog_stage") == "generating_analysis":
        selected_complaint = agent_session_state.get("selected_complaint")
        collected_answers = agent_session_state.get("collected_answers")

        if not selected_complaint:
            agent_session_state["dialog_stage"] = "awaiting_category"
            return "Ocorreu um erro antes de gerar a análise. Vamos recomeçar. Por favor, escolha uma categoria."

        prompt_final_para_llm = GerarAnaliseFinal(queixa_selecionada=selected_complaint, respostas_coletadas=collected_answers)
        
        try:
            # MODIFICADO: Chame o método no llm_component
            final_analysis_response = llm_component.generate_content(prompt_final_para_llm)
            final_analysis_text = final_analysis_response.text if hasattr(final_analysis_response, 'text') else str(final_analysis_response)

        except Exception as e:
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
    
    # Fallback if no stage is matched
    agent_session_state["dialog_stage"] = "awaiting_category"
    return "Ocorreu um erro inesperado no fluxo da conversa. Vamos recomeçar. Por favor, escolha uma categoria."

    # --- Fim da lógica de diálogo ---

# 3. MUDANÇA AQUI: Use diretamente o LlmAgent como root_agent
root_agent = llm_component

# Remova a classe PredictVetAppAgent por enquanto

