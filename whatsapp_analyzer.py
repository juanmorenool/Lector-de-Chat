import streamlit as st
import pandas as pd
import re
import plotly.graph_objects as go
import plotly.express as px
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

# ==================== CONFIGURACIÓN DE COLORES Y EMOJIS ====================
SENDER_CONFIG = {
    'Ana': {
        'color': '#FFD700',  # Amarillo oro
        'emoji': '🍌',
        'light_color': '#FFED4E'
    },
    'Juan José': {
        'color': '#FF8C00',  # Naranja oscuro
        'emoji': '🍊',
        'light_color': '#FFA500'
    }
}

LOVE_PALETTE = {
    'te_quiero': '#FF69B4',      # Rosa fuerte
    'te_amo': '#FF1493',          # Rosa profundo
    'me_encantas': '#FFB6C1',     # Rosa claro
    'amor': '#FFC0CB'             # Rosa pastel
}

# Estilos
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #FFB6D9 0%, #FFE5EC 100%);
        padding: 20px;
        border-radius: 10px;
        color: #8B1A62;
        text-align: center;
        border-left: 5px solid #FF69B4;
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
    .love-summary {
        background: linear-gradient(135deg, #FFE5EC 0%, #FFF0F5 100%);
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #FF69B4;
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
                    'date_only': date_obj.date(),
                    'month': date_obj.strftime('%Y-%m'),
                    'month_name': date_obj.strftime('%B %Y'),
                    'hour': date_obj.hour,
                    'weekday': date_obj.strftime('%A'),
                    'weekday_num': date_obj.weekday()
                })
            except:
                pass

    return pd.DataFrame(messages)

