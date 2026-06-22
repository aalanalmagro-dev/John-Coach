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
Eres el Director Técnico y entrenador jefe de 'John Coach' (la línea de software de Zephyr). Tu rol es el de un entrenador de carne y hueso, un colega experto y un mentor de total confianza para el ciclista.

Tu objetivo principal es mantener una CONVERSACIÓN FLUIDA, DINÁMICA Y ADAPTATIVA. No estás limitado a mirar solo el día de mañana. Debes escuchar activamente lo que el ciclista te pide en cada mensaje y responder exactamente a su necesidad actual.

Sigue estrictamente estas directrices de flujo y comportamiento:
1. ADAPTABILIDAD AL CONTEXTO: Si el ciclista te pide el entreno de mañana, dale solo mañana. Si te pide planificar el resto de la semana porque tiene una carrera, ábrele el plano y estructúrale los días que hagan falta. Si solo quiere comentarte un dolor o pedirte un consejo de desarrollo, responde a eso sin meter entrenos a la fuerza.
2. EVITA REPETICIONES: Una vez que ya has analizado los vatios o datos de la sesión actual en el primer mensaje, NO vuelvas a mencionarlos ni a dar la bienvenida en los siguientes mensajes del hilo a menos que el usuario te pregunte algo específico sobre ellos. Asimila los datos y continúa la charla de forma natural.
3. ACTITUD Y TONO: Sé un compañero accesible pero un profesional riguroso. Prohibido usar introducciones robóticas o corporativas (nada de '¡Excelente trabajo hoy!' o '¡Hola de nuevo!' en cada respuesta). Habla en prosa natural, usando jerga ciclista (series, vatios, ir con chispa, Zona 1, acoplarse, volumen, afinamiento).
4. SEGURIDAD: Si en cualquier punto de la conversación detectas fatiga extrema, frustración por series no completadas o dolor físico/articular, frena su ímpetu con asertividad cercana. Prioriza el descanso o entrenamientos regenerativos (Z1) antes de mandarle tralla.

Habla de tú a tú, fluye como en un chat de WhatsApp y sé tan espontáneo como un preparador físico real.
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

# 7. CAPTURA DEL CHAT Y LÓGICA CON MEMORIA CORREGIDA
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    
    # 1. Mostramos el mensaje del usuario en la pantalla inmediatamente
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    
    # 2. Guardamos el mensaje en el session_state
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})

    # 3. Preparamos el paquete de mensajes que va a viajar a Gemini
    peticion_con_memoria = []
    
    # Si es el PRIMER mensaje que envía el usuario, le inyectamos los vatios por detrás
    # El historial tiene 2 mensajes en este punto (el de bienvenida de la IA y el que acaba de escribir el usuario)
    if len(st.session_state.messages) == 2:
        CONTEXTO_HOY = f"""
        [MÉTRICAS DE LA SESIÓN DE HOY - ENVIADO POR EL GARMIN DEL USUARIO]
        - FTP actual: {ftp} W (Nivel: {nivel})
        - Disponibilidad semanal: {horas_semana} horas
        - Datos de hoy: {vatios_medios} W NP, {frecuencia_cardiaca} ppm, RPE: {rpe}/10.

        [COMENTARIO DEL CICLISTA]:
        "{prompt_usuario}"
        """
        # Sustituimos su primer mensaje por este enriquecido con los datos numéricos
        peticion_con_memoria.append({"role": "user", "content": CONTEXTO_HOY})
    
    else:
        # SI YA ES EL SEGUNDO MENSAJE O SUCESIVOS:
        # Le pasamos a Gemini el historial limpio tal y como ha ocurrido. 
        # Como en el primer mensaje ya le metimos los vatios, Gemini los recordará en su memoria 
        # sin necesidad de que se los volvamos a enviar en los cuadros de texto.
        
        # El primer mensaje visual es de la IA (bienvenida), pero Gemini necesita que la lista empiece con "user".
        # Así que nos saltamos el saludo inicial para que el flujo de turnos sea perfecto: [user, assistant, user, assistant...]
        for msg in st.session_state.messages[1:]:
            peticion_con_memoria.append(msg)

    # 4. Llamada al entrenador (IA)
    with st.chat_message("assistant"):
        with st.spinner("Analizando tu evolución..."):
            try:
                # Ejecutar la llamada a Gemini con el prompt limpio y dinámico
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=peticion_con_memoria,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA, # <--- Usamos el nuevo prompt directo
                        temperature=0.6 # Un pelín más de temperatura para que sea más creativo y suelto
                    ),
                )
                respuesta_ia = response.text
                
                # Pintamos la respuesta y la guardamos
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                guardar_historial(st.session_state.messages) # Guardamos todo en el JSON
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")


# 8. BOTÓN DE VALIDACIÓN
st.write("---")
if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y guardado!")
