import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
from datetime import datetime
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
    'Ana': '#FFD700',
    'Juan José': '#FF8C00',
    'Juan Jo': '#FF8C00',
    'primary': '#FF6B6B',
    'secondary': '#FF9A8B',
    'accent': '#FFB6C1',
    'text': '#4A4A4A',
    'salmon_dark': '#FA8072',
    'rose': '#FF69B4',
    'nivel1': '#FF6B6B',
    'nivel2': '#FF69B4',
    'nivel3': '#FFA07A',
    'nivel4': '#FFD700',
}

EMOJIS = {'Ana': '🍌', 'Juan José': '🍊', 'Juan Jo': '🍊'}

NIVEL_LABELS = {
    'nivel1': '💘 Nivel 1 — Declaraciones directas',
    'nivel2': '💗 Nivel 2 — Vocativos románticos',
    'nivel3': '✨ Nivel 3 — Adjetivos directos',
    'nivel4': '💋 Nivel 4 — Gestos de afecto',
}

SUBTYPE_LABELS = {
    'te_quiero': 'Te quiero', 'te_amo': 'Te amo', 'me_encantas': 'Me encantas',
    'te_extrano': 'Te extraño', 'me_gustas': 'Me gustas', 'te_adoro': 'Te adoro',
    'mi_amor': 'Mi amor', 'mi_vida': 'Mi vida', 'corazon': 'Corazón',
    'hermosa': 'Hermosa', 'guapa': 'Guapa', 'preciosa': 'Preciosa',
    'linda': 'Linda', 'bonita': 'Bonita',
    'besos': 'Besos', 'abrazos': 'Abrazos',
}

EMOJI_CHARS = '❤️💕💖💗💓💝💘🥰😍🫶✨🥺😘'

