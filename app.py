import streamlit as st
import json
import os
import requests
import base64
from google import genai
from google.genai import types

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="John Coach", page_icon="🚴", layout="centered")
st.title("🚴 John Coach")
st.subheader("Modo Piloto: Conectado en tiempo real a Intervals.icu")

# 2. INICIALIZAR EL CLIENTE DE IA
client = genai.Client()

# =====================================================================
# CONEXIÓN EN TIEMPO REAL CON LA API DE INTERVALS.ICU
# =====================================================================

@st.cache_data(ttl=30)  # TTL bajo para probar ahora mismo
def obtener_metricas_intervals():
    try:
        # Forzar lectura limpia
        athlete_id = str(st.secrets["INTERVALS_ATHLETE_ID"]).strip().lower()
        api_key = str(st.secrets["INTERVALS_API_KEY"]).strip()
        
        # Dejamos solo los números
        clean_id = athlete_id.replace('i', '')
        
        # El endpoint de perfil de atleta oficial en Intervals necesita barra al final
        url = f"https://intervals.icu/api/v1/athlete/{clean_id}/"
        
        # Creamos la cabecera de autenticación básica de forma manual en base64
        # Formato: "athlete:tu_api_key"
        credenciales = f"athlete:{api_key}"
        credenciales_bytes = credenciales.encode('utf-8')
        base64_credenciales = base64.b64encode(credenciales_bytes).decode('utf-8')
        
        headers = {
            'User-Agent': 'JohnCoach-App/1.0',
            'Authorization': f'Basic {base64_credenciales}',
            'Accept': 'application/json'
        }
        
        # Hacemos la llamada limpia usando solo los headers
        respuesta = requests.get(url, headers=headers, timeout=10)
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return {
                "exito": True,
                "ftp": datos.get("icu_ftp", 250),
                "ctl": round(datos.get("ctl", 0), 1),
                "atl": round(datos.get("atl", 0), 1),
                "balance": round(datos.get("ctl", 0) - datos.get("atl", 0), 1),
                "ramp_rate": round(datos.get("ramp_rate", 0), 1),
                "nombre": datos.get("name", "Atleta Piloto")
            }
        else:
            st.error(f"No se han podido cargar los datos automáticos: {metricas.get('error')}")
            
            # 🕵️‍♂️ BLOQUE DE DIAGNÓSTICO TEMPORAL
            st.warning("🔍 [ZONA DE DEPURACIÓN] Vamos a comprobar qué está leyendo el código:")
            try:
                raw_id = st.secrets["INTERVALS_ATHLETE_ID"]
                raw_key = st.secrets["INTERVALS_API_KEY"]
                
                # Mostramos el ID tal cual llega
                st.write(f"• ID en Secrets: `{raw_id}` (Longitud: {len(str(raw_id))} caracteres)")
                
                # Mostramos la Key de forma segura (Ocultando el centro)
                if len(raw_key) > 8:
                    ofuscada = f"{raw_key[:4]}••••••••{raw_key[-4:]}"
                else:
                    ofuscada = "¡La clave es demasiado corta!"
                    
                st.write(f"• API Key en Secrets: `{ofuscada}` (Longitud total: {len(raw_key)} caracteres)")
                
            except Exception as e:
                st.error(f"Error al intentar leer los Secrets desde el código: {e}")
    except Exception as e:
        return {"exito": False, "error": f"Error de conexión: {str(e)}"}


# =====================================================================
# 🔥 ¡REVISA QUE ESTA LÍNEA DE AQUÍ ABAJO ESTÉ PUESTA! 🔥
# =====================================================================
# Ejecutamos la carga de datos de Intervals y creamos la variable 'metricas'
with st.spinner("Sincronizando con tu perfil de Intervals.icu..."):
    metricas = obtener_metricas_intervals() # <--- ESTA ES LA LÍNEA CRUCIAL

# =====================================================================
# INTERFAZ: PANEL DE CONTROL INTEGRADO
# =====================================================================

if metricas.get("exito"):
    st.success(f"🤖 ¡Conectado al perfil de **{metricas['nombre']}**!")
    
    # Mostramos tus datos reales de rendimiento en 4 tarjetas guapísimas
    col_ftp, col_ctl, col_atl, col_tsb = st.columns(4)
    with col_ftp:
        st.metric(label="FTP Actual", value=f"{metricas['ftp']} W")
    with col_ctl:
        st.metric(label="CTL (Fitness)", value=metricas['ctl'])
    with col_atl:
        st.metric(label="ATL (Fatiga)", value=metricas['atl'])
    with col_tsb:
        # El balance de estrés (TSB) nos dice si estás fresco o al límite
        st.metric(label="Forma (TSB)", value=f"{metricas['balance']}")
        
    # Guardamos los vatios automáticos para el backend
    ftp_intervals = metricas['ftp']
