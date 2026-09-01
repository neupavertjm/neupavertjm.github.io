"""Genera los manuales PDF de cada proyecto a partir de una plantilla compartida.

Uso: python build_manuals.py
Requiere: pip install playwright && playwright install msedge (o usar el canal msedge del sistema)
No se referencia desde index.html — es una herramienta de mantenimiento interna.
"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
TEMPLATES = ROOT / "templates"
IMG = ROOT / "img"
TEMPLATES.mkdir(exist_ok=True)

STYLE = """
  @page { size: A4; margin: 20mm 18mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --ink: #1b1c1f; --body: #2c2d2e; --muted: #52534f; --dim: #86877f;
    --accent: #8a5c0e; --accent-ink: #fbf7ee; --accent2: #1c6f66;
    --bg: #f5f4ef; --rule: #dedcd4; --status-border: #e3d6bb;
  }
  body {
    font-family: 'IBM Plex Sans', -apple-system, 'Segoe UI', system-ui, sans-serif;
    color: var(--body); line-height: 1.55; font-size: 10.5pt; background: #ffffff;
  }
  header { border-bottom: 2px solid var(--rule); padding-bottom: 12px; margin-bottom: 6px; break-inside: avoid; page-break-inside: avoid; }
  header .name {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 8.5pt; color: var(--accent2); letter-spacing: 0.04em; text-transform: lowercase;
  }
  header .name::before { content: '// '; color: var(--dim); }
  h1 {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 21pt; font-weight: 600; color: var(--ink); margin-top: 6px; letter-spacing: -0.01em;
  }
  .subtitle { color: var(--muted); font-size: 11pt; margin-top: 4px; }
  .badge {
    display: inline-block; font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 7.5pt; font-weight: 700; text-transform: lowercase; letter-spacing: 0.03em;
    padding: 3px 10px; border-radius: 3px; border: 1px solid var(--status-border); color: var(--accent); margin-top: 8px;
  }
  .stack { font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-size: 8.5pt; color: var(--accent2); margin-top: 10px; }
  h2 {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 9pt; font-weight: 600; text-transform: lowercase; letter-spacing: 0.05em;
    color: var(--accent2); margin-top: 22px; margin-bottom: 9px;
  }
  h2::before { content: '// '; color: var(--dim); }
  p { margin-bottom: 8px; }
  ul { margin: 6px 0 10px 20px; }
  li { margin-bottom: 4px; }
  .flow { display: grid; gap: 10px; margin-top: 6px; }
  .flow figure { border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; break-inside: avoid; page-break-inside: avoid; }
  .flow img { width: 100%; display: block; }
  .flow figcaption {
    font-family: 'IBM Plex Sans', -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 7.5pt; color: var(--muted); padding: 5px 8px; border-top: 1px solid var(--rule); background: var(--bg);
  }
  .flow figcaption strong { color: var(--ink); }
  .services {
    background: var(--bg); border-left: 3px solid var(--accent2); padding: 10px 14px; border-radius: 0 6px 6px 0;
    break-inside: avoid; page-break-inside: avoid;
  }
  .services li::marker { color: var(--accent2); }
  .noshots { font-style: italic; color: var(--muted); font-size: 9.5pt; margin-top: 4px; }
  footer {
    margin-top: 26px; padding-top: 10px; border-top: 1px solid var(--rule);
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 8pt; color: var(--dim); display: flex; justify-content: space-between;
    break-inside: avoid; page-break-inside: avoid;
  }
"""

PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{style}</style>
</head>
<body>
  <header>
    <div class="name">Juan Manuel Neupavert Alzola</div>
    <h1>{title_html}</h1>
    <div class="subtitle">{subtitle}</div>
    <div class="badge">{badge}</div>
  </header>
  <div class="stack">{stack}</div>

  <h2>Qué hace</h2>
  {que_hace}

  {extra_sections}

  {flow_section}

  <h2>{services_heading}</h2>
  <div class="services"><ul>{services}</ul></div>

  <footer><span>neupavert.com</span><span>juanmanuel@neupavert.com</span></footer>
</body>
</html>
"""


