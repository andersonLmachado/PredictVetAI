import sys
import os
import json # For pretty printing dicts
from unittest.mock import patch 

# Ensure 'PredictVet' can be imported. Assumes script is run from repo root.
sys.path.insert(0, os.getcwd())

# Import after sys.path modification
from PredictVet import agent as PredictVetAgentModule # Import the module for llm_component access
from PredictVet.agent import handle_predictvet_interaction # Specific function to test
from PredictVet.tools import load_dataframes # Explicit load
from PredictVet import tools as PredictVetToolsModule # For direct df access

# --- Mocking LLM Component by direct replacement ---
class MockLLMResponse:
    def __init__(self, text_response):
        self.text = text_response

class MockLlmComponentInstance:
    def generate_content(self, prompt_text): 
        print(f"MockLlmComponentInstance.generate_content called with prompt: {prompt_text[:70]}...")
        return MockLLMResponse(f"Análise LLM simulada (via MockLlmComponentInstance) para: {prompt_text[:100]}...")

# --- Helper Function for Simulation ---
def simulate_interaction(session_state, user_message_text):
    print(f"\nUser: \"{user_message_text}\"")
    output = handle_predictvet_interaction( 
        new_message=user_message_text,
        agent_session_state=session_state
    )
    print(f"Agent: {output}")
    print(f"Session State: {json.dumps(session_state, indent=2, ensure_ascii=False)}")
    return output

# --- Test Function with Direct Mock Replacement & Specific Tool Mocking ---
def run_all_tests():
    print("Attempting to replace PredictVetAgentModule.llm_component with a mock.")
    
    original_llm_component = PredictVetAgentModule.llm_component
    PredictVetAgentModule.llm_component = MockLlmComponentInstance()
    
    print("LLM component has been replaced with MockLlmComponentInstance for tests.")

    try:
        # Scenario 1: Happy Path
        print("\n\n--- Scenario 1: Happy Path ---")
        agent_session_state_s1 = {}
        simulate_interaction(agent_session_state_s1, "INICIAR_FLUXO")
        simulate_interaction(agent_session_state_s1, "Gastrointestinal") 
        simulate_interaction(agent_session_state_s1, "Vômito")
        simulate_interaction(agent_session_state_s1, "Ontem à noite, após comer grama.")
        simulate_interaction(agent_session_state_s1, "Olá") # Test new conversation after reset
        print(f"\nFinal Session State for Scenario 1: {json.dumps(agent_session_state_s1, indent=2, ensure_ascii=False)}")

        # Scenario 2: Invalid Category Selection
        print("\n\n--- Scenario 2: Invalid Category Selection ---")
        agent_session_state_s2 = {}
        simulate_interaction(agent_session_state_s2, "INICIAR_FLUXO")
        simulate_interaction(agent_session_state_s2, "Categoria Super Inválida 9000")
        simulate_interaction(agent_session_state_s2, "Pele e Pelos") 

        # Scenario 3: Invalid Complaint Selection
        print("\n\n--- Scenario 3: Invalid Complaint Selection ---")
        agent_session_state_s3 = {}
        simulate_interaction(agent_session_state_s3, "INICIAR_FLUXO")
        simulate_interaction(agent_session_state_s3, "Pele e Pelos") 
        simulate_interaction(agent_session_state_s3, "Queixa Muito Específica Que Não Existe")
        # Corrected to use "Coceira" as per CSV data
        simulate_interaction(agent_session_state_s3, "Coceira") 

        # Scenario 4: Tool Error (Mocking ListarCategorias to simulate error)
        print("\n\n--- Scenario 4: Tool Error (ListarCategorias returning error) ---")
        agent_session_state_s4 = {}
        
        # Patching 'ListarCategorias' in the module where it's looked up by handle_predictvet_interaction
        # which is PredictVetAgentModule (PredictVet.agent)
        with patch.object(PredictVetAgentModule, 'ListarCategorias', return_value=["Error: Queixas DataFrame not loaded. Cannot list categories."]) as mock_listar_cat:
            print("\nSimulated: PredictVetAgentModule.ListarCategorias will now return an error.")
            simulate_interaction(agent_session_state_s4, "INICIAR_FLUXO")
            mock_listar_cat.assert_called_once() # Ensure it was called
        print("\nRestored: PredictVetAgentModule.ListarCategorias (mock exited scope).")
    
    finally:
        PredictVetAgentModule.llm_component = original_llm_component
        print("\nOriginal LLM component restored.")

# --- Main Execution Block ---
if __name__ == "__main__":
    print("\n--- Initial Data Loading ---")
    load_dataframes() 
    
    if PredictVetToolsModule.queixas_df is None or PredictVetToolsModule.diagnostico_df is None:
        print("ERROR: DataFrames did not load. Test execution aborted. Check paths and file integrity (e.g., PredictVet/planilha_queixas_tutor.csv).")
    else:
        print("DataFrames loaded successfully for testing.")
        run_all_tests()

    print("\n\n--- Test Execution Finished ---")