else:
    st.error(f"No se han podido cargar los datos automáticos: {metricas.get('error')}")
    ftp_intervals = 250 # Valor por defecto si falla la API

# 3. INTERFAZ: BARRA LATERAL REPROGRAMADA
st.sidebar.header("📊 Ajustes del Piloto")
nivel = st.sidebar.selectbox("Nivel", ["Cicloturista", "Amateur / Máster", "Competición"])
horas_semana = st.sidebar.slider("Horas disponibles esta semana", 4, 20, 10)

# Formulario para simular el entrenamiento del día actual
st.write("---")
st.subheader("📥 Datos de la salida que acabas de hacer")
col1, col2, col3 = st.columns(3)
with col1:
    vatios_medios = st.number_input("Vatios Medios NP de hoy", value=200)
with col2:
    frecuencia_cardiaca = st.number_input("Pulsaciones Medias", value=140)
with col3:
    rpe = st.slider("Esfuerzo percibido (1 al 10)", 1, 10, 6)

# =====================================================================
# PROMPT DEL SISTEMA ACTUALIZADO CON CIENCIA DE INTERVALS
# =====================================================================
PROMPT_SISTEMA = f"""
Eres el Director Técnico y entrenador jefe de 'John Coach'. Tu rol es el de un entrenador de carne y hueso, un colega experto y un mentor de total confianza para el ciclista.

Tu objetivo principal es mantener una CONVERSACIÓN FLUIDA, DINÁMICA Y ADAPTATIVA basada en métricas científicas avanzadas de rendimiento (procedentes de Intervals.icu).

Métricas fijas de tu atleta actual:
- FTP del ciclista: {ftp_intervals} W.
- Estado físico actual (CTL/Fitness): {metricas.get('ctl', 'N/A')}.
- Fatiga acumulada (ATL): {metricas.get('atl', 'N/A')}.
- Balance actual (TSB/Forma): {metricas.get('balance', 'N/A')}. (Si es muy negativo, está en zona de fatiga óptima pero al límite; si es positivo, está fresco).

Sigue estrictamente estas directrices de flujo y comportamiento:
1. ADAPTABILIDAD AL CONTEXTO: Si el ciclista te pide el entreno de mañana, dale solo mañana. Si te pide planificar el resto de la semana porque tiene una carrera, ábrele el plano y estructúrale los días que hagan falta usando las métricas de CTL y ATL para justificar el descanso o la carga.
2. EVITA REPETICIONES: Una vez analizados los datos del día en el primer mensaje, no vuelvas a recordarle sus métricas de forma robótica. Úsalas como contexto de fondo para guiar tus decisiones.
3. TONO: Habla de tú a tú, cercano, en prosa natural, usando jerga ciclista pura (series, ir con chispa, Zona 1, acoplarse, vaciarse, afilar el punto). Prohibido usar saludos corporativos repetitivos.
"""

# =====================================================================
# HISTORIAL Y LÓGICA DE CHAT PERSISTENTE (JSON LOCAL)
# =====================================================================
ARCHIVO_HISTORIAL = "historial_entrenamientos.json"

def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"role": "assistant", "content": f"¡Hola! Acabo de sincronizar tu cuenta de Intervals. Tu CTL está en {metricas.get('ctl')} y tu fatiga en {metricas.get('atl')}. Cuéntame, ¿cómo ha ido la sesión de hoy y cómo planteamos los siguientes días?"}
    ]

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)

if "messages" not in st.session_state:
    st.session_state.messages = cargar_historial()

# Pintar el historial en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Captura del chat y envío con memoria limpia
if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})

    peticion_con_memoria = []
    
    # Inyección de los datos del entrenamiento de hoy solo en el primer mensaje de la sesión
    if len(st.session_state.messages) == 2:
        CONTEXTO_HOY = f"""
        [MÉTRICAS DE LA SESIÓN GRABADAS HOY]
        - Esfuerzo de hoy: {vatios_medios} W NP, {frecuencia_cardiaca} ppm, RPE: {rpe}/10.
        - Disponibilidad de tiempo: {horas_semana} horas.
        
        Comentario inicial del ciclista: "{prompt_usuario}"
        """
        peticion_con_memoria.append({"role": "user", "content": CONTEXTO_HOY})
    else:
        for msg in st.session_state.messages[1:]:
            peticion_con_memoria.append(msg)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=peticion_con_memoria,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        temperature=0.6
                    ),
                )
                respuesta_ia = response.text
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                guardar_historial(st.session_state.messages)
                
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")

# Botón de validación
st.write("---")
if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y guardado!")
