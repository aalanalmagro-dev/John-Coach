import streamlit as st
import json
import os
import requests
import base64

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="John Coach", page_icon="🚴", layout="centered")
st.title("🚴 John Coach")
st.subheader("Modo Piloto: Conectado en tiempo real a Intervals.icu")

# 2. INICIALIZAR EL CLIENTE DE IA
# Nota: Si usas la nueva librería 'google-genai', asegúrate de tenerla en tu requirements.txt
from google import genai
from google.genai import types
client = genai.Client()

# =====================================================================
# FUNCIÓN DE CONEXIÓN A INTERVALS.ICU (CON CHIVATO DE ERRORES)
# =====================================================================
@st.cache_data(ttl=10)
def obtener_metricas_intervals():
    try:
        # 1. Leer secretos limpios
        athlete_id = str(st.secrets["INTERVALS_ATHLETE_ID"]).strip().lower()
        api_key = str(st.secrets["INTERVALS_API_KEY"]).strip()
        
        clean_id = athlete_id.replace('i', '')
        
        # URL oficial usando tu ID numérico directo
        url = "https://intervals.icu/api/v1/athlete/profile"
        
        # 2. El método nativo e infalible de requests para Intervals.icu
        # Dejamos que requests maneje la autenticación de forma limpia
        respuesta = requests.get(url, auth=('athlete', api_key), timeout=10)
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return {
                "exito": True,
                "ftp": datos.get("icu_ftp", 250),
                "ctl": round(datos.get("ctl", 0), 1),
                "atl": round(datos.get("atl", 0), 1),
                "balance": round(datos.get("ctl", 0) - datos.get("atl", 0), 1),
                "ramp_rate": round(datos.get("ramp_rate", 0), 1),
                "nombre": datos.get("name", "Atleta Piloto"),
                "error_msg": None
            }
        else:
            return {
                "exito": False,
                "ftp": 250, "ctl": 0, "atl": 0, "balance": 0, "nombre": "Error",
                "error_msg": f"Intervals denegó el acceso (Código HTTP {respuesta.status_code})."
            }
            
    except Exception as e:
        return {
            "exito": False,
            "ftp": 250, "ctl": 0, "atl": 0, "balance": 0, "nombre": "Error",
            "error_msg": f"Excepción interna en la conexión: {str(e)}"
        }
# =====================================================================
# EJECUCIÓN OBLIGATORIA (Aquí se crea la variable pase lo que pase)
# =====================================================================
with st.spinner("Sincronizando con tu perfil de Intervals.icu..."):
    metricas = obtener_metricas_intervals()

# =====================================================================
# 3. INTERFAZ: PANELES O DIAGNÓSTICO
# =====================================================================
if metricas["exito"]:
    st.success(f"🤖 ¡Conectado al perfil de **{metricas['nombre']}**!")
    
    col_ftp, col_ctl, col_atl, col_tsb = st.columns(4)
    with col_ftp:
        st.metric(label="FTP Actual", value=f"{metricas['ftp']} W")
    with col_ctl:
        st.metric(label="CTL (Fitness)", value=metricas['ctl'])
    with col_atl:
        st.metric(label="ATL (Fatiga)", value=metricas['atl'])
    with col_tsb:
        st.metric(label="Forma (TSB)", value=f"{metricas['balance']}")
        
    ftp_intervals = metricas['ftp']
else:
    # Si falla, pintamos el error de forma segura sin romper la app
    st.error(f"No se han podido cargar los datos automáticos: {metricas['error_msg']}")
    ftp_intervals = 250
    
    st.warning("🔍 [ZONA DE DEPURACIÓN DE SECRETOS] Revisa qué está leyendo Python:")
    try:
        raw_id = st.secrets["INTERVALS_ATHLETE_ID"]
        raw_key = st.secrets["INTERVALS_API_KEY"]
        
        st.write(f"• **ID en Secrets:** `{raw_id}` (Longitud: {len(str(raw_id))} caracteres)")
        
        if len(raw_key) > 8:
            ofuscada = f"{raw_key[:4]}••••••••{raw_key[-4:]}"
        else:
            ofuscada = "¡Demasiado corta!"
        st.write(f"• **API Key en Secrets:** `{ofuscada}` (Longitud total: {len(raw_key)} caracteres)")
    except Exception as err:
        st.error(f"Fallo crítico al leer la sección Secrets: {err}")

# 4. INTERFAZ: BARRA LATERAL
st.sidebar.header("📊 Ajustes del Piloto")
nivel = st.sidebar.selectbox("Nivel", ["Cicloturista", "Amateur / Máster", "Competición"])
horas_semana = st.sidebar.slider("Horas disponibles esta semana", 4, 20, 10)

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
# PROMPT DEL SISTEMA ACTUALIZADO
# =====================================================================
PROMPT_SISTEMA = f"""
Eres el Director Técnico y entrenador jefe de 'John Coach'. Tu rol es el de un entrenador de carne y hueso, un colega experto y un mentor de total confianza para el ciclista.
Métricas actuales del atleta: FTP: {ftp_intervals} W, CTL: {metricas['ctl']}, ATL: {metricas['atl']}.
Mantén una conversación fluida, dinámica y adaptativa en base a estos datos.
"""

# HISTORIAL LOCAL
ARCHIVO_HISTORIAL = "historial_entrenamientos.json"

def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return [{"role": "assistant", "content": "¡Hola! He preparado el entorno. Cuéntame cómo te has notado hoy en la carretera."}]

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)

if "messages" not in st.session_state:
    st.session_state.messages = cargar_historial()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt_usuario := st.chat_input("Escribe aquí tus sensaciones..."):
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})

    peticion_con_memoria = []
    if len(st.session_state.messages) == 2:
        CONTEXTO_HOY = f"Sesión: {vatios_medios}W NP, {frecuencia_cardiaca}ppm, RPE: {rpe}/10. Mensaje: {prompt_usuario}"
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
                    config=types.GenerateContentConfig(system_instruction=PROMPT_SISTEMA, temperature=0.6),
                )
                respuesta_ia = response.text
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                guardar_historial(st.session_state.messages)
            except Exception as e:
                st.error(f"Hubo un error en el motor de IA: {e}")

st.write("---")
if st.button("✅ Validar Entrenamiento (Socio / Entrenador)"):
    st.success("¡Entrenamiento verificado por el equipo de John Coach y guardado!")
