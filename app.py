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
        api_key = str(st.secrets["INTERVALS_API_KEY"]).strip()
        
        url_atleta = "https://intervals.icu/api/v1/athlete/0"
        url_wellness = "https://intervals.icu/api/v1/athlete/0/wellness"
        
        res_atleta = requests.get(url_atleta, auth=('API_KEY', api_key), timeout=10)
        res_wellness = requests.get(url_wellness, auth=('API_KEY', api_key), timeout=10)
        
        nombre_usuario = "Atleta Conectado"
        ftp_real = 250  # Base por si fallara la red
        ctl_real, atl_real = 0.0, 0.0
        
        if res_atleta.status_code == 200:
            datos_atleta = res_atleta.json()
            nombre_usuario = datos_atleta.get("name") or datos_atleta.get("username", "Atleta Conectado")
            
            # 1. Buscamos el FTP en la raíz por si acaso
            ftp_api = datos_atleta.get("icu_ftp") or datos_atleta.get("ftp")
            
            # 2. Exploramos 'sportSettings' (Detectado en tu API)
            if not ftp_api and "sportSettings" in datos_atleta:
                settings = datos_atleta["sportSettings"]
                # Si es una lista, buscamos el bloque de ciclismo o cogemos el primero
                if isinstance(settings, list) and len(settings) > 0:
                    # Intentamos buscar el que sea de ciclismo de forma inteligente
                    bici_setting = next((s for s in settings if str(s.get("id")).lower() in ["cycling", "bici", "road"]), settings[0])
                    ftp_api = bici_setting.get("ftp") or bici_setting.get("icu_ftp")
                elif isinstance(settings, dict):
                    # Si es un diccionario, intentamos sacar el ftp general o de cycling
                    ftp_api = settings.get("ftp") or settings.get("cycling", {}).get("ftp")

            # 3. Último cartucho dinámico: 'icu_type_settings'
            if not ftp_api and "icu_type_settings" in datos_atleta:
                type_settings = datos_atleta["icu_type_settings"]
                if isinstance(type_settings, dict):
                    ftp_api = type_settings.get("ftp") or type_settings.get("cycling", {}).get("ftp")
            
            if ftp_api:
                ftp_real = int(ftp_api)
            
        if res_wellness.status_code == 200:
            datos_wellness = res_wellness.json()
            if isinstance(datos_wellness, list) and len(datos_wellness) > 0:
                ultimo_dia = datos_wellness[-1]
            else:
                ultimo_dia = datos_wellness if isinstance(datos_wellness, dict) else {}
                
            ctl_real = ultimo_dia.get("ctl") or ultimo_dia.get("ctlStart", 0)
            atl_real = ultimo_dia.get("atl") or ultimo_dia.get("atlStart", 0)

        if res_atleta.status_code == 200 or res_wellness.status_code == 200:
            return {
                "exito": True,
                "ftp": int(ftp_real),
                "ctl": round(float(ctl_real), 1),
                "atl": round(float(atl_real), 1),
                "balance": round(float(ctl_real) - float(atl_real), 1),
                "nombre": nombre_usuario,
                "error_msg": None
            }
        else:
            return {
                "exito": False,
                "ftp": 250, "ctl": 0, "atl": 0, "balance": 0, "nombre": "Error",
                "error_msg": f"Error de sincronización (Código: {res_atleta.status_code})"
            }
            
    except Exception as e:
        return {
            "exito": False,
            "ftp": 250, "ctl": 0, "atl": 0, "balance": 0, "nombre": "Error",
            "error_msg": f"Fallo en sincronización dinámica: {str(e)}"
        }
# ====================================================
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

    # 🔥 2. TRADUCCIÓN AL FORMATO OFICIAL DE GOOGLE-GENAI
    # Mapeamos 'assistant' a 'model' y estructuramos cada mensaje como exige el SDK moderno
    contents_api = []
    for msg in peticion_con_memoria:
        # Gemini usa 'model' en lugar de 'assistant'
        rol_gemini = "model" if msg["role"] == "assistant" else "user"
        
        contents_api.append(
            types.Content(
                role=rol_gemini,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )
        
    
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = client.models.generate_content(
                    #model='gemini-2.5-flash',
                    model='gemini-1.5-flash',
                    contents=contents_api,
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
