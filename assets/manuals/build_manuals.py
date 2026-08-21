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
  body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a2e; line-height: 1.55; font-size: 11.5pt; }
  header { border-bottom: 3px solid #2563eb; padding-bottom: 10px; margin-bottom: 4px; break-inside: avoid; page-break-inside: avoid; }
  header .name {
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 9pt; color: #6b7280; letter-spacing: 0.04em; text-transform: uppercase;
  }
  h1 { font-size: 22pt; margin-top: 4px; }
  .subtitle { color: #6b7280; font-size: 12pt; margin-top: 2px; }
  .badge {
    display: inline-block; font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 8pt; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    padding: 2px 9px; border-radius: 999px; border: 1px solid #d1d5db; color: #6b7280; margin-top: 6px;
  }
  .stack { font-family: -apple-system, 'Segoe UI', system-ui, sans-serif; font-size: 9pt; color: #6b7280; margin-top: 8px; }
  h2 {
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 10pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
    color: #2563eb; margin-top: 22px; margin-bottom: 8px;
    border-bottom: 1px solid #d1d5db; padding-bottom: 4px;
  }
  p { margin-bottom: 8px; }
  ul { margin: 6px 0 10px 20px; }
  li { margin-bottom: 4px; }
  .flow { display: grid; gap: 10px; margin-top: 6px; }
  .flow figure { border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; break-inside: avoid; page-break-inside: avoid; }
  .flow img { width: 100%; display: block; }
  .flow figcaption {
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 8pt; color: #6b7280; padding: 5px 8px; border-top: 1px solid #d1d5db; background: #fafafa;
  }
  .flow figcaption strong { color: #1a1a2e; }
  .services {
    background: #f5f7fa; border-left: 3px solid #e8640a; padding: 10px 14px; border-radius: 0 6px 6px 0;
    break-inside: avoid; page-break-inside: avoid;
  }
  .services li::marker { color: #e8640a; }
  .noshots { font-style: italic; color: #6b7280; font-size: 10pt; margin-top: 4px; }
  footer {
    margin-top: 26px; padding-top: 10px; border-top: 1px solid #d1d5db;
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 8.5pt; color: #6b7280; display: flex; justify-content: space-between;
    break-inside: avoid; page-break-inside: avoid;
  }
"""

PAGE = """<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>{title}</title><style>{style}</style></head>
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

  {flow_section}

  <h2>{services_heading}</h2>
  <div class="services"><ul>{services}</ul></div>

  <footer><span>neupavertjm.github.io</span><span>neupavertjm@gmail.com</span></footer>
</body>
</html>
"""


def render_flow(images, cols):
    if not images:
        return (
            "<h2>Estado actual</h2>"
            '<p class="noshots">Este proyecto está en una fase temprana y aún no tiene capturas de interfaz '
            "que mostrar — el apartado de «Qué hace» de arriba describe su funcionamiento previsto.</p>"
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
          services, services_heading="Servicios que puedo ofrecer con esto"):
    que_hace_html = "\n".join(f"<p>{p}</p>" for p in que_hace_paragraphs)
    services_html = "\n".join(f"<li>{s}</li>" for s in services)
    html = PAGE.format(
        title=title,
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
    badge="Prototipo",
    stack="Python · Transformers · PyMuPDF · 100% local",
    que_hace_paragraphs=[
        "Recibe un PDF escaneado y decide, página a página, si ya contiene texto digital o si necesita reconocimiento óptico de caracteres. El resultado es un documento con el mismo contenido, pero con todo el texto ya buscable, copiable y exportable.",
        'Cada página reconocida queda marcada internamente con su número de origen, de forma que cualquier búsqueda o cita posterior sobre ese texto apunta siempre al lugar exacto del documento original — esto es lo que permite, por ejemplo, que una herramienta de consulta documental (ver RagDesk) pueda citar «página 14» con total fiabilidad.',
        "Cuando el sistema no puede leer un fragmento con suficiente confianza, lo señala explícitamente en vez de rellenarlo con una suposición — una decisión deliberada para no introducir errores silenciosos en un documento que después alguien va a dar por bueno.",
    ],
    images=[
        ("ocr-antes.png", "PDF escaneado de partida", "Punto de partida", "un PDF escaneado, sin texto digital."),
        ("ocr-progreso.png", "Digitalización en curso", "Procesamiento", "cada página se analiza y digitaliza en local."),
        ("ocr-resultado.png", "Texto buscable resultante", "Resultado", "el texto queda buscable y verificable página a página."),
        ("ocr-exportar.png", "Exportación a Word", "Exportación", "el documento final se exporta ya listo para usar."),
    ],
    cols=2,
    services=[
        "<strong>Digitalización de archivo histórico o administrativo</strong> — actas, expedientes, escrituras — para que quede buscable en texto.",
        "<strong>Migración puntual de papel a formato digital</strong> para despachos, gestorías y notarías.",
        "<strong>Primer paso de un flujo mayor de consulta documental</strong>: una vez digitalizado, el archivo puede alimentar un asistente de búsqueda en lenguaje natural (ver el manual de RagDesk).",
    ],
))

PROJECTS.append(build(
    slug="ragdesk",
    title="RagDesk (Asistente documental privado)",
    title_html='RagDesk <span style="color:#6b7280; font-weight:400;">(Asistente documental privado)</span>',
    subtitle="Responde preguntas en lenguaje natural sobre tus documentos, citando siempre la página exacta",
    badge="En desarrollo",
    stack="FastAPI · LlamaIndex · Ollama · local o en la nube",
    que_hace_paragraphs=[
        "Indexa una colección de documentos — los que salen del Digitalizador OCR, o cualquier PDF/Word ya digital — y responde preguntas sobre ellos en lenguaje natural, citando siempre la página exacta de origen de cada respuesta.",
        "Puede funcionar enteramente en el ordenador del cliente, sin que ningún documento salga de la máquina ni pase por servicios externos; también admite modelos en la nube como alternativa configurable cuando eso conviene más.",
        "La cita a página exacta no es un añadido cosmético: es lo que permite verificar cada respuesta contra el documento original en segundos, en vez de tener que confiar a ciegas en lo que dice el asistente.",
    ],
    images=[
        ("ragdesk-chat.png", "Pregunta en lenguaje natural", "Pregunta", "se escribe la consulta en lenguaje natural, sin sintaxis especial."),
        ("ragdesk-respuesta.png", "Respuesta con cita de página", "Respuesta citada", "la respuesta llega con la página exacta del documento de origen."),
        ("ragdesk-documentos.png", "Documentos ingestados", "Documentos indexados", "el archivo completo queda disponible para consulta."),
    ],
    cols=3,
    services=[
        "<strong>Asistente de consulta interna</strong> para despachos y gestorías sobre su propia normativa, contratos o expedientes.",
        "<strong>Puesta en marcha de un «buscador inteligente» privado</strong> sobre un archivo ya digitalizado.",
        "<strong>Mantenimiento y ampliación mensual</strong> conforme se añaden documentos nuevos a la colección.",
    ],
))

PROJECTS.append(build(
    slug="neualz",
    title="NeuAlz (Lector de PDF y base de conocimiento)",
    title_html='NeuAlz <span style="color:#6b7280; font-weight:400;">(Lector de PDF y base de conocimiento)</span>',
    subtitle="Convierte cada fragmento subrayado en una ficha de cita clasificada y buscable",
    badge="Prototipo",
    stack="Tauri · Rust · SQLite (FTS5)",
    que_hace_paragraphs=[
        "Al leer un PDF, seleccionar un fragmento lo convierte al instante en una ficha con autor, obra, año, tipo de fuente y un salto directo de vuelta a esa página exacta del documento.",
        "Las fichas se pueden buscar tanto por coincidencia de texto como por significado (búsqueda semántica), y se exportan a formatos de bibliografía estándar: APA, BibTeX, CSL-JSON.",
        "Existen variantes de la misma aplicación ajustadas a distintos tipos de fuente: académica (artículos, libros, tesis), legal (normas, sentencias) y empresarial (informes, procedimientos, contratos) — cada una con los campos de metadatos que tienen sentido para ese contexto.",
    ],
    images=[],
    cols=2,
    services=[
        "<strong>Organización de bibliografía extensa</strong> para investigadores, despachos o equipos que manejan muchas fuentes y necesitan volver a encontrarlas meses después.",
        "<strong>Adaptación de la ficha de cita a un dominio concreto</strong> (normativa legal, documentación interna de empresa) como variante específica de la aplicación.",
    ],
))

PROJECTS.append(build(
    slug="alzolab",
    title="AlzoLab",
    title_html="AlzoLab",
    subtitle="Laboratorio de lingüística de corpus en el navegador, sin escribir código",
    badge="En producción",
    stack="Python · Streamlit · spaCy",
    que_hace_paragraphs=[
        "Convierte un conjunto de textos en un corpus analizable sin escribir una línea de código: importación desde varias fuentes (web, Wikipedia, archivos propios), limpieza y normalización, análisis morfosintáctico con spaCy, extracción automática de términos relevantes (C-value) y concordancias KWIC para ver cada término en su contexto real de uso.",
        "Todo el flujo — desde subir los textos hasta exportar los resultados — ocurre dentro de la misma interfaz, pensado para alguien sin experiencia de programación.",
    ],
    images=[
        ("alzolab-importar.png", "Importación de textos", "Importación", "múltiples fuentes: web, Wikipedia o archivos propios."),
        ("alzolab-limpiar.png", "Limpieza y normalización", "Limpieza", "normalización del texto antes del análisis."),
        ("alzolab-analizar.png", "Análisis con spaCy", "Análisis", "análisis morfosintáctico automático."),
        ("alzolab-concordancia.png", "Concordancias KWIC", "Concordancias", "cada término en su contexto real de uso."),
    ],
    cols=2,
    services=[
        "<strong>Extracción de terminología especializada</strong> de un fondo documental (técnico, jurídico, médico) como base para un glosario o una memoria de traducción.",
        "<strong>Análisis de corpus a medida</strong> para traductores, editoriales o equipos de contenido que trabajan con grandes volúmenes de texto.",
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
        "<strong>Confección y mantenimiento de un glosario terminológico multilingüe</strong> para una empresa o equipo de traducción.",
        "<strong>Integración de ese glosario en las herramientas que ya se usan a diario</strong> (Word, Trados, memoQ) vía NeupaTerm Connect.",
    ],
))

PROJECTS.append(build(
    slug="neupalang",
    title="NeupaLang (Documentación lingüística)",
    title_html='NeupaLang <span style="color:#6b7280; font-weight:400;">(Documentación lingüística)</span>',
    subtitle="Plataforma para la documentación de lenguas minoritarias y en peligro",
    badge="En desarrollo",
    stack="FastAPI · React · Tauri",
    que_hace_paragraphs=[
        "Da soporte a la documentación de lenguas en riesgo de desaparición: importa datos desde herramientas ya usadas por lingüistas de campo (FLEx, ELAN, CLDF), aplica el estándar de glosa interlineal de Leipzig y deja constancia del consentimiento informado de cada hablante conforme a los principios CARE/FAIR.",
        "El editor funciona sin conexión, pensado para trabajo de campo en zonas sin acceso a internet fiable.",
    ],
    images=[],
    cols=2,
    services_heading="Para quién es útil",
    services=[
        "Equipos de documentación lingüística y proyectos de investigación sobre lenguas minoritarias que necesitan trabajar con datos de campo de forma rigurosa y éticamente responsable.",
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