def render_flow(images, cols):
    if not images:
        return (
            "<h2>Estado actual</h2>"
            '<p class="noshots">Este documento todavía no incluye capturas de interfaz '
            "— el apartado de «Qué hace» de arriba describe su funcionamiento.</p>"
        )
    figs = "\n".join(
        f'<figure><img src="../img/{src}" alt="{alt}">'
        f"<figcaption><strong>{n}. {label}</strong> — {desc}</figcaption></figure>"
        for n, (src, alt, label, desc) in enumerate(images, start=1)
    )
    return (
        "<h2>Cómo se ve en uso</h2>"
        f'<div class="flow" style="grid-template-columns: repeat({cols}, 1fr);">{figs}</div>'
    )


def build(slug, title_html, title, subtitle, badge, stack, que_hace_paragraphs, images, cols,
          services, services_heading="Servicios que puedo ofrecer con esto", extra_sections=None):
    que_hace_html = "\n".join(f"<p>{p}</p>" for p in que_hace_paragraphs)
    services_html = "\n".join(f"<li>{s}</li>" for s in services)
    extra_sections = extra_sections or []
    extra_html = "\n".join(
        f"<h2>{heading}</h2>\n" + "\n".join(f"<p>{p}</p>" for p in paragraphs)
        for heading, paragraphs in extra_sections
    )
    html = PAGE.format(
        title=title,
        extra_sections=extra_html,
        style=STYLE,
        title_html=title_html,
        subtitle=subtitle,
        badge=badge,
        stack=stack,
        que_hace=que_hace_html,
        flow_section=render_flow(images, cols),
        services_heading=services_heading,
        services=services_html,
    )
    out_html = TEMPLATES / f"{slug}.html"
    out_html.write_text(html, encoding="utf-8")
    return out_html


PROJECTS = []

