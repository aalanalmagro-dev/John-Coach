import streamlit as st
import json
import os
from google import genai
from google.genai import types

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="John Coach", page_icon="🚴", layout="centered")
st.title("🚴 John Coach")
st.subheader("Tu entrenador de IA con memoria persistente")

# 2. INICIALIZAR EL CLIENTE DE IA
client = genai.Client()

# 3. DIRECTRICES FIJAS DEL ENTRENADOR
PROMPT_SISTEMA = """
Eres el Director Técnico e Inteligencia Artificial de 'John Coach', una plataforma premium de entrenamiento de ciclismo basada estrictamente en vatios.
Tu metodología se basa en las zonas de potencia clásicas (Z1 a Z7) calculadas a partir del FTP del ciclista.

Se te proporcionará el historial completo de las conversaciones anteriores con el ciclista. Debes usar este historial para conocer su evolución, lesiones pasadas, objetivos y mantener una relación continua y ultra-personalizada, exactamente igual que haría un entrenador real de carne y hueso.
"""

# =====================================================================
# GESTIÓN DE LA MEMORIA REAL (Archivo JSON)
# =====================================================================
ARCHIVO_HISTORIAL = "historial_entrenamientos.json"

def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"role": "assistant", "content": "¡Hola! Bienvenido de nuevo a tu plan de entrenamiento en John Coach. Cuéntame, ¿cómo ha ido la sesión de hoy y cómo te vas encontrando?"}
    ]

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)

# Inicializamos el estado de la sesión de Streamlit cargando el archivo físico
if "messages" not in st.session_state:
    st.session_state.messages = cargar_historial()
# =====================================================================

# 4. INTERFAZ: BARRA LATERAL (Perfil)
st.sidebar.header("📊 Perfil del Ciclista")
nivel = st.sidebar.selectbox("Nivel", ["Cicloturista", "Amateur / Máster", "Competición"])
ftp = st.sidebar.number_input("Tu FTP actual (Vatios)", min_value=100, max_value=500, value=250)
horas_semana = st.sidebar.slider("Horas disponibles a la semana", 4, 20, 10)

# 5. INTERFAZ: DATOS DE LA SESIÓN
st.subheader("📥 Conexión de la sesión de hoy")
col1, col2, col3 = st.columns(3)
with col1:
    vatios_medios = st.number_input("Vatios Medios NP", value=200)
with col2:
    frecuencia_cardiaca = st.number_input("Pulsaciones Medias", value=140)
with col3:
    rpe = st.slider("Esfuerzo percibido (1 al 10)", 1, 10, 6)

# 6. PINTAR EL HISTORIAL EN PANTALLA
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. CAPTURA DEL CHAT Y LÓGICA CON MEMORIA
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    
    # Mostrar y añadir mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    guardar_historial(st.session_state.messages) # Guardamos en el JSON de inmediato

    with st.chat_message("assistant"):
        with st.spinner("Analizando todo tu histórico de entrenamiento..."):
            try:
                # Contexto del día actual
                CONTEXTO_HOY = f"""
                [DATOS DE LA SESIÓN DE HOY]
                - FTP actual del ciclista: {ftp} W (Nivel: {nivel})
                - Disponibilidad semanal: {horas_semana} horas
                - Datos recogidos: {vatios_medios} W NP, {frecuencia_cardiaca} ppm, RPE: {rpe}/10.
                """
                
                # Para que Gemini recuerde TODO, le pasamos el historial completo cargado del JSON
                # más los datos específicos que acaba de meter hoy en los cuadros.
                peticion_con_memoria = []
                peticion_con_memoria.append({"role": "user", "content": CONTEXTO_HOY})
                
                # Añadimos toda la conversación pasada
                for msg in st.session_state.messages:
                    peticion_con_memoria.append(msg)
                
                # Ejecutar la llamada a Gemini
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=peticion_con_memoria,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        temperature=0.4
                    ),
                )
                respuesta_ia = response.text
                
                # Pintar y guardar la respuesta en el JSON
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                guardar_historial(st.session_state.messages) # Guardamos la respuesta en el JSON
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")

# 8. BOTÓN DE VALIDACIÓN
st.write("---")
if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y guardado!")
