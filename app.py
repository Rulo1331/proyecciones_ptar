import streamlit as st

# INTENTO INCORRECTO CON BOTONES
col1, col2 = st.columns(2)
with col1:
    btn_ph = st.button("Ingresar pH")
with col2:
    btn_dqo = st.button("Ingresar DQO")

if btn_ph:
    st.write("Has entrado a la vista de pH")
    valor_ph = st.number_input("Ingresa el pH:")
    # ¡EL PROBLEMA!: En cuanto el usuario escriba el número de pH, 
    # Streamlit se recarga. Al recargarse, el botón `btn_ph` vuelve a ser False.
    # Resultado: La vista de pH desaparece frente a sus ojos antes de que pueda guardar.
