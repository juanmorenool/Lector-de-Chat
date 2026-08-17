import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import calendar

# ==================== CONFIGURACIÓN DE PÁGINA ====================
st.set_page_config(
    page_title="WhatsApp Chat Analyzer - Palabras del Corazón",
    page_icon="💌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== PALETA DE COLORES SALMÓN / ROSADA ====================
COLORS = {
    'Ana': '#FFD700',           # Amarillo banana
    'Juan José': '#FF8C00',     # Naranja
    'Juan Jo': '#FF8C00',       # Naranja
    'primary': '#FF6B6B',
    'secondary': '#FF9A8B',
    'accent': '#FFB6C1',
    'bg': '#FFF0F0',
    'text': '#4A4A4A',
    'gradient_start': '#FF9A8B',
    'gradient_end': '#FF6B6B',
    'salmon_light': '#FFE5E5',
    'salmon_mid': '#FFA07A',
    'salmon_dark': '#FA8072',
    'rose': '#FF69B4',
    'coral': '#F08080'
}

EMOJIS = {
    'Ana': '🍌',
    'Juan José': '🍊',
    'Juan Jo': '🍊'
}

# ==================== ESTILOS CSS PERSONALIZADOS ====================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #FFF5F5 0%, #FFE8E8 100%);
    }

    .metric-card {
        background: linear-gradient(135deg, #FF9A8B 0%, #FF6B6B 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        margin: 10px 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-label {
        font-size: 13px;
        opacity: 0.95;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    .love-card {
        background: linear-gradient(135deg, #FFB6C1 0%, #FF69B4 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 105, 180, 0.3);
    }

    .period-card {
        background: linear-gradient(135deg, #FFA07A 0%, #FA8072 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(250, 128, 114, 0.3);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #FFE5E5 0%, #FFD5D5 100%);
        border-radius: 12px 12px 0 0;
        padding: 10px 24px;
        font-weight: 600;
        color: #FF6B6B;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF9A8B 0%, #FF6B6B 100%) !important;
        color: white !important;
    }

    .stSlider > div > div > div {
        background: linear-gradient(90deg, #FF9A8B, #FF6B6B) !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #FF6B6B !important;
    }

    .sender-badge-ana {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
    }
    .sender-badge-juanjo {
        background: linear-gradient(135deg, #FF8C00 0%, #FF6347 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
    }

    .love-quote {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%);
        border-left: 4px solid #FF69B4;
        padding: 16px 20px;
        border-radius: 0 12px 12px 0;
        margin: 8px 0;
        font-style: italic;
        color: #4A4A4A;
    }

    .word-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(255, 107, 107, 0.1);
        border: 1px solid #FFE5E5;
        transition: all 0.3s ease;
    }
    .word-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(255, 107, 107, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES AUXILIARES ====================

def get_sender_color(sender):
    """Devuelve el color asignado a cada remitente"""
    sender_clean = sender.strip()
    if 'Ana' in sender_clean:
        return COLORS['Ana']
    elif 'Juan' in sender_clean:
        return COLORS['Juan José']
    return COLORS['primary']

def get_sender_emoji(sender):
    """Devuelve el emoji asignado a cada remitente"""
    sender_clean = sender.strip()
    if 'Ana' in sender_clean:
        return EMOJIS['Ana']
    elif 'Juan' in sender_clean:
        return EMOJIS['Juan José']
    return '💕'

def get_sender_badge(sender):
    """Devuelve HTML con el badge del remitente"""
    emoji = get_sender_emoji(sender)
    if 'Ana' in sender:
        return f'<span class="sender-badge-ana">{emoji} {sender}</span>'
    else:
        return f'<span class="sender-badge-juanjo">{emoji} {sender}</span>'

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
            if not message.strip():
                continue
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                # Parsear hora
                time_clean = time_str.strip().lower()
                if 'am' in time_clean or 'pm' in time_clean:
                    time_obj = datetime.strptime(time_clean, '%I:%M:%S %p').time()
                else:
                    time_obj = datetime.strptime(time_clean, '%H:%M:%S').time()

                full_datetime = datetime.combine(date_obj.date(), time_obj)

                messages.append({
                    'datetime': full_datetime,
                    'date': date_obj,
                    'time': time_str,
                    'hour': time_obj.hour,
                    'sender': sender.strip(),
                    'message': message.strip(),
                    'date_only': date_obj.date(),
                    'month': date_obj.month,
                    'month_name': calendar.month_name[date_obj.month],
                    'year_month': date_obj.strftime('%Y-%m'),
                    'day_of_week': date_obj.strftime('%A'),
                    'day_name': date_obj.strftime('%a')
                })
            except Exception as e:
                pass

    return pd.DataFrame(messages)

def is_valid_love_expression(msg_lower, base_phrase, intensifiers):
    """
    Verifica si una expresión de amor es válida.
    base_phrase: 'te quiero' o 'te amo'
    intensifiers: lista de palabras permitidas después de la frase base
    """
    if base_phrase not in msg_lower:
        return False

    emoji_chars = '❤️💕💖💗💓💝💘🥰😍🫶✨'

    # Encontrar todas las ocurrencias
    for match in re.finditer(rf'\b{re.escape(base_phrase)}\b', msg_lower):
        end_pos = match.end()
        rest = msg_lower[end_pos:]
        rest_clean = rest.strip()

        # Si no hay nada más o empieza con puntuación → válido
        if not rest_clean:
            return True

        # Permitir solo puntuación/emojis después de la frase
        only_symbols = re.sub(rf'[\s\.,;:!?\-¡¿{emoji_chars}]', '', rest_clean)
        if not only_symbols:
            return True

        # Obtener la siguiente palabra
        words_after = rest_clean.split()
        if not words_after:
            return True

        next_word = re.sub(r'[^\wáéíóúñ]', '', words_after[0].lower())
        trailing_text = rest_clean[len(words_after[0]):].strip()
        trailing_only_symbols = re.sub(rf'[\s\.,;:!?\-¡¿{emoji_chars}]', '', trailing_text)

        # Si la siguiente palabra es un intensificador y no hay más palabras reales → válido
        if next_word in intensifiers and not trailing_only_symbols:
            return True

    return False

@st.cache_data
def find_love_expressions(df):
    """Encuentra expresiones de amor válidas"""

    # Intensificadores permitidos para "te quiero" (estricto)
    tq_intensifiers = [
        'mucho', 'muchisimo', 'muchísimo', 'demasiado', 'demasiaado', 'demasiadoo'
    ]

    # Intensificadores permitidos para "te amo" (estricto)
    ta_intensifiers = [
        'mucho', 'muchisimo', 'muchísimo', 'demasiado', 'demasiaado', 'demasiadoo'
    ]

    results = {
        'te_quiero': [],
        'te_amo': [],
        'me_encantas': [],
        'amor': []
    }

    for idx, row in df.iterrows():
        msg = row['message']
        msg_lower = msg.lower()

        # Te quiero (solo frases válidas, no "te quiero besar")
        if is_valid_love_expression(msg_lower, 'te quiero', tq_intensifiers):
            results['te_quiero'].append({
                'datetime': row['datetime'],
                'date': row['date'],
                'time': row['time'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

        # Te amo (solo frases válidas)
        if is_valid_love_expression(msg_lower, 'te amo', ta_intensifiers):
            results['te_amo'].append({
                'datetime': row['datetime'],
                'date': row['date'],
                'time': row['time'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

        # Me encantas
        if re.search(r'\bme encantas\b', msg_lower):
            results['me_encantas'].append({
                'datetime': row['datetime'],
                'date': row['date'],
                'time': row['time'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

        # Amor como vocativo/término cariñoso
        if re.search(r'(?:^|[^\w])amor(?:[^\w]|$)', msg_lower):
            results['amor'].append({
                'datetime': row['datetime'],
                'date': row['date'],
                'time': row['time'],
                'sender': row['sender'],
                'message': row['message'],
                'idx': idx
            })

    return results

@st.cache_data
def find_palabra_del_dia(df):
    """Extrae todas las 'palabra del día' y sus definiciones"""
    palabras = []
    patterns = [
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+(\w+)[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+["\']?(\w+)["\']?[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
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
                    'datetime': row['datetime'],
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

# ==================== FUNCIONES DE GRÁFICAS INTERACTIVAS ====================

def plot_love_by_sender(items, title, color_map):
    """Gráfica de barras interactiva por remitente"""
    counts = count_by_sender(items)
    if not counts:
        return None

    df_plot = pd.DataFrame([
        {'Remitente': k, 'Cantidad': v, 'Emoji': get_sender_emoji(k), 'Color': get_sender_color(k)}
        for k, v in counts.items()
    ])

    fig = px.bar(
        df_plot,
        x='Remitente',
        y='Cantidad',
        color='Remitente',
        color_discrete_map=color_map,
        text='Cantidad',
        title=title,
        height=400
    )
    fig.update_traces(
        textposition='outside',
        textfont_size=16,
        marker_line_width=2,
        marker_line_color='white'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=13, color=COLORS['text']),
        title_font_size=18,
        title_font_color=COLORS['primary'],
        showlegend=False,
        xaxis_title='',
        yaxis_title='Veces dicho',
        hoverlabel=dict(bgcolor='white', font_size=14),
        margin=dict(t=60, b=40)
    )
    return fig

def plot_timeline(items, title, color, granularity='D'):
    """Timeline interactivo con Plotly"""
    if not items:
        return None

    df_plot = pd.DataFrame(items)

    if granularity == 'H':
        df_plot['period'] = df_plot['datetime'].dt.floor('h')
        x_title = 'Fecha y hora'
        y_title = 'Expresiones por hora'
        hover_template = '<b>%{x|%d/%m/%Y %H:00}</b><br>Expresiones: %{y}<extra></extra>'
    elif granularity == 'M':
        df_plot['period'] = df_plot['datetime'].dt.to_period('M').dt.to_timestamp()
        x_title = 'Mes'
        y_title = 'Expresiones por mes'
        hover_template = '<b>%{x|%m/%Y}</b><br>Expresiones: %{y}<extra></extra>'
    else:
        df_plot['period'] = df_plot['datetime'].dt.floor('D')
        x_title = 'Fecha'
        y_title = 'Expresiones por día'
        hover_template = '<b>%{x|%d/%m/%Y}</b><br>Expresiones: %{y}<extra></extra>'

    timeline = df_plot.groupby('period').size().reset_index(name='count').sort_values('period')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline['period'],
        y=timeline['count'],
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=8, color=color, line=dict(width=2, color='white')),
        fill='tozeroy',
        fillcolor=f'rgba(255, 107, 107, 0.15)',
        hovertemplate=hover_template
    ))

    fig.update_layout(
        title=title,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=13, color=COLORS['text']),
        title_font_size=18,
        title_font_color=COLORS['primary'],
        xaxis_title=x_title,
        yaxis_title=y_title,
        hovermode='x unified',
        margin=dict(t=60, b=40)
    )
    return fig

def plot_heatmap_by_hour(df_filtered):
    """Heatmap de actividad por día de semana y hora"""
    if df_filtered.empty:
        return None

    pivot = df_filtered.pivot_table(
        index='day_of_week',
        columns='hour',
        values='message',
        aggfunc='count',
        fill_value=0
    )

    # Ordenar días de semana
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    fig = px.imshow(
        pivot.values,
        x=[f'{h:02d}:00' for h in pivot.columns],
        y=day_labels[:len(pivot)],
        color_continuous_scale='Peach',
        title='🔥 Mapa de calor: Actividad por día y hora',
        height=350
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=12),
        title_font_size=16,
        title_font_color=COLORS['primary']
    )
    return fig

def plot_monthly_trend(items, title):
    """Tendencia mensual de expresiones de amor"""
    if not items:
        return None

    df_plot = pd.DataFrame(items)
    df_plot['year_month'] = df_plot['date'].dt.strftime('%Y-%m')
    monthly = df_plot.groupby('year_month').size().reset_index(name='count')
    monthly['fecha'] = pd.to_datetime(monthly['year_month'])
    monthly = monthly.sort_values('fecha')

    fig = px.bar(
        monthly,
        x='year_month',
        y='count',
        text='count',
        title=title,
        color_discrete_sequence=[COLORS['salmon_dark']],
        height=350
    )
    fig.update_traces(
        textposition='outside',
        marker_line_width=2,
        marker_line_color='white',
        marker_color=COLORS['salmon_dark']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=13),
        title_font_size=16,
        title_font_color=COLORS['primary'],
        xaxis_title='Mes',
        yaxis_title='Cantidad',
        showlegend=False,
        margin=dict(t=60, b=40)
    )
    return fig

def plot_radar_love(love_expr):
    """Gráfica radar de expresiones de amor"""
    categories = ['Te Quiero', 'Te Amo', 'Me Encantas', 'Amor']
    values = [
        len(love_expr['te_quiero']),
        len(love_expr['te_amo']),
        len(love_expr['me_encantas']),
        len(love_expr['amor'])
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(255, 107, 107, 0.3)',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=10, color=COLORS['primary'])
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(values) * 1.2]),
            bgcolor='rgba(255, 240, 240, 0.5)'
        ),
        showlegend=False,
        title='💝 Radar de Amor',
        title_font_size=18,
        title_font_color=COLORS['primary'],
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=13),
        height=450
    )
    return fig

# ==================== INTERFAZ PRINCIPAL ====================

st.title("💌 WhatsApp Chat Analyzer")
st.markdown("<p style='color: #FF6B6B; font-size: 18px; font-weight: 600;'>✨ Análisis de expresiones de amor y palabras del día ✨</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📤 Cargar Chat")
    uploaded_file = st.file_uploader("Sube tu chat de WhatsApp (.txt)", type='txt')

    st.divider()

    if uploaded_file:
        st.success("✅ Chat cargado correctamente")

    st.info("""
    **Cómo usar:**
    1. Exporta tu chat de WhatsApp (sin multimedia)
    2. Carga el archivo .txt aquí
    3. ¡Explora los datos con los filtros! 💕

    **Se busca:**
    - Te quiero / Te amo (puramente)
    - Me encantas
    - Palabra del día
    """)

    st.divider()
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #FFE5E5, #FFF0F0); border-radius: 12px;'>
        <p style='margin: 0; font-size: 24px;'>🍌 Ana + 🍊 Juan Jo</p>
        <p style='margin: 5px 0 0 0; color: #FF6B6B; font-size: 12px;'>Colores personalizados</p>
    </div>
    """, unsafe_allow_html=True)

if uploaded_file:
    try:
        text_content = uploaded_file.read().decode('utf-8')
        df = parse_whatsapp_chat(text_content)

        if len(df) == 0:
            st.error("❌ No se pudo parsear el archivo. Verifica que sea un chat de WhatsApp válido.")
        else:
            # ==================== FILTROS INTERACTIVOS ====================
            st.divider()
            st.subheader("🔍 Filtros Interactivos")

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)

            available_months = sorted(df['year_month'].unique())
            month_options = ['Todos'] + [datetime.strptime(m, '%Y-%m').strftime('%B %Y') for m in available_months]
            selected_month = None

            with col_f1:
                selected_month_label = st.selectbox("📅 Filtrar por mes", month_options)
                if selected_month_label != 'Todos':
                    selected_month = available_months[month_options.index(selected_month_label) - 1]

            with col_f2:
                min_date = df['date'].min().date()
                max_date = df['date'].max().date()
                date_range = st.date_input(
                    "📆 Rango de fechas",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )

            with col_f3:
                hour_range = st.slider(
                    "⏰ Rango de horas",
                    min_value=0,
                    max_value=23,
                    value=(0, 23)
                )

            with col_f4:
                days_map = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes',
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                available_days = [d for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] if d in df['day_of_week'].unique()]
                selected_days = st.multiselect(
                    "🗓️ Filtrar por día",
                    options=available_days,
                    default=available_days,
                    format_func=lambda x: days_map.get(x, x)
                )

            filter_mask = pd.Series(True, index=df.index)
            if selected_month:
                filter_mask &= (df['year_month'] == selected_month)
            if len(date_range) == 2:
                filter_mask &= (df['date_only'] >= date_range[0]) & (df['date_only'] <= date_range[1])
            filter_mask &= (df['hour'] >= hour_range[0]) & (df['hour'] <= hour_range[1])
            if selected_days:
                filter_mask &= df['day_of_week'].isin(selected_days)
            else:
                filter_mask &= False

            df_filtered = df[filter_mask].copy()

            if df_filtered.empty:
                st.warning("⚠️ No hay mensajes con esos filtros. Ajusta mes, día, fecha u hora.")
                st.stop()

            # Procesar datos filtrados
            love_expr = find_love_expressions(df_filtered)
            palabras_dia = find_palabra_del_dia(df_filtered)

            # ==================== ESTADÍSTICAS GENERALES ====================
            st.divider()
            st.header("📊 Estadísticas Generales")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📝 MENSAJES TOTALES</div>
                    <div class="metric-value">{len(df_filtered):,}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                fecha_inicio_dt = df_filtered['date'].min()
                fecha_fin_dt = df_filtered['date'].max()
                fecha_inicio = fecha_inicio_dt.strftime('%d/%m/%Y')
                fecha_fin = fecha_fin_dt.strftime('%d/%m/%Y')
                dias_totales = (fecha_fin_dt - fecha_inicio_dt).days + 1
                st.markdown(f"""
                <div class="period-card">
                    <div class="metric-label">📅 PERÍODO</div>
                    <div class="metric-value" style="font-size: 22px; line-height: 1.25;">{fecha_inicio} → {fecha_fin}</div>
                    <div style="font-size: 14px; margin-top: 10px; opacity: 0.95;">{dias_totales} días juntos 💕</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                remitentes = df_filtered['sender'].unique()
                remitentes_html = '<br>'.join([f"{get_sender_emoji(r)} {r}" for r in remitentes])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">👥 REMITENTES</div>
                    <div class="metric-value" style="font-size: 32px;">{len(remitentes)}</div>
                    <div style="font-size: 14px; margin-top: 8px; opacity: 0.9;">{remitentes_html}</div>
                </div>
                """, unsafe_allow_html=True)

            # ==================== EXPRESIONES DE AMOR ====================
            st.divider()
            st.header("💕 Expresiones de Amor")

            # Métricas de amor en tarjetas
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                count_tq = len(love_expr['te_quiero'])
                first_tq = love_expr['te_quiero'][0]['date'].strftime('%d/%m/%Y') if love_expr['te_quiero'] else 'N/A'
                st.markdown(f"""
                <div class="love-card">
                    <div style="font-size: 28px;">💘</div>
                    <div class="metric-value">{count_tq}</div>
                    <div class="metric-label">Te Quiero</div>
                    <div style="font-size: 11px; margin-top: 6px; opacity: 0.9;">Primero: {first_tq}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                count_ta = len(love_expr['te_amo'])
                first_ta = love_expr['te_amo'][0]['date'].strftime('%d/%m/%Y') if love_expr['te_amo'] else 'N/A'
                st.markdown(f"""
                <div class="love-card">
                    <div style="font-size: 28px;">💖</div>
                    <div class="metric-value">{count_ta}</div>
                    <div class="metric-label">Te Amo</div>
                    <div style="font-size: 11px; margin-top: 6px; opacity: 0.9;">Primero: {first_ta}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                count_me = len(love_expr['me_encantas'])
                st.markdown(f"""
                <div class="love-card">
                    <div style="font-size: 28px;">🥰</div>
                    <div class="metric-value">{count_me}</div>
                    <div class="metric-label">Me Encantas</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                count_amor = len(love_expr['amor'])
                st.markdown(f"""
                <div class="love-card">
                    <div style="font-size: 28px;">💝</div>
                    <div class="metric-value">{count_amor}</div>
                    <div class="metric-label">Amor (general)</div>
                </div>
                """, unsafe_allow_html=True)

            # Tabs para diferentes vistas
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Comparación por Remitente",
                "📈 Timeline Detallado",
                "📅 Tendencia Mensual",
                "💝 Radar de Amor"
            ])

            with tab1:
                col1, col2 = st.columns(2)

                with col1:
                    color_map_tq = {s: get_sender_color(s) for s in df_filtered['sender'].unique()}
                    fig = plot_love_by_sender(
                        love_expr['te_quiero'],
                        f"🍌🍊 ¿Quién dice más 'Te Quiero'?",
                        color_map_tq
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No se encontraron 'te quiero' en el período seleccionado")

                with col2:
                    fig = plot_love_by_sender(
                        love_expr['te_amo'],
                        f"🍌🍊 ¿Quién dice más 'Te Amo'?",
                        color_map_tq
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No se encontraron 'te amo' en el período seleccionado")

            with tab2:
                granularity_label = st.selectbox(
                    "🕒 Precisión del timeline",
                    ["Hora", "Día", "Mes"],
                    index=1,
                    key="timeline_granularity"
                )
                granularity_map = {"Hora": "H", "Día": "D", "Mes": "M"}
                selected_granularity = granularity_map[granularity_label]

                col1, col2 = st.columns(2)

                with col1:
                    fig = plot_timeline(
                        love_expr['te_quiero'],
                        "💘 Timeline de 'Te Quiero'",
                        COLORS['primary'],
                        selected_granularity
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fig = plot_timeline(
                        love_expr['te_amo'],
                        "💖 Timeline de 'Te Amo'",
                        COLORS['rose'],
                        selected_granularity
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                # Timeline combinado
                if love_expr['te_quiero'] or love_expr['te_amo']:
                    st.subheader("📊 Timeline Comparativo: Te Quiero vs Te Amo")

                    fig = go.Figure()

                    if love_expr['te_quiero']:
                        tq_df = pd.DataFrame(love_expr['te_quiero'])
                        if selected_granularity == 'H':
                            tq_df['period'] = tq_df['datetime'].dt.floor('h')
                        elif selected_granularity == 'M':
                            tq_df['period'] = tq_df['datetime'].dt.to_period('M').dt.to_timestamp()
                        else:
                            tq_df['period'] = tq_df['datetime'].dt.floor('D')
                        tq_timeline = tq_df.groupby('period').size().reset_index(name='count').sort_values('period')

                        fig.add_trace(go.Scatter(
                            x=tq_timeline['period'],
                            y=tq_timeline['count'],
                            mode='lines+markers',
                            name='Te Quiero 💘',
                            line=dict(color=COLORS['primary'], width=3),
                            marker=dict(size=8),
                            fill='tozeroy',
                            fillcolor='rgba(255, 107, 107, 0.1)'
                        ))

                    if love_expr['te_amo']:
                        ta_df = pd.DataFrame(love_expr['te_amo'])
                        if selected_granularity == 'H':
                            ta_df['period'] = ta_df['datetime'].dt.floor('h')
                        elif selected_granularity == 'M':
                            ta_df['period'] = ta_df['datetime'].dt.to_period('M').dt.to_timestamp()
                        else:
                            ta_df['period'] = ta_df['datetime'].dt.floor('D')
                        ta_timeline = ta_df.groupby('period').size().reset_index(name='count').sort_values('period')

                        fig.add_trace(go.Scatter(
                            x=ta_timeline['period'],
                            y=ta_timeline['count'],
                            mode='lines+markers',
                            name='Te Amo 💖',
                            line=dict(color=COLORS['rose'], width=3),
                            marker=dict(size=8),
                            fill='tozeroy',
                            fillcolor='rgba(255, 105, 180, 0.1)'
                        ))

                    fig.update_layout(
                        height=450,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Poppins', size=13),
                        title_font_size=16,
                        title_font_color=COLORS['primary'],
                        xaxis_title='Fecha',
                        yaxis_title='Expresiones',
                        hovermode='x unified',
                        legend=dict(
                            orientation='h',
                            yanchor='bottom',
                            y=1.02,
                            xanchor='right',
                            x=1
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tab3:
                col1, col2 = st.columns(2)

                with col1:
                    fig = plot_monthly_trend(love_expr['te_quiero'], "💘 'Te Quiero' por Mes")
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fig = plot_monthly_trend(love_expr['te_amo'], "💖 'Te Amo' por Mes")
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

            with tab4:
                col1, col2 = st.columns([2, 1])

                with col1:
                    fig = plot_radar_love(love_expr)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("""
                    <div style="padding: 20px; background: linear-gradient(135deg, #FFF0F5, #FFE4E1); border-radius: 16px; height: 100%;">
                        <h4 style="color: #FF6B6B; margin-bottom: 15px;">💝 Resumen de Expresiones</h4>
                    """, unsafe_allow_html=True)

                    total_expr = sum([
                        len(love_expr['te_quiero']),
                        len(love_expr['te_amo']),
                        len(love_expr['me_encantas']),
                        len(love_expr['amor'])
                    ])

                    st.markdown(f"""
                        <p style="font-size: 32px; font-weight: 700; color: #FF6B6B; margin: 0;">{total_expr}</p>
                        <p style="color: #666; margin-bottom: 20px;">expresiones totales</p>

                        <p>💘 Te Quiero: <b>{len(love_expr['te_quiero'])}</b></p>
                        <p>💖 Te Amo: <b>{len(love_expr['te_amo'])}</b></p>
                        <p>🥰 Me Encantas: <b>{len(love_expr['me_encantas'])}</b></p>
                        <p>💝 Amor: <b>{len(love_expr['amor'])}</b></p>
                    </div>
                    """, unsafe_allow_html=True)

            # Mostrar ejemplos recientes
            with st.expander("📋 Ver ejemplos recientes de 'Te Quiero' y 'Te Amo'"):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("💘 Últimos 'Te Quiero'")
                    for item in love_expr['te_quiero'][-5:]:
                        st.markdown(f"""
                        <div class="love-quote">
                            <p style="margin: 0; font-weight: 600; color: #FF6B6B;">
                                {get_sender_emoji(item['sender'])} {item['sender']} — {item['date'].strftime('%d/%m/%Y %H:%M')}
                            </p>
                            <p style="margin: 8px 0 0 0;">{item['message']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                with col2:
                    st.subheader("💖 Últimos 'Te Amo'")
                    for item in love_expr['te_amo'][-5:]:
                        st.markdown(f"""
                        <div class="love-quote">
                            <p style="margin: 0; font-weight: 600; color: #FF69B4;">
                                {get_sender_emoji(item['sender'])} {item['sender']} — {item['date'].strftime('%d/%m/%Y %H:%M')}
                            </p>
                            <p style="margin: 8px 0 0 0;">{item['message']}</p>
                        </div>
                        """, unsafe_allow_html=True)

            # ==================== PALABRA DEL DÍA ====================
            st.divider()
            st.header("📚 Palabra del Día")

            if palabras_dia:
                st.metric("📖 Total de Palabras Encontradas", len(palabras_dia))

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("🍌🍊 Palabras por Remitente")
                    palabras_by_sender = count_by_sender(palabras_dia)

                    fig = go.Figure()
                    for sender, count in palabras_by_sender.items():
                        fig.add_trace(go.Bar(
                            x=[sender],
                            y=[count],
                            name=f"{get_sender_emoji(sender)} {sender}",
                            marker_color=get_sender_color(sender),
                            text=[count],
                            textposition='outside',
                            textfont_size=16
                        ))

                    fig.update_layout(
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Poppins', size=13),
                        showlegend=True,
                        legend=dict(orientation='h', yanchor='bottom', y=1.02),
                        xaxis_title='',
                        yaxis_title='Palabras compartidas',
                        margin=dict(t=80, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("✨ Últimas Palabras del Día")
                    for palabra in palabras_dia[-5:]:
                        emoji = get_sender_emoji(palabra['sender'])
                        color = get_sender_color(palabra['sender'])
                        st.markdown(f"""
                        <div class="word-card" style="margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                <span style="font-size: 24px;">{emoji}</span>
                                <span style="font-size: 20px; font-weight: 700; color: {color};">
                                    {palabra['palabra'].upper()}
                                </span>
                                <span style="color: #999; font-size: 12px;">
                                    {palabra['date'].strftime('%d/%m/%Y')}
                                </span>
                            </div>
                            <p style="margin: 0; color: #555; font-style: italic;">
                                ✨ {palabra['definicion']}
                            </p>
                            <p style="margin: 6px 0 0 0; font-size: 11px; color: #999;">
                                Por: {palabra['sender']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                # Tabla completa
                with st.expander("📖 Ver todas las Palabras del Día"):
                    palabras_df = pd.DataFrame(palabras_dia)[['date', 'sender', 'palabra', 'definicion']]
                    palabras_df['date'] = palabras_df['date'].dt.strftime('%d/%m/%Y')
                    palabras_df['emoji'] = palabras_df['sender'].apply(get_sender_emoji)
                    palabras_df = palabras_df[['date', 'emoji', 'sender', 'palabra', 'definicion']]
                    palabras_df.columns = ['Fecha', '', 'Remitente', 'Palabra', 'Definición']

                    st.dataframe(
                        palabras_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            '': st.column_config.Column(width='small'),
                            'Palabra': st.column_config.Column(width='medium'),
                            'Definición': st.column_config.Column(width='large')
                        }
                    )

                    csv = palabras_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar Palabras (CSV)",
                        data=csv,
                        file_name="palabras_del_dia.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("No se encontraron 'palabra del día' en el período seleccionado 😢")

            # ==================== ESTADÍSTICAS ADICIONALES ====================
            st.divider()
            st.header("📈 Estadísticas Adicionales")

            tab_a1, tab_a2, tab_a3 = st.tabs([
                "👥 Remitentes Más Activos",
                "⏰ Actividad por Hora",
                "🔥 Mapa de Calor"
            ])

            with tab_a1:
                top_senders = df_filtered['sender'].value_counts().reset_index()
                top_senders.columns = ['Remitente', 'Mensajes']
                top_senders['Emoji'] = top_senders['Remitente'].apply(get_sender_emoji)
                top_senders['Color'] = top_senders['Remitente'].apply(get_sender_color)

                fig = px.bar(
                    top_senders,
                    x='Mensajes',
                    y='Remitente',
                    orientation='h',
                    color='Remitente',
                    color_discrete_map={r: c for r, c in zip(top_senders['Remitente'], top_senders['Color'])},
                    text='Mensajes',
                    title='🍌🍊 ¿Quién es más hablador?',
                    height=350
                )
                fig.update_traces(
                    textposition='outside',
                    textfont_size=14,
                    marker_line_width=2,
                    marker_line_color='white'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Poppins', size=13),
                    title_font_size=16,
                    title_font_color=COLORS['primary'],
                    showlegend=False,
                    yaxis_title='',
                    margin=dict(t=60, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab_a2:
                hourly = df_filtered.groupby('hour').size().reset_index(name='Mensajes')

                fig = px.bar(
                    hourly,
                    x='hour',
                    y='Mensajes',
                    color='Mensajes',
                    color_continuous_scale='Peach',
                    title='⏰ ¿A qué hora hablan más?',
                    height=350
                )
                fig.update_traces(
                    marker_line_width=1,
                    marker_line_color='white'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Poppins', size=13),
                    title_font_size=16,
                    title_font_color=COLORS['primary'],
                    xaxis_title='Hora del día',
                    yaxis_title='Mensajes',
                    coloraxis_showscale=False,
                    margin=dict(t=60, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab_a3:
                fig = plot_heatmap_by_hour(df_filtered)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos suficientes para el mapa de calor")

            # ==================== RESUMEN DE NUESTRO AMOR ====================
            st.divider()
            st.header("💕 Resumen de Nuestro Amor")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                prom_amor = len(love_expr['te_quiero']) + len(love_expr['te_amo']) + len(love_expr['me_encantas'])
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 32px;">💞</div>
                    <div class="metric-value">{prom_amor}</div>
                    <div class="metric-label">Expresiones de Amor</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                dias_activos = len(df_filtered['date'].dt.date.unique())
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 32px;">📅</div>
                    <div class="metric-value">{dias_activos}</div>
                    <div class="metric-label">Días Conversando</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                promedio_msgs = len(df_filtered) / dias_activos if dias_activos > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 32px;">💬</div>
                    <div class="metric-value">{promedio_msgs:.1f}</div>
                    <div class="metric-label">Mensajes por Día</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 32px;">📖</div>
                    <div class="metric-value">{len(palabras_dia)}</div>
                    <div class="metric-label">Palabras del Día</div>
                </div>
                """, unsafe_allow_html=True)

            # Mensaje final romántico
            st.markdown("""
            <div style="text-align: center; padding: 30px; margin-top: 20px; background: linear-gradient(135deg, #FFE5E5 0%, #FFF0F5 100%); border-radius: 20px; border: 2px solid #FFB6C1;">
                <p style="font-size: 24px; color: #FF6B6B; font-weight: 700; margin: 0;">
                    🍌 + 🍊 = 💕
                </p>
                <p style="font-size: 16px; color: #666; margin-top: 10px; font-style: italic;">
                    "El amor no se mide en mensajes, pero cada uno cuenta una historia."
                </p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:
    # Pantalla de bienvenida
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <p style="font-size: 64px; margin-bottom: 20px;">💌</p>
        <h2 style="color: #FF6B6B;">Bienvenidos al Analizador de Amor</h2>
        <p style="color: #888; font-size: 16px; max-width: 500px; margin: 0 auto;">
            Carga tu chat de WhatsApp para descubrir cuántas veces se han dicho 
            <b>Te Quiero</b>, <b>Te Amo</b> y explorar todas sus palabras del día juntos.
        </p>
        <p style="margin-top: 30px; font-size: 40px;">🍌 💕 🍊</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ Ver formato esperado del chat"):
        st.code("""[6/8/2025, 6:20:34 am] Ana: Hola Juanjo
[6/8/2025, 6:28:43 am] Juan José: Hola Ana! Te quiero ❤️
[10/8/2026, 8:53:02 pm] Ana: La palabra del día que me dio Claude es petricor, que es el olor que desprende la tierra seca cuando llueve :)
""")
