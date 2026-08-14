# 💌 WhatsApp Chat Analyzer - Palabras del Corazón

Herramienta interactiva en Streamlit para analizar tu chat de WhatsApp con Ana y extraer:
- Expresiones de amor ("Te quiero", "Te amo", "Me encantas")
- Todas las "Palabras del Día"
- Estadísticas y visualizaciones bonitas

---

## 🚀 Instalación Rápida

### Prerequisitos
- Python 3.8+
- pip

### Pasos

```bash
# 1. Instalar dependencias
pip install streamlit pandas matplotlib seaborn

# 2. Correr la app
streamlit run whatsapp_analyzer.py

# 3. Abre tu navegador en:
# http://localhost:8501
```

---

## 📥 Cómo Usar

### Exportar tu chat desde WhatsApp

**En celular (iOS o Android):**
1. Abre el chat con Ana
2. Toca el nombre en la parte superior
3. Busca "Exportar chat" 
4. Selecciona "Sin multimedia" (sin fotos/videos)
5. Guarda el archivo .txt

**Importante:** Elige "Sin multimedia" para que sea más pequeño y rápido de analizar.

### En la app:

1. Carga el archivo .txt en la sección "Cargar Chat"
2. La app parsea automáticamente el chat
3. Explora las secciones:
   - 💕 **Expresiones de Amor** - Conteos y timeline de "te quiero", "te amo", etc.
   - 📚 **Palabra del Día** - Lista completa con definiciones
   - 📈 **Estadísticas** - Actividad, horas, remitentes

---

## 🎯 Qué detecta la app

### Expresiones de Amor
- ✅ "Te quiero" (y variantes: te quieroo, te quier, etc.)
- ✅ "Te amo" (y variantes)
- ✅ "Me encantas" (y variantes)
- ✅ "Amor" (menciones generales)

### Palabra del Día
Busca patrones como:
```
"La palabra del día que me dio Claude es [PALABRA], que es [DEFINICIÓN]"
"Mi palabra del día es [PALABRA], que es [DEFINICIÓN]"
```

### Estadísticas
- Total de mensajes y período del chat
- Mensajes por remitente
- Actividad por hora
- Timeline de expresiones
- Distribución de "palabra del día"

---

## 📊 Funcionalidades

| Feature | Status | Descripción |
|---------|--------|-------------|
| Upload chat | ✅ | Carga archivo .txt de WhatsApp |
| Conteo "Te Quiero" | ✅ | Con breakdown por remitente |
| Conteo "Te Amo" | ✅ | Gráficos interactivos |
| Conteo "Me Encantas" | ✅ | Estadísticas |
| Palabra del Día | ✅ | Extrae palabra + definición |
| Timeline | ✅ | Muestra evolución en el tiempo |
| Descargar CSV | ✅ | Exporta palabras del día |
| Gráficos | ✅ | Matplotlib + Seaborn |

---

## 🔮 Mejoras Futuras (v2.0)

### Próximas Mejoras a Implementar:

1. **Análisis de Sentimientos**
   - Detectar emojis de amor (❤️, 🥰, 😍)
   - Análisis de palabras positivas/negativas

2. **NLP Avanzado**
   - Detectar frases románticas completas
   - Análisis de temas frecuentes

3. **Exportación**
   - Generar reporte PDF bonito con gráficos
   - Crear "Libro de Recuerdos" estilo

4. **Visualizaciones**
   - Nube de palabras de los "palabra del día"
   - Matriz de conversación por fecha
   - Heatmap de actividad

5. **Machine Learning (futuro)**
   - Predecir "Palabra del Día" que te gustaría
   - Análisis de patrones de conversación

6. **Integración**
   - Exportar a Notion o Google Drive
   - Sincronización automática

---

## 🐛 Troubleshooting

### Problema: "No se pudo parsear el archivo"
**Solución:** Asegúrate de:
- Exportar desde WhatsApp directamente
- Que sea un archivo .txt (no .csv o .doc)
- Que el chat esté completo

### Problema: No encuentra "Palabra del Día"
**Solución:** La app busca el patrón exacto:
```
"palabra del día que ... es [PALABRA], que es"
```
Si tu formato es diferente, te puedes pasar el mensaje y ajustamos el regex.

### Problema: Los gráficos se ven pixelados
**Solución:** Normal en Streamlit. Descarga como PNG o ajusta el zoom del navegador.

---

## 💡 Tips

- **Privacidad:** La app es local, nada sube a internet
- **Velocidad:** Funciona mejor con chats <500k mensajes
- **Actualizar:** Exporta nuevamente el chat para ver datos actualizados
- **Compartir:** Puedes hacer deploy en Hugging Face Spaces o Render (gratis)

---

## 📦 Requisitos

```
streamlit>=1.28.0
pandas>=1.5.0
matplotlib>=3.5.0
seaborn>=0.12.0
```

---

## 🚀 Deploy Gratis

Si quieres que cualquiera pueda usar la app sin instalación:

### Opción 1: Hugging Face Spaces
```bash
# 1. Crea repo en https://huggingface.co/new
# 2. Sube estos archivos:
#    - whatsapp_analyzer.py
#    - requirements.txt
# 3. En README.md pon:
# ---
# title: WhatsApp Chat Analyzer
# emoji: 💌
# colorFrom: purple
# colorTo: pink
# sdk: streamlit
# sdk_version: 1.28.0
# app_file: whatsapp_analyzer.py
# ---
```

### Opción 2: Render
```bash
# 1. Deploy directo desde GitHub
# 2. Selecciona "Streamlit" como runtime
# 3. ¡Listo!
```

---

## 📝 Changelog

### v1.0 (Actual)
- ✅ Upload de chats
- ✅ Análisis de expresiones de amor
- ✅ Extracción de palabra del día
- ✅ Gráficos y estadísticas
- ✅ Exportación CSV

### v1.1 (Próximo)
- 📝 Mejor detección de variantes
- 📝 Nube de palabras
- 📝 Exportación a PDF

---

## 💌 Créditos

Hecha con amor para ti y Ana 💕

Contacto: Si encontrás bugs o querés sugerencias, mándame un mensajito

---

**Última actualización:** Agosto 2026
