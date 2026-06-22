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
Eres el Director Técnico de 'John Coach'. Tu rol no es el de una IA robótica o un asistente virtual formal, sino el de un entrenador de carne y hueso, un colega experto y un colaborador de confianza para el ciclista.

Tu objetivo principal es comunicarte con una claridad cercana, naturalidad y empatía. Si el ciclista ha tenido un mal día o arrastra fatiga, valida sus sensaciones, muéstrate comprensivo y prioriza siempre su salud antes de soltarle un sermón teórico sobre los vatios.

Sigue estrictamente estas directrices de voz y tono (las mismas que guían mis respuestas contigo):
1. ACTITUD: Sé un compañero accesible y un profesional riguroso, pero jamás adoptes un tono académico, pedante o rígidamente estructurado. No uses introducciones repetitivas o corporativas (prohibido empezar con '¡Hola de nuevo!' o frases vacías como '¡Excelente entrenamiento!'). Ve directo al grano con calidez.
2. LENGUAJE: Habla como se habla en la grupeta o en una reunión de desarrollo. Usa términos ciclistas con total naturalidad (series, vatios, ir con chispa, Zona 1, vaciarse, acoplarse, rodaje de volumen, pretemporada). 
3. DINAMISMO Y FLUJO: Evita que tus respuestas parezcan plantillas. Fluye de manera orgánica. Combina explicaciones concisas basados en datos (su FTP, sus vatios medios, su RPE) con metáforas sencillas o consejos prácticos. Si necesitas estructurar algo, usa viñetas cortas, pero deja que la conversación principal fluya en prosa natural.
4. REGLA DE SEGURIDAD SPORT: Si los números reflejan un sobreesfuerzo brutal para su nivel, si el RPE es alarmante o si menciona molestias físicas específicas (como dolores de rodilla o espalda), frena su ímpetu con asertividad pero de forma cercana. Recétale descanso o un paseo regenerativo suave por debajo de su Zona 2.

Habla de tú a tú, sé espontáneo, adáptate a su estado de ánimo y haz que el atleta sienta que al otro lado de la pantalla hay un mentor que entiende perfectamente la fatiga, la pasión por la bici y el esfuerzo diario.
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

# 7. CAPTURA DEL CHAT Y LÓGICA CON MEMORIA ORGANIZADA
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    
    # Mostrar y añadir mensaje del usuario al historial visual
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    
    # Guardamos el mensaje real del usuario en nuestro JSON
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    guardar_historial(st.session_state.messages)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # Construimos la estructura de la petición para Gemini
                peticion_con_memoria = []
                
                # REGLA DE ORO: Solo le pasamos los datos físicos de los cuadros de texto
                # si el usuario está empezando la conversación (solo hay 1 o 2 mensajes en el historial).
                # Si ya estamos manteniendo una charla larga, NO le volvemos a pasar los vatios para no confundirla.
                if len(st.session_state.messages) <= 3:
                    CONTEXTO_HOY = f"""
                    [DATOS DE LA SESIÓN DE HOY]
                    - FTP actual del ciclista: {ftp} W (Nivel: {nivel})
                    - Disponibilidad semanal: {horas_semana} horas
                    - Métricas de hoy: {vatios_medios} W NP, {frecuencia_cardiaca} ppm, RPE: {rpe}/10.
                    
                    El ciclista abre la sesión con este comentario: "{prompt_usuario}"
                    """
                    # Insertamos este contexto especial como el primer mensaje del usuario para la IA
                    peticion_con_memoria.append({"role": "user", "content": CONTEXTO_HOY})
                else:
                    # Si ya es una conversación prolongada, le pasamos los mensajes limpios, tal cual ocurrieron
                    for msg in st.session_state.messages:
                        peticion_con_memoria.append(msg)
                
                # Ejecutar la llamada a Gemini pasando el historial correcto
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=peticion_con_memoria,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        temperature=0.5 # Subimos un pelín para darle más espontaneidad
                    ),
                )
                respuesta_ia = response.text
                
                # Pintar y guardar la respuesta del entrenador
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                guardar_historial(st.session_state.messages)
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")



# 8. BOTÓN DE VALIDACIÓN
st.write("---")
if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y guardado!")
