import streamlit as st
import json
from google import genai
from google.genai import types
 
# 1. CONFIGURACIÓN DE LA PÁGINA (Siempre la primera línea de Streamlit)
st.set_page_config(page_title="John Coach", page_icon="🚴", layout="centered")
st.title("🚴 John Coach")
st.subheader("Tu prototipo de entrenador personal con IA")