PROJECTS.append(build(
    slug="ocr-digitalizador",
    title="Digitalizador documental (OCR local)",
    title_html='Digitalizador documental <span style="color:#6b7280; font-weight:400;">(OCR local)</span>',
    subtitle="Convierte documentos escaneados en texto buscable y editable — sin conexión a internet",
    badge="En desarrollo",
    stack="Python · Transformers · PyMuPDF · 100% local",
    que_hace_paragraphs=[
        "Recibe un PDF escaneado o una foto y decide, página a página, si ya contiene texto digital o si necesita reconocimiento óptico de caracteres. Tiene dos modos: uno rápido para el uso normal y otro más lento y preciso, pensado para páginas con letra pequeña o mala calidad de escaneo.",
        "Cuando el sistema no puede leer un fragmento con suficiente confianza, lo marca explícitamente como «página ilegible» en vez de rellenarlo con una suposición; si el texto reconocido tiene más palabras raras de lo normal, avisa para que se revise antes de darlo por bueno — una decisión deliberada para no introducir errores silenciosos en un documento que después alguien va a dar por bueno.",
        "El resultado no es solo un texto suelto: junto al PDF original se genera una copia con el escaneo intacto visualmente pero con una capa de texto invisible superpuesta, así que se puede buscar y seleccionar texto en cualquier lector de PDF normal, sin depender del programa.",
        "Para un archivo completo, el modo Biblioteca procesa una carpeta entera y da el estado de cada documento — correcto, parcial o fallido — para revisar solo lo que de verdad necesita atención en vez de repasar documento por documento.",
    ],
    images=[
        ("ocr-antes.png", "PDF escaneado de partida", "Punto de partida", "un PDF escaneado, sin texto digital."),
        ("ocr-progreso.png", "Digitalización en curso", "Procesamiento", "cada página se analiza y digitaliza en local."),
        ("ocr-resultado.png", "Texto buscable resultante", "Resultado", "el texto queda buscable y verificable página a página."),
        ("ocr-exportar.png", "Exportación a Word", "Exportación", "el documento final se exporta ya listo para usar."),
    ],
    cols=2,
    services=[
        "<strong>Digitalización de archivo histórico o administrativo</strong> — actas, expedientes, escrituras — con entrega tanto del texto extraído como del PDF original con capa de búsqueda añadida, sin alterar el escaneo.",
        "<strong>Migración puntual de papel a formato digital</strong> para despachos, gestorías y notarías, con un informe de qué documentos han quedado perfectos y cuáles necesitan revisión manual.",
        "<strong>Primer paso de un flujo mayor de consulta documental</strong>: el texto extraído puede alimentar directamente un asistente de búsqueda en lenguaje natural (ver el manual de RagDesk).",
    ],
    extra_sections=[
        ("Detalle técnico", [
            "Cada documento se procesa página a página: primero se comprueba si ya tiene una capa de texto digital (PDF nativo); si no, se aplica reconocimiento óptico con un modelo de visión-lenguaje (Transformers), no un OCR clásico basado solo en patrones de píxeles — lo que ayuda con letra manuscrita o escaneos de peor calidad.",
            "El modo «Base» sacrifica velocidad por precisión para esos casos difíciles. La salida se guarda en dos formatos independientes por documento: un <code>.md</code> con el texto extraído (pensado para alimentar después un índice de búsqueda) y un PDF idéntico visualmente al original pero con una capa de texto invisible superpuesta — el escaneo en sí nunca se modifica.",
        ]),
        ("Ejemplo concreto", [
            "Un lote de 50 expedientes escaneados de una gestoría: el proceso por lotes los digitaliza uno a uno, marcando cada documento como correcto, parcial (algunas páginas sí, otras no — típico en documentos con sellos o manuscritos encima del texto) o fallido. Es habitual que 2-3 de esos 50 salgan como «parcial» por mala calidad de escaneo; no es señal de que algo esté mal, es la realidad de digitalizar papel antiguo.",
        ]),
        ("Cómo empezamos", [
            "Necesito uno o varios documentos de muestra (PDF escaneado o foto) representativos de tu archivo, para probar el resultado real antes de comprometerte a nada. Si el archivo es grande, se hace primero una prueba de alcance reducido sobre una carpeta pequeña.",
            "Recibes el texto extraído y el PDF con capa de búsqueda de cada documento; los originales en papel, si me los facilitas físicamente, se devuelven en el mismo estado en que llegaron.",
        ]),
    ],
))

