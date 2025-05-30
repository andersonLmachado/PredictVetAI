import pandas as pd
from google.adk.tools import FunctionTool
import os
import traceback

# DataFrame Placeholders
queixas_df = None
diagnostico_df = None

def load_dataframes():
    """
    Loads the dataframes from the CSV files.
    """
    global queixas_df, diagnostico_df
    print(f"Current Working Directory: {os.getcwd()}")

    try:
        # Ensure paths are correct relative to the script's execution context
        # For example, if running from d:\PredictVetAgent, these paths should be correct.
        queixas_path = "PredictVet/planilha_queixas_tutor.csv"
        diagnostico_path = "PredictVet/planilha_diagnostico_exames.csv"
        
        print(f"Attempting to load queixas_df from absolute path: {os.path.abspath(queixas_path)}")
        queixas_df = pd.read_csv(queixas_path)
        print("Successfully loaded queixas_df.")
        print("queixas_df.head():")
        print(queixas_df.head())
        print("queixas_df.info():")
        queixas_df.info()
        print("queixas_df['Categoria'].unique():")
        print(queixas_df['Categoria'].unique())

        print(f"Attempting to load diagnostico_df from absolute path: {os.path.abspath(diagnostico_path)}")
        diagnostico_df = pd.read_csv(diagnostico_path)
        print("Successfully loaded diagnostico_df.")
        print("diagnostico_df.head():")
        print(diagnostico_df.head())
        print("diagnostico_df.info():")
        diagnostico_df.info()
        # print("Dataframes loaded successfully.")
    except FileNotFoundError as fnf_error:
        print(f"Error: File not found. Absolute path checked: {os.path.abspath(queixas_path if 'queixas_path' in locals() else diagnostico_path)}. Details: {fnf_error}")
        # DataFrames will remain None, tools should handle this.
    except pd.errors.EmptyDataError as ede_error:
        print(f"Error: One or both CSV files are empty. Details: {ede_error}")
        # DataFrames will remain None.
    except pd.errors.ParserError as pe_error:
        print(f"Error: Failed to parse one or both CSV files. Check for malformed data. Details: {pe_error}")
        # DataFrames will remain None.
    except Exception as e:
        print(f"An unexpected error occurred while loading dataframes: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        # DataFrames will remain None.

# Example of how a tool will use load_dataframes (do not implement the tool itself yet):
# def ListarCategorias():
# if queixas_df is None:
# load_dataframes()
# # ... rest of the tool logic using queixas_df

# Tool functions
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
        print("ListarCategorias: queixas_df is None or not loaded.")
        return ["Error: Queixas DataFrame not loaded. Cannot list categories."]
    
    if 'Categoria' not in queixas_df.columns:
        print("ListarCategorias: 'Categoria' column missing.")
        return ["Error: 'Categoria' column missing from Queixas DataFrame."]

    try:
        categories = queixas_df['Categoria'].unique().tolist()
        print(f"ListarCategorias: Returning categories: {categories}")
        return categories
    except Exception as e:
        print(f"ListarCategorias: Error: {e}")
        return [f"Error listing categories: {e}"]

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
        print("ListarQueixasPorCategoria: queixas_df is None or not loaded.")
        return ["Error: Queixas DataFrame not loaded. Cannot list queixas."]

    if 'Categoria' not in queixas_df.columns or 'Queixa' not in queixas_df.columns:
        print("ListarQueixasPorCategoria: Required columns missing.")
        return ["Error: Required columns ('Categoria' or 'Queixa') missing from Queixas DataFrame."]

    try:
        filtered_queixas = queixas_df[queixas_df['Categoria'] == categoria]
        if filtered_queixas.empty:
            print(f"ListarQueixasPorCategoria: No queixas found for category: {categoria}")
            return [f"No queixas found for category: {categoria}"]
        queixas_list = filtered_queixas['Queixa'].unique().tolist()
        print(f"ListarQueixasPorCategoria: Returning queixas: {queixas_list} for category: {categoria}")
        return queixas_list
    except Exception as e:
        print(f"ListarQueixasPorCategoria: Error for category {categoria}: {e}")
        return [f"Error listing queixas for category {categoria}: {e}"]

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
        # Ensure it returns a string, not a Series/DataFrame element if only one.
        return str(pergunta_row['Pergunta_Especifica'].iloc[0]) 
    except Exception as e:
        return f"Error generating specific question for queixa {queixa}: {e}"

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
    if isinstance(respostas_coletadas, dict):
        for pergunta, resposta in respostas_coletadas.items():
            respostas_formatadas += f"Pergunta: {pergunta}, Resposta: {resposta}\n"
    else:
        # Handle case where respostas_coletadas might not be a dict as expected
        respostas_formatadas = "Respostas coletadas não estão no formato esperado.\n"


    contexto_diagnostico_str = "Informação de diagnóstico específica para esta queixa não disponível."
    diagnostico_possivel = "N/A"
    exames_sugeridos = "N/A"
    procedimentos_adicionais = "N/A"

    if diagnostico_df is not None:
        if 'Queixa' not in diagnostico_df.columns:
            pass 
        else:
            diagnostico_info = diagnostico_df[diagnostico_df['Queixa'] == queixa_selecionada]
            if not diagnostico_info.empty:
                diagnostico_row = diagnostico_info.iloc[0]
                diagnostico_possivel = diagnostico_row.get('Diagnostico_Possivel', "N/A")
                exames_sugeridos = diagnostico_row.get('Exames_Sugeridos', "N/A")
                procedimentos_adicionais = diagnostico_row.get('Procedimentos_Adicionais', "N/A")
                
                contexto_diagnostico_str = f"Diagnóstico Possível: {diagnostico_possivel}\nExames Sugeridos: {exames_sugeridos}\nProcedimentos Adicionais: {procedimentos_adicionais}"
    
    instrucao_llm = "Com base nas informações fornecidas, gere uma análise detalhada para o médico veterinário apresentar ao tutor, incluindo possíveis diagnósticos, exames recomendados e próximos passos."

    prompt_final = f"{persona}\n\nQueixa Principal: {queixa_selecionada}\n\nRespostas Coletadas:\n{respostas_formatadas}\nContexto do Diagnóstico:\n{contexto_diagnostico_str}\n\nInstrução:\n{instrucao_llm}"
    
    return prompt_final

# Create FunctionTool instances
listar_categorias_tool = FunctionTool(func=ListarCategorias)
listar_queixas_por_categoria_tool = FunctionTool(func=ListarQueixasPorCategoria)
gerar_pergunta_especifica_tool = FunctionTool(func=GerarPerguntaEspecifica)
processar_resposta_pergunta_tool = FunctionTool(func=ProcessarRespostaPergunta)
gerar_analise_final_tool = FunctionTool(func=GerarAnaliseFinal)

# List of all tools to be imported by the agent
all_tools = [
    listar_categorias_tool,
    listar_queixas_por_categoria_tool,
    gerar_pergunta_especifica_tool,
    processar_resposta_pergunta_tool,
    gerar_analise_final_tool,
]

if __name__ == "__main__":
    load_dataframes()
    if queixas_df is not None:
        print("\nQueixas DataFrame head:")
        print(queixas_df.head())
        # Test ListarCategorias
        print("\nTestando ListarCategorias:")
        print(ListarCategorias())
        # Test ListarQueixasPorCategoria (example category)
        if not queixas_df.empty and 'Categoria' in queixas_df.columns:
            example_category = queixas_df['Categoria'].iloc[0]
            print(f"\nTestando ListarQueixasPorCategoria para '{example_category}':")
            print(ListarQueixasPorCategoria(categoria=example_category))
        # Test GerarPerguntaEspecifica (example queixa)
        if not queixas_df.empty and 'Queixa' in queixas_df.columns:
            example_queixa = queixas_df['Queixa'].iloc[0]
            print(f"\nTestando GerarPerguntaEspecifica para '{example_queixa}':")
            print(GerarPerguntaEspecifica(queixa=example_queixa))

    else:
        print("\nQueixas DataFrame is None. Check CSV file paths and integrity.")
    
    if diagnostico_df is not None:
        print("\nDiagnostico DataFrame head:")
        print(diagnostico_df.head())
        # Test GerarAnaliseFinal (example)
        print("\nTestando GerarAnaliseFinal (exemplo):")
        print(GerarAnaliseFinal(queixa_selecionada="Vômito", respostas_coletadas={"Cor do vômito?": "Amarelo"}))

    else:
        print("\nDiagnostico DataFrame is None. Check CSV file paths and integrity.")

    # Test ProcessarRespostaPergunta
    print("\nTestando ProcessarRespostaPergunta:")
    print(ProcessarRespostaPergunta(queixa="Dermatite", pergunta_feita="Há lesões na pele?", resposta_usuario="Sim, vermelhidão e coceira."))
