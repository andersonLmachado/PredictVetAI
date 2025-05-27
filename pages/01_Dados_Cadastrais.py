import streamlit as st

st.set_page_config(layout="wide") # Optional: Use wide layout for more space

st.title("Dados Cadastrais do Pet")

st.write("Preencha as informações de seu pet abaixo. Todos os campos são de preenchimento opcional.")

with st.form(key="pet_registration_form"):
    st.header("Informações do Pet")
    
    nome = st.text_input("Nome")
    idade = st.text_input("Idade do animal de estimação")
    raca = st.text_input("Raça do animal de estimação")
    peso = st.text_input("Peso atual do animal de estimação (kg)")
    
    st.subheader("Saúde e Histórico Médico")
    status_vacinacao = st.text_area("Status de vacinação do animal de estimação")
    reacoes_adversas = st.text_area("Reações adversas a vacinas ou medicamentos no passado")
    status_desparasitacao = st.text_area("Status de desparasitação do animal de estimação")
    pulgas_carrapatos = st.text_area("Presença de Pulgas/Carrapatos recentes")
    historico_doencas_cronicas = st.text_area("Histórico de doenças crônicas")
    historico_cirurgias = st.text_area("Histórico de cirurgias")
    medicamentos_atuais = st.text_area("Medicamentos atuais")
    alergias_conhecidas = st.text_area("Alergias conhecidas")
    historico_problemas_pele = st.text_area("Histórico de problemas de pele")
    
    st.subheader("Dieta e Hábitos")
    dieta_atual = st.text_area("Dieta atual do animal de estimação")
    frequencia_refeicoes = st.text_area("Frequência de refeições do animal de estimação")
    contato_outros_animais = st.text_area("Contato frequente com outros animais")
    acesso_areas_externas = st.text_area("Acesso a áreas externas")
    rotina_exercicios = st.text_area("Rotina de exercícios")
    
    st.subheader("Comportamento e Ambiente")
    perda_ganho_peso_recente = st.text_area("Perda ou ganho de peso recente")
    mudanca_ambiente_recente = st.text_area("Mudança recente no ambiente (mudança de casa, novos animais)")
    alteracoes_comportamento = st.text_area("Alterações de comportamento")
    
    st.subheader("Outras Informações")
    status_esterilizacao = st.text_area("Status de esterilização/castração")

    # Submit button
    submitted = st.form_submit_button("Salvar Cadastro")
    
    if submitted:
        # For now, just show a success message.
        # In a real application, this is where you would save the data.
        st.success("Cadastro do pet salvo com sucesso! (Dados ainda não persistidos)")
        # Optionally, display the collected data (for debugging/confirmation)
        st.write("Dados Coletados:")
        st.json({
            "Nome": nome,
            "Idade": idade,
            "Raça": raca,
            "Peso": peso,
            "Status de Vacinação": status_vacinacao,
            "Reações Adversas": reacoes_adversas,
            "Status de Desparasitação": status_desparasitacao,
            "Pulgas/Carrapatos Recentes": pulgas_carrapatos,
            "Dieta Atual": dieta_atual,
            "Frequência de Refeições": frequencia_refeicoes,
            "Histórico de Doenças Crônicas": historico_doencas_cronicas,
            "Histórico de Cirurgias": historico_cirurgias,
            "Medicamentos Atuais": medicamentos_atuais,
            "Alergias Conhecidas": alergias_conhecidas,
            "Contato Frequente com Outros Animais": contato_outros_animais,
            "Acesso a Áreas Externas": acesso_areas_externas,
            "Status de Esterilização/Castração": status_esterilizacao,
            "Rotina de Exercícios": rotina_exercicios,
            "Histórico de Problemas de Pele": historico_problemas_pele,
            "Perda ou Ganho de Peso Recente": perda_ganho_peso_recente,
            "Mudança Recente no Ambiente": mudanca_ambiente_recente,
            "Alterações de Comportamento": alteracoes_comportamento
        })

st.sidebar.markdown("---")
st.sidebar.markdown("Navegue pelas seções:")
# The main app page (app.py) will be the default 'home' page.
# Streamlit automatically lists pages from the 'pages' directory.