PROJECTS.append(build(
    slug="ragdesk",
    title="RagDesk (Asistente documental privado)",
    title_html='RagDesk <span style="color:#6b7280; font-weight:400;">(Asistente documental privado)</span>',
    subtitle="Responde preguntas en lenguaje natural sobre tus documentos, citando siempre la página exacta",
    badge="En desarrollo",
    stack="FastAPI · LlamaIndex · Ollama o proveedor en la nube · app de escritorio (Tauri)",
    que_hace_paragraphs=[
        "Indexa una colección de documentos — los que salen del Digitalizador OCR, o cualquier PDF/Word ya digital — y responde preguntas sobre ellos en lenguaje natural, citando siempre la página exacta de origen de cada respuesta.",
        "Puede funcionar enteramente en el ordenador del cliente, sin que ningún documento salga de la máquina ni pase por servicios externos; también admite modelos en la nube como alternativa configurable cuando eso conviene más.",
        "La cita a página exacta no es un añadido cosmético: es lo que permite verificar cada respuesta contra el documento original en segundos, en vez de tener que confiar a ciegas en lo que dice el asistente.",
        "Además de la interfaz web hay una aplicación de escritorio: la versión que se entrega al cliente es de solo consulta — pregunta, ve la cita, abre el documento de origen —, sin opción de subir o borrar nada por error. Gestionar qué documentos hay indexados es un modo aparte, solo para la fase de preparación del archivo.",
    ],
    images=[
        ("ragdesk-chat.png", "Pregunta en lenguaje natural", "Pregunta", "se escribe la consulta en lenguaje natural, sin sintaxis especial."),
        ("ragdesk-respuesta.png", "Respuesta con cita de página", "Respuesta citada", "la respuesta llega con la página exacta del documento de origen."),
        ("ragdesk-documentos.png", "Documentos ingestados", "Documentos indexados", "el archivo completo queda disponible para consulta."),
    ],
    cols=3,
    services=[
        "<strong>Asistente de consulta interna</strong> para despachos y gestorías sobre su propia normativa, contratos o expedientes.",
        "<strong>Prueba de alcance reducido</strong> sobre unos pocos documentos tuyos, antes de decidir si conviene ampliarlo a todo el archivo.",
        "<strong>Mantenimiento y ampliación mensual</strong> conforme se añaden documentos nuevos a la colección.",
    ],
    extra_sections=[
        ("Detalle técnico", [
            "Divide cada documento en fragmentos de tamaño ajustable, con solapamiento entre fragmentos para no perder contexto en los cortes, y los convierte en vectores semánticos (embeddings) guardados en una base vectorial local. Al preguntar, primero recupera los fragmentos más relevantes por similitud semántica — no por palabra clave exacta — y se los pasa al modelo de lenguaje para que redacte la respuesta citando de dónde salió cada fragmento.",
            "El modelo de lenguaje es intercambiable: local (Ollama) o en la nube (Anthropic, OpenAI), con los embeddings quedándose en local incluso cuando el modelo de lenguaje es en la nube, si así conviene por coste o velocidad.",
        ]),
        ("Ejemplo concreto", [
            "Un despacho con 300 contratos de arrendamiento ya digitalizados: en vez de buscar «cláusula de renovación» y revisar a mano cada resultado, se pregunta directamente «¿qué contratos tienen renovación automática a más de un año?» y la respuesta llega con la lista de contratos y la página exacta de cada cláusula citada, lista para verificar en segundos.",
        ]),
        ("Cómo empezamos", [
            "Hace falta que el archivo ya esté digitalizado (si no, se combina primero con el Digitalizador OCR). Empezamos con una prueba de alcance reducido sobre unos pocos documentos tuyos — 2 a 5 bastan — para que veas el resultado real antes de decidir si conviene ampliarlo a todo el archivo.",
            "La entrega puede ser la app de escritorio (modo de solo consulta) o acceso a la interfaz web, según lo que encaje mejor con tu equipo.",
        ]),
    ],
))

PROJECTS.append(build(
    slug="clientworkspace",
    title="ClientWorkspace (Puesto de mando documental)",
    title_html='ClientWorkspace <span style="color:#6b7280; font-weight:400;">(Puesto de mando documental)</span>',
    subtitle="Orquesta el OCR y RagDesk en un único flujo por cliente y proyecto, sin mezclar nunca sus documentos",
    badge="Prototipo",
    stack="FastAPI · React/Vite · SQLite (FTS5) · orquesta procesos existentes",
    que_hace_paragraphs=[
        "Organiza el trabajo documental de varios clientes a la vez sin que sus archivos, bases de datos o índices se mezclen nunca entre sí: cada cliente y cada proyecto tiene su propia carpeta aislada, con su propia base de datos SQLite.",
        "Al importar documentos calcula el hash de cada archivo para detectar duplicados exactos antes de procesarlos dos veces, y deja los originales intactos — todo el procesamiento posterior trabaja sobre copias.",
        "El OCR y la extracción de metadatos (fechas, referencias, con un nivel de confianza explícito) se ejecutan como trabajos en segundo plano con seguimiento de progreso, y cada documento procesado queda automáticamente indexado para búsqueda de texto completo.",
        "Para consulta documental privada, puede dar de alta una instancia de RagDesk propia y aislada para cada cliente — el índice de cada proyecto vive dentro de su propia carpeta, nunca compartido entre clientes.",
    ],
    images=[
        ("clientworkspace-clientes.png", "Panel de clientes", "Clientes", "cada cliente con sus proyectos, sin mezclar datos entre ellos."),
        ("clientworkspace-proyecto.png", "Inventario de un proyecto", "Inventario", "estado de OCR, duplicados detectados e instancia RagDesk del cliente."),
        ("clientworkspace-busqueda.png", "Búsqueda de texto completo", "Búsqueda", "resultados con el fragmento resaltado dentro del documento."),
        ("clientworkspace-foco.png", "Modo de sesión enfocada", "Modo foco", "tarea actual, pendientes de revisión y cronómetro de la sesión."),
    ],
    cols=2,
    services=[
        "<strong>Puesto de mando para gestionar varios clientes de digitalización o consulta documental a la vez</strong>, sin depender de carpetas sueltas ni scripts manuales.",
        "<strong>Aislamiento garantizado entre clientes</strong>: útil cuando la confidencialidad entre expedientes o cuentas es un requisito, no solo una preferencia.",
    ],
))

