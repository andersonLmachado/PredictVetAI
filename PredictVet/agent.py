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
    instruction="Você é um assistente veterinário especializado em ajudar médicos veterinários no momento do atendimento de cães e gatos. Sempre responda em português brasileiro (PT-BR).",
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
        print(f"Agent: ListarCategorias returned: {available_categories}")
        
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
        print(f"Agent: Formatted categories_list for display: \n{categories_list}")

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
            print(f"Agent: ListarCategorias (re-fetch) returned: {available_categories}")
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
            print(f"Agent: ListarQueixasPorCategoria returned for '{selected_category_name}': {queixas}")
            
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
            print(f"Agent: Formatted queixas_list for display: \n{queixas_list}")

            return f"""✅ **Ótimo! Você selecionou: {selected_category_name}**

Agora, por favor, **escolha a queixa específica** que você gostaria de analisar:

{queixas_list}
Você pode digitar o **número** ou o **nome da queixa**."""

        else:
            # Categoria inválida - mostra as opções novamente
            categories_list = ""
            for i, categoria in enumerate(available_categories, 1):
                categories_list += f"{i}. {categoria}\n"
            print(f"Agent: Re-displaying formatted categories_list due to invalid input: \n{categories_list}")
            
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
            print(f"Agent: ListarQueixasPorCategoria (re-fetch) returned for '{selected_category}': {available_complaints}")
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
            print(f"Agent: GerarPerguntaEspecifica returned for '{selected_complaint_name}': {pergunta}")
            
            if "Error:" in pergunta:
                return f"❌ Houve um problema ao gerar a pergunta para '{selected_complaint_name}': {pergunta}. Por favor, selecione a queixa novamente."

            # Atualiza o estado
            agent_session_state["selected_complaint"] = selected_complaint_name
            agent_session_state["current_step"] = "answer_question"
            agent_session_state["last_question_asked"] = pergunta
            print(f"Agent: Displaying specific question: {pergunta}")

            return f"""📋 **Queixa selecionada: {selected_complaint_name}**

Para uma análise mais precisa, preciso de uma informação adicional:

**{pergunta}**

Por favor, forneça sua resposta com o máximo de detalhes possível."""

        else:
            # Queixa inválida - mostra as opções novamente
            queixas_list = ""
            for i, queixa in enumerate(available_complaints, 1):
                queixas_list += f"{i}. {queixa}\n"
            print(f"Agent: Re-displaying formatted queixas_list due to invalid input: \n{queixas_list}")
            
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
        
        # MUDANÇA AQUI: Vai direto para confirmação da análise, não gera imediatamente
        agent_session_state["current_step"] = "confirm_analysis"

        return f"""✅ **Informação registrada com sucesso!**

**Resumo da consulta:**
• **Categoria:** {agent_session_state.get("selected_category")}
• **Queixa:** {selected_complaint}
• **Pergunta:** {last_question}
• **Resposta:** {user_message_text}

Agora posso gerar uma análise completa com recomendações técnicas baseadas nessas informações.

**Deseja que eu prossiga com a análise final?** (Digite **"sim"** para continuar ou **"não"** se quiser adicionar mais informações)"""

    # --- CONFIRMAR ANÁLISE ---
    elif current_step == "confirm_analysis":
        selected_complaint = agent_session_state.get("selected_complaint")
        collected_answers = agent_session_state.get("collected_answers")

        if not selected_complaint or not collected_answers:
            agent_session_state["current_step"] = "initial"
            return "❌ Erro no fluxo. Digite 'INICIAR' para recomeçar."

        # Normalize user input
        normalized_input = user_message_text.lower().strip()

        if normalized_input in ["sim", "s", "claro", "pode", "yes", "y", "ok", "prosseguir", "continuar"]:
            # Gera análise final
            prompt_final_para_llm = GerarAnaliseFinal(queixa_selecionada=selected_complaint, respostas_coletadas=collected_answers)
            print(f"Agent: GerarAnaliseFinal tool returned prompt: {prompt_final_para_llm}")

            try:
                final_analysis_response = llm_component.generate_content(prompt_final_para_llm)
                print(f"Agent: LLM (Gemini) raw response object: {final_analysis_response}")
                final_analysis_text = final_analysis_response.text if hasattr(final_analysis_response, 'text') else str(final_analysis_response)
                print(f"Agent: Extracted LLM analysis text: {final_analysis_text}")

                # Reset para próxima interação
                agent_session_state["current_step"] = "initial"
                agent_session_state["selected_category"] = None
                agent_session_state["selected_complaint"] = None
                agent_session_state["collected_answers"] = {}
                agent_session_state["last_question_asked"] = None
                agent_session_state["available_categories"] = []
                agent_session_state["available_complaints"] = []

                message_to_return = f"""🔍 **Análise Veterinária Completa**

**Caso:** {selected_complaint}

{final_analysis_text}

---
💡 **Para uma nova consulta, digite 'INICIAR' ou envie uma nova mensagem.**"""
                print(f"Agent: Final message string being returned to Streamlit (with analysis): \n{message_to_return}")
                return message_to_return

            except Exception as e:
                # Reset state even on error during generation
                agent_session_state["current_step"] = "initial"
                agent_session_state["selected_category"] = None
                agent_session_state["selected_complaint"] = None
                agent_session_state["collected_answers"] = {}
                agent_session_state["last_question_asked"] = None
                agent_session_state["available_categories"] = []
                agent_session_state["available_complaints"] = []
                return f"❌ Erro ao gerar a análise final: {e}. Digite 'INICIAR' para tentar novamente."

        elif normalized_input in ["não", "n", "ainda não", "nao", "no", "adicionar", "mais"]:
            # Volta para permitir adicionar mais informações
            agent_session_state["current_step"] = "answer_question"
            return """📝 **Perfeito!** Você pode adicionar mais informações sobre o caso.

Por favor, forneça detalhes adicionais que considere relevantes para a análise (sintomas adicionais, histórico, comportamento do animal, etc.):"""

        else:
            # Resposta não clara
            return """❓ **Não entendi sua resposta.**

Por favor, responda:
• **"sim"** - para prosseguir com a análise final
• **"não"** - para adicionar mais informações ao caso

Digite sua escolha:"""

    # --- FALLBACK ---
    else:
        agent_session_state["current_step"] = "initial"
        return "❌ Estado inesperado. Digite 'INICIAR' para começar uma nova consulta."

# 3. Use directamente o LlmAgent como root_agent
root_agent = llm_component