# ==================== ESTILOS CSS ====================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    .main { background: linear-gradient(135deg, #FFF5F5 0%, #FFE8E8 100%); }
    .metric-card {
        background: linear-gradient(135deg, #FF9A8B 0%, #FF6B6B 100%);
        padding: 20px; border-radius: 16px; color: white; text-align: center;
        box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
    }
    .metric-value { font-size: 38px; font-weight: 700; margin: 8px 0; }
    .metric-label { font-size: 12px; opacity: 0.95; font-weight: 500; letter-spacing: 0.5px; }
    .love-card {
        background: linear-gradient(135deg, #FFB6C1 0%, #FF69B4 100%);
        padding: 18px; border-radius: 16px; color: white; text-align: center;
        box-shadow: 0 8px 32px rgba(255, 105, 180, 0.3);
    }
    .period-card {
        background: linear-gradient(135deg, #FFA07A 0%, #FA8072 100%);
        padding: 20px; border-radius: 16px; color: white; text-align: center;
        box-shadow: 0 8px 32px rgba(250, 128, 114, 0.3);
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #FFE5E5 0%, #FFD5D5 100%);
        border-radius: 12px 12px 0 0; padding: 10px 20px; font-weight: 600; color: #FF6B6B;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF9A8B 0%, #FF6B6B 100%) !important; color: white !important;
    }
    .love-quote {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%);
        border-left: 4px solid #FF69B4; padding: 14px 18px; border-radius: 0 12px 12px 0;
        margin: 8px 0; font-style: italic; color: #4A4A4A;
    }
    .word-card {
        background: white; border-radius: 16px; padding: 20px;
        box-shadow: 0 4px 20px rgba(255, 107, 107, 0.1); border: 1px solid #FFE5E5;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES AUXILIARES ====================

def get_sender_color(sender):
    s = sender.strip()
    if 'Ana' in s: return COLORS['Ana']
    elif 'Juan' in s: return COLORS['Juan José']
    return COLORS['primary']

def get_sender_emoji(sender):
    s = sender.strip()
    if 'Ana' in s: return EMOJIS['Ana']
    elif 'Juan' in s: return EMOJIS['Juan José']
    return '💕'

def collapse_elongation(text):
    """Colapsa letras repetidas 3+ veces a 1 sola: 'te quierooo' -> 'te quiero',
    'muuuucho' -> 'mucho'. Así detectamos variantes de escritura sin perder precisión."""
    return re.sub(r'(.)\1{2,}', r'\1', text)

# ==================== PARSING ====================

@st.cache_data
def parse_whatsapp_chat(text):
    lines = text.strip().split('\n')
    messages = []
    pattern = r'(?:\u200e)?\[(\d{1,2}/\d{1,2}/\d{4}),\s(\d{1,2}:\d{2}:\d{2}\s?(?:am|pm)?)\]\s([^:]+):\s?(.*)$'

    for raw_line in lines:
        line = raw_line.rstrip('\r\n')
        match = re.match(pattern, line)
        if match:
            date_str, time_str, sender, message = match.groups()
            if not message.strip():
                continue
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                time_clean = time_str.strip().lower()
                if 'am' in time_clean or 'pm' in time_clean:
                    time_obj = datetime.strptime(time_clean, '%I:%M:%S %p').time()
                else:
                    time_obj = datetime.strptime(time_clean, '%H:%M:%S').time()
                full_dt = datetime.combine(date_obj.date(), time_obj)
                messages.append({
                    'datetime': full_dt, 'date': date_obj, 'time': time_str,
                    'hour': time_obj.hour, 'sender': sender.strip(),
                    'message': message.strip(), 'date_only': date_obj.date(),
                    'month': date_obj.month, 'month_name': calendar.month_name[date_obj.month],
                    'year_month': date_obj.strftime('%Y-%m'),
                    'day_of_week': date_obj.strftime('%A'), 'day_name': date_obj.strftime('%a')
                })
            except Exception:
                pass
    return pd.DataFrame(messages)

# ==================== DETECCIÓN DE EXPRESIONES DE AMOR (4 NIVELES) ====================

def _is_vocative(msg, phrase):
    """Determina si 'phrase' aparece como vocativo (dirigido a la persona):
    al inicio del mensaje, después de coma/punto, o al final del mensaje.
    Excluye usos como 'en mi vida', 'de mi vida' (frases hechas, no vocativo)."""
    found = False
    detail = None
    for m in re.finditer(r'\b' + re.escape(phrase) + r'\b', msg):
        start, end = m.span()
        before_raw = msg[:start]
        before = before_raw.rstrip(' ,.!?¡¿')
        after = msg[end:].lstrip()

        prev_word = before.split()[-1] if before.split() else ''
        if prev_word in ('en', 'de', 'toda'):
            continue  # "en mi vida", "de mi vida", "toda mi vida" -> no es vocativo

        is_start = (start == 0) or before_raw.rstrip().endswith((',', '.')) or before == ''
        after_clean = re.sub(r'[\s\.,;:!?\-¡¿' + EMOJI_CHARS + r']', '', after)
        is_end = (after_clean == '')

        if is_start or is_end:
            found = True
            detail = msg[max(0, start - 15):min(len(msg), end + 15)]
            break
    return found, detail

def _is_negated(msg, start_idx):
    """Revisa si la frase está precedida por una negación cercana ('no te quiero', 'ya no te amo')."""
    before = msg[max(0, start_idx - 20):start_idx]
    return bool(re.search(r'\bno\s+(?:te\s+\w+\s+)?$', before))

@st.cache_data
def classify_love_expressions(df):
    """
    Clasifica expresiones de amor en 4 niveles, tal como se acordó:
    Nivel 1 - Declaraciones directas (te quiero, te amo, me encantas, te extraño, me gustas, te adoro)
              Se permiten variantes/alargamientos ('te quierooo', 'te quiero mucho hermosa', etc.)
    Nivel 2 - Vocativos románticos (mi amor, mi vida, corazón) SOLO cuando funcionan como vocativo
    Nivel 3 - Adjetivos directos (hermosa, guapa, preciosa, linda, bonita) SOLO cuando son vocativo
    Nivel 4 - Gestos de afecto (besos, abrazos)
    """
    results = {
        'nivel1': defaultdict(list),
        'nivel2': defaultdict(list),
        'nivel3': defaultdict(list),
        'nivel4': defaultdict(list),
    }

    nivel1_phrases = {
        'te_quiero': 'te quiero', 'te_amo': 'te amo', 'me_encantas': 'me encantas',
        'te_extrano': 'te extraño', 'me_gustas': 'me gustas', 'te_adoro': 'te adoro',
    }
    nivel2_phrases = {'mi_amor': 'mi amor', 'mi_vida': 'mi vida'}
    nivel3_phrases = {
        'hermosa': 'hermosa', 'guapa': 'guapa', 'preciosa': 'preciosa',
        'linda': 'linda', 'bonita': 'bonita',
    }

    for idx, row in df.iterrows():
        msg_collapsed = collapse_elongation(row['message'].lower())
        item_base = {
            'datetime': row['datetime'], 'date': row['date'], 'time': row['time'],
            'sender': row['sender'], 'message': row['message'], 'idx': idx,
        }

        # ---- Nivel 1 ----
        for key, phrase in nivel1_phrases.items():
            m = re.search(r'\b' + re.escape(phrase) + r'\b', msg_collapsed)
            if m and not _is_negated(msg_collapsed, m.start()):
                results['nivel1'][key].append(item_base)

        # ---- Nivel 2 ----
        for key, phrase in nivel2_phrases.items():
            if phrase in msg_collapsed:
                ok, detail = _is_vocative(msg_collapsed, phrase)
                if ok:
                    results['nivel2'][key].append({**item_base, 'contexto': detail})
        # corazón (con o sin tilde)
        if re.search(r'coraz[oó]n', msg_collapsed):
            m = re.search(r'coraz[oó]n', msg_collapsed)
            phrase_found = m.group()
            ok, detail = _is_vocative(msg_collapsed, phrase_found)
            if ok:
                results['nivel2']['corazon'].append({**item_base, 'contexto': detail})

        # ---- Nivel 3 ----
        for key, phrase in nivel3_phrases.items():
            if phrase in msg_collapsed:
                ok, detail = _is_vocative(msg_collapsed, phrase)
                if ok:
                    results['nivel3'][key].append({**item_base, 'contexto': detail})

        # ---- Nivel 4 ----
        if re.search(r'\bbes[oi]', msg_collapsed):
            results['nivel4']['besos'].append(item_base)
        if re.search(r'\babrazo', msg_collapsed):
            results['nivel4']['abrazos'].append(item_base)

    return results

@st.cache_data
def find_palabra_del_dia(df):
    palabras = []
    patterns = [
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+(\w+)[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
        r'(?:la\s+)?palabra\s+(?:del\s+)?día\s+(?:es|de)\s+["\']?(\w+)["\']?[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
        r'(?:mi|la)\s+palabra\s+(?:del\s+)?día\s+(?:es|fue)\s+(\w+)[^\w]*(?:,\s*)?que\s+es\s+([^\.]+)',
    ]
    for idx, row in df.iterrows():
        msg = row['message']
        for pattern in patterns:
            for match in re.finditer(pattern, msg, re.IGNORECASE):
                palabra = match.group(1)
                definicion = match.group(2).strip() if match.group(2) else "Sin definición"
                palabras.append({
                    'datetime': row['datetime'], 'date': row['date'], 'sender': row['sender'],
                    'palabra': palabra, 'definicion': definicion, 'mensaje_completo': row['message']
                })
    return palabras

def flatten_level(level_dict):
    """Convierte {subtype: [items]} en una sola lista, agregando 'subtype'."""
    flat = []
    for subtype, items in level_dict.items():
        for it in items:
            flat.append({**it, 'subtype': subtype})
    return flat

def count_by_sender(items):
    counter = defaultdict(int)
    for item in items:
        counter[item['sender']] += 1
    return dict(counter)

# ==================== GRÁFICAS ====================

def plot_by_sender(items, title, color_map):
    counts = count_by_sender(items)
    if not counts:
        return None
    df_plot = pd.DataFrame([{'Remitente': k, 'Cantidad': v} for k, v in counts.items()])
    fig = px.bar(df_plot, x='Remitente', y='Cantidad', color='Remitente',
                 color_discrete_map=color_map, text='Cantidad', title=title, height=380)
    fig.update_traces(textposition='outside', textfont_size=16, marker_line_width=2, marker_line_color='white')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       font=dict(family='Poppins', size=13, color=COLORS['text']),
                       title_font_size=17, title_font_color=COLORS['primary'],
                       showlegend=False, xaxis_title='', yaxis_title='Veces', margin=dict(t=55, b=40))
    return fig

def plot_by_subtype(items, title, color):
    counts = defaultdict(int)
    for it in items:
        counts[SUBTYPE_LABELS.get(it['subtype'], it['subtype'])] += 1
    if not counts:
        return None
    df_plot = pd.DataFrame([{'Tipo': k, 'Cantidad': v} for k, v in counts.items()]).sort_values('Cantidad', ascending=True)
    fig = px.bar(df_plot, x='Cantidad', y='Tipo', orientation='h', text='Cantidad', title=title, height=350)
    fig.update_traces(marker_color=color, textposition='outside', marker_line_width=1, marker_line_color='white')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       font=dict(family='Poppins', size=13), title_font_size=16,
                       title_font_color=COLORS['primary'], yaxis_title='', xaxis_title='',
                       margin=dict(t=55, b=30))
    return fig

def plot_timeline(items, title, color, granularity='D'):
    if not items:
        return None
    df_plot = pd.DataFrame(items)
    if granularity == 'H':
        df_plot['period'] = df_plot['datetime'].dt.floor('h')
        x_title, hover = 'Fecha y hora', '<b>%{x|%d/%m/%Y %H:00}</b><br>Expresiones: %{y}<extra></extra>'
    elif granularity == 'M':
        df_plot['period'] = df_plot['datetime'].dt.to_period('M').dt.to_timestamp()
        x_title, hover = 'Mes', '<b>%{x|%m/%Y}</b><br>Expresiones: %{y}<extra></extra>'
    else:
        df_plot['period'] = df_plot['datetime'].dt.floor('D')
        x_title, hover = 'Fecha', '<b>%{x|%d/%m/%Y}</b><br>Expresiones: %{y}<extra></extra>'

    timeline = df_plot.groupby('period').size().reset_index(name='count').sort_values('period')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline['period'], y=timeline['count'], mode='lines+markers',
        line=dict(color=color, width=3), marker=dict(size=8, color=color, line=dict(width=2, color='white')),
        fill='tozeroy', fillcolor='rgba(255, 107, 107, 0.15)', hovertemplate=hover
    ))
    fig.update_layout(title=title, height=380, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       font=dict(family='Poppins', size=13, color=COLORS['text']),
                       title_font_size=17, title_font_color=COLORS['primary'],
                       xaxis_title=x_title, yaxis_title='Expresiones', hovermode='x unified', margin=dict(t=55, b=40))
    return fig