PROJECTS.append(build(
    slug="neualz",
    title="NeuAlz (Lector de PDF y base de conocimiento)",
    title_html='NeuAlz <span style="color:#6b7280; font-weight:400;">(Lector de PDF y base de conocimiento)</span>',
    subtitle="Lee, resalta y organiza tus PDF en una biblioteca de citas — todo en local",
    badge="En desarrollo",
    stack="Tauri v2 · Rust · React + TypeScript · pdf.js · búsqueda semántica opcional vía Ollama",
    que_hace_paragraphs=[
        "Al seleccionar un fragmento de un PDF se puede resaltar (8 colores) con una nota opcional, o dejar una nota independiente sin resaltar nada. Cada resaltado queda vinculado a una ficha de cita clasificada, buscable por coincidencia de texto y, si se activa un modelo local (Ollama), también por significado.",
        "El PDF original no se modifica nunca sin confirmación explícita: el programa guarda antes una copia intacta, y toda la información — resaltados, notas, biblioteca de citas — vive en local, sin depender de ningún servicio en la nube.",
        "Existen tres variantes compiladas del mismo programa, cada una mostrando solo los campos de cita que tienen sentido para su contexto: académica (artículo, libro, capítulo, tesis), legal (norma, sentencia, vigencia) y empresarial (informe, procedimiento, manual, contrato) — se entrega la que corresponda, sin selector ni mezcla entre ellas.",
        "Por ahora no incorpora OCR ni anotaciones PDF nativas (/Annots) para interoperar con otros lectores — el resaltado se incrusta como capa visual propia sobre el PDF, no como anotación estándar; si hace falta esa interoperabilidad, es una ampliación pendiente, no algo ya resuelto.",
    ],
    images=[],
    cols=2,
    services=[
        "<strong>Organización de bibliografía o jurisprudencia extensa</strong> para investigadores, despachos o equipos que manejan muchas fuentes y necesitan volver a encontrarlas meses después.",
        "<strong>Entrega en la variante de tu sector</strong> — académica, legal o empresarial — cada una con los campos de cita que tienen sentido para ese contexto, sin coste de desarrollo adicional al ya compartir el mismo código base.",
    ],
    extra_sections=[
        ("Detalle técnico", [
            "Cada resaltado y nota se guarda en un archivo auxiliar junto al PDF (<code>&lt;nombre&gt;.pdf.neualz.json</code>), con escritura atómica — nunca puede quedar el archivo a medio escribir aunque el programa se cierre mal — y detección de si el PDF cambió desde la última vez que se guardaron las anotaciones (mediante hash SHA-256), para avisar si los resaltados podrían haberse desalineado.",
            "La biblioteca de citas vive en una base de datos SQLite local separada, con copia de seguridad automática cada vez que se añade o edita una cita. La única acción que modifica el PDF original pide confirmación explícita y siempre guarda antes una copia intacta.",
        ]),
        ("Ejemplo concreto", [
            "Un despacho de abogados que acumula sentencias y normativa en PDF y necesita volver a encontrar «esa sentencia que hablaba de tal cosa» meses después. Con la variante legal, cada resaltado queda vinculado a una ficha con el tipo de fuente (norma o sentencia), artículo/considerando y vigencia — buscable por texto o por significado, con salto directo a la página exacta del PDF.",
        ]),
        ("Cómo empezamos", [
            "Se entrega como instalador de Windows (.exe) de la variante que corresponda a tu sector — académica, legal o empresarial —, sin necesidad de cuenta ni conexión a internet para el uso normal. Requiere Windows 10/11 de 64 bits y 8 GB de RAM (16 GB si se activa la búsqueda semántica). Todo funciona en local desde el primer minuto.",
        ]),
    ],
))

