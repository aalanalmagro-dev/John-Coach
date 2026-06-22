import streamlit as st
import json
from google import genai
from google.genai import types

# 1. CONFIGURACIÓN DE LA PÁGINA (Siempre la primera línea de Streamlit)
st.set_page_config(page_title="John Coach", page_icon="🚴", layout="centered")
st.title("🚴 John Coach")
st.subheader("Tu prototipo de entrenador personal con IA")

# 2. INICIALIZAR EL CLIENTE DE IA
client = genai.Client()

# 3. DIRECTRICES FIJAS DEL ENTRENADOR (Metodología de tu socio)
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

# 4. INTERFAZ: BARRA LATERAL (Perfil del Ciclista)
st.sidebar.header("📊 Perfil del Ciclista")
nivel = st.sidebar.selectbox("Nivel", ["Cicloturista", "Amateur / Máster", "Competición"])
ftp = st.sidebar.number_input("Tu FTP actual (Vatios)", min_value=100, max_value=500, value=250)
horas_semana = st.sidebar.slider("Horas disponibles a la semana", 4, 20, 10)

# 5. INTERFAZ: CUADRO DE DATOS DE LA SESIÓN (Simulación Garmin/Strava)
st.subheader("📥 Conexión de la sesión de hoy")
col1, col2, col3 = st.columns(3)
with col1:
    vatios_medios = st.number_input("Vatios Medios NP", value=200)
with col2:
    frecuencia_cardiaca = st.number_input("Pulsaciones Medias", value=140)
with col3:
    rpe = st.slider("Esfuerzo percibido (1 al 10)", 1, 10, 6)

# 6. HISTORIAL DEL CHAT (Para mantener la memoria de la conversación)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! ¿Cómo ha ido el entrenamiento de hoy? Revisa los datos de arriba, añade tus sensaciones aquí abajo y ajustamos lo de mañana."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. CAPTURA DEL CHAT Y LOGICA DEL BACKEND
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    
    # Mostrar el mensaje del usuario inmediatamente
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})

    # Llamada a la IA pasando todo el contexto agrupado
    with st.chat_message("assistant"):
        with st.spinner("Tu entrenador está analizando los datos..."):
            try:
                # Construimos el contexto dinámico con los valores actuales de los botones
                CONTEXTO_CICLISTA = f"""
                [PERFIL DEL ATLETA]
                - Nivel actual: {nivel}
                - FTP (Umbral de Potencia): {ftp} W
                - Disponibilidad semanal: {horas_semana} horas

                [DATOS DE LA SESIÓN DE HOY]
                - Potencia Normalizada (NP): {vatios_medios} W
                - Frecuencia Cardíaca Media: {frecuencia_cardiaca} ppm
                - Esfuerzo Percibido (RPE): {rpe} sobre 10
                """
                
                contenido_peticion = f"""
                {CONTEXTO_CICLISTA}
                
                [SENSACIONES SUBJETIVAS DEL CICLISTA]
                "{prompt_usuario}"
                
                En base a todo lo anterior, analiza la sesión de hoy y prescribe detalladamente la sesión de mañana.
                """
                
                # Ejecutar la llamada a Gemini
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contenido_peticion,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        temperature=0.3
                    ),
                )
                respuesta_ia = response.text
                
                # Pintar la respuesta en la web
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")

# 8. BOTÓN DE VALIDACIÓN PARA TU SOCIO (Feedback del entrenador)
st.write("---")
if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y guardado!")