def find_love_expressions(df):
    """
    Encuentra expresiones de amor específicas:
    - Te quiero / Te quiero mucho / Te quiero demasiado
    - Te amo / Te amo mucho
    - Me encantas
    - Amor (vocativo)
    """
    results = {
        'te_quiero': [],
        'te_amo': [],
        'me_encantas': [],
        'amor': []
    }

    for idx, row in df.iterrows():
        msg = row['message']
        msg_lower = msg.lower()

        # Te quiero: solo "te quiero", "te quiero mucho", "te quiero demasiado"
        # Evita "no te quiero", "que te quiero" en ciertos contextos
        if re.search(r'\bte quiero(?:\s+(?:mucho|demasiado|un montón|muchísimo|más que nada))?\b', msg_lower):
            # Validar que no sea negado
            if not re.search(r'\b(?:no|nunca)\s+te quiero\b', msg_lower):
                results['te_quiero'].append({
                    'date': row['date'],
                    'sender': row['sender'],
                    'message': row['message'],
                    'idx': idx,
                    'month': row['month'],
                    'hour': row['hour'],
                    'weekday': row['weekday']
                })

        # Te amo: solo "te amo", "te amo mucho"
        if re.search(r'\bte amo(?:\s+(?:mucho|un montón|muchísimo))?\b', msg_lower):
            if not re.search(r'\b(?:no|nunca)\s+te amo\b', msg_lower):
                results['te_amo'].append({
                    'date': row['date'],
                    'sender': row['sender'],
                    'message': row['message'],
                    'idx': idx,
                    'month': row['month'],
                    'hour': row['hour'],
                    'weekday': row['weekday']
                })

        # Me encantas (solo específicamente a ti)
        if re.search(r'\bme encantas\b', msg_lower):
            results['me_encantas'].append({
                'date': row['date'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx,
                'month': row['month'],
                'hour': row['hour'],
                'weekday': row['weekday']
            })

        # Amor (general, como saludo o término cariñoso)
        if re.search(r'(?:^|[^\w])amor(?:[^\w]|$)', msg_lower):
            results['amor'].append({
                'date': row['date'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx,
                'month': row['month'],
                'hour': row['hour'],
                'weekday': row['weekday']
            })

    return results

def find_palabra_del_dia(df):
    """Extrae todas las 'palabra del día' y sus definiciones"""
    palabras = []
    patterns = [
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+(\w+)[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
        r"(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+[\"']?(\w+)[\"']?[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)",
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
                    'mensaje_completo': row['message'],
                    'month': row['month']
                })

    return palabras

def get_sender_color(sender):
    """Retorna configuración de color para un remitente"""
    return SENDER_CONFIG.get(sender, {'color': '#888888', 'emoji': '💬', 'light_color': '#CCCCCC'})

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
    - Te quiero / Te quiero mucho
    - Te amo
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
                fecha_inicio = df['date'].min().strftime('%d de %B de %Y')
                fecha_fin = df['date'].max().strftime('%d de %B de %Y')
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📅 Período</div>
                        <div class="metric-value" style="font-size: 24px; margin: 5px 0;">
                            {fecha_inicio} <br/> → {fecha_fin}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
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
                if love_expr['te_quiero']:
                    first_tq = love_expr['te_quiero'][0]['date'].strftime('%d/%m/%Y')
                    st.metric("Te Quiero", count_tq, delta=f"❤️ desde {first_tq}")
                else:
                    st.metric("Te Quiero", count_tq)

            with col2:
                count_ta = len(love_expr['te_amo'])
                if love_expr['te_amo']:
                    first_ta = love_expr['te_amo'][0]['date'].strftime('%d/%m/%Y')
                    st.metric("Te Amo", count_ta, delta=f"💗 desde {first_ta}")
                else:
                    st.metric("Te Amo", count_ta)

            with col3:
                count_me = len(love_expr['me_encantas'])
                st.metric("Me Encantas", count_me)

            with col4:
                count_amor = len(love_expr['amor'])
                st.metric("Amor (general)", count_amor)

            # ==================== SECCIÓN TE QUIERO ====================
            st.subheader("💗 Análisis Detallado: Te Quiero")

            if love_expr['te_quiero']:
                tq_df = pd.DataFrame(love_expr['te_quiero'])
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    meses_disponibles = sorted(tq_df['month'].unique())
                    meses_dict = {m: pd.Timestamp(m).strftime('%B %Y') for m in meses_disponibles}
                    mes_filtro = st.selectbox(
                        "Filtrar por Mes (Te Quiero)",
                        options=[None] + meses_disponibles,
                        format_func=lambda x: "Todos los meses" if x is None else meses_dict[x],
                        key="te_quiero_mes"
                    )
                
                with col2:
                    horas_disponibles = sorted(tq_df['hour'].unique())
                    hora_filtro = st.multiselect(
                        "Filtrar por Hora",
                        options=horas_disponibles,
                        default=horas_disponibles,
                        key="te_quiero_hora"
                    )
                
                with col3:
                    dias_disponibles = sorted(tq_df['weekday'].unique())
                    dia_filtro = st.multiselect(
                        "Filtrar por Día",
                        options=dias_disponibles,
                        default=dias_disponibles,
                        key="te_quiero_dia"
                    )
                
                # Aplicar filtros
                tq_filtrado = tq_df.copy()
                if mes_filtro:
                    tq_filtrado = tq_filtrado[tq_filtrado['month'] == mes_filtro]
                tq_filtrado = tq_filtrado[tq_filtrado['hour'].isin(hora_filtro)]
                tq_filtrado = tq_filtrado[tq_filtrado['weekday'].isin(dia_filtro)]

                # Gráficas interactivas
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("¿Quién dice más 'Te Quiero'?")
                    tq_by_sender = tq_filtrado['sender'].value_counts()
                    
                    fig = go.Figure()
                    for sender in tq_by_sender.index:
                        config = get_sender_color(sender)
                        fig.add_trace(go.Bar(
                            x=[sender],
                            y=[tq_by_sender[sender]],
                            name=sender,
                            marker_color=config['color'],
                            text=[f"{config['emoji']} {tq_by_sender[sender]}"],
                            textposition="auto",
                            hovertemplate=f"<b>{sender}</b><br>{tq_by_sender[sender]} veces<extra></extra>"
                        ))
                    
                    fig.update_layout(
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="Veces",
                        height=400,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("'Te Quiero' por Hora del Día")
                    tq_by_hour = tq_filtrado.groupby('hour').size()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=tq_by_hour.index,
                        y=tq_by_hour.values,
                        mode='lines+markers',
                        name='Te Quiero',
                        line=dict(color='#FF69B4', width=3),
                        marker=dict(size=8, color='#FF1493'),
                        fill='tozeroy',
                        fillcolor='rgba(255, 105, 180, 0.2)',
                        hovertemplate="<b>Hora: %{x}:00</b><br>%{y} expresiones<extra></extra>"
                    ))
                    
                    fig.update_layout(
                        xaxis_title="Hora del Día",
                        yaxis_title="Expresiones",
                        height=400,
                        template="plotly_white",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Timeline temporal
                st.subheader("📊 Timeline: 'Te Quiero' en el Tiempo")
                tq_timeline = tq_filtrado.groupby('date_only').size()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=tq_timeline.index,
                    y=tq_timeline.values,
                    mode='lines+markers',
                    name='Te Quiero',
                    line=dict(color='#FF69B4', width=3),
                    marker=dict(size=6, color='#FF1493'),
                    fill='tozeroy',
                    fillcolor='rgba(255, 105, 180, 0.2)',
                    hovertemplate="<b>%{x}</b><br>%{y} expresiones<extra></extra>"
                ))
                
                fig.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Expresiones por Día",
                    height=400,
                    template="plotly_white",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Ejemplos
                with st.expander("📋 Ver ejemplos de 'Te Quiero'"):
                    for idx, item in enumerate(tq_filtrado.tail(10).iterrows()):
                        item_data = item[1]
                        config = get_sender_color(item_data['sender'])
                        st.write(f"**{config['emoji']} {item_data['sender']}** [{item_data['date'].strftime('%d/%m/%Y %H:%M')}]")
                        st.write(f"> {item_data['message']}")
                        st.divider()
            else:
                st.info("No se encontraron 'te quiero'")

            # ==================== SECCIÓN TE AMO ====================
            st.subheader("💗 Análisis Detallado: Te Amo")

            if love_expr['te_amo']:
                ta_df = pd.DataFrame(love_expr['te_amo'])
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    meses_disponibles_ta = sorted(ta_df['month'].unique())
                    meses_dict_ta = {m: pd.Timestamp(m).strftime('%B %Y') for m in meses_disponibles_ta}
                    mes_filtro_ta = st.selectbox(
                        "Filtrar por Mes (Te Amo)",
                        options=[None] + meses_disponibles_ta,
                        format_func=lambda x: "Todos los meses" if x is None else meses_dict_ta[x],
                        key="te_amo_mes"
                    )
                
                with col2:
                    horas_disponibles_ta = sorted(ta_df['hour'].unique())
                    hora_filtro_ta = st.multiselect(
                        "Filtrar por Hora (Te Amo)",
                        options=horas_disponibles_ta,
                        default=horas_disponibles_ta,
                        key="te_amo_hora"
                    )
                
                with col3:
                    dias_disponibles_ta = sorted(ta_df['weekday'].unique())
                    dia_filtro_ta = st.multiselect(
                        "Filtrar por Día (Te Amo)",
                        options=dias_disponibles_ta,
                        default=dias_disponibles_ta,
                        key="te_amo_dia"
                    )
                
                # Aplicar filtros
                ta_filtrado = ta_df.copy()
                if mes_filtro_ta:
                    ta_filtrado = ta_filtrado[ta_filtrado['month'] == mes_filtro_ta]
                ta_filtrado = ta_filtrado[ta_filtrado['hour'].isin(hora_filtro_ta)]
                ta_filtrado = ta_filtrado[ta_filtrado['weekday'].isin(dia_filtro_ta)]

                # Gráficas interactivas
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("¿Quién dice más 'Te Amo'?")
                    ta_by_sender = ta_filtrado['sender'].value_counts()
                    
                    fig = go.Figure()
                    for sender in ta_by_sender.index:
                        config = get_sender_color(sender)
                        fig.add_trace(go.Bar(
                            x=[sender],
                            y=[ta_by_sender[sender]],
                            name=sender,
                            marker_color=config['color'],
                            text=[f"{config['emoji']} {ta_by_sender[sender]}"],
                            textposition="auto",
                            hovertemplate=f"<b>{sender}</b><br>{ta_by_sender[sender]} veces<extra></extra>"
                        ))
                    
                    fig.update_layout(
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="Veces",
                        height=400,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("'Te Amo' por Hora del Día")
                    ta_by_hour = ta_filtrado.groupby('hour').size()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=ta_by_hour.index,
                        y=ta_by_hour.values,
                        mode='lines+markers',
                        name='Te Amo',
                        line=dict(color='#FF1493', width=3),
                        marker=dict(size=8, color='#C71585'),
                        fill='tozeroy',
                        fillcolor='rgba(255, 20, 147, 0.2)',
                        hovertemplate="<b>Hora: %{x}:00</b><br>%{y} expresiones<extra></extra>"
                    ))
                    
                    fig.update_layout(
                        xaxis_title="Hora del Día",
                        yaxis_title="Expresiones",
                        height=400,
                        template="plotly_white",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Timeline temporal
                st.subheader("📊 Timeline: 'Te Amo' en el Tiempo")
                ta_timeline = ta_filtrado.groupby('date_only').size()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ta_timeline.index,
                    y=ta_timeline.values,
                    mode='lines+markers',
                    name='Te Amo',
                    line=dict(color='#FF1493', width=3),
                    marker=dict(size=6, color='#C71585'),
                    fill='tozeroy',
                    fillcolor='rgba(255, 20, 147, 0.2)',
                    hovertemplate="<b>%{x}</b><br>%{y} expresiones<extra></extra>"
                ))
                
                fig.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Expresiones por Día",
                    height=400,
                    template="plotly_white",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Ejemplos
                with st.expander("📋 Ver ejemplos de 'Te Amo'"):
                    for idx, item in enumerate(ta_filtrado.tail(10).iterrows()):
                        item_data = item[1]
                        config = get_sender_color(item_data['sender'])
                        st.write(f"**{config['emoji']} {item_data['sender']}** [{item_data['date'].strftime('%d/%m/%Y %H:%M')}]")
                        st.write(f"> {item_data['message']}")
                        st.divider()
            else:
                st.info("No se encontraron 'te amo'")

            # ==================== PALABRA DEL DÍA ====================
            st.divider()
            st.header("📚 Palabra del Día")

            if palabras_dia:
                st.metric("Total de Palabras Encontradas", len(palabras_dia))

                # Filtro por mes
                col1, col2 = st.columns(2)
                with col1:
                    meses_palabras = sorted(pd.DataFrame(palabras_dia)['month'].unique())
                    meses_dict_pd = {m: pd.Timestamp(m).strftime('%B %Y') for m in meses_palabras}
                    mes_filtro_pd = st.selectbox(
                        "Filtrar Palabras por Mes",
                        options=[None] + meses_palabras,
                        format_func=lambda x: "Todos los meses" if x is None else meses_dict_pd[x],
                        key="palabras_mes"
                    )

                palabras_filtradas = palabras_dia
                if mes_filtro_pd:
                    palabras_filtradas = [p for p in palabras_dia if p['month'] == mes_filtro_pd]

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Palabras por Remitente")
                    palabras_by_sender = count_by_sender(palabras_filtradas)
                    
                    fig = go.Figure()
                    for sender in palabras_by_sender.keys():
                        config = get_sender_color(sender)
                        fig.add_trace(go.Bar(
                            x=[sender],
                            y=[palabras_by_sender[sender]],
                            name=sender,
                            marker_color=config['color'],
                            text=[f"{config['emoji']} {palabras_by_sender[sender]}"],
                            textposition="auto"
                        ))
                    
                    fig.update_layout(
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="Palabras Compartidas",
                        height=400,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("Últimas Palabras del Día")
                    # Mostrar las últimas 5 palabras
                    for palabra in reversed(palabras_filtradas[-5:]):
                        with st.container():
                            config = get_sender_color(palabra['sender'])
                            st.write(f"**{palabra['palabra'].upper()}** - {config['emoji']} {palabra['sender']}")
                            st.caption(f"📅 {palabra['date'].strftime('%d/%m/%Y')}")
                            st.info(f"✨ {palabra['definicion']}")

                # Tabla completa de palabras
                with st.expander("📖 Ver todas las Palabras del Día"):
                    palabras_df = pd.DataFrame(palabras_filtradas)[['date', 'sender', 'palabra', 'definicion']]
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
                
                fig = go.Figure()
                for sender in top_senders.index:
                    config = get_sender_color(sender)
                    fig.add_trace(go.Bar(
                        y=[sender],
                        x=[top_senders[sender]],
                        orientation='h',
                        marker_color=config['color'],
                        text=[f"{config['emoji']} {top_senders[sender]}"],
                        textposition="auto",
                        name=sender
                    ))
                
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Número de Mensajes",
                    height=300,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Actividad por Hora")
                hourly = df['hour'].value_counts().sort_index()
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=hourly.index,
                    y=hourly.values,
                    marker_color='#FFB6D9',
                    text=hourly.values,
                    textposition="auto",
                    hovertemplate="<b>%{x}:00</b><br>%{y} mensajes<extra></extra>"
                ))
                
                fig.update_layout(
                    xaxis_title="Hora del Día",
                    yaxis_title="Mensajes",
                    height=300,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

            # ==================== RESUMEN DE NUESTRO AMOR ====================
            st.divider()
            st.markdown("""
                <div class="love-summary">
                    <h2 style="text-align: center; color: #D63384;">💑 RESUMEN DE NUESTRO AMOR 💑</h2>
                </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                prom_amor = len(love_expr['te_quiero']) + len(love_expr['te_amo']) + len(love_expr['me_encantas'])
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">💗 Expresiones Totales</div>
                        <div class="metric-value">{prom_amor}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                dias_activos = len(df['date'].dt.date.unique())
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📅 Días Juntos</div>
                        <div class="metric-value">{dias_activos}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                promedio_msgs = len(df) / dias_activos if dias_activos > 0 else 0
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">💬 Msgs/Día</div>
                        <div class="metric-value">{promedio_msgs:.1f}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                if len(palabras_dia) > 0:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">📚 Palabras del Día</div>
                            <div class="metric-value">{len(palabras_dia)}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">📚 Palabras del Día</div>
                            <div class="metric-value">0</div>
                        </div>
                    """, unsafe_allow_html=True)

            # Resumen por persona
            st.subheader("💕 Desglose por Persona")
            col1, col2 = st.columns(2)
            
            with col1:
                for sender in sorted(df['sender'].unique()):
                    config = get_sender_color(sender)
                    total_tq = len([x for x in love_expr['te_quiero'] if x['sender'] == sender])
                    total_ta = len([x for x in love_expr['te_amo'] if x['sender'] == sender])
                    total_me = len([x for x in love_expr['me_encantas'] if x['sender'] == sender])
                    total_amor = len([x for x in love_expr['amor'] if x['sender'] == sender])
                    
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {config['light_color']} 0%, rgba(255, 255, 255, 0.8) 100%); 
                                    padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {config['color']};">
                            <h4>{config['emoji']} {sender}</h4>
                            <p><b>Te Quiero:</b> {total_tq} | <b>Te Amo:</b> {total_ta} | <b>Me Encantas:</b> {total_me} | <b>Amor:</b> {total_amor}</p>
                        </div>
                    """, unsafe_allow_html=True)

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