PROJECTS.append(build(
    slug="alzolab",
    title="AlzoLab",
    title_html="AlzoLab",
    subtitle="Laboratorio de lingüística de corpus en el navegador, sin escribir código",
    badge="En producción",
    stack="FastAPI · React + Vite · spaCy · Docker",
    que_hace_paragraphs=[
        "Convierte un conjunto de textos en un corpus analizable sin escribir una línea de código: importación desde varias fuentes (web, Wikipedia, archivos propios), limpieza y normalización, análisis morfosintáctico con spaCy, extracción automática de términos relevantes y concordancias KWIC para ver cada término en su contexto real de uso. Funciona en español e inglés — un único selector cambia tanto el idioma de la interfaz como el modelo de spaCy usado en el análisis.",
        "La extracción terminológica usa el algoritmo C-value (Frantzi, Ananiadou y Mima, 2000), un método estadístico-lingüístico estándar en la literatura de extracción terminológica, no una heurística improvisada.",
        "Todo el flujo — desde subir los textos hasta exportar los resultados — ocurre dentro de la misma interfaz, pensado para alguien sin experiencia de programación. El código es abierto (MIT) y está en GitHub, con tests automáticos en cada cambio.",
    ],
    images=[
        ("alzolab-importar.png", "Importación de textos", "Importación", "múltiples fuentes: web, Wikipedia o archivos propios."),
        ("alzolab-limpiar.png", "Limpieza y normalización", "Limpieza", "normalización del texto antes del análisis."),
        ("alzolab-analizar.png", "Análisis con spaCy", "Análisis", "análisis morfosintáctico automático."),
        ("alzolab-concordancia.png", "Concordancias KWIC", "Concordancias", "cada término en su contexto real de uso."),
    ],
    cols=2,
    services=[
        "<strong>Extracción de terminología especializada</strong> de un fondo documental (técnico, jurídico, médico) como base para un glosario o una memoria de traducción, en español o en inglés.",
        "<strong>Análisis de corpus a medida</strong> para traductores, editoriales o equipos de contenido que trabajan con grandes volúmenes de texto — importación desde web, Wikipedia o archivos propios incluida.",
        "<strong>Puesta en marcha de una instancia propia</strong> si necesitas mantener tu corpus separado del demostrador público.",
    ],
    extra_sections=[
        ("Detalle técnico", [
            "La lógica de análisis de corpus vive separada del framework web (<code>backend/app/core</code>), como funciones puras que reciben datos y devuelven estructuras — se pueden probar y reutilizar sin levantar ningún servidor. El contrato entre el frontend (React) y el backend (FastAPI) es JSON tipado con Pydantic, no strings sueltos que hay que re-interpretar.",
            "Todo el pipeline — importación con trafilatura/jusText/BeautifulSoup, limpieza con reglas regex protegidas contra ataques ReDoS, análisis con spaCy, extracción terminológica — corre dentro de un único contenedor Docker, lo que hace que la demo pública y una instancia privada para un cliente sean exactamente el mismo despliegue.",
        ]),
        ("Ejemplo concreto", [
            "Una editorial que quiere identificar la terminología propia de una colección de manuales técnicos antes de traducirlos: se importan los documentos, se limpian automáticamente, y la pestaña de Terminología devuelve una lista de candidatos rankeados por relevancia estadística — en minutos, no releyendo cientos de páginas a mano para anotar términos.",
        ]),
        ("Cómo empezamos", [
            "La demo pública ya está accesible sin instalar nada — es la forma más rápida de ver si encaja con lo que necesitas. Si el corpus tiene que quedar separado del demostrador público (por volumen o por confidencialidad), se despliega una instancia propia con el mismo contenedor Docker.",
        ]),
    ],
))

