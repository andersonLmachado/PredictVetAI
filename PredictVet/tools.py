import pandas as pd
from google.adk.tools import tool

# DataFrame Placeholders
queixas_df = None
diagnostico_df = None

def load_dataframes():
    """
    Loads the dataframes from the CSV files.
    """
    global queixas_df, diagnostico_df

    try:
        queixas_df = pd.read_csv("PredictVet/planilha_queixas_tutor.csv")
        diagnostico_df = pd.read_csv("PredictVet/planilha_diagnostico_exames.csv")
        # print("Dataframes loaded successfully.") # Intentionally commented out for now
    except FileNotFoundError:
        # print("Error: One or both CSV files not found. Please ensure the files are in the PredictVet directory.") # Intentionally commented out
        # Tools will handle the case where dataframes are None.
        pass
    except Exception as e:
        # print(f"An error occurred while loading dataframes: {e}") # Intentionally commented out
        pass # Tools will handle other exceptions if dataframes remain None.

# Example of how a tool will use load_dataframes (do not implement the tool itself yet):
# def ListarCategorias():
# if queixas_df is None:
# load_dataframes()
# # ... rest of the tool logic using queixas_df

if __name__ == "__main__":
    load_dataframes()
    if queixas_df is not None:
        print("\nQueixas DataFrame head:")
        print(queixas_df.head())
    else:
        print("\nQueixas DataFrame is None. Check CSV file paths and integrity.")
    if diagnostico_df is not None:
        print("\nDiagnostico DataFrame head:")
        print(diagnostico_df.head())
    else:
        print("\nDiagnostico DataFrame is None. Check CSV file paths and integrity.")


@tool
def ListarCategorias() -> list[str]:
    """
    Lists unique categories from the 'queixas_df' DataFrame.
    Ensures load_dataframes() is called if queixas_df is None.
    Returns a list of unique strings from the 'Categoria' column.
    Handles potential errors if queixas_df is None or 'Categoria' column is missing.
    """
    global queixas_df
    if queixas_df is None:
        load_dataframes()

    if queixas_df is None:
        return ["Error: Queixas DataFrame not loaded. Cannot list categories."]
    
    if 'Categoria' not in queixas_df.columns:
        return ["Error: 'Categoria' column missing from Queixas DataFrame."]

    try:
        return queixas_df['Categoria'].unique().tolist()
    except Exception as e:
        return [f"Error listing categories: {e}"]

@tool
def ListarQueixasPorCategoria(categoria: str) -> list[str]:
    """
    Lists unique complaints for a given category from the 'queixas_df' DataFrame.
    Ensures load_dataframes() is called if queixas_df is None.
    Filters queixas_df for rows where 'Categoria' matches the input categoria.
    Returns a list of unique strings from the 'Queixa' column for that category.
    Handles cases where the category is not found or queixas_df is unavailable.
    """
    global queixas_df
    if queixas_df is None:
        load_dataframes()

    if queixas_df is None:
        return ["Error: Queixas DataFrame not loaded. Cannot list queixas."]

    if 'Categoria' not in queixas_df.columns or 'Queixa' not in queixas_df.columns:
        return ["Error: Required columns ('Categoria' or 'Queixa') missing from Queixas DataFrame."]

    try:
        filtered_queixas = queixas_df[queixas_df['Categoria'] == categoria]
        if filtered_queixas.empty:
            return [f"No queixas found for category: {categoria}"]
        return filtered_queixas['Queixa'].unique().tolist()
    except Exception as e:
        return [f"Error listing queixas for category {categoria}: {e}"]

@tool
def GerarPerguntaEspecifica(queixa: str) -> str:
    """
    Generates a specific question for a given complaint from the 'queixas_df' DataFrame.
    Ensures load_dataframes() is called if queixas_df is None.
    Finds the first row in queixas_df where 'Queixa' matches the input queixa.
    Returns the string from the 'Pergunta_Especifica' column for that row.
    Handles cases where the queixa is not found or queixas_df is unavailable.
    If multiple questions exist for the same queixa, returns the first one.
    """
    global queixas_df
    if queixas_df is None:
        load_dataframes()

    if queixas_df is None:
        return "Error: Queixas DataFrame not loaded. Cannot generate specific question."

    if 'Queixa' not in queixas_df.columns or 'Pergunta_Especifica' not in queixas_df.columns:
        return "Error: Required columns ('Queixa' or 'Pergunta_Especifica') missing from Queixas DataFrame."

    try:
        pergunta_row = queixas_df[queixas_df['Queixa'] == queixa]
        if pergunta_row.empty:
            return f"No specific question found for queixa: {queixa}"
        return pergunta_row['Pergunta_Especifica'].iloc[0]
    except Exception as e:
        return f"Error generating specific question for queixa {queixa}: {e}"

