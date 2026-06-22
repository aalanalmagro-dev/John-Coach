import streamlit as st
import json
from google import genai
from google.genai import types

# 1. Configuración de la página web (Frontend)
st.set_page_config(page_title="John Coach", page_icon="🚴", layout="centered")
st.title("🚴 John Coach")
st.subheader("Tu entrenador de ciclismo personal")

# Inicializamos el cliente de la IA (Backend)
client = genai.Client()

PROMPT_SISTEMA = """
Eres el entrenador de ciclismo de la plataforma. Tu metodología se basa en vatios.
Debes analizar lo que dice el ciclista y prescribir el entrenamiento de mañana.
Si muestra fatiga extrema o dolor, el día siguiente es descanso o Zona 1 (menos de 150W).
Insiste siempre en mantener la calma y recuperar bien.
"""

# 2. Gestión del Estado de la Sesión (Base de datos temporal en memoria)
# Esto simula el backend guardando el historial para que el chat tenga memoria
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola Jon! ¿Cómo ha ido el entrenamiento de series de hoy? Cuéntame tus sensaciones y vatios para ajustar lo de mañana."}
    ]

# 3. Pintar el historial de mensajes en la pantalla (Frontend)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Capturar la respuesta del usuario (Frontend)
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones (ej: Hoy no he podido acabar las series...)"):
    
    # Mostramos el mensaje del usuario en la web inmediatamente
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})

    # 5. Procesar la respuesta con la IA (Backend integrado)
    with st.chat_message("assistant"):
        with st.spinner("Tu entrenador está analizando los datos..."):
            try:
                # Opcional: Aquí podrías meter código Python que calcule vatios antes de llamar a la IA
                
                # Llamada a la API
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_usuario,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        temperature=0.3
                    ),
                )
                respuesta_ia = response.text
                
                # Pintamos la respuesta en el Frontend
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")



st.sidebar.header("📊 Perfil del Ciclista")
nivel = st.sidebar.selectbox("Nivel", ["Cicloturista", "Amateur / Máster", "Competición"])
ftp = st.sidebar.number_input("Tu FTP actual (Vatios)", min_value=100, max_value=500, value=250)
horas_semana = st.sidebar.slider("Horas disponibles a la semana", 4, 20, 10)


if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y enviado al calendario!")
    # Aquí en el futuro enviarías un correo o un push al móvil del cliente


st.subheader("📥 Conexión de la sesión de hoy")
col1, col2, col3 = st.columns(3)
with col1:
    vatios_medios = st.number_input("Vatios Medios NP", value=200)
with col2:
    frecuencia_cardiaca = st.number_input("Pulsaciones Medias", value=140)
with col3:
    rpe = st.slider("Esfuerzo percibido (1 al 10)", 1, 10, 6)