PROJECTS.append(build(
    slug="neupaterm",
    title="NeupaTerm (Plataforma terminológica)",
    title_html='NeupaTerm <span style="color:#6b7280; font-weight:400;">(Plataforma terminológica)</span>',
    subtitle="Gestión terminológica multilingüe, independiente del CAT, con acceso desde cualquier herramienta",
    badge="En desarrollo",
    stack="React/Vite · FastAPI · PostgreSQL · spaCy",
    que_hace_paragraphs=[
        "Centraliza la terminología de un equipo o proyecto en fichas bilingües estructuradas — no una hoja de cálculo — con categoría gramatical, contextos de uso y equivalencias por idioma, por pares de idiomas (ES · EN · PT · DE · IT · FR).",
        "Incluye extracción de términos candidatos mediante NLP, y NeupaTerm Connect permite consultar esa terminología directamente desde Word, Trados, memoQ o cualquier otra aplicación, sin salir a buscarla aparte.",
    ],
    images=[
        ("neupaterm-landing.png", "Página de acceso", "Acceso", "página de entrada a la plataforma."),
        ("neupaterm-dashboard.png", "Panel de inicio", "Panel", "vista general de los glosarios del usuario."),
        ("neupaterm-ficha.png", "Ficha terminológica", "Ficha", "metadatos completos de un término bilingüe."),
        ("neupaterm-connect.png", "Acceso por API", "Connect", "consulta de terminología desde herramientas externas."),
    ],
    cols=2,
    services=[
        "<strong>Confección y mantenimiento de un glosario terminológico multilingüe</strong> para una empresa o equipo de traducción, con fichas por par de idioma en vez de una hoja de cálculo compartida.",
        "<strong>Integración de ese glosario en las herramientas que ya se usan a diario</strong> (Word, Trados, memoQ) vía NeupaTerm Connect, sin salir a buscar el término aparte.",
        "<strong>Extracción inicial de candidatos terminológicos</strong> mediante NLP sobre tu propio corpus, como punto de partida en vez de vaciar el glosario desde cero.",
    ],
    extra_sections=[
        ("Detalle técnico", [
            "Cada ficha terminológica se guarda por par de idiomas (por ejemplo ES→EN es una ficha distinta de ES→PT), con categoría gramatical, contextos de uso reales y notas, en vez de una única entrada genérica multilingüe difícil de mantener. La extracción de candidatos usa spaCy sobre el corpus que subas.",
            "NeupaTerm Connect expone esa terminología como una consulta rápida integrada en Word, Trados o memoQ, para no tener que salir de la herramienta de traducción a buscar el término aparte.",
        ]),
        ("Ejemplo concreto", [
            "Un equipo de traducción de software en 4 idiomas que hasta ahora mantenía el glosario en una hoja de cálculo compartida, con términos duplicados y equivalencias inconsistentes entre traductores. Migrar ese glosario a fichas por par de idiomas, con contexto de uso real, evita que dos traductores usen dos términos distintos para el mismo concepto en el mismo proyecto.",
        ]),
        ("Cómo empezamos", [
            "La plataforma ya está accesible en línea — se puede solicitar acceso y probarla directamente. Para migrar un glosario ya existente (hoja de cálculo, TBX, TMX) se importa una vez y queda estructurado por pares de idioma desde el primer día.",
        ]),
    ],
))

