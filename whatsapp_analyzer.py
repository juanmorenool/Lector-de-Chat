import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from datetime import datetime
import json

# Configurar página
st.set_page_config(
    page_title="WhatsApp Chat Analyzer - Palabras del Corazón",
    page_icon="💌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 48px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES DE PARSING ====================

@st.cache_data
def parse_whatsapp_chat(text):
    """Parsea el chat de WhatsApp y retorna dataframe estructurado"""
    lines = text.strip().split('\n')
    messages = []

    # Patrón actualizado: permite \u200e al inicio y maneja el espacio narrow no-break
    pattern = r'(?:\u200e)?\[(\d{1,2}/\d{1,2}/\d{4}),\s(\d{1,2}:\d{2}:\d{2}\s?(?:am|pm)?)\]\s([^:]+):\s?(.*)$'

    for line in lines:
        match = re.match(pattern, line)
        if match:
            date_str, time_str, sender, message = match.groups()
            # Saltar mensajes vacíos o de sistema
            if not message.strip():
                continue
            try:
                # Parsear fecha
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                messages.append({
                    'date': date_obj,
                    'time': time_str,
                    'sender': sender.strip(),
                    'message': message.strip(),
                    'date_only': date_obj.date()
                })
            except:
                pass

    return pd.DataFrame(messages)

def find_love_expressions(df):
    """Encuentra expresiones de amor: 'te quiero', 'te amo', 'me encantas'"""
    results = {
        'te_quiero': [],
        'te_amo': [],
        'me_encantas': [],
        'amor': []
    }

    for idx, row in df.iterrows():
        msg = row['message']
        msg_lower = msg.lower()

        # Te quiero (evita "te quiero" dentro de otras palabras, busca como frase)
        if re.search(r'\bte quier[o\w]*\b', msg_lower):
            results['te_quiero'].append({
                'date': row['date'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

        # Te amo (evita "te amanece", "te amas", etc.)
        if re.search(r'\bte amo\b', msg_lower):
            results['te_amo'].append({
                'date': row['date'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

        # Me encantas (evita "me encanta", "me encantaría")
        if re.search(r'\bme encantas\b', msg_lower):
            results['me_encantas'].append({
                'date': row['date'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

        # Amor (general, como saludo o término cariñoso)
        # Solo cuenta si es "amor" como vocativo o término directo
        if re.search(r'(?:^|[^\w])amor(?:[^\w]|$)', msg_lower):
            results['amor'].append({
                'date': row['date'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

    return results

def find_palabra_del_dia(df):
    """Extrae todas las 'palabra del día' y sus definiciones"""
    palabras = []
    # Patrones comunes
    patterns = [
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+(\w+)[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+["']?(\w+)["']?[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
        r'(?:mi|la)\s+palabra\s+(?:del\s+)?día\s+(?:es|fue)\s+(\w+)[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
    ]

    for idx, row in df.iterrows():
        msg = row['message']
        for pattern in patterns:
            matches = re.finditer(pattern, msg, re.IGNORECASE)
            for match in matches:
                palabra = match.group(1)
                definicion = match.group(2).strip() if match.group(2) else "Sin definición"
                palabras.append({
                    'date': row['date'],
                    'sender': row['sender'],
                    'palabra': palabra,
                    'definicion': definicion,
                    'mensaje_completo': row['message']
                })

    return palabras

def count_by_sender(items):
    """Cuenta items por remitente"""
    counter = defaultdict(int)
    for item in items:
        counter[item['sender']] += 1
    return dict(counter)

# ==================== INTERFAZ PRINCIPAL ====================

st.title("💌 WhatsApp Chat Analyzer")
st.subheader("Análisis de expresiones de amor y palabras del día")

# Sidebar
with st.sidebar:
    st.header("📤 Cargar Chat")
    uploaded_file = st.file_uploader("Sube tu chat de WhatsApp (.txt)", type='txt')

    st.divider()
    st.info("""
    **Cómo usar:**
    1. Exporta tu chat de WhatsApp (sin multimedia)
    2. Carga el archivo .txt aquí
    3. ¡Explora los datos! 💕

    **Se busca:**
    - Te quiero / Te amo
    - Me encantas
    - Palabra del día
    """)

if uploaded_file:
    # Leer y parsear el archivo
    try:
        text_content = uploaded_file.read().decode('utf-8')
        df = parse_whatsapp_chat(text_content)

        if len(df) == 0:
            st.error("❌ No se pudo parsear el archivo. Verifica que sea un chat de WhatsApp válido.")
        else:
            # Procesar datos
            love_expr = find_love_expressions(df)
            palabras_dia = find_palabra_del_dia(df)

            # ==================== ESTADÍSTICAS GENERALES ====================
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("📝 Mensajes Totales", len(df))
            with col2:
                fecha_inicio = df['date'].min().strftime('%d/%m/%Y')
                fecha_fin = df['date'].max().strftime('%d/%m/%Y')
                st.metric("📅 Período", f"{fecha_inicio} a {fecha_fin}")
            with col3:
                remitentes = df['sender'].nunique()
                st.metric("👥 Remitentes", remitentes)

            # ==================== EXPRESIONES DE AMOR ====================
            st.divider()
            st.header("💕 Expresiones de Amor")

            # Métricas de amor
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                count_tq = len(love_expr['te_quiero'])
                first_tq = love_expr['te_quiero'][0]['date'].strftime('%d/%m') if love_expr['te_quiero'] else 'N/A'
                st.metric("Te Quiero", count_tq, delta=f"❤️ desde {first_tq}")

            with col2:
                count_ta = len(love_expr['te_amo'])
                st.metric("Te Amo", count_ta)

            with col3:
                count_me = len(love_expr['me_encantas'])
                st.metric("Me Encantas", count_me)

            with col4:
                count_amor = len(love_expr['amor'])
                st.metric("Amor (general)", count_amor)

            # Distribución por remitente
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Te Quiero por Remitente")
                tq_by_sender = count_by_sender(love_expr['te_quiero'])
                if tq_by_sender:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    names = list(tq_by_sender.keys())
                    values = list(tq_by_sender.values())
                    colors = ['#667eea', '#764ba2']
                    ax.bar(names, values, color=colors[:len(names)])
                    ax.set_ylabel("Veces")
                    ax.set_title("¿Quién dice más 'Te Quiero'?")
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig, use_container_width=True)
                else:
                    st.info("No se encontraron 'te quiero'")

            with col2:
                st.subheader("Te Amo por Remitente")
                ta_by_sender = count_by_sender(love_expr['te_amo'])
                if ta_by_sender:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    names = list(ta_by_sender.keys())
                    values = list(ta_by_sender.values())
                    colors = ['#f093fb', '#f5576c']
                    ax.bar(names, values, color=colors[:len(names)])
                    ax.set_ylabel("Veces")
                    ax.set_title("¿Quién dice más 'Te Amo'?")
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig, use_container_width=True)
                else:
                    st.info("No se encontraron 'te amo'")

            # Timeline de expresiones
            st.subheader("📊 Timeline de 'Te Quiero'")
            if love_expr['te_quiero']:
                te_quiero_df = pd.DataFrame(love_expr['te_quiero'])
                te_quiero_df['date_only'] = te_quiero_df['date'].dt.date
                te_quiero_timeline = te_quiero_df.groupby('date_only').size()

                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(te_quiero_timeline.index, te_quiero_timeline.values, marker='o', linewidth=2, markersize=6, color='#667eea')
                ax.fill_between(te_quiero_timeline.index, te_quiero_timeline.values, alpha=0.3, color='#667eea')
                ax.set_xlabel("Fecha")
                ax.set_ylabel("Expresiones por Día")
                ax.set_title("Frecuencia de 'Te Quiero' en el Tiempo")
                plt.xticks(rotation=45)
                st.pyplot(fig, use_container_width=True)

            # Mostrar ejemplos
            with st.expander("📋 Ver ejemplos de 'Te Quiero'"):
                for item in love_expr['te_quiero'][-10:]:  # Últimos 10
                    st.write(f"**{item['sender']}** [{item['date'].strftime('%d/%m/%Y')}]")
                    st.write(f"> {item['message']}")
                    st.divider()

            # ==================== PALABRA DEL DÍA ====================
            st.divider()
            st.header("📚 Palabra del Día")

            if palabras_dia:
                st.metric("Total de Palabras Encontradas", len(palabras_dia))

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Palabras por Remitente")
                    palabras_by_sender = count_by_sender(palabras_dia)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    names = list(palabras_by_sender.keys())
                    values = list(palabras_by_sender.values())
                    colors = ['#4facfe', '#00f2fe']
                    ax.bar(names, values, color=colors[:len(names)])
                    ax.set_ylabel("Palabras Compartidas")
                    ax.set_title("¿Quién comparte más palabras?")
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig, use_container_width=True)

                with col2:
                    st.subheader("Últimas Palabras del Día")
                    # Mostrar las últimas 5 palabras
                    for palabra in palabras_dia[-5:]:
                        with st.container():
                            st.write(f"**{palabra['palabra'].upper()}** - {palabra['sender']}")
                            st.caption(f"📅 {palabra['date'].strftime('%d/%m/%Y')}")
                            st.info(f"✨ {palabra['definicion']}")

                # Tabla completa de palabras
                with st.expander("📖 Ver todas las Palabras del Día"):
                    palabras_df = pd.DataFrame(palabras_dia)[['date', 'sender', 'palabra', 'definicion']]
                    palabras_df['date'] = palabras_df['date'].dt.strftime('%d/%m/%Y')
                    st.dataframe(palabras_df, use_container_width=True, hide_index=True)

                    # Descargar como CSV
                    csv = palabras_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar Palabras (CSV)",
                        data=csv,
                        file_name="palabras_del_dia.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No se encontraron 'palabra del día' en el chat 😢")

            # ==================== ESTADÍSTICAS ADICIONALES ====================
            st.divider()
            st.header("📈 Estadísticas Adicionales")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Remitentes Más Activos")
                top_senders = df['sender'].value_counts()
                fig, ax = plt.subplots(figsize=(8, 4))
                top_senders.plot(kind='barh', ax=ax, color=['#667eea', '#764ba2', '#f093fb'])
                ax.set_xlabel("Número de Mensajes")
                st.pyplot(fig, use_container_width=True)

            with col2:
                st.subheader("Actividad por Hora")
                df['hour'] = df['date'].dt.hour
                hourly = df['hour'].value_counts().sort_index()
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(hourly.index, hourly.values, color='#667eea', alpha=0.7)
                ax.set_xlabel("Hora del Día")
                ax.set_ylabel("Mensajes")
                ax.set_title("¿Cuándo hablan más?")
                st.pyplot(fig, use_container_width=True)

            # ==================== RESUMEN ====================
            st.divider()
            st.header("📊 Resumen Ejecutivo")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                prom_amor = len(love_expr['te_quiero']) + len(love_expr['te_amo']) + len(love_expr['me_encantas'])
                st.metric("Total Expresiones Amor", prom_amor)
            with col2:
                dias_activos = len(df['date'].dt.date.unique())
                st.metric("Días Activos", dias_activos)
            with col3:
                promedio_msgs = len(df) / dias_activos if dias_activos > 0 else 0
                st.metric("Promedio Msgs/Día", f"{promedio_msgs:.1f}")
            with col4:
                if len(palabras_dia) > 0:
                    st.metric("Palabras del Día", len(palabras_dia))
                else:
                    st.metric("Palabras del Día", 0)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("👈 Carga un archivo de chat de WhatsApp para comenzar")

    # Mostrar ejemplo de formato
    with st.expander("ℹ️ Ver formato esperado"):
        st.code("""[6/8/2025, 6:20:34 am] Ana: Hola Juanjo
[6/8/2025, 6:28:43 am] Juan José: Hola Ana! Te quiero ❤️
[10/8/2026, 8:53:02 pm] Ana: La palabra del día que me dio Claude es petricor, que es el olor que desprende la tierra seca cuando llueve :)
""")