def plot_monthly_trend(items, title, color):
    if not items:
        return None
    df_plot = pd.DataFrame(items)
    df_plot['year_month'] = df_plot['date'].dt.strftime('%Y-%m')
    monthly = df_plot.groupby('year_month').size().reset_index(name='count')
    monthly['fecha'] = pd.to_datetime(monthly['year_month'])
    monthly = monthly.sort_values('fecha')
    fig = px.bar(monthly, x='year_month', y='count', text='count', title=title, height=350)
    fig.update_traces(marker_color=color, textposition='outside', marker_line_width=2, marker_line_color='white')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       font=dict(family='Poppins', size=13), title_font_size=16,
                       title_font_color=COLORS['primary'], xaxis_title='Mes', yaxis_title='Cantidad',
                       showlegend=False, margin=dict(t=55, b=40))
    return fig

def plot_radar_levels(level_counts):
    categories = list(NIVEL_LABELS.values())
    values = [level_counts.get(k, 0) for k in NIVEL_LABELS.keys()]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]], fill='toself',
        fillcolor='rgba(255, 107, 107, 0.3)', line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=10, color=COLORS['primary'])
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(values) * 1.2 if max(values) else 1]),
                   bgcolor='rgba(255, 240, 240, 0.5)'),
        showlegend=False, title='💝 Radar de Amor por Nivel', title_font_size=18,
        title_font_color=COLORS['primary'], paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=12), height=450
    )
    return fig