PROJECTS.append(build(
    slug="neupalang",
    title="NeupaLang (Documentación lingüística)",
    title_html='NeupaLang <span style="color:#6b7280; font-weight:400;">(Documentación lingüística)</span>',
    subtitle="Plataforma para la documentación de lenguas minoritarias y en peligro",
    badge="En desarrollo",
    stack="Tauri (app offline) · FastAPI + PostgreSQL (web) · React",
    que_hace_paragraphs=[
        "Da soporte a la documentación de lenguas en riesgo de desaparición: modelo lexema → acepción → ejemplo glosado, corpus de textos anotados e informantes con consentimiento, con la app de escritorio como artefacto principal y la web como sincronización/escaparate.",
        "El consentimiento no es un añadido de cara a la galería: cada informante registra tipo de consentimiento, fecha, testigo, alcance de uso (académico, educativo, publicación…) y permisos separados para nombre, audio, imagen y uso comercial, con revocación registrada y generación de PDF de consentimiento — siguiendo los principios CARE y FAIR.",
        "Exporta a los formatos que ya usan los lingüistas de campo — LIFT (FLEx/WeSay), CLDF, ELAN (.eaf), glosa interlineal Leipzig, códigos ISO 639-3 — para que los datos no queden cautivos de esta herramienta.",
        "El léxico, el corpus y la exportación ya son funcionales, con la suite de pruebas del backend en verde; el editor de escritorio funciona sin conexión, pensado para trabajo de campo en zonas sin acceso a internet fiable.",
    ],
    images=[],
    cols=2,
    services_heading="Para quién es útil",
    services=[
        "Equipos de documentación lingüística y proyectos de investigación sobre lenguas minoritarias que necesitan trabajar con datos de campo de forma rigurosa y éticamente responsable, con interoperabilidad real hacia FLEx/ELAN en vez de un formato propio cerrado.",
    ],
    extra_sections=[
        ("Detalle técnico", [
            "El modelo de datos tiene cuatro niveles anidados — lengua, informante, lexema, acepción, ejemplo — cada uno con sus propios metadatos de sensibilidad y derechos (CARE), no un único campo de «notas» genérico.",
            "La app de escritorio (Tauri + SQLite local) es el artefacto principal: el dato vive en el dispositivo del investigador desde el primer momento, con la web como sincronización y escaparate, no como almacén primario. El backend tiene cerca de 590 pruebas automáticas en verde, cubriendo desde la exportación a los formatos estándar hasta el propio modelo de consentimiento.",
        ]),
        ("Ejemplo concreto", [
            "Un proyecto de documentación de una lengua indígena con trabajo de campo en una zona sin internet fiable: el investigador registra el lexema, su glosa interlineal (formato Leipzig) y el consentimiento del hablante — incluyendo si autoriza solo uso académico o también publicación — directamente en el dispositivo; los datos se sincronizan cuando vuelve a tener conexión, sin haber dependido de ella durante el trabajo de campo.",
        ]),
        ("Estado y disponibilidad", [
            "Es un proyecto de investigación a largo plazo, no un producto cerrado a la venta: si tu proyecto de documentación lingüística encaja con este enfoque, hablamos de qué fase está lista para tu caso concreto antes de comprometer nada.",
        ]),
    ],
))

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    for html_path in PROJECTS:
        pdf_path = ROOT / f"{html_path.stem}.pdf"
        page.goto(html_path.resolve().as_uri())
        page.pdf(path=str(pdf_path), format="A4", print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        print(f"{pdf_path.name}: {pdf_path.stat().st_size} bytes")
    browser.close()
