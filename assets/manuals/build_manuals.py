"""Genera los manuales PDF de cada proyecto a partir de una plantilla compartida.

Uso: python build_manuals.py
Requiere: pip install playwright && playwright install msedge (o usar el canal msedge del sistema)
No se referencia desde index.html — es una herramienta de mantenimiento interna.

Contenido a fondo, redactado a partir de los repos de cada programa. Las capturas
nuevas todavía no existen: se marcan como cajas de "captura pendiente" con la
descripción exacta de la toma que hace falta (ver `pending_shots` en cada build()).
"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
TEMPLATES = ROOT / "templates"
IMG = ROOT / "img"
TEMPLATES.mkdir(exist_ok=True)

STYLE = """
  @page { size: A4; margin: 18mm 17mm 16mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --ink: #1b1c1f; --body: #2c2d2e; --muted: #52534f; --dim: #86877f;
    --accent: #8a5c0e; --accent-ink: #fbf7ee; --accent2: #1c6f66;
    --bg: #f5f4ef; --rule: #dedcd4; --status-border: #e3d6bb;
  }
  body {
    font-family: 'IBM Plex Sans', -apple-system, 'Segoe UI', system-ui, sans-serif;
    color: var(--body); line-height: 1.55; font-size: 10.25pt; background: #ffffff;
  }
  header { border-bottom: 2px solid var(--rule); padding-bottom: 12px; margin-bottom: 4px; break-inside: avoid; page-break-inside: avoid; }
  header .name {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 8.5pt; color: var(--accent2); letter-spacing: 0.04em; text-transform: lowercase;
  }
  header .name::before { content: '// '; color: var(--dim); }
  h1 {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 20pt; font-weight: 600; color: var(--ink); margin-top: 6px; letter-spacing: -0.01em;
  }
  .subtitle { color: var(--muted); font-size: 10.75pt; margin-top: 4px; max-width: 46em; }
  .badge {
    display: inline-block; font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 7.5pt; font-weight: 700; text-transform: lowercase; letter-spacing: 0.03em;
    padding: 3px 10px; border-radius: 3px; border: 1px solid var(--status-border); color: var(--accent); margin-top: 8px;
  }
  .stack { font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-size: 8.25pt; color: var(--accent2); margin-top: 10px; }
  h2 {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
    font-size: 9pt; font-weight: 600; text-transform: lowercase; letter-spacing: 0.05em;
    color: var(--accent2); margin-top: 20px; margin-bottom: 8px;
    break-after: avoid; page-break-after: avoid;
  }
  h2::before { content: '// '; color: var(--dim); }
  h3 {
    font-size: 10pt; font-weight: 600; color: var(--ink); margin-top: 13px; margin-bottom: 4px;
    break-after: avoid; page-break-after: avoid;
  }
  p { margin-bottom: 7px; }
  .lead { font-size: 10.75pt; color: var(--muted); }
  ul, ol { margin: 5px 0 9px 18px; }
  li { margin-bottom: 3px; }
  li::marker { color: var(--accent2); }
  strong { color: var(--ink); }
  code {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-size: 8.5pt;
    background: var(--bg); border: 1px solid var(--rule); border-radius: 3px; padding: 0 3px;
  }
  .flow { display: grid; gap: 9px; margin-top: 6px; }
  .flow figure { border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; break-inside: avoid; page-break-inside: avoid; }
  .flow img { width: 100%; display: block; }
  .flow figcaption {
    font-family: 'IBM Plex Sans', -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 7.5pt; color: var(--muted); padding: 5px 8px; border-top: 1px solid var(--rule); background: var(--bg);
  }
  .flow figcaption strong { color: var(--ink); }
  .shots-pending { display: grid; gap: 8px; margin-top: 6px; }
  @media print { .shots-pending { grid-template-columns: 1fr 1fr; } }
  .ph {
    border: 1px dashed var(--accent2); border-radius: 6px; padding: 11px 13px; background: #fbfaf6;
    break-inside: avoid; page-break-inside: avoid;
  }
  .ph .pht {
    font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-size: 6.75pt; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent2); display: block; margin-bottom: 3px;
  }
  .ph strong { display: block; font-size: 9pt; color: var(--ink); margin-bottom: 2px; }
  .ph span.d { font-size: 8.25pt; color: var(--muted); line-height: 1.45; }
  .faq dt { font-weight: 600; color: var(--ink); font-size: 9.75pt; margin-top: 9px; }
  .faq dd { margin: 2px 0 0; color: var(--body); }
  .services {
    background: var(--bg); border-left: 3px solid var(--accent2); padding: 10px 14px; border-radius: 0 6px 6px 0;
    break-inside: avoid; page-break-inside: avoid;
  }
  .services ul { margin-left: 16px; }
  .noshots { font-style: italic; color: var(--muted); font-size: 9.5pt; margin-top: 4px; }
  footer {
    margin-top: 24px; padding-top: 10px; border-top: 1px solid var(--rule);
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

  <h2>El problema</h2>
  {problema}

  <h2>Qué hace</h2>
  {que_hace}

  {extra_sections}

  {flow_section}

  {faq_section}

  <h2>{services_heading}</h2>
  <div class="services"><ul>{services}</ul></div>

  <footer><span>neupavert.com</span><span>juanmanuel@neupavert.com</span></footer>
</body>
</html>
"""


def _body(items):
    """Cada elemento: si empieza por '<' se emite tal cual (ul, ol, h3, tabla);
    si no, se envuelve en <p>."""
    out = []
    for it in items:
        s = it.strip()
        out.append(s if s.startswith("<") else f"<p>{s}</p>")
    return "\n".join(out)


def render_flow(images, cols, pending):
    blocks = []
    if images:
        figs = "\n".join(
            f'<figure><img src="../img/{src}" alt="{alt}">'
            f"<figcaption><strong>{n}. {label}</strong> — {desc}</figcaption></figure>"
            for n, (src, alt, label, desc) in enumerate(images, start=1)
        )
        blocks.append(
            f'<div class="flow" style="grid-template-columns: repeat({cols}, 1fr);">{figs}</div>'
        )
    if pending:
        phs = "\n".join(
            f'<div class="ph"><span class="pht">captura pendiente</span>'
            f"<strong>{label}</strong><span class=\"d\">{desc}</span></div>"
            for label, desc in pending
        )
        blocks.append(f'<div class="shots-pending">{phs}</div>')
    if not blocks:
        return ""
    return "<h2>Cómo se ve en uso</h2>\n" + "\n".join(blocks)


def render_faq(faq):
    if not faq:
        return ""
    items = "\n".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in faq)
    return f'<h2>Preguntas frecuentes</h2>\n<dl class="faq">{items}</dl>'


def build(slug, title_html, title, subtitle, badge, stack,
          problema, que_hace_paragraphs, images, cols, services,
          services_heading="Servicios que puedo ofrecer con esto",
          extra_sections=None, faq=None, pending_shots=None):
    extra_sections = extra_sections or []
    extra_html = "\n".join(
        f"<h2>{heading}</h2>\n" + _body(paragraphs)
        for heading, paragraphs in extra_sections
    )
    html = PAGE.format(
        title=title,
        style=STYLE,
        title_html=title_html,
        subtitle=subtitle,
        badge=badge,
        stack=stack,
        problema=_body(problema),
        que_hace=_body(que_hace_paragraphs),
        extra_sections=extra_html,
        flow_section=render_flow(images, cols, pending_shots),
        faq_section=render_faq(faq),
        services_heading=services_heading,
        services="\n".join(f"<li>{s}</li>" for s in services),
    )
    out_html = TEMPLATES / f"{slug}.html"
    out_html.write_text(html, encoding="utf-8")
    return out_html


PROJECTS = []

# ───────────────────────────────────────────────────────────────────────────────
# 1. Digitalización documental (escáner + OCR local)
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="ocr-digitalizador",
    title="Digitalización documental (escáner + OCR local)",
    title_html='Digitalización documental <span style="color:#6b7280; font-weight:400;">(escáner + OCR local)</span>',
    subtitle="Del papel (o del PDF escaneado sin texto) a un archivo buscable, clasificado y con control de calidad — sin que los documentos salgan del equipo",
    badge="Servicio activo",
    stack="Escáner cenital CZUR · programa propio de digitalización · reconocimiento de texto 100% local · entrega en Markdown + PDF buscable",
    problema=[
        "Un archivo en papel, o una carpeta llena de PDF que en realidad son fotos de páginas, no se puede buscar, ni indexar, ni citar. Para encontrar un dato hay que abrir documento por documento. Cuando el volumen crece — cientos de expedientes, actas o contratos — eso deja de ser viable.",
        "La salida rápida sería subirlo todo a un servicio de OCR en la nube. Pero eso significa mandar documentación sensible a un tercero solo para convertirla, y en muchos casos (datos personales, expedientes, historiales) eso ni siquiera es una opción legalmente cómoda.",
        "Y hay un problema de fondo con el OCR automático: cuando el sistema no está seguro de lo que ha leído, la tentación es rellenar el hueco con una suposición. Un error silencioso en un documento que después alguien va a dar por bueno es peor que un hueco marcado como tal.",
    ],
    que_hace_paragraphs=[
        "Digitalizo tu archivo con un <strong>escáner cenital CZUR</strong> — la cámara va por encima, así que no hay que desencuadernar libros ni forzar el lomo, y el ritmo de captura es de segundos por página. Sobre las imágenes resultantes corre un <strong>programa propio de reconocimiento de texto que funciona enteramente en local</strong>, en mi equipo, sin conexión a ningún servicio externo.",
        "Antes de entregarte nada, el texto pasa por <strong>tres pasadas de corrección</strong>, de la más automática a la más manual:",
        "<ol>"
        "<li><strong>Limpieza determinista.</strong> Reglas que eliminan los artefactos típicos del OCR: guiones de final de línea que parten palabras, saltos de línea sobrantes, cabeceras y pies de página repetidos en cada hoja, espaciado irregular.</li>"
        "<li><strong>Corrector ortográfico con diccionario local.</strong> Sobre el texto ya limpio, marca las palabras improbables y propone corrección — a nivel de palabra, sin reinterpretar el sentido. El diccionario se amplía con la terminología propia de tu dominio para que no marque como error lo que es vocabulario técnico.</li>"
        "<li><strong>Revisión humana página a página.</strong> Reviso el texto reconocido con la imagen de la página al lado, corrijo lo que haga falta y marco cada página como revisada. Los fragmentos que la máquina no ha podido leer con confianza se dejan señalados explícitamente, nunca inventados.</li>"
        "</ol>",
        "El entregable por cada documento son <strong>dos archivos</strong>: el texto en formato Markdown (pensado para buscar, indexar o alimentar después un asistente de consulta) y un <strong>PDF buscable</strong> — tu escaneo, visualmente intacto, con una capa de texto invisible superpuesta, de modo que se puede buscar y seleccionar texto en cualquier lector de PDF normal.",
    ],
    extra_sections=[
        ("Cómo se trabaja un archivo entero", [
            "Para una carpeta grande, cada documento se procesa por separado y queda con un estado claro: <strong>correcto</strong> (todas las páginas reconocidas y revisadas), <strong>parcial</strong> (algunas páginas sí, otras marcadas para revisar — típico en documentos con sellos, firmas o anotaciones manuscritas sobre el texto) o <strong>fallido</strong> (calidad de escaneo insuficiente, se avisa antes de seguir).",
            "Eso te permite concentrar la revisión en lo que de verdad la necesita, en vez de repasar documento por documento a ciegas. En un lote real es normal que un pequeño porcentaje salga como «parcial»: no es señal de que algo esté mal, es la realidad de digitalizar papel antiguo o con mucha intervención manual encima.",
        ]),
        ("Dónde viven tus documentos", [
            "Todo el proceso ocurre en un equipo con el disco cifrado, en una carpeta exclusiva para tu organización, sin mezclarse con material de ningún otro cliente. Los documentos no se envían a servicios de inteligencia artificial en la nube salvo que lo autorices por escrito para una tarea concreta.",
            "Cumplido el plazo de conservación que acordemos, tus datos se eliminan de forma segura y recibes un certificado de qué se ha borrado y cuándo. Si me facilitas originales en papel, se devuelven en el mismo estado en que llegaron.",
        ]),
        ("Un caso concreto", [
            "Una gestoría con unos 50 expedientes en papel, cada uno de entre 10 y 40 páginas, mezcla de impresos, formularios rellenados a mano y correspondencia. Se capturan con el CZUR en una tarde, el reconocimiento y la limpieza corren en local durante la noche, y la revisión se centra en las ~8 páginas que el sistema ha marcado como dudosas (casi todas por firmas o sellos encima del texto).",
            "El resultado es una carpeta con los 50 expedientes en texto buscable y en PDF con capa de búsqueda, más un pequeño informe de qué documentos quedaron perfectos y cuáles conviene que alguien de la gestoría revise una segunda vez.",
        ]),
        ("Cómo empezamos", [
            "Necesito <strong>uno o varios documentos de muestra</strong> representativos de tu archivo (una foto o un PDF escaneado bastan) para hacerte una prueba real y que veas el resultado antes de comprometerte a nada.",
            "Si el archivo es grande, empezamos con una <strong>prueba de alcance reducido</strong> sobre una carpeta pequeña; a partir de ahí cerramos por escrito qué se entrega, en qué plazo y a qué precio sobre un alcance definido.",
        ]),
    ],
    images=[],
    cols=2,
    pending_shots=[
        ("Captura con el escáner CZUR", "El escáner cenital en funcionamiento sobre un documento encuadernado, mostrando que no hace falta forzar el lomo."),
        ("Punto de partida vs. resultado", "Un PDF escaneado sin capa de texto al lado del mismo documento ya buscable, para ver el antes y el después."),
        ("Revisión página a página", "Pantalla de revisión con el texto reconocido a la izquierda y la imagen de la página a la derecha, y el botón de «marcar como revisada»."),
        ("Estado de un lote", "Lista de documentos de una carpeta con su estado (correcto / parcial / fallido) y el número de páginas pendientes de revisar."),
        ("Fragmento marcado como ilegible", "Detalle del texto donde un fragmento que la máquina no pudo leer con confianza aparece señalado en vez de rellenado con una suposición."),
        ("Entrega final", "La carpeta de entrega con, por cada documento, su archivo Markdown y su PDF buscable."),
    ],
    faq=[
        ("¿Hay que desencuadernar los libros o expedientes cosidos?",
         "No. El escáner es cenital (la cámara va por encima), así que se digitaliza con el documento abierto, sin desmontarlo ni dañarlo."),
        ("¿Reconoce texto manuscrito?",
         "Depende de la letra y de la calidad. El texto mecanografiado o impreso se reconoce bien; el manuscrito, según el caso — y lo que no se pueda leer con confianza se marca como dudoso, no se inventa."),
        ("¿Necesita conexión a internet?",
         "No. Tanto la captura como el reconocimiento de texto funcionan enteramente en local."),
        ("¿Qué pasa con los originales en papel?",
         "Si me los facilitas físicamente, se devuelven en el mismo estado en que llegaron. También puedo trabajar solo con escaneos que me envíes tú por un canal seguro."),
        ("¿Esto sirve para montar después un buscador o un asistente de consulta?",
         "Sí — el texto en Markdown está pensado precisamente para eso. Es el primer paso natural antes de un sistema de consulta documental en lenguaje natural (ver el manual de RagDesk)."),
    ],
    services=[
        "<strong>Digitalización de archivo histórico o administrativo</strong> — actas, expedientes, escrituras, correspondencia — con entrega del texto extraído y del PDF original con capa de búsqueda añadida, sin alterar el escaneo.",
        "<strong>Migración puntual de papel a formato digital</strong> para gestorías, despachos y notarías, con un informe de qué documentos han quedado perfectos y cuáles necesitan una segunda revisión.",
        "<strong>Preparación del archivo para un sistema de consulta</strong>: el texto extraído alimenta directamente un asistente de búsqueda en lenguaje natural o un índice documental.",
    ],
))

# ───────────────────────────────────────────────────────────────────────────────
# 2. RagDesk
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="ragdesk",
    title="RagDesk (Asistente documental privado)",
    title_html='RagDesk <span style="color:#6b7280; font-weight:400;">(Asistente documental privado)</span>',
    subtitle="Responde preguntas en lenguaje natural sobre una colección de documentos, citando siempre la página exacta de origen — y diciendo «no lo sé» cuando la respuesta no está en el material",
    badge="Demo pública en vivo",
    stack="FastAPI · LlamaIndex · ChromaDB · embeddings multilingües en proceso · Ollama / OpenAI / Anthropic · app de escritorio (Tauri) o despliegue web multi-inquilino",
    problema=[
        "Buscar por palabra clave en cientos o miles de páginas falla en cuanto la respuesta está formulada de otra manera: si el documento dice «prórroga tácita» y tú buscas «renovación automática», no aparece. Y aunque aparezca, sigues teniendo que abrir cada resultado y leerlo.",
        "Un asistente genérico como ChatGPT o Claude responde con fluidez, pero mezcla lo que hay en tus documentos con su conocimiento general — y no puedes distinguir una cosa de la otra. Cuando la respuesta importa (un contrato, una norma, un expediente), confiar a ciegas no es aceptable.",
        "Y para muchas organizaciones, subir toda su documentación a un servicio de terceros para poder consultarla no es una opción.",
    ],
    que_hace_paragraphs=[
        "RagDesk indexa una colección de documentos — los que salen del proceso de digitalización, o cualquier PDF, Word, Markdown o texto ya digital — y responde preguntas sobre ellos en lenguaje natural. Cada respuesta viene con sus <strong>fuentes</strong>: el archivo y la página exactos de donde ha salido cada dato.",
        "Cuando el documento tiene su PDF buscable emparejado, la cita no es solo «página 14»: al desplegarla, RagDesk <strong>abre el PDF dentro de la propia aplicación, salta a esa página y dibuja un recuadro sobre el párrafo exacto</strong>. Verificar una respuesta pasa de ser un acto de fe a un vistazo de tres segundos. Es una capa visual al mostrarlo; el archivo original nunca se modifica.",
        "Tiene una <strong>salvaguarda contra respuestas inventadas</strong>: si ningún fragmento del corpus supera un umbral de relevancia, al modelo se le dice explícitamente que no hay contexto, y el asistente responde que la información no está en los documentos — en vez de contestar de memoria.",
        "Puede funcionar <strong>enteramente en el equipo del cliente</strong> (modelo de lenguaje local con Ollama, base de vectores local, embeddings en proceso), sin que ningún documento salga de la máquina; o usar un modelo en la nube (Anthropic, OpenAI) como alternativa configurable cuando conviene por coste o velocidad, manteniendo aun así los documentos y su índice en local.",
        "Se entrega de dos formas, según lo que encaje con tu equipo: como <strong>aplicación de escritorio de solo consulta</strong> (una ventana nativa — preguntar, ver la cita, abrir el documento — sin ninguna opción de subir o borrar por error), o como <strong>acceso web</strong> a un servicio alojado y multi-inquilino, para clientes sin hardware potente que solo quieren entrar por el navegador.",
    ],
    extra_sections=[
        ("Cómo funciona por dentro", [
            "Cada documento se divide en fragmentos de tamaño ajustable, con solapamiento entre fragmentos para no perder contexto en los cortes, y se convierten en <strong>vectores semánticos</strong> (embeddings) guardados en una base vectorial local. Al llegar una pregunta, se recuperan primero los fragmentos más parecidos <em>por significado</em> — no por coincidencia de palabras — y se le pasan al modelo de lenguaje para que redacte la respuesta citando de dónde salió cada dato.",
            "El modelo de embeddings por defecto es multilingüe (<code>paraphrase-multilingual-MiniLM</code>); el umbral de relevancia que activa el «no lo sé» está calibrado para ese modelo y se recalibra si se cambia. En el despliegue web hay además un <strong>reranker</strong> que reordena los fragmentos recuperados con un modelo más fino — mejora mucho las preguntas por un término concreto.",
            "El modelo de lenguaje es intercambiable sin tocar el resto: local (Ollama) o en la nube (Anthropic, OpenAI). Una regla de <em>grounding</em> fija —responder solo desde el contexto, nunca citar una fuente que no esté presente, admitir cuando algo no está— se añade a cada consulta y no la puede debilitar la configuración de cada cliente.",
        ]),
        ("Caché de preguntas verificadas", [
            "Para no volver a pagar una llamada al modelo por una pregunta que ya se respondió, RagDesk guarda pares de pregunta y respuesta verificados y los reutiliza cuando llega una pregunta <strong>semánticamente parecida</strong>.",
            "Antes de llamar al modelo, compara la pregunta con las guardadas. Si encuentra una muy cercana, <strong>no responde directamente</strong>: sugiere la respuesta guardada y pregunta «¿te refieres a esto?». Si dices que sí, la respuesta llega al instante y sin coste; si dices que no, se responde con normalidad. Esa confirmación es lo que hace segura la caché — equivocarse solo cuesta un «no».",
            "Hay un panel de revisión donde un especialista puede aprobar, rechazar o <strong>editar</strong> una respuesta guardada antes de darle validez. Para un cliente con expertos internos, se puede configurar que nada se sirva hasta que alguien lo apruebe.",
        ]),
        ("El despliegue web, en detalle", [
            "La versión alojada sirve a varios clientes desde un solo servicio. Cada cliente tiene sus propios usuarios y uno o más <strong>RAGs</strong> (cada RAG = un corpus consultable, con su propia «persona» y configuración). El aislamiento entre clientes está verificado: un usuario solo accede a los recursos de su organización.",
            "Tres niveles de acceso: <strong>administrador general</strong> (crea clientes, crea RAGs, sube los documentos), <strong>administrador de cliente</strong> (gestiona los usuarios de su organización) y <strong>miembro</strong> (solo hace preguntas). Subir y borrar documentos es siempre competencia del administrador general.",
            "Puedes probar este modo en vivo en <strong>ragdesk.neupavert.com</strong>.",
        ]),
        ("Un caso concreto", [
            "Un despacho con 300 contratos de arrendamiento ya digitalizados. En vez de buscar «cláusula de renovación» y revisar a mano cada resultado, se pregunta directamente: «¿qué contratos tienen renovación automática por un plazo superior a un año?». La respuesta llega con la lista de contratos y la página exacta de cada cláusula citada, cada una a un clic de verse resaltada en su PDF.",
        ]),
        ("Cómo empezamos", [
            "Se hace una <strong>prueba de alcance reducido</strong> sobre unos pocos documentos tuyos — con 2 a 5 basta — para que veas el resultado real antes de decidir si conviene ampliarlo a todo el archivo.",
            "Ahí decidimos dos cosas: si el modelo de lenguaje va <strong>en local</strong> (nada sale del equipo, necesita una máquina con algo de potencia) o <strong>en la nube</strong> (más rápido y barato de arrancar, con los documentos aun así en local); y si la entrega es la <strong>app de escritorio</strong> o el <strong>acceso web</strong>.",
            "Hace falta que el archivo esté ya digitalizado; si no lo está, se combina primero con el servicio de digitalización.",
        ]),
    ],
    images=[
        ("ragdesk-chat.png", "Pregunta en lenguaje natural", "Pregunta", "se escribe la consulta como a una persona, sin sintaxis especial."),
        ("ragdesk-respuesta.png", "Respuesta con cita de página", "Respuesta citada", "la respuesta llega con el archivo y la página exactos de origen."),
        ("ragdesk-documentos.png", "Documentos ingestados", "Documentos indexados", "el archivo completo, disponible para consulta y paginado."),
    ],
    cols=3,
    pending_shots=[
        ("Recuadro sobre el párrafo citado en el PDF", "El visor de PDF integrado abierto en la página citada, con un recuadro dibujado sobre el párrafo exacto del que sale la respuesta."),
        ("Respuesta «no lo sé»", "El asistente respondiendo que la información no está en los documentos, en vez de improvisar una respuesta."),
        ("Confirmación de la caché", "El aviso «ya hay una respuesta guardada para una pregunta parecida: …» con los botones Sí / No."),
        ("Consola del despliegue web", "La vista de administrador general de ragdesk.neupavert.com: lista de clientes, y por cliente sus usuarios y sus RAGs."),
    ],
    faq=[
        ("¿Puedo tener varios clientes con archivos distintos?",
         "En la app de escritorio, cada instalación tiene un único índice: para clientes distintos, instalaciones separadas. El despliegue web sí es multi-inquilino de serie."),
        ("¿Necesita internet?",
         "En la versión local, solo la primera vez, para descargar los modelos. Después funciona sin conexión. En la versión web, se entra por el navegador."),
        ("¿Se puede inventar una respuesta igualmente?",
         "El diseño lo evita con el umbral de relevancia, la regla de grounding y la cita obligatoria. Con un modelo local pequeño todavía puede fallar en algún caso; para producción se recomienda un modelo en la nube, que es mucho más fiable siguiendo esas reglas."),
        ("¿Mis documentos salen del equipo?",
         "En la versión local, no: ni los documentos ni el índice. Si se usa un modelo de lenguaje en la nube, solo viaja el fragmento de texto necesario para responder cada pregunta, nunca el archivo entero — y aun así es opcional."),
        ("¿Qué formatos admite?",
         "PDF, Word (.docx), Markdown y texto plano. Los PDF que vienen del proceso de digitalización llevan además la información de posición que permite el recuadro sobre el párrafo citado."),
    ],
    services=[
        "<strong>Asistente de consulta interna</strong> para despachos, gestorías y empresas sobre su propia normativa, contratos, manuales o expedientes — con cita a página verificable.",
        "<strong>Prueba de alcance reducido</strong> sobre unos pocos documentos tuyos, antes de decidir si conviene ampliarlo a todo el archivo.",
        "<strong>Elección de despliegue</strong>: 100% local en tu equipo, o acceso web alojado para equipos sin hardware potente.",
        "<strong>Mantenimiento y ampliación mensual</strong> conforme se añaden documentos nuevos a la colección, con revisión periódica de la caché de respuestas.",
    ],
))

# ───────────────────────────────────────────────────────────────────────────────
# 3. NeuAlz
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="neualz",
    title="NeuAlz (Lector de PDF y base de conocimiento)",
    title_html='NeuAlz <span style="color:#6b7280; font-weight:400;">(Lector de PDF y base de conocimiento)</span>',
    subtitle="Lee, resalta y organiza tus PDF en una biblioteca de citas clasificada y buscable, con salto directo a la página original — todo en local",
    badge="En desarrollo",
    stack="Tauri v2 · Rust · React 19 + TypeScript · pdf.js · pdf-lib · búsqueda semántica opcional vía Ollama · sidecar JSON junto al PDF",
    problema=[
        "Lees un artículo, un libro o una sentencia en PDF, resaltas los fragmentos que importan, quizá anotas algo al margen. Meses después necesitas «esa cita que hablaba de tal cosa» y no hay forma de encontrarla salvo reabrir documentos uno por uno.",
        "Los resaltados, además, quedan atrapados dentro del lector con el que los hiciste, sin una vista de conjunto y sin poder buscarlos como lo que son: una base de conocimiento personal.",
        "Y los lectores que sí prometen organizar tus fuentes suelen pedir que subas tus PDF a su nube y confíes en que sigan existiendo dentro de cinco años.",
    ],
    que_hace_paragraphs=[
        "NeuAlz es un <strong>visor de PDF de escritorio</strong> pensado para leer con comodidad y para no perder lo que subrayas. Al seleccionar un fragmento se puede resaltar en ocho colores —dibujados con mezcla de color como un rotulador real, con la intensidad ajustable y guardada entre sesiones— con una nota de texto opcional. También hay resaltado manual a mano alzada para páginas escaneadas sin texto seleccionable, y notas independientes que no necesitan resaltar nada.",
        "Cada resaltado queda vinculado a una <strong>ficha de cita clasificada</strong>, buscable por coincidencia de texto y —si activas un modelo local con Ollama— también por significado. Desde la ficha se salta directamente a la página exacta del PDF donde está el fragmento.",
        "Nada sale de tu equipo. Los resaltados, notas y la biblioteca de citas viven en local: cada PDF guarda su información en un <strong>archivo auxiliar junto a él</strong> (escritura atómica — nunca queda a medio escribir aunque el programa se cierre mal), y el programa detecta por huella digital si el PDF ha cambiado desde la última vez, para avisarte de que los resaltados podrían haberse desalineado. <strong>El PDF original no se modifica nunca sin que lo pidas explícitamente.</strong>",
        "Se exporta a Markdown, agrupado por página, para pegar en Obsidian o alimentar después un sistema de consulta documental. Y trae lo que se espera de un lector serio: miniaturas de página con carga perezosa (no revienta con libros largos), modo de lectura claro / sepia / nocturno, rotación de página con los resaltados recalculados para seguir alineados, búsqueda de texto (Ctrl+F) en todo el documento, y recuerdo de la última página y el zoom de cada archivo.",
    ],
    extra_sections=[
        ("Tres variantes, un solo código", [
            "Existen tres compilaciones del mismo programa, cada una mostrando solo los campos de cita que tienen sentido en su contexto:",
            "<ul>"
            "<li><strong>Académica</strong> — artículo, libro, capítulo, tesis; autoría, año, publicación, DOI.</li>"
            "<li><strong>Legal</strong> — tipo de fuente (norma o sentencia), artículo o considerando, y vigencia (una norma derogada no es intercambiable con su reemplazo).</li>"
            "<li><strong>Empresarial</strong> — informe, procedimiento, manual, contrato; referencia interna, fecha, responsable.</li>"
            "</ul>",
            "Se entrega la variante que corresponde a tu sector, sin selector ni mezcla entre ellas, y sin coste de desarrollo adicional al compartir todas el mismo código base.",
        ]),
        ("El menú «Guardar PDF», en detalle", [
            "El guardado está separado en tres acciones independientes, no en un botón que decide todo:",
            "<ul>"
            "<li><strong>PDF original (sin resaltados)</strong> — copia el archivo tal cual a <code>Original_&lt;archivo&gt;.pdf</code>. No es destructivo, no pide confirmación.</li>"
            "<li><strong>PDF con resaltados (sobrescribe este archivo)</strong> — incrusta los resaltados como rectángulos translúcidos y reemplaza el archivo abierto. Es la única acción destructiva: pide confirmación y siempre asegura antes la copia intacta del original.</li>"
            "<li><strong>PDF con resaltados — guardar como…</strong> — igual, pero a la ubicación que elijas; el archivo abierto no se toca.</li>"
            "</ul>",
        ]),
        ("Qué no hace (todavía)", [
            "Para ser honesto sobre el alcance actual: <strong>no incorpora OCR</strong> — cuando una página no tiene texto seleccionable, lo avisa, pero no la reconoce (para eso está el servicio de digitalización). No imprime. Y los resaltados que se incrustan en el PDF son <strong>rectángulos visuales</strong>, no anotaciones estándar <code>/Annots</code>, así que no se editan desde otros lectores. La búsqueda funciona a nivel de fragmento interno de pdf.js: una coincidencia que quede partida entre dos fragmentos contiguos puede no encontrarse.",
            "Cada una de esas cosas es una ampliación identificada, no código a medio terminar en el programa.",
        ]),
        ("Un caso concreto", [
            "Un despacho que acumula sentencias y normativa en PDF y necesita volver a encontrar «esa sentencia que hablaba de tal cosa» meses después. Con la variante legal, cada resaltado queda vinculado a una ficha con el tipo de fuente, el artículo o considerando y la vigencia — buscable por texto o por significado, con salto directo a la página exacta.",
        ]),
        ("Cómo empezamos", [
            "Se entrega como <strong>instalador de Windows</strong> (<code>.msi</code> y <code>-setup.exe</code>) de la variante que corresponda a tu sector, sin necesidad de cuenta ni de conexión a internet para el uso normal. Requiere Windows 10/11 de 64 bits (el componente WebView2 ya viene instalado en sistemas actualizados). La búsqueda semántica opcional necesita tener Ollama con un modelo local.",
            "Todo funciona en local desde el primer minuto; la biblioteca de citas se puede llevar de un equipo a otro copiando su base de datos.",
        ]),
    ],
    images=[],
    cols=2,
    pending_shots=[
        ("Lectura con resaltado", "Una página de PDF con varios resaltados de distintos colores y el menú flotante de selección (elegir color / + Nota)."),
        ("Ficha de cita", "El panel lateral con la ficha de una cita: el fragmento, su clasificación (variante legal: tipo de fuente, artículo, vigencia) y el botón de saltar a la página."),
        ("Biblioteca de citas buscable", "La vista de conjunto de todas las citas, con el buscador y el filtro por tipo, y el conmutador de búsqueda por texto / por significado."),
        ("Aviso de PDF modificado", "El aviso que aparece al reabrir un documento cuya huella ha cambiado desde que se guardaron las anotaciones."),
        ("Menú «Guardar PDF»", "El menú desplegable del header con las tres acciones de guardado separadas."),
        ("Exportación a Markdown", "Un fragmento del .md exportado, con las citas agrupadas por página."),
    ],
    faq=[
        ("¿Modifica mis PDF?",
         "Solo si lo pides explícitamente con «PDF con resaltados (sobrescribe)», y aun entonces guarda antes una copia intacta del original. El resto de acciones y las anotaciones del día a día nunca tocan el archivo."),
        ("¿Dónde se guardan los resaltados?",
         "En un archivo auxiliar (.json) junto a cada PDF, y la biblioteca de citas en una base de datos local separada. Todo en tu equipo, nada en la nube."),
        ("¿Puedo buscar por significado y no solo por palabras?",
         "Sí, si tienes Ollama con un modelo local instalado. Sin él, la búsqueda por texto exacto sigue funcionando."),
        ("¿Sirve para páginas escaneadas?",
         "Se pueden leer y marcar a mano alzada, pero NeuAlz no reconoce su texto. Si necesitas texto buscable a partir de un escaneo, eso es el servicio de digitalización."),
        ("¿Qué pasa si el programa se cierra de golpe?",
         "Las anotaciones viven en el archivo auxiliar, no en memoria, y se escriben de forma atómica. Además hay una pantalla de recuperación si algo falla al renderizar, sin perder nada."),
    ],
    services=[
        "<strong>Organización de bibliografía o jurisprudencia extensa</strong> para investigadores, despachos o equipos que manejan muchas fuentes y necesitan reencontrarlas meses después.",
        "<strong>Entrega en la variante de tu sector</strong> — académica, legal o empresarial — cada una con los campos de cita que tienen sentido para ese contexto.",
        "<strong>Puesta en marcha y traspaso de la biblioteca de citas</strong> entre equipos, y ajuste del diccionario y las clasificaciones a tu dominio.",
    ],
))

# ───────────────────────────────────────────────────────────────────────────────
# 4. ClientWorkspace
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="clientworkspace",
    title="ClientWorkspace (Puesto de mando documental)",
    title_html='ClientWorkspace <span style="color:#6b7280; font-weight:400;">(Puesto de mando documental)</span>',
    subtitle="Orquesta todo el flujo del papel a la consulta —captura, digitalización, corrección, búsqueda— por cliente y por proyecto, sin mezclar nunca sus documentos",
    badge="Prototipo — Fase 1 operativa",
    stack="FastAPI · React + Vite · SQLite (FTS5) · orquesta procesos existentes por subprocess · 100% local",
    problema=[
        "Llevar el trabajo documental de varios clientes a la vez — digitalización de uno, consulta de otro, corrección de un tercero — con carpetas sueltas y scripts que se lanzan a mano es frágil y lento. Y basta un despiste para que el archivo de un cliente acabe donde no debe.",
        "Cuando la confidencialidad entre expedientes o entre cuentas es un requisito y no solo una buena práctica, «tener cuidado» no es una garantía suficiente.",
        "Cada pieza del flujo (el escáner, el reconocimiento de texto, el asistente de consulta, el análisis de corpus) es una herramienta distinta, con sus dependencias y su forma de arrancar. Encadenarlas a mano en cada proyecto es tiempo perdido.",
    ],
    que_hace_paragraphs=[
        "ClientWorkspace es el <strong>puesto de mando local</strong> desde el que gestiono los servicios documentales de varios clientes a la vez. Cada cliente y cada proyecto tienen su <strong>propia carpeta aislada y su propia base de datos</strong>: los archivos, los índices y los metadatos de un cliente nunca se mezclan con los de otro. La carpeta de originales de cada proyecto es inmutable — todo el procesamiento posterior trabaja sobre copias.",
        "Al importar documentos calcula la huella digital de cada archivo para <strong>detectar duplicados exactos</strong> antes de procesarlos dos veces, y deja un inventario de qué hay en cada proyecto y en qué estado.",
        "Desde ahí orquesta el flujo completo, apoyándose en las herramientas que ya existen: <strong>captura</strong> con el escáner CZUR (vigilando su carpeta de salida e importando lo nuevo), <strong>reconocimiento de texto y corrección</strong> (limpieza automática, corrector con diccionario local, revisión humana página a página), <strong>consulta</strong> con una instancia de RagDesk propia y aislada por cliente, <strong>búsqueda de texto exacto</strong> sobre todo el proyecto con fragmento resaltado, <strong>extracción de metadatos</strong> (fecha, autor, número de expediente — de los metadatos del PDF, del nombre de archivo y de las primeras líneas, con un nivel de confianza según cuántas fuentes coinciden) y <strong>exportación</strong> del resultado a una carpeta local o a una unidad de red.",
        "Incluye además un <strong>modo de sesión enfocada</strong> a pantalla completa para el trabajo de revisión: la tarea actual, el contador de documentos pendientes y revisados, un cronómetro de la sesión y notas. Y actúa como lanzador de NeuAlz y AlzoLab sobre el proyecto activo, sin absorber su interfaz.",
    ],
    extra_sections=[
        ("Estado real del proyecto", [
            "Es importante ser preciso aquí. La <strong>Fase 1</strong> — el núcleo: alta de clientes y proyectos, sistema de archivos aislado, importación con deduplicación por huella e inventario — está <strong>implementada y probada</strong>, con la batería de pruebas del backend en verde.",
            "Las fases siguientes (mapeo de estados del reconocimiento de texto, corrección en tres pasadas, búsqueda de texto completo, instancia de RagDesk por cliente, modo foco, exportación a la nube) están <strong>diseñadas y en buena parte escritas</strong>, pero pendientes de verificación de principio a fin. Es un entorno de trabajo propio en construcción, no un producto cerrado.",
        ]),
        ("Cómo está montado", [
            "Un solo backend, un solo frontend. La navegación es un árbol <strong>cliente → proyecto → documento</strong>, no un formulario. Los procesos pesados (reconocimiento de texto con GPU, el motor de RAG con su modelo de lenguaje) corren como procesos aparte con su propio entorno de dependencias, invocados cuando hacen falta — nunca se fusionan sus librerías con las del puesto de mando.",
            "Todo funciona <strong>100% en local</strong>: el principio rector es que el dato no sale del equipo. Los clientes objetivo son gestorías, despachos y notarías, donde eso es la condición de partida.",
        ]),
        ("Un caso concreto", [
            "Alguien que ofrece digitalización y consulta documental como servicio a cinco despachos a la vez. En vez de cinco conjuntos de carpetas y cinco listas de tareas en un cuaderno, tiene un único panel: cada despacho con sus proyectos, el estado de digitalización de cada uno, los duplicados que se han detectado, y su instancia de RagDesk lista para que el despacho consulte su propio archivo — sin ningún punto en el que los documentos de un despacho puedan acabar mezclados con los de otro.",
        ]),
        ("Cómo encaja con un cliente", [
            "El cliente <strong>no recibe el puesto de mando</strong> — es mi herramienta de trabajo como proveedor. Lo que el cliente recibe es el entregable: sus documentos digitalizados (texto + PDF buscable), su instancia de RagDesk si ha contratado consulta, y el informe de control de calidad.",
            "El valor de ClientWorkspace para el cliente es indirecto pero real: la garantía de que su documentación se trabaja aislada, sobre copias, con los originales intactos y con un rastro claro de qué se ha hecho y cuándo.",
        ]),
    ],
    images=[
        ("clientworkspace-clientes.png", "Panel de clientes", "Clientes", "cada cliente con sus proyectos, sin mezclar datos entre ellos."),
        ("clientworkspace-proyecto.png", "Inventario de un proyecto", "Inventario", "estado de digitalización, duplicados detectados e instancia RagDesk del cliente."),
        ("clientworkspace-busqueda.png", "Búsqueda de texto completo", "Búsqueda", "resultados con el fragmento resaltado dentro del documento."),
        ("clientworkspace-foco.png", "Modo de sesión enfocada", "Modo foco", "tarea actual, pendientes de revisión y cronómetro de la sesión."),
    ],
    cols=2,
    pending_shots=[
        ("Árbol cliente → proyecto → documento", "La navegación lateral en árbol, con un cliente desplegado en sus proyectos y un proyecto en sus documentos."),
        ("Importación con deduplicación", "El diálogo de importación mostrando archivos nuevos aceptados y duplicados exactos descartados por huella."),
        ("Extracción de metadatos con confianza", "Un documento con sus metadatos extraídos (fecha, autor, nº de expediente) y el indicador de confianza de cada campo."),
    ],
    faq=[
        ("¿El cliente usa ClientWorkspace?",
         "No. Es el puesto de mando del proveedor. El cliente recibe el entregable digitalizado y, si procede, su instancia de RagDesk."),
        ("¿Cómo se garantiza que no se mezclan documentos de clientes distintos?",
         "Cada cliente y cada proyecto tienen carpeta y base de datos separadas por diseño; la carpeta de originales es inmutable y todo el proceso trabaja sobre copias."),
        ("¿Está terminado?",
         "El núcleo (Fase 1) sí y está probado. Las fases que orquestan reconocimiento de texto, consulta y exportación están escritas pero pendientes de verificación completa."),
        ("¿Funciona sin internet?",
         "Sí. Todo es local. La exportación a Drive/OneDrive es opcional y requiere credenciales; la exportación a carpeta local o unidad de red no."),
    ],
    services=[
        "<strong>Gestión de varios clientes de digitalización o consulta documental a la vez</strong>, sin depender de carpetas sueltas ni de scripts lanzados a mano.",
        "<strong>Aislamiento garantizado entre clientes</strong>: útil cuando la confidencialidad entre expedientes o cuentas es un requisito, no una preferencia.",
        "<strong>Trazabilidad del trabajo</strong>: qué documentos se han procesado, en qué estado están y qué se ha entregado.",
    ],
))

# ───────────────────────────────────────────────────────────────────────────────
# 5. AlzoLab
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="alzolab",
    title="AlzoLab",
    title_html="AlzoLab",
    subtitle="Laboratorio de lingüística de corpus en el navegador: del texto en bruto a términos, concordancias y métricas, sin escribir una línea de código",
    badge="En producción · demo pública",
    stack="FastAPI · React + Vite · spaCy (ES/EN) · trafilatura · jusText · Docker · código abierto (MIT)",
    problema=[
        "Construir un corpus para investigación lingüística o para un proyecto de NLP suele significar pegar scripts sueltos: uno para descargar páginas web, otro para limpiar el HTML, otro para etiquetar con spaCy, otro para volcar a CSV. Es repetitivo y poco reproducible.",
        "Para quien viene de la lingüística y no quiere montar una infraestructura nueva en cada experimento, esa barrera técnica se come el tiempo que debería ir al análisis.",
        "Y las herramientas consolidadas de lingüística de corpus (Sketch Engine y similares) son potentes pero pesadas, de pago y difíciles de desplegar en una instancia propia sobre un corpus confidencial.",
    ],
    que_hace_paragraphs=[
        "AlzoLab es una <strong>única aplicación web con el flujo completo guiado en pestañas</strong>, disponible en español e inglés — un mismo selector cambia el idioma de la interfaz y el modelo de spaCy usado en el análisis. Convierte un conjunto de textos en un corpus analizable sin escribir código:",
        "<ol>"
        "<li><strong>Importar</strong> — extrae el contenido de páginas web (artículos y noticias, limpiando menús y anuncios con trafilatura / jusText / BeautifulSoup), de Wikipedia, o de archivos propios (<code>.txt</code>, <code>.pdf</code>, <code>.docx</code>), con normalización de caracteres y deduplicado. Se revisa qué entra en cada corpus antes de añadirlo.</li>"
        "<li><strong>Limpiar</strong> — reglas de expresión regular con <strong>vista previa antes/después en vivo</strong> y una guardia que evita reglas capaces de colgar el sistema.</li>"
        "<li><strong>Analizar</strong> — etiquetado gramatical y morfológico con spaCy: distribución de categorías, lemas frecuentes, n-gramas y métricas léxicas (riqueza de vocabulario, hápax, densidad). El resultado se cachea por corpus.</li>"
        "<li><strong>Terminología</strong> — términos candidatos filtrados por patrón gramatical y rankeados con el algoritmo <strong>C-value</strong> (Frantzi, Ananiadou y Mima, 2000), un método estándar en la literatura de extracción terminológica, no una heurística improvisada.</li>"
        "<li><strong>Concordancia (KWIC)</strong> — busca una palabra o frase y la muestra centrada, con su contexto izquierdo y derecho alineados.</li>"
        "<li><strong>Exportar</strong> — descarga del corpus o del análisis en <code>.txt</code>, <code>.json</code> o <code>.csv</code>.</li>"
        "</ol>",
        "Todo ocurre dentro de la misma interfaz, pensada para alguien sin experiencia de programación. El código es abierto (licencia MIT), está en GitHub y pasa una batería de pruebas automáticas en cada cambio.",
    ],
    extra_sections=[
        ("Cómo funciona por dentro", [
            "La <strong>lógica de análisis de corpus vive separada del framework web</strong>: son funciones puras que reciben datos y devuelven estructuras, de modo que se pueden probar y reutilizar sin levantar ningún servidor. El contrato entre la interfaz (React) y el backend (FastAPI) es JSON tipado y validado, no cadenas de texto que haya que re-interpretar.",
            "Todo el proceso — importación, limpieza, análisis con spaCy, extracción terminológica — corre dentro de <strong>un único contenedor Docker</strong>. Eso hace que la demo pública y una instancia privada para un cliente sean exactamente el mismo despliegue, sin diferencias de comportamiento.",
        ]),
        ("Un caso concreto", [
            "Una editorial que quiere identificar la terminología propia de una colección de manuales técnicos antes de traducirlos. Se importan los documentos, se limpian automáticamente, y la pestaña de Terminología devuelve una lista de candidatos ordenados por relevancia estadística — en minutos, en vez de releer cientos de páginas a mano anotando términos.",
            "A partir de ahí, las concordancias KWIC permiten ver cómo se usa realmente cada término candidato en su contexto, para decidir cuáles entran en el glosario y con qué definición.",
        ]),
        ("Cómo empezamos", [
            "La <strong>demo pública</strong> ya está accesible sin instalar nada — es la forma más rápida de ver si encaja con lo que necesitas (se duerme con la inactividad y despierta en la primera visita).",
            "Si el corpus tiene que quedar separado del demostrador público, por volumen o por confidencialidad, se despliega una <strong>instancia propia</strong> con el mismo contenedor Docker, en tu servidor o en uno que yo gestione.",
        ]),
    ],
    images=[
        ("alzolab-importar.png", "Importación de textos", "Importar", "múltiples fuentes: web, Wikipedia o archivos propios, con revisión previa."),
        ("alzolab-limpiar.png", "Limpieza y normalización", "Limpiar", "reglas regex con vista previa antes/después."),
        ("alzolab-analizar.png", "Análisis con spaCy", "Analizar", "categorías, lemas, n-gramas y métricas léxicas."),
        ("alzolab-concordancia.png", "Concordancias KWIC", "Concordancia", "cada término en su contexto real de uso."),
    ],
    cols=2,
    pending_shots=[
        ("Pestaña de Terminología", "La lista de términos candidatos rankeados por C-value, con su puntuación y su frecuencia."),
        ("Exportación", "El diálogo de exportación del corpus o del análisis en txt / json / csv."),
    ],
    faq=[
        ("¿Mis textos se quedan guardados en algún sitio?",
         "La demo pública trabaja sobre datos de sesión y de ejemplo; no es para material confidencial. Para eso se despliega una instancia propia y aislada."),
        ("¿En qué idiomas funciona?",
         "Español e inglés, tanto la interfaz como el análisis (cada uno con su modelo de spaCy)."),
        ("¿Qué es el C-value?",
         "Un método estadístico-lingüístico estándar para puntuar qué secuencias de palabras de un corpus son términos reales y no combinaciones casuales, teniendo en cuenta también los términos anidados dentro de otros más largos."),
        ("¿Puedo quedarme el código?",
         "Sí: es abierto, con licencia MIT, en GitHub. El servicio que ofrezco es el despliegue, la puesta a punto sobre tu corpus y el análisis."),
    ],
    services=[
        "<strong>Extracción de terminología especializada</strong> de un fondo documental (técnico, jurídico, médico) como base para un glosario o una memoria de traducción, en español o en inglés.",
        "<strong>Análisis de corpus a medida</strong> para traductores, editoriales o equipos de contenido que trabajan con grandes volúmenes de texto.",
        "<strong>Puesta en marcha de una instancia propia</strong> si necesitas mantener tu corpus separado del demostrador público.",
    ],
))

# ───────────────────────────────────────────────────────────────────────────────
# 6. NeupaTerm
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="neupaterm",
    title="NeupaTerm (Plataforma terminológica)",
    title_html='NeupaTerm <span style="color:#6b7280; font-weight:400;">(Plataforma terminológica)</span>',
    subtitle="Gestión terminológica multilingüe independiente del CAT, con fichas por par de idiomas y consulta desde cualquier herramienta de traducción",
    badge="Beta · accesible en línea",
    stack="FastAPI · React 18 + Vite · PostgreSQL · Redis/RQ · spaCy (ES·EN·FR·DE·IT) · NeupaTerm Connect (Tauri, offline-first) · Stripe · Render + Vercel",
    problema=[
        "El glosario terminológico de un equipo suele acabar en una hoja de cálculo compartida. Con el tiempo aparecen términos duplicados, equivalencias que no coinciden entre traductores y ninguna forma de saber cuál es la versión buena.",
        "Además, esa hoja está fuera de la herramienta donde se traduce: hay que salir del CAT (Trados, memoQ, Word), buscar el término y volver — decenas de veces al día.",
        "Y una entrada terminológica de verdad no es una fila de dos columnas: un término tiene categoría gramatical, contextos de uso, notas, un estado (¿es el preferido? ¿está desaconsejado?) y relaciones con otros conceptos. Nada de eso cabe bien en una hoja de cálculo.",
    ],
    que_hace_paragraphs=[
        "NeupaTerm es una <strong>plataforma web de gestión terminológica multilingüe, independiente del CAT</strong>. La terminología se organiza en <strong>fichas por par de idiomas</strong> (ES · EN · PT · DE · IT · FR): ES→EN es una ficha distinta de ES→PT, cada una con su categoría gramatical, sus contextos de uso reales y sus notas — en vez de una única entrada genérica multilingüe difícil de mantener.",
        "Cada término tiene un <strong>ciclo de vida</strong> explícito (preferido, admitido, desaconsejado, obsoleto, prohibido), de modo que el glosario no solo dice cómo se traduce algo, sino también qué <em>no</em> usar.",
        "La <strong>búsqueda es difusa y multi-glosario</strong>: encuentra el término aunque lo escribas con una errata, sin tilde o en otra forma flexionada, y busca a la vez en todos los glosarios a los que tienes acceso.",
        "Importa y exporta en <strong>seis formatos</strong> — TBX (v2 y v3), XLIFF 2.1, TMX, CSV, Excel y JSON — para que la terminología no quede cautiva de la herramienta y se pueda mover a y desde cualquier flujo de traducción.",
        "Incluye un <strong>extractor terminológico</strong> basado en NLP (spaCy) para sacar candidatos de tu propio corpus como punto de partida, un <strong>editor visual de ontología</strong> para ver y editar las relaciones entre conceptos como un grafo, y la posibilidad de <strong>compartir glosarios</strong> con otros usuarios con permisos de solo lectura o de edición. La interfaz está traducida a cinco idiomas.",
    ],
    extra_sections=[
        ("NeupaTerm Connect", [
            "Connect es una <strong>aplicación de escritorio</strong> que pone la terminología a un atajo de teclado desde <strong>Word, Trados, memoQ o cualquier otra aplicación</strong>. Funciona <em>offline-first</em>: mantiene una copia local de los glosarios, así que la consulta es instantánea y no depende de la conexión, y se sincroniza con la plataforma cuando la hay.",
            "Es la pieza que convierte el glosario de «algo que hay que ir a mirar» en «algo que está siempre a la vista mientras traduces».",
        ]),
        ("Cómo funciona por dentro", [
            "Backend en FastAPI con PostgreSQL; la búsqueda difusa combina similitud de trigramas, distancia de edición y normalización de acentos a nivel de base de datos. Las tareas pesadas (importaciones grandes, extracción terminológica sobre un corpus) van a una cola de trabajos con Redis.",
            "Autenticación con token de sesión en memoria y refresco en cookie httpOnly, con opción de entrar con Google. Planes de usuario gestionados con Stripe. Observabilidad con seguimiento de errores y registro de auditoría. Integración continua en cada cambio; backend en Render, interfaz en Vercel (<code>neupaterm.com</code>).",
        ]),
        ("El origen del proyecto", [
            "NeupaTerm nació como el instrumento experimental de una investigación doctoral en Lingüística Aplicada. El modelo de datos terminológico — la ficha por par de idiomas, el grafo conceptual con relaciones jerárquicas, partitivas y asociativas — es una decisión de diseño con fundamento teórico, no una improvisación de producto.",
        ]),
        ("Un caso concreto", [
            "Un equipo de traducción de software en cuatro idiomas que mantenía el glosario en una hoja de cálculo compartida, con términos duplicados y equivalencias inconsistentes entre traductores. Migrar ese glosario a fichas por par de idiomas, con contexto de uso real y estado de cada término, evita que dos traductores usen dos términos distintos para el mismo concepto en el mismo proyecto — y con Connect, cada uno lo tiene delante sin salir de su CAT.",
        ]),
        ("Cómo empezamos", [
            "La plataforma está <strong>accesible en línea</strong> (<code>neupaterm.com</code>): se puede solicitar acceso y probarla directamente.",
            "Para migrar un glosario ya existente (hoja de cálculo, TBX, TMX) se importa una vez y queda estructurado por pares de idioma desde el primer día. Si hace falta, hago yo la limpieza y el mapeo de campos del glosario de partida.",
        ]),
    ],
    images=[
        ("neupaterm-landing.png", "Página de acceso", "Acceso", "entrada a la plataforma."),
        ("neupaterm-dashboard.png", "Panel de inicio", "Panel", "vista general de los glosarios del usuario."),
        ("neupaterm-ficha.png", "Ficha terminológica", "Ficha", "categoría, contextos y equivalencias de un término, por par de idiomas."),
        ("neupaterm-connect.png", "NeupaTerm Connect", "Connect", "consulta de terminología desde herramientas externas."),
    ],
    cols=2,
    pending_shots=[
        ("Búsqueda difusa multi-glosario", "Un resultado de búsqueda con una errata en la consulta que aun así encuentra el término, mostrando de qué glosario viene cada resultado."),
        ("Editor de ontología", "El grafo de relaciones entre conceptos, con una relación jerárquica seleccionada y editable."),
        ("Ciclo de vida del término", "Una ficha mostrando el estado del término (preferido / admitido / desaconsejado / prohibido) y el historial de cambios."),
        ("Importación TBX / TMX", "El asistente de importación con la previsualización del mapeo de campos del archivo de origen."),
    ],
    faq=[
        ("¿Depende de un CAT concreto?",
         "No. NeupaTerm es independiente de la herramienta de traducción; Connect la consulta desde Word, Trados, memoQ o cualquier aplicación, y los formatos de export (TBX, TMX, XLIFF) permiten alimentar el termbase de cada CAT si se prefiere."),
        ("¿Funciona la consulta sin conexión?",
         "Connect sí: mantiene una copia local y consulta offline; sincroniza cuando hay red. La plataforma web necesita conexión."),
        ("¿Puedo traer mi glosario actual?",
         "Sí, desde hoja de cálculo, TBX o TMX. Se importa una vez y queda estructurado por pares de idioma."),
        ("¿En qué idiomas trabaja?",
         "Las fichas cubren pares entre español, inglés, portugués, alemán, italiano y francés. La interfaz está traducida a cinco idiomas."),
    ],
    services=[
        "<strong>Confección y mantenimiento de un glosario terminológico multilingüe</strong> para una empresa o equipo de traducción, con fichas por par de idioma en vez de una hoja de cálculo.",
        "<strong>Integración del glosario en las herramientas del día a día</strong> (Word, Trados, memoQ) vía NeupaTerm Connect.",
        "<strong>Extracción inicial de candidatos terminológicos</strong> mediante NLP sobre tu propio corpus, como punto de partida.",
        "<strong>Migración y limpieza</strong> de un glosario existente (hoja de cálculo, TBX, TMX) hacia una estructura mantenible.",
    ],
))

# ───────────────────────────────────────────────────────────────────────────────
# 7. NeupaLang
# ───────────────────────────────────────────────────────────────────────────────
PROJECTS.append(build(
    slug="neupalang",
    title="NeupaLang (Documentación lingüística)",
    title_html='NeupaLang <span style="color:#6b7280; font-weight:400;">(Documentación lingüística)</span>',
    subtitle="Plataforma para documentar lenguas minoritarias y en peligro: lexicón, corpus anotado, informantes con consentimiento e interoperabilidad real con FLEx y ELAN",
    badge="En desarrollo",
    stack="FastAPI · SQLAlchemy 2 · PostgreSQL (full-text) · React 18 + TypeScript · i18n ES·EN·FR·DE·IT · export LIFT / EAF / CLDF",
    problema=[
        "De las cerca de 7000 lenguas del mundo, una parte muy grande está en peligro de desaparición. La documentación de campo es la forma de preservarlas — y las herramientas para hacerla son en su mayoría software de escritorio antiguo (FLEx, Toolbox), con una curva de aprendizaje de meses y sin colaboración entre equipos distribuidos.",
        "Los datos, además, suelen quedar atrapados en formatos propietarios: si la herramienta deja de mantenerse, el trabajo de años se vuelve difícil de recuperar.",
        "Y la dimensión ética — el consentimiento de los hablantes, qué usos autorizan, qué material es sensible o sagrado — se suele gestionar aparte, en documentos sueltos, cuando debería ser parte del propio registro.",
    ],
    que_hace_paragraphs=[
        "NeupaLang es una <strong>plataforma web de documentación lingüística</strong> para lingüistas, investigadores y comunidades. Cubre los tres frentes del trabajo de campo en un mismo sitio:",
        "<ul>"
        "<li><strong>Lexicón</strong> — entradas con transcripción fonética (IPA, con teclado asistido y validación), categoría gramatical y variantes ortográficas; cada entrada con varias <strong>acepciones</strong>, y cada acepción con sus <strong>ejemplos</strong> en formato de glosa interlineal. Subíndices automáticos para homónimos. Historial de cambios completo, con posibilidad de volver a una versión anterior.</li>"
        "<li><strong>Corpus textual</strong> — narrativas, conversaciones, textos rituales, con metadatos (género, registro, fecha y lugar de grabación, sensibilidad). Cada texto se divide en <strong>líneas anotadas morfema a morfema</strong>, alineables con audio o vídeo por marcas de tiempo, y los lexemas mencionados se vinculan al diccionario.</li>"
        "<li><strong>Informantes</strong> — colaboradores registrados con código anónimo y datos demográficos, y sobre todo con <strong>consentimiento informado</strong> estructurado: tipo (oral, escrito, grabado), alcance (solo investigación, publicación, difusión pública), fecha, vigencia y revocación registrada. Si un informante revoca el consentimiento, su material asociado se marca como restringido.</li>"
        "</ul>",
        "Las <strong>glosas interlineales</strong> siguen las Leipzig Glossing Rules, con más de 60 abreviaturas estándar y un editor que se puede usar en modo texto libre o palabra por palabra. Cada lengua puede definir <strong>campos personalizados</strong> (clase nominal, tono, clasificador, etimología, préstamos…) que aparecen luego en cada entrada.",
        "El trabajo es <strong>colaborativo</strong>, con roles de propietario, editor y solo lectura, glosarios públicos o privados, notificaciones y búsqueda de texto completo multilingüe. La interfaz está disponible en cinco idiomas.",
    ],
    extra_sections=[
        ("Interoperabilidad: los datos no quedan cautivos", [
            "NeupaLang importa y exporta los formatos que ya usan los lingüistas de campo, para que se pueda entrar y salir sin fricción:",
            "<ul>"
            "<li><strong>FLEx / WeSay</strong> (formato LIFT) — importación y exportación completas, con estrategia de fusión configurable (omitir, sobrescribir o combinar duplicados).</li>"
            "<li><strong>ELAN</strong> (formato EAF) — importación y exportación, con mapeo de las capas de anotación (referencia, transcripción, traducción).</li>"
            "<li><strong>Praat</strong> — exportación a EAF.</li>"
            "<li><strong>CLDF</strong> — exportación a Cross-Linguistic Data Formats, el estándar para archivos lingüísticos y catálogos como Glottolog.</li>"
            "</ul>",
            "Más exportación a JSON (copia de seguridad completa), CSV (hojas de cálculo) y PDF (impresión y publicación). Los códigos de lengua siguen el estándar ISO 639-3.",
        ]),
        ("Gestión ética integrada (CARE / FAIR)", [
            "El consentimiento y la sensibilidad no son un añadido: forman parte del modelo de datos. Cada nivel — lengua, informante, entrada, texto — lleva sus propios metadatos de sensibilidad y de derechos, siguiendo los principios <strong>CARE</strong> (soberanía de los datos de las comunidades) y <strong>FAIR</strong> (datos localizables, accesibles, interoperables y reutilizables).",
            "En la práctica: un texto puede marcarse como público, restringido o sagrado; un informante puede autorizar solo uso académico y no publicación; y esa distinción se respeta en las exportaciones y en quién puede ver qué.",
        ]),
        ("Estado del proyecto", [
            "El lexicón, el corpus y la exportación a los formatos estándar están <strong>funcionales</strong>, con una batería de varios cientos de pruebas automáticas del backend en verde. Está en desarrollo un <strong>editor de escritorio con modo sin conexión</strong>, pensado para el trabajo de campo en zonas sin acceso fiable a internet, que sincroniza al recuperar la conexión.",
            "Es un proyecto de investigación a largo plazo, no un producto cerrado a la venta.",
        ]),
        ("Un caso concreto", [
            "Un proyecto de documentación de una lengua indígena con trabajo de campo en una zona sin internet fiable. El investigador registra el lexema, su glosa interlineal y el consentimiento del hablante — incluyendo si autoriza solo uso académico o también publicación — en el dispositivo; los datos se sincronizan cuando vuelve a tener conexión, sin haber dependido de ella durante el trabajo de campo. Al terminar la campaña, exporta a FLEx para seguir en su flujo habitual, o a CLDF para archivar.",
        ]),
        ("Cómo encajaría un proyecto", [
            "Si tu equipo de documentación lingüística trabaja con este enfoque, hablamos de qué fase está lista para tu caso concreto antes de comprometer nada: puesta en marcha de una instancia, importación de datos existentes desde FLEx o ELAN, definición de los campos personalizados de la lengua y formación del equipo.",
        ]),
    ],
    images=[],
    cols=2,
    pending_shots=[
        ("Ficha de lexema", "Una entrada del diccionario con su transcripción IPA, categoría, variantes y sus acepciones desplegadas."),
        ("Editor de glosa interlineal (IGT)", "El editor palabra por palabra con las tres líneas (original, segmentación, glosa Leipzig) y la traducción libre."),
        ("Ficha de informante con consentimiento", "El formulario de consentimiento estructurado: tipo, alcance, fecha, vigencia y el botón de revocación."),
        ("Corpus: línea anotada", "Un texto del corpus con una línea segmentada morfema a morfema y alineada con su marca de tiempo de audio."),
        ("Importar/exportar", "El diálogo de interoperabilidad mostrando FLEx (LIFT), ELAN (EAF) y CLDF con la estrategia de fusión."),
    ],
    faq=[
        ("¿Sustituye a FLEx o a ELAN?",
         "No pretende sustituirlos: se integra con ellos. Se puede empezar un proyecto en NeupaLang y exportarlo a FLEx, o traer datos de ELAN y seguir en la web."),
        ("¿Cómo se gestiona el consentimiento de los hablantes?",
         "De forma estructurada dentro del propio registro: tipo, alcance, vigencia y revocación. Una revocación marca el material asociado como restringido y se respeta en las exportaciones."),
        ("¿Funciona sin conexión para el trabajo de campo?",
         "La plataforma web necesita conexión. El editor de escritorio con modo sin conexión, pensado para eso, está en desarrollo."),
        ("¿Qué formatos de salida hay?",
         "LIFT (FLEx/WeSay), EAF (ELAN, Praat), CLDF, más JSON, CSV y PDF. Códigos de lengua en ISO 639-3."),
    ],
    services=[
        "Equipos de documentación lingüística y proyectos de investigación sobre lenguas minoritarias que necesitan trabajar con datos de campo de forma rigurosa y éticamente responsable, con interoperabilidad real hacia FLEx y ELAN en vez de un formato propio cerrado.",
        "Puesta en marcha de una instancia, importación de datos existentes y definición de los campos personalizados de cada lengua.",
    ],
    services_heading="Para quién es útil",
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