def plot_heatmap_by_hour(df_filtered):
    if df_filtered.empty:
        return None
    pivot = df_filtered.pivot_table(index='day_of_week', columns='hour', values='message', aggfunc='count', fill_value=0)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])
    fig = px.imshow(pivot.values, x=[f'{h:02d}:00' for h in pivot.columns], y=day_labels[:len(pivot)],
                     color_continuous_scale='Peach', title='🔥 Mapa de calor: Actividad por día y hora', height=350)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       font=dict(family='Poppins', size=12), title_font_size=16, title_font_color=COLORS['primary'])
    return fig

# ==================== INTERFAZ PRINCIPAL ====================

st.title("💌 WhatsApp Chat Analyzer")
st.markdown("<p style='color: #FF6B6B; font-size: 18px; font-weight: 600;'>✨ Análisis de expresiones de amor y palabras del día ✨</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📤 Cargar Chat")
    uploaded_file = st.file_uploader("Sube tu chat de WhatsApp (.txt)", type='txt')
    st.divider()
    if uploaded_file:
        st.success("✅ Chat cargado correctamente")
    st.info("""
    **Sistema de 4 niveles de amor:**
    - 💘 **Nivel 1**: te quiero, te amo, me encantas, te extraño, me gustas, te adoro (con variantes: "te quierooo", "te quiero mucho", etc.)
    - 💗 **Nivel 2**: mi amor, mi vida, corazón (solo como vocativo)
    - ✨ **Nivel 3**: hermosa, guapa, preciosa, linda, bonita (dirigidos a la persona)
    - 💋 **Nivel 4**: besos, abrazos
    """)
    st.divider()
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #FFE5E5, #FFF0F0); border-radius: 12px;'>
        <p style='margin: 0; font-size: 24px;'>🍌 Ana + 🍊 Juan Jo</p>
    </div>
    """, unsafe_allow_html=True)

if uploaded_file:
    try:
        text_content = uploaded_file.read().decode('utf-8')
        df = parse_whatsapp_chat(text_content)

        if len(df) == 0:
            st.error("❌ No se pudo parsear el archivo. Verifica que sea un chat de WhatsApp válido.")
        else:
            # ==================== FILTROS ====================
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
                min_date, max_date = df['date'].min().date(), df['date'].max().date()
                date_range = st.date_input("📆 Rango de fechas", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            with col_f3:
                hour_range = st.slider("⏰ Rango de horas", min_value=0, max_value=23, value=(0, 23))
            with col_f4:
                days_map = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves',
                            'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
                available_days = [d for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] if d in df['day_of_week'].unique()]
                selected_days = st.multiselect("🗓️ Filtrar por día", options=available_days, default=available_days, format_func=lambda x: days_map.get(x, x))

            filter_mask = pd.Series(True, index=df.index)
            if selected_month:
                filter_mask &= (df['year_month'] == selected_month)
            if len(date_range) == 2:
                filter_mask &= (df['date_only'] >= date_range[0]) & (df['date_only'] <= date_range[1])
            filter_mask &= (df['hour'] >= hour_range[0]) & (df['hour'] <= hour_range[1])
            filter_mask &= df['day_of_week'].isin(selected_days) if selected_days else False

            df_filtered = df[filter_mask].copy()

            if df_filtered.empty:
                st.warning("⚠️ No hay mensajes con esos filtros. Ajusta mes, día, fecha u hora.")
                st.stop()

            love_expr = classify_love_expressions(df_filtered)
            palabras_dia = find_palabra_del_dia(df_filtered)

            nivel1 = flatten_level(love_expr['nivel1'])
            nivel2 = flatten_level(love_expr['nivel2'])
            nivel3 = flatten_level(love_expr['nivel3'])
            nivel4 = flatten_level(love_expr['nivel4'])
            level_counts = {'nivel1': len(nivel1), 'nivel2': len(nivel2), 'nivel3': len(nivel3), 'nivel4': len(nivel4)}
            color_map_senders = {s: get_sender_color(s) for s in df_filtered['sender'].unique()}

            # ==================== ESTADÍSTICAS GENERALES ====================
            st.divider()
            st.header("📊 Estadísticas Generales")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">📝 MENSAJES TOTALES</div>
                <div class="metric-value">{len(df_filtered):,}</div></div>""", unsafe_allow_html=True)
            with col2:
                fecha_inicio_dt, fecha_fin_dt = df_filtered['date'].min(), df_filtered['date'].max()
                dias_totales = (fecha_fin_dt - fecha_inicio_dt).days + 1
                st.markdown(f"""<div class="period-card"><div class="metric-label">📅 PERÍODO</div>
                <div class="metric-value" style="font-size: 20px; line-height: 1.25;">{fecha_inicio_dt.strftime('%d/%m/%Y')} → {fecha_fin_dt.strftime('%d/%m/%Y')}</div>
                <div style="font-size: 14px; margin-top: 10px; opacity: 0.95;">{dias_totales} días juntos 💕</div></div>""", unsafe_allow_html=True)
            with col3:
                remitentes = df_filtered['sender'].unique()
                remitentes_html = '<br>'.join([f"{get_sender_emoji(r)} {r}" for r in remitentes])
                st.markdown(f"""<div class="metric-card"><div class="metric-label">👥 REMITENTES</div>
                <div class="metric-value" style="font-size: 30px;">{len(remitentes)}</div>
                <div style="font-size: 13px; margin-top: 8px; opacity: 0.9;">{remitentes_html}</div></div>""", unsafe_allow_html=True)

            # ==================== EXPRESIONES DE AMOR — 4 NIVELES ====================
            st.divider()
            st.header("💕 Expresiones de Amor — Sistema de 4 Niveles")

            col1, col2, col3, col4 = st.columns(4)
            for col, key, emoji, items in zip(
                [col1, col2, col3, col4], ['nivel1', 'nivel2', 'nivel3', 'nivel4'],
                ['💘', '💗', '✨', '💋'], [nivel1, nivel2, nivel3, nivel4]
            ):
                with col:
                    st.markdown(f"""<div class="love-card"><div style="font-size: 26px;">{emoji}</div>
                    <div class="metric-value">{len(items)}</div>
                    <div class="metric-label">{NIVEL_LABELS[key].split('—')[1].strip()}</div></div>""", unsafe_allow_html=True)

            total_expr = sum(level_counts.values())
            st.markdown(f"<p style='text-align:center; margin-top:14px; font-size:16px; color:#666;'>Total de expresiones de amor detectadas: <b style='color:#FF6B6B;'>{total_expr}</b></p>", unsafe_allow_html=True)

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "💘 Nivel 1", "💗 Nivel 2", "✨ Nivel 3", "💋 Nivel 4", "📊 Comparativa"
            ])

            level_items_map = {'nivel1': (nivel1, COLORS['nivel1']), 'nivel2': (nivel2, COLORS['nivel2']),
                                'nivel3': (nivel3, COLORS['nivel3']), 'nivel4': (nivel4, COLORS['nivel4'])}

            for tab, key in zip([tab1, tab2, tab3, tab4], ['nivel1', 'nivel2', 'nivel3', 'nivel4']):
                items, color = level_items_map[key]
                with tab:
                    if not items:
                        st.info("No se encontraron expresiones de este nivel en el período seleccionado.")
                    else:
                        c1, c2 = st.columns(2)
                        with c1:
                            fig = plot_by_sender(items, f"¿Quién dice más? — {NIVEL_LABELS[key]}", color_map_senders)
                            if fig: st.plotly_chart(fig, use_container_width=True)
                        with c2:
                            fig = plot_by_subtype(items, "Desglose por tipo de expresión", color)
                            if fig: st.plotly_chart(fig, use_container_width=True)

                        gran_label = st.selectbox("🕒 Precisión del timeline", ["Día", "Semana", "Mes"], index=0, key=f"gran_{key}")
                        gran_map = {"Día": "D", "Semana": "D", "Mes": "M"}
                        fig = plot_timeline(items, f"Timeline — {NIVEL_LABELS[key]}", color, gran_map[gran_label])
                        if fig: st.plotly_chart(fig, use_container_width=True)

                        fig = plot_monthly_trend(items, f"Tendencia mensual — {NIVEL_LABELS[key]}", color)
                        if fig: st.plotly_chart(fig, use_container_width=True)

                        with st.expander(f"📋 Ver ejemplos recientes"):
                            for item in items[-8:]:
                                sub_label = SUBTYPE_LABELS.get(item['subtype'], item['subtype'])
                                st.markdown(f"""<div class="love-quote">
                                <p style="margin:0; font-weight:600; color:{color};">
                                {get_sender_emoji(item['sender'])} {item['sender']} — {item['date'].strftime('%d/%m/%Y')} · <i>{sub_label}</i></p>
                                <p style="margin:8px 0 0 0;">{item['message']}</p></div>""", unsafe_allow_html=True)

            with tab5:
                c1, c2 = st.columns([2, 1])
                with c1:
                    fig = plot_radar_levels(level_counts)
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.markdown("""<div style="padding: 20px; background: linear-gradient(135deg, #FFF0F5, #FFE4E1); border-radius: 16px; height: 100%;">
                    <h4 style="color: #FF6B6B; margin-bottom: 15px;">💝 Resumen por Nivel</h4>""", unsafe_allow_html=True)
                    resumen_html = "".join([f"<p>{emoji} {NIVEL_LABELS[k].split('—')[1].strip()}: <b>{level_counts[k]}</b></p>"
                                             for k, emoji in zip(['nivel1', 'nivel2', 'nivel3', 'nivel4'], ['💘', '💗', '✨', '💋'])])
                    st.markdown(f"""<p style="font-size: 30px; font-weight: 700; color: #FF6B6B; margin: 0;">{total_expr}</p>
                    <p style="color: #666; margin-bottom: 16px;">expresiones totales</p>{resumen_html}</div>""", unsafe_allow_html=True)

                # Comparación combinada por remitente entre niveles
                st.subheader("👥 Comparación por remitente entre niveles")
                rows = []
                for key in ['nivel1', 'nivel2', 'nivel3', 'nivel4']:
                    items, _ = level_items_map[key]
                    for sender, cnt in count_by_sender(items).items():
                        rows.append({'Nivel': NIVEL_LABELS[key].split('—')[1].strip(), 'Remitente': sender, 'Cantidad': cnt})
                if rows:
                    df_comp = pd.DataFrame(rows)
                    fig = px.bar(df_comp, x='Nivel', y='Cantidad', color='Remitente',
                                 color_discrete_map=color_map_senders, barmode='group', height=400)
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                       font=dict(family='Poppins', size=13), xaxis_title='', yaxis_title='Cantidad',
                                       legend=dict(orientation='h', yanchor='bottom', y=1.02))
                    st.plotly_chart(fig, use_container_width=True)

            # ==================== PALABRA DEL DÍA ====================
            st.divider()
            st.header("📚 Palabra del Día")

            if palabras_dia:
                st.metric("📖 Total de Palabras Encontradas", len(palabras_dia))
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("🍌🍊 Palabras por Remitente")
                    palabras_by_sender = count_by_sender(palabras_dia)
                    fig = go.Figure()
                    for sender, count in palabras_by_sender.items():
                        fig.add_trace(go.Bar(x=[sender], y=[count], name=f"{get_sender_emoji(sender)} {sender}",
                                              marker_color=get_sender_color(sender), text=[count],
                                              textposition='outside', textfont_size=16))
                    fig.update_layout(height=380, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                       font=dict(family='Poppins', size=13), showlegend=True,
                                       legend=dict(orientation='h', yanchor='bottom', y=1.02),
                                       xaxis_title='', yaxis_title='Palabras compartidas', margin=dict(t=80, b=40))
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.subheader("✨ Últimas Palabras del Día")
                    for palabra in palabras_dia[-5:]:
                        emoji, color = get_sender_emoji(palabra['sender']), get_sender_color(palabra['sender'])
                        st.markdown(f"""<div class="word-card" style="margin-bottom: 12px;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                        <span style="font-size:24px;">{emoji}</span>
                        <span style="font-size:20px; font-weight:700; color:{color};">{palabra['palabra'].upper()}</span>
                        <span style="color:#999; font-size:12px;">{palabra['date'].strftime('%d/%m/%Y')}</span></div>
                        <p style="margin:0; color:#555; font-style:italic;">✨ {palabra['definicion']}</p>
                        <p style="margin:6px 0 0 0; font-size:11px; color:#999;">Por: {palabra['sender']}</p></div>""", unsafe_allow_html=True)

                with st.expander("📖 Ver todas las Palabras del Día"):
                    palabras_df = pd.DataFrame(palabras_dia)[['date', 'sender', 'palabra', 'definicion']]
                    palabras_df['date'] = palabras_df['date'].dt.strftime('%d/%m/%Y')
                    palabras_df['emoji'] = palabras_df['sender'].apply(get_sender_emoji)
                    palabras_df = palabras_df[['date', 'emoji', 'sender', 'palabra', 'definicion']]
                    palabras_df.columns = ['Fecha', '', 'Remitente', 'Palabra', 'Definición']
                    st.dataframe(palabras_df, use_container_width=True, hide_index=True)
                    csv = palabras_df.to_csv(index=False)
                    st.download_button("📥 Descargar Palabras (CSV)", data=csv, file_name="palabras_del_dia.csv",
                                        mime="text/csv", use_container_width=True)
            else:
                st.info("No se encontraron 'palabra del día' en el período seleccionado 😢")

            # ==================== ESTADÍSTICAS ADICIONALES ====================
            st.divider()
            st.header("📈 Estadísticas Adicionales")
            tab_a1, tab_a2, tab_a3 = st.tabs(["👥 Remitentes Más Activos", "⏰ Actividad por Hora", "🔥 Mapa de Calor"])

            with tab_a1:
                top_senders = df_filtered['sender'].value_counts().reset_index()
                top_senders.columns = ['Remitente', 'Mensajes']
                fig = px.bar(top_senders, x='Mensajes', y='Remitente', orientation='h', color='Remitente',
                             color_discrete_map=color_map_senders, text='Mensajes',
                             title='🍌🍊 ¿Quién es más hablador?', height=350)
                fig.update_traces(textposition='outside', textfont_size=14, marker_line_width=2, marker_line_color='white')
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   font=dict(family='Poppins', size=13), title_font_size=16,
                                   title_font_color=COLORS['primary'], showlegend=False, yaxis_title='', margin=dict(t=60, b=40))
                st.plotly_chart(fig, use_container_width=True)

            with tab_a2:
                hourly = df_filtered.groupby('hour').size().reset_index(name='Mensajes')
                fig = px.bar(hourly, x='hour', y='Mensajes', color='Mensajes', color_continuous_scale='Peach',
                             title='⏰ ¿A qué hora hablan más?', height=350)
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   font=dict(family='Poppins', size=13), title_font_size=16,
                                   title_font_color=COLORS['primary'], xaxis_title='Hora del día', yaxis_title='Mensajes',
                                   coloraxis_showscale=False, margin=dict(t=60, b=40))
                st.plotly_chart(fig, use_container_width=True)

            with tab_a3:
                fig = plot_heatmap_by_hour(df_filtered)
                if fig: st.plotly_chart(fig, use_container_width=True)
                else: st.info("No hay datos suficientes para el mapa de calor")

            # ==================== RESUMEN FINAL ====================
            st.divider()
            st.header("💕 Resumen de Nuestro Amor")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""<div class="metric-card"><div style="font-size:32px;">💞</div>
                <div class="metric-value">{total_expr}</div><div class="metric-label">Expresiones de Amor</div></div>""", unsafe_allow_html=True)
            with col2:
                dias_activos = len(df_filtered['date'].dt.date.unique())
                st.markdown(f"""<div class="metric-card"><div style="font-size:32px;">📅</div>
                <div class="metric-value">{dias_activos}</div><div class="metric-label">Días Conversando</div></div>""", unsafe_allow_html=True)
            with col3:
                promedio_msgs = len(df_filtered) / dias_activos if dias_activos > 0 else 0
                st.markdown(f"""<div class="metric-card"><div style="font-size:32px;">💬</div>
                <div class="metric-value">{promedio_msgs:.1f}</div><div class="metric-label">Mensajes por Día</div></div>""", unsafe_allow_html=True)
            with col4:
                st.markdown(f"""<div class="metric-card"><div style="font-size:32px;">📖</div>
                <div class="metric-value">{len(palabras_dia)}</div><div class="metric-label">Palabras del Día</div></div>""", unsafe_allow_html=True)

            st.markdown("""<div style="text-align: center; padding: 30px; margin-top: 20px; background: linear-gradient(135deg, #FFE5E5 0%, #FFF0F5 100%); border-radius: 20px; border: 2px solid #FFB6C1;">
            <p style="font-size: 24px; color: #FF6B6B; font-weight: 700; margin: 0;">🍌 + 🍊 = 💕</p>
            <p style="font-size: 16px; color: #666; margin-top: 10px; font-style: italic;">"El amor no se mide en mensajes, pero cada uno cuenta una historia."</p></div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.markdown("""<div style="text-align: center; padding: 60px 20px;">
    <p style="font-size: 64px; margin-bottom: 20px;">💌</p>
    <h2 style="color: #FF6B6B;">Bienvenidos al Analizador de Amor</h2>
    <p style="color: #888; font-size: 16px; max-width: 500px; margin: 0 auto;">
    Carga tu chat de WhatsApp para descubrir cuántas veces se han dicho
    <b>Te Quiero</b>, <b>Te Amo</b> y sus variantes, además de explorar todas sus palabras del día juntos.</p>
    <p style="margin-top: 30px; font-size: 40px;">🍌 💕 🍊</p></div>""", unsafe_allow_html=True)

    with st.expander("ℹ️ Ver formato esperado del chat"):
        st.code("""[6/8/2025, 6:20:34 am] Ana: Hola Juanjo
[6/8/2025, 6:28:43 am] Juan José: Hola Ana! Te quiero muchoo ❤️
[10/8/2026, 8:53:02 pm] Ana: La palabra del día que me dio Claude es petricor, que es el olor que desprende la tierra seca cuando llueve :)
""")
