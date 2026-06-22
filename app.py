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


# =====================================================================
# CONFIGURACIÓN DEL PROMPT DINÁMICO (El cerebro de John Coach)
# =====================================================================

# 1. Definimos las directrices fijas del entrenador (Metodología de tu socio)
PROMPT_SISTEMA = """
Eres el Director Técnico e Inteligencia Artificial de 'John Coach', una plataforma premium de entrenamiento de ciclismo basada estrictamente en vatios. 

Tu metodología se basa en las zonas de potencia clásicas (Z1 a Z7) calculadas a partir del FTP del ciclista.
Tus respuestas deben ser:
- Claras, motivadoras y profesionales (habla como un entrenador de carne y hueso).
- Breves (máximo 2-3 párrafos).
- Centradas en prescribir de forma exacta la sesión de MAÑANA.

REGLAS DE SEGURIDAD ABSOLUTAS:
1. Si el ciclista reporta un RPE (esfuerzo) muy superior a lo normal para sus vatios, muestra fatiga extrema o menciona dolor físico/articular, es OBLIGATORIO recetar descanso total o Zona 1 (recuperación activa por debajo del 55% de su FTP).
2. Prioriza siempre la salud y la consistencia a largo plazo antes que machacar al deportista.
"""

# 2. Creamos el contexto del atleta en tiempo real con las variables de Streamlit
CONTEXTO_CICLISTA = f"""
[PERFIL DEL ATLETA]
- Nivel actual: {nivel}
- FTP (Umbral de Potencia Funcional): {ftp} W
- Disponibilidad semanal máxima: {horas_semana} horas

[DATOS DE LA SESIÓN DE HOY (Simulación Garmin/Strava)]
- Potencia Normalizada (NP): {vatios_medios} W
- Frecuencia Cardíaca Media: {frecuencia_cardiaca} ppm
- Esfuerzo Percibido (RPE): {rpe} sobre 10 (Donde 10 es agónico)
"""

# =====================================================================
# LLAMADA A LA API DE GEMINI (Dentro del bloque 'if prompt_usuario:')
# =====================================================================

# Cuando el usuario escribe en el chat, unimos todo en la petición:
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    
    # ... (aquí va tu código actual para pintar el mensaje del usuario en pantalla) ...

    with st.chat_message("assistant"):
        with st.spinner("Tu entrenador está analizando los datos..."):
            try:
                # Combinamos el contexto de los widgets con el texto del chat
                contenido_peticion = f"""
                {CONTEXTO_CICLISTA}
                
                [SENSACIONES SUBJETIVAS DEL CICLISTA EN EL CHAT]
                "{prompt_usuario}"
                
                En base a todo lo anterior, analiza la sesión de hoy y prescribe detalladamente la sesión de mañana.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contenido_peticion,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        temperature=0.3 # Temperatura baja para que sea preciso y no invente
                    ),
                )
                
                respuesta_ia = response.text
                
                # ... (aquí pintas la respuesta en el frontend y la guardas en el session_state) ...
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")

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

    
    # Mostramos el mensaje del usuario en la web inmediatamente
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})






