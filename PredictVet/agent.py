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

        if not available_categories or (isinstance(available_categories, list) and available_categories and "Error:" in available_categories[0]):
            # Clear sensitive state but keep dialog stage for potential retry if applicable,
            # or reset completely if error is persistent.
            agent_session_state["selected_category"] = None
            # agent_session_state.clear() # Consider if a full clear is always best here
            return f"Desculpe, houve um problema ao carregar as categorias. ({available_categories[0] if available_categories else 'Nenhuma categoria disponível.'}). Por favor, tente iniciar a conversa novamente mais tarde."

        # Check if it's the initial interaction or user requests category listing
        if not user_message_text or user_message_text == "INICIAR_FLUXO":
            response_text = "Olá! Para começarmos, por favor, escolha uma categoria de sintomas abaixo:\n" + "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return response_text

        # User has provided input, try to match it
        selected_category_name = None
        try:
            user_input_as_int = int(user_message_text)
            if 1 <= user_input_as_int <= len(available_categories):
                selected_category_name = available_categories[user_input_as_int - 1]
        except ValueError:
            # Not a number, try direct match (case-insensitive)
            for cat in available_categories:
                if user_message_text.lower() == cat.lower():
                    selected_category_name = cat
                    break
        
        if selected_category_name:
            agent_session_state["selected_category"] = selected_category_name
            agent_session_state["dialog_stage"] = "awaiting_complaint"
            
            queixas = ListarQueixasPorCategoria(categoria=selected_category_name)
            if not queixas or (isinstance(queixas, list) and queixas and "Error:" in queixas[0]):
                agent_session_state["dialog_stage"] = "awaiting_category" # Revert state
                agent_session_state["selected_category"] = None
                error_msg = queixas[0] if queixas and isinstance(queixas, list) else "Nenhuma queixa disponível."
                # Re-list categories for the user
                category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
                return f"Houve um problema ao listar as queixas para '{selected_category_name}': {error_msg}. Por favor, escolha uma categoria novamente:\n{category_list_str}"

            # Successfully got complaints
            response_text = f"Entendido. Queixas comuns para '{selected_category_name}':\n" + \
                            "\n".join([f"{i+1}. {q}" for i, q in enumerate(queixas)]) + \
                            "\nPor favor, selecione uma queixa."
            return response_text
        else:
            # Invalid input
            response_text = "Opção inválida. Por favor, escolha uma categoria da lista:\n" + \
                            "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return response_text

    # Stage: "awaiting_complaint"
    elif dialog_stage == "awaiting_complaint":
        selected_category = agent_session_state.get("selected_category")
        if not selected_category:
            agent_session_state["dialog_stage"] = "awaiting_category"
            # Attempt to list categories again for a smoother recovery
            available_categories = ListarCategorias()
            if not available_categories or (isinstance(available_categories, list) and available_categories and "Error:" in available_categories[0]):
                return "Parece que nenhuma categoria foi selecionada e houve um problema ao recarregar as categorias. Por favor, tente reiniciar a conversa."
            category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return f"Parece que nenhuma categoria foi selecionada. Por favor, escolha uma categoria primeiro:\n{category_list_str}"

        queixas_validas = ListarQueixasPorCategoria(categoria=selected_category)
        if not queixas_validas or (isinstance(queixas_validas, list) and queixas_validas and "Error:" in queixas_validas[0]):
            agent_session_state["dialog_stage"] = "awaiting_category" # Revert state
            agent_session_state["selected_category"] = None
            error_msg = queixas_validas[0] if queixas_validas and isinstance(queixas_validas, list) else "Nenhuma queixa disponível."
            # Re-list categories for the user
            available_categories = ListarCategorias() # Attempt to get categories for recovery
            if not available_categories or (isinstance(available_categories, list) and "Error:" in available_categories[0]):
                 return f"Desculpe, houve um problema ao carregar as queixas para '{selected_category}' ({error_msg}) e também ao recarregar as categorias. Por favor, tente reiniciar a conversa."
            category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return f"Desculpe, houve um problema ao carregar as queixas para '{selected_category}': {error_msg}. Por favor, tente selecionar uma categoria novamente:\n{category_list_str}"

        selected_complaint_name = None
        try:
            user_input_as_int = int(user_message_text)
            if 1 <= user_input_as_int <= len(queixas_validas):
                selected_complaint_name = queixas_validas[user_input_as_int - 1]
        except ValueError:
            # Not a number, try direct match (case-insensitive)
            for q_valida in queixas_validas:
                if user_message_text.lower() == q_valida.lower():
                    selected_complaint_name = q_valida
                    break
        
        if selected_complaint_name:
            agent_session_state["selected_complaint"] = selected_complaint_name
            agent_session_state["dialog_stage"] = "awaiting_specific_answer"
            pergunta = GerarPerguntaEspecifica(queixa=selected_complaint_name)
            
            if "Error:" in pergunta: # Assuming error is returned as a string starting with "Error:"
                 agent_session_state["dialog_stage"] = "awaiting_complaint" # Revert to complaint selection
                 agent_session_state["selected_complaint"] = None
                 # Re-list complaints for the user
                 complaint_list_str = "\n".join([f"{i+1}. {q}" for i, q in enumerate(queixas_validas)])
                 return f"Houve um problema ao gerar a pergunta para '{selected_complaint_name}': {pergunta}. Por favor, selecione a queixa novamente para '{selected_category}':\n{complaint_list_str}"
            
            agent_session_state["last_question_asked"] = pergunta
            return pergunta
        else:
            # Invalid input, re-list complaints
            complaint_list_str = "\n".join([f"{i+1}. {q}" for i, q in enumerate(queixas_validas)])
            return f"Opção inválida. Por favor, selecione uma queixa válida da lista para '{selected_category}':\n{complaint_list_str}"

    # Stage: "awaiting_specific_answer"
    elif dialog_stage == "awaiting_specific_answer":
        selected_complaint = agent_session_state.get("selected_complaint")
        last_question = agent_session_state.get("last_question_asked")

        if not selected_complaint or not last_question:
            # Critical state missing, reset to beginning
            agent_session_state["dialog_stage"] = "awaiting_category"
            agent_session_state["selected_category"] = None
            agent_session_state["selected_complaint"] = None
            agent_session_state["collected_answers"] = {}
            agent_session_state["last_question_asked"] = None
            # Attempt to list categories again for a smoother recovery
            available_categories = ListarCategorias()
            if not available_categories or (isinstance(available_categories, list) and available_categories and "Error:" in available_categories[0]):
                return "Ocorreu um erro no fluxo (faltando queixa ou pergunta) e houve um problema ao recarregar as categorias. Por favor, tente reiniciar a conversa."
            category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return f"Ocorreu um erro no fluxo da conversa (queixa ou pergunta anterior não encontrada). Vamos recomeçar. Por favor, escolha uma categoria:\n{category_list_str}"
        
        agent_session_state["collected_answers"][last_question] = user_message_text
        agent_session_state["dialog_stage"] = "generating_analysis"
        # Fall through to "generating_analysis"

    # Stage: "generating_analysis" (allow fall-through by using 'if' not 'elif')
    if agent_session_state.get("dialog_stage") == "generating_analysis": # Note: Intentionally 'if' to allow fall-through
        selected_complaint = agent_session_state.get("selected_complaint")
        collected_answers = agent_session_state.get("collected_answers")

        if not selected_complaint: # Should have been caught earlier, but as a safeguard
            agent_session_state["dialog_stage"] = "awaiting_category"
            agent_session_state["selected_category"] = None
            agent_session_state["selected_complaint"] = None
            agent_session_state["collected_answers"] = {}
            agent_session_state["last_question_asked"] = None
            available_categories = ListarCategorias()
            if not available_categories or (isinstance(available_categories, list) and available_categories and "Error:" in available_categories[0]):
                return "Ocorreu um erro antes de gerar a análise (queixa não encontrada) e houve um problema ao recarregar as categorias. Por favor, tente reiniciar a conversa."
            category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return f"Ocorreu um erro antes de gerar a análise (queixa não encontrada). Vamos recomeçar. Por favor, escolha uma categoria:\n{category_list_str}"

        prompt_final_para_llm = GerarAnaliseFinal(queixa_selecionada=selected_complaint, respostas_coletadas=collected_answers)
        
        final_analysis_text = ""
        try:
            # Assuming .run() is the correct method for LlmAgent based on common ADK patterns
            # and the AttributeError for generate_content.
            # The structure of final_analysis_response from .run() might also need checking.
            # Reverting to original generate_content, assuming the issue is with mocking Pydantic model instances.
            final_analysis_response = llm_component.generate_content(prompt_final_para_llm)
            
            # Ensure text extraction is robust
            if hasattr(final_analysis_response, 'text'):
                final_analysis_text = final_analysis_response.text
            elif isinstance(final_analysis_response, (str, dict)): # ADK might wrap it differently
                 # Attempt to extract text if it's a dict, or use as is if str
                if isinstance(final_analysis_response, dict) and 'text' in final_analysis_response:
                    final_analysis_text = final_analysis_response['text']
                elif isinstance(final_analysis_response, str):
                    final_analysis_text = final_analysis_response
                else: # Fallback for unknown structure
                    final_analysis_text = str(final_analysis_response)
            else: # Fallback for other types
                final_analysis_text = str(final_analysis_response)

            if not final_analysis_text: # Handle cases where text extraction yields empty
                raise ValueError("A resposta da análise final estava vazia.")

        except Exception as e:
            # Reset state before returning error to allow user to restart cleanly
            agent_session_state["dialog_stage"] = "awaiting_category"
            agent_session_state["selected_category"] = None
            agent_session_state["selected_complaint"] = None
            agent_session_state["collected_answers"] = {}
            agent_session_state["last_question_asked"] = None
            # Attempt to list categories again for a smoother recovery
            available_categories = ListarCategorias()
            if not available_categories or (isinstance(available_categories, list) and available_categories and "Error:" in available_categories[0]):
                 return f"Desculpe, ocorreu um erro ao gerar a análise final ({e}) e também ao recarregar as categorias. Por favor, tente reiniciar a conversa."
            category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
            return f"Desculpe, ocorreu um erro ao gerar a análise final: {e}. Vamos tentar novamente do início. Por favor, escolha uma categoria:\n{category_list_str}"

        # CRUCIAL: Reset state for the next conversation BEFORE returning the analysis
        agent_session_state["dialog_stage"] = "awaiting_category"
        agent_session_state["selected_category"] = None
        agent_session_state["selected_complaint"] = None
        agent_session_state["collected_answers"] = {}
        agent_session_state["last_question_asked"] = None
        
        return final_analysis_text
    
    # Fallback if no stage is matched (should ideally not be reached if logic is correct)
    # Reset state and try to guide user back to start
    agent_session_state["dialog_stage"] = "awaiting_category"
    agent_session_state["selected_category"] = None
    agent_session_state["selected_complaint"] = None
    agent_session_state["collected_answers"] = {}
    agent_session_state["last_question_asked"] = None
    available_categories = ListarCategorias()
    if not available_categories or (isinstance(available_categories, list) and available_categories and "Error:" in available_categories[0]):
        return "Ocorreu um erro inesperado no fluxo da conversa e não foi possível carregar as categorias. Por favor, tente reiniciar a conversa."
    category_list_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_categories)])
    return f"Ocorreu um erro inesperado no fluxo da conversa. Vamos recomeçar. Por favor, escolha uma categoria:\n{category_list_str}"

    # --- Fim da lógica de diálogo ---

# 3. MUDANÇA AQUI: Use diretamente o LlmAgent como root_agent
root_agent = llm_component

# Remova a classe PredictVetAppAgent por enquanto

