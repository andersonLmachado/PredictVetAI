from PredictVet.tools import all_tools
from google.adk.agents import LlmAgent
from PredictVet.tools import (
    load_dataframes,
    ListarCategorias,
    ListarQueixasPorCategoria,
    GerarPerguntaEspecifica,
    GerarAnaliseFinal
)

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
    instruction="Você é um assistente veterinário especializado em ajudar médicos veterinários no momento do atendimento de cães e gatos.",
    tools=all_tools
)

# 2. Função de lógica de diálogo REFINADA
def handle_predictvet_interaction(
    new_message: Content,
    agent_session_state: dict,
    **kwargs
) -> str:
    """
    Processa uma nova mensagem do usuário e gerencia o fluxo do diálogo para PredictVet.
    Versão refinada que é mais proativa na apresentação de opções.
    """
    # Ensure agent_session_state is initialized
    if not isinstance(agent_session_state, dict):
        agent_session_state = {}

    # Initialize state variables if they don't exist
    agent_session_state.setdefault("current_step", "initial")
    agent_session_state.setdefault("selected_category", None)
    agent_session_state.setdefault("selected_complaint", None)
    agent_session_state.setdefault("collected_answers", {})
    agent_session_state.setdefault("last_question_asked", None)

    user_message_text = ""
    # Parse new_message
    if hasattr(new_message, 'parts') and new_message.parts:
        part = new_message.parts[0]
        if hasattr(part, 'text'):
            user_message_text = part.text.strip()
    elif isinstance(new_message, str):
        user_message_text = new_message.strip()

    current_step = agent_session_state.get("current_step")

    # --- ESTADO INICIAL OU REINÍCIO ---
    if current_step == "initial" or user_message_text.upper() in ["INICIAR_FLUXO", "INICIAR", "COMEÇAR"]:
        # Carrega categorias e apresenta mensagem de boas-vindas com lista
        available_categories = ListarCategorias()
        
        if not available_categories or (available_categories and "Error:" in available_categories[0]):
            agent_session_state.clear()
            return f"❌ Desculpe, houve um problema ao carregar as categorias: {available_categories[0] if available_categories else 'Nenhuma categoria disponível.'}. Por favor, tente novamente mais tarde."

        # Formata a lista de categorias numerada
        categories_list = ""
        for i, categoria in enumerate(available_categories, 1):
            categories_list += f"{i}. {categoria}\n"

        # Atualiza o estado
        agent_session_state["current_step"] = "choose_category"
        agent_session_state["available_categories"] = available_categories

        return f"""🐾 **Olá! Eu sou o PredictVet**, seu assistente veterinário especializado.

Estou aqui para ajudar médicos veterinários com informações técnicas sobre sintomas, diagnósticos e tratamentos para cães e gatos.

Para começar, por favor, **escolha a categoria de sintoma** que você gostaria de analisar:

{categories_list}
Você pode digitar o **número** ou o **nome da categoria**."""

    # --- ESCOLHA DE CATEGORIA ---
    elif current_step == "choose_category":
        available_categories = agent_session_state.get("available_categories", [])
        
        # Se não temos as categorias em cache, recarrega
        if not available_categories:
            available_categories = ListarCategorias()
            agent_session_state["available_categories"] = available_categories
        
        if not available_categories or "Error:" in available_categories[0]:
            agent_session_state["current_step"] = "initial"
            return "❌ Erro ao carregar categorias. Digite 'INICIAR' para tentar novamente."

        selected_category_name = None
        
        # Tenta interpretar como número
        try:
            user_input_as_int = int(user_message_text)
            if 1 <= user_input_as_int <= len(available_categories):
                selected_category_name = available_categories[user_input_as_int - 1]
        except ValueError:
            # Tenta match direto (case-insensitive)
            for categoria in available_categories:
                if user_message_text.lower() == categoria.lower():
                    selected_category_name = categoria
                    break

        if selected_category_name:
            # Carrega queixas para a categoria selecionada
            queixas = ListarQueixasPorCategoria(categoria=selected_category_name)
            
            if not queixas or (queixas and "Error:" in queixas[0]):
                return f"❌ Houve um problema ao listar as queixas para '{selected_category_name}': {queixas[0] if queixas else 'Nenhuma queixa disponível.'}. Por favor, escolha uma categoria novamente."

            # Formata a lista de queixas numerada
            queixas_list = ""
            for i, queixa in enumerate(queixas, 1):
                queixas_list += f"{i}. {queixa}\n"

            # Atualiza o estado
            agent_session_state["selected_category"] = selected_category_name
            agent_session_state["current_step"] = "choose_complaint"
            agent_session_state["available_complaints"] = queixas

            return f"""✅ **Ótimo! Você selecionou: {selected_category_name}**

Agora, por favor, **escolha a queixa específica** que você gostaria de analisar:

{queixas_list}
Você pode digitar o **número** ou o **nome da queixa**."""

        else:
            # Categoria inválida - mostra as opções novamente
            categories_list = ""
            for i, categoria in enumerate(available_categories, 1):
                categories_list += f"{i}. {categoria}\n"
            
            return f"""❌ **Categoria não reconhecida.** Por favor, escolha uma das opções abaixo:

{categories_list}
Digite o **número** ou o **nome exato** da categoria."""

    # --- ESCOLHA DE QUEIXA ---
    elif current_step == "choose_complaint":
        selected_category = agent_session_state.get("selected_category")
        available_complaints = agent_session_state.get("available_complaints", [])

        if not selected_category:
            agent_session_state["current_step"] = "initial"
            return "❌ Erro no fluxo. Digite 'INICIAR' para recomeçar."

        # Se não temos as queixas em cache, recarrega
        if not available_complaints:
            available_complaints = ListarQueixasPorCategoria(categoria=selected_category)
            agent_session_state["available_complaints"] = available_complaints

        if not available_complaints or "Error:" in available_complaints[0]:
            agent_session_state["current_step"] = "choose_category"
            return f"❌ Erro ao carregar queixas para '{selected_category}'. Por favor, escolha a categoria novamente."

        selected_complaint_name = None

        # Tenta interpretar como número
        try:
            user_input_as_int = int(user_message_text)
            if 1 <= user_input_as_int <= len(available_complaints):
                selected_complaint_name = available_complaints[user_input_as_int - 1]
        except ValueError:
            # Tenta match direto (case-insensitive)
            for queixa in available_complaints:
                if user_message_text.lower() == queixa.lower():
                    selected_complaint_name = queixa
                    break

        if selected_complaint_name:
            # Gera pergunta específica
            pergunta = GerarPerguntaEspecifica(queixa=selected_complaint_name)
            
            if "Error:" in pergunta:
                return f"❌ Houve um problema ao gerar a pergunta para '{selected_complaint_name}': {pergunta}. Por favor, selecione a queixa novamente."

            # Atualiza o estado
            agent_session_state["selected_complaint"] = selected_complaint_name
            agent_session_state["current_step"] = "answer_question"
            agent_session_state["last_question_asked"] = pergunta

            return f"""📋 **Queixa selecionada: {selected_complaint_name}**

Para uma análise mais precisa, preciso de uma informação adicional:

**{pergunta}**

Por favor, forneça sua resposta com o máximo de detalhes possível."""

        else:
            # Queixa inválida - mostra as opções novamente
            queixas_list = ""
            for i, queixa in enumerate(available_complaints, 1):
                queixas_list += f"{i}. {queixa}\n"
            
            return f"""❌ **Queixa não reconhecida.** Por favor, escolha uma das opções para **{selected_category}**:

{queixas_list}
Digite o **número** ou o **nome exato** da queixa."""

    # --- RESPOSTA À PERGUNTA ---
    elif current_step == "answer_question":
        selected_complaint = agent_session_state.get("selected_complaint")
        last_question = agent_session_state.get("last_question_asked")

        if not selected_complaint or not last_question:
            agent_session_state["current_step"] = "initial"
            return "❌ Erro no fluxo. Digite 'INICIAR' para recomeçar."

        # Armazena a resposta
        agent_session_state["collected_answers"][last_question] = user_message_text
        agent_session_state["current_step"] = "generating_analysis"

        # Gera análise final
        collected_answers = agent_session_state.get("collected_answers")
        prompt_final_para_llm = GerarAnaliseFinal(queixa_selecionada=selected_complaint, respostas_coletadas=collected_answers)
        
        try:
            final_analysis_response = llm_component.generate_content(prompt_final_para_llm)
            final_analysis_text = final_analysis_response.text if hasattr(final_analysis_response, 'text') else str(final_analysis_response)

            # Reset para próxima interação
            agent_session_state["current_step"] = "initial"
            agent_session_state["selected_category"] = None
            agent_session_state["selected_complaint"] = None
            agent_session_state["collected_answers"] = {}
            agent_session_state["last_question_asked"] = None
            agent_session_state["available_categories"] = []
            agent_session_state["available_complaints"] = []

            return f"""🔍 **Análise Completa para: {selected_complaint}**

{final_analysis_text}

---
💡 **Para uma nova consulta, digite 'INICIAR' ou envie uma nova mensagem.**"""

        except Exception as e:
            agent_session_state["current_step"] = "initial"
            return f"❌ Erro ao gerar a análise final: {e}. Digite 'INICIAR' para tentar novamente."

    # --- FALLBACK ---
    else:
        agent_session_state["current_step"] = "initial"
        return "❌ Estado inesperado. Digite 'INICIAR' para começar uma nova consulta."

# 3. Use diretamente o LlmAgent como root_agent
root_agent = llm_component