@tool
def ProcessarRespostaPergunta(queixa: str, pergunta_feita: str, resposta_usuario: str) -> dict:
    """
    Processes the user's response to a specific question.
    This tool is primarily for state management by the agent.
    Returns a dictionary with queixa, question, response, and status.
    """
    return {
        "queixa_processada": queixa,
        "pergunta_respondida": pergunta_feita,
        "resposta_dada": resposta_usuario,
        "status": "resposta_registrada_aguardando_analise"
    }

@tool
def GerarAnaliseFinal(queixa_selecionada: str, respostas_coletadas: dict) -> str:
    """
    Generates a final analysis prompt for the LLM based on the selected complaint and collected answers.
    Ensures load_dataframes() is called if diagnostico_df is None.
    Looks up queixa_selecionada in diagnostico_df.
    Constructs and returns a detailed prompt string for the LLM.
    """
    global diagnostico_df
    if diagnostico_df is None:
        load_dataframes()

    persona = "Você é um assistente veterinário especializado em ajudar médicos veterinários no momento do atendimento de cães e gatos. Você deve fornecer informações precisas e úteis sobre sintomas, tratamentos e cuidados gerais. Seja carinhoso, atencioso e profissional em suas respostas."
    
    respostas_formatadas = ""
    for pergunta, resposta in respostas_coletadas.items():
        respostas_formatadas += f"Pergunta: {pergunta}, Resposta: {resposta}\n"

    contexto_diagnostico_str = "Informação de diagnóstico específica para esta queixa não disponível."
    diagnostico_possivel = "N/A"
    exames_sugeridos = "N/A"
    procedimentos_adicionais = "N/A"

    if diagnostico_df is not None:
        if 'Queixa' not in diagnostico_df.columns:
            # This case should ideally not happen if CSV is correct.
            # The prompt will proceed with "Informação de diagnóstico específica... não disponível."
            pass 
        else:
            diagnostico_info = diagnostico_df[diagnostico_df['Queixa'] == queixa_selecionada]
            if not diagnostico_info.empty:
                diagnostico_row = diagnostico_info.iloc[0]
                # Check if columns exist before trying to access them
                diagnostico_possivel = diagnostico_row['Diagnostico_Possivel'] if 'Diagnostico_Possivel' in diagnostico_row else "N/A"
                exames_sugeridos = diagnostico_row['Exames_Sugeridos'] if 'Exames_Sugeridos' in diagnostico_row else "N/A"
                procedimentos_adicionais = diagnostico_row['Procedimentos_Adicionais'] if 'Procedimentos_Adicionais' in diagnostico_row else "N/A"
                
                contexto_diagnostico_str = f"Diagnóstico Possível: {diagnostico_possivel}\nExames Sugeridos: {exames_sugeridos}\nProcedimentos Adicionais: {procedimentos_adicionais}"
            # If diagnostico_info is empty, contexto_diagnostico_str remains as "Informação de diagnóstico específica... não disponível."
    
    # If diagnostico_df is None, the prompt will also use the default "Informação de diagnóstico específica... não disponível."

    instrucao_llm = "Com base nas informações fornecidas, gere uma análise detalhada para o médico veterinário apresentar ao tutor, incluindo possíveis diagnósticos, exames recomendados e próximos passos."

    prompt_final = f"{persona}\n\nQueixa Principal: {queixa_selecionada}\n\nRespostas Coletadas:\n{respostas_formatadas}\nContexto do Diagnóstico:\n{contexto_diagnostico_str}\n\nInstrução:\n{instrucao_llm}"
    
    return prompt_final
