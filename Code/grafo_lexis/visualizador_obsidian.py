"""Visualizador interactivo tipo 'Cerebro de Obsidian' (física force-directed) para el Grafo LEXIS."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import networkx as nx

from .reporte_rotas import RUTA_KNOWLEDGE_GRAPH_DEFECTO

# Paleta de colores neón estilo Obsidian Dark Graph para cada ley y tipo de nodo
COLORES_NODOS = {
    "ley:cc_tlax": "#38BDF8",      # Azul cielo brillante (Código Civil)
    "ley:cpc_tlax": "#818CF8",     # Índigo (Código Proc. Civiles)
    "ley:cp_tlax": "#F87171",      # Rojo coral (Código Penal)
    "ley:cpp_tlax": "#FB923C",     # Naranja (Código Proc. Penales)
    "ley:cpeum": "#FBBF24",        # Dorado (Constitución CPEUM)
    "ley:lft": "#34D399",          # Esmeralda (Ley Federal del Trabajo)
    "NormaExterna": "#A855F7",     # Púrpura (Normas externas)
    "Semilla": "#22D3EE",          # Cian brillante (Artículo recuperado directamente por RAG)
}


def extraer_datos_subgrafo_consulta(
    grafo: nx.MultiDiGraph,
    expansion: Dict[str, Any],
    incluir_nodos_ley: bool = True,
) -> Dict[str, Any]:
    """
    Convierte el resultado de `expandir_contexto_hits` (nodos semilla, vecinos citados salientes,
    vecinos afectados entrantes y normas externas) en un diccionario `{nodes, edges}` listo
    para renderizar el cerebro interactivo tipo Obsidian.
    """
    semillas: List[str] = expansion.get("nodos_semilla", [])
    salientes: List[Dict[str, Any]] = expansion.get("vecinos_citados_salientes", [])
    entrantes: List[Dict[str, Any]] = expansion.get("vecinos_afectados_entrantes", [])
    externas: List[Dict[str, Any]] = expansion.get("normas_externas_mencionadas", [])

    nodos_incluidos: Set[str] = set()
    nodos_vis: List[Dict[str, Any]] = []
    aristas_vis: List[Dict[str, Any]] = []
    leyes_presentes: Set[str] = set()

    def agregar_nodo_articulo(art_id: str, rol: str) -> None:
        if art_id in nodos_incluidos or not grafo.has_node(art_id):
            return
        nodos_incluidos.add(art_id)
        d = grafo.nodes[art_id]
        ley_id = d.get("ley_id", "ley:cc_tlax")
        leyes_presentes.add(ley_id)
        ley_corto = grafo.nodes.get(ley_id, {}).get("clave", ley_id)
        etiqueta = d.get("etiqueta_normalizada", art_id)
        texto_resumen = (d.get("texto_completo") or "")[:340].replace("\n", " ")

        es_semilla = rol == "semilla"
        color_base = COLORES_NODOS.get(ley_id, "#38BDF8")
        nodos_vis.append(
            {
                "id": art_id,
                "label": f"{ley_corto} | {etiqueta}",
                "title": f"[{ley_corto}] {etiqueta} ({d.get('jerarquia', '')})\nRol: {rol.upper()}\n\n{texto_resumen}...",
                "rol": rol,
                "ley_id": ley_id,
                "color": "#22D3EE" if es_semilla else color_base,
                "border": "#FFFFFF" if es_semilla else color_base,
                "size": 19 if es_semilla else 13,
            }
        )

    # 1. Agregar nodos semilla (recuperados directamente por ChromaDB / BM25)
    for sem_id in semillas:
        agregar_nodo_articulo(sem_id, "semilla")

    # 2. Agregar vecinos salientes (citados por las semillas) y sus aristas
    for vec in salientes:
        dest_id = vec["articulo_id"]
        sem_id = vec["desde_semilla_id"]
        agregar_nodo_articulo(dest_id, "citado_saliente")
        aristas_vis.append(
            {
                "from": sem_id,
                "to": dest_id,
                "label": vec.get("clase", "REFIERE_A"),
                "title": f"Cita ({vec.get('clase')}): \"{vec.get('texto_referencia', '')}\"",
                "color": "#38BDF8" if vec.get("relacion") == "entre_leyes" else "#94A3B8",
                "dashes": False,
                "width": 2.4 if vec.get("relacion") == "entre_leyes" else 1.6,
            }
        )

    # 3. Agregar vecinos entrantes (artículos que remiten/afectan a las semillas)
    for vec_in in entrantes:
        orig_id = vec_in["articulo_id"]
        sem_id = vec_in["hacia_semilla_id"]
        agregar_nodo_articulo(orig_id, "afectado_entrante")
        aristas_vis.append(
            {
                "from": orig_id,
                "to": sem_id,
                "label": vec_in.get("clase", "REFIERE_A"),
                "title": f"Remite aquí ({vec_in.get('clase')}): \"{vec_in.get('texto_referencia', '')}\"",
                "color": "#F472B6",
                "dashes": False,
                "width": 1.8,
            }
        )

    # 4. Agregar normas externas si existen
    for idx, ext in enumerate(externas):
        ext_nombre = ext.get("norma_externa", f"Norma Externa {idx+1}")
        ext_id = f"ext:{ext_nombre}"
        if ext_id not in nodos_incluidos:
            nodos_incluidos.add(ext_id)
            nodos_vis.append(
                {
                    "id": ext_id,
                    "label": ext_nombre[:32] + ("..." if len(ext_nombre) > 32 else ""),
                    "title": f"Norma Externa: {ext_nombre}\nArtículo mencionado: {ext.get('articulo_mencionado')}",
                    "rol": "norma_externa",
                    "ley_id": "NormaExterna",
                    "color": COLORES_NODOS["NormaExterna"],
                    "border": "#E9D5FF",
                    "size": 12,
                }
            )
        aristas_vis.append(
            {
                "from": ext["origen_id"],
                "to": ext_id,
                "label": f"Art. {ext.get('articulo_mencionado', '')}",
                "title": f"Menciona norma externa: \"{ext.get('texto_referencia', '')}\"",
                "color": "#A855F7",
                "dashes": True,
                "width": 1.5,
            }
        )

    # 5. Opcionalmente agregar los nodos Ley contenedores
    if incluir_nodos_ley:
        for ley_id in sorted(leyes_presentes):
            if not grafo.has_node(ley_id):
                continue
            d_ley = grafo.nodes[ley_id]
            nodos_vis.append(
                {
                    "id": ley_id,
                    "label": f"LEY: {d_ley.get('clave', ley_id)}",
                    "title": f"Ley: {d_ley.get('nombre_oficial', ley_id)}\nÁmbito: {d_ley.get('ambito', '')}",
                    "rol": "ley",
                    "ley_id": ley_id,
                    "color": COLORES_NODOS.get(ley_id, "#64748B"),
                    "border": "#F8FAFC",
                    "size": 24,
                }
            )
            for nid in list(nodos_incluidos):
                if nid.startswith("articulo:") and grafo.nodes[nid].get("ley_id") == ley_id:
                    aristas_vis.append(
                        {
                            "from": ley_id,
                            "to": nid,
                            "label": "CONTIENE",
                            "title": f"{d_ley.get('nombre_corto')} contiene {nid}",
                            "color": "#334155",
                            "dashes": True,
                            "width": 1.0,
                        }
                    )

    return {"nodes": nodos_vis, "edges": aristas_vis}


def extraer_datos_cerebro_global(
    grafo: nx.MultiDiGraph,
    max_nodos_articulos: int = 180,
    ley_filtro: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extrae el núcleo más conectado del grafo completo (las 6 leyes, las normas externas y los
    artículos con más citas entrantes/salientes y puentes entre leyes) para explorar el
    'Cerebro Jurídico' completo con física fluida tipo Obsidian.
    """
    grados_ref: Dict[str, int] = {}
    aristas_ref: List[Any] = []

    for u, v, d in grafo.edges(data=True):
        tipo = d.get("tipo")
        if tipo in ("REFIERE_A", "MENCIONA_NORMA"):
            if str(v).startswith("ley:"):
                continue
            if ley_filtro and d.get("origen_ley_id") != ley_filtro and d.get("destino_ley_id") != ley_filtro:
                continue
            peso = 3 if d.get("relacion") == "entre_leyes" else 1
            grados_ref[u] = grados_ref.get(u, 0) + peso
            grados_ref[v] = grados_ref.get(v, 0) + peso
            aristas_ref.append((u, v, d))

    top_articulos = {
        nid
        for nid, _ in sorted(grados_ref.items(), key=lambda x: x[1], reverse=True)[
            :max_nodos_articulos
        ]
    }

    nodos_vis: List[Dict[str, Any]] = []
    aristas_vis: List[Dict[str, Any]] = []

    for nid in top_articulos:
        if not grafo.has_node(nid):
            continue
        d = grafo.nodes[nid]
        tipo_nodo = d.get("tipo_nodo")
        if tipo_nodo == "NormaExterna":
            nodos_vis.append(
                {
                    "id": nid,
                    "label": d.get("nombre", nid)[:28],
                    "title": f"Norma Externa: {d.get('nombre', nid)}",
                    "rol": "norma_externa",
                    "ley_id": "NormaExterna",
                    "color": COLORES_NODOS["NormaExterna"],
                    "border": "#E9D5FF",
                    "size": 12,
                }
            )
        elif tipo_nodo == "Articulo":
            ley_id = d.get("ley_id", "ley:cc_tlax")
            clave = grafo.nodes.get(ley_id, {}).get("clave", ley_id)
            etiqueta = d.get("etiqueta_normalizada", nid)
            grado = grados_ref.get(nid, 1)
            tam = min(24, 9 + int(grado * 0.6))
            resumen = (d.get("texto_completo") or "")[:280].replace("\n", " ")
            nodos_vis.append(
                {
                    "id": nid,
                    "label": f"{clave} {d.get('numero', '')}",
                    "title": f"[{clave}] {etiqueta} ({d.get('jerarquia', '')})\nConexiones: {grado}\n\n{resumen}...",
                    "rol": "articulo",
                    "ley_id": ley_id,
                    "color": COLORES_NODOS.get(ley_id, "#38BDF8"),
                    "border": "#0F172A",
                    "size": tam,
                }
            )

    for u, v, d in aristas_ref:
        if u in top_articulos and v in top_articulos:
            es_cruzada = d.get("relacion") == "entre_leyes"
            aristas_vis.append(
                {
                    "from": u,
                    "to": v,
                    "label": d.get("clase", ""),
                    "title": f"{u} -> {v}\nClase: {d.get('clase')}\nRef: \"{d.get('texto_referencia', '')}\"",
                    "color": "#FBBF24" if es_cruzada else "#475569",
                    "dashes": d.get("tipo") == "MENCIONA_NORMA",
                    "width": 2.0 if es_cruzada else 1.1,
                }
            )

    return {"nodes": nodos_vis, "edges": aristas_vis}


def generar_html_obsidian(
    datos_grafo: Dict[str, Any],
    altura_px: int = 560,
    titulo: str = "Cerebro Jurídico LEXIS — Vista tipo Obsidian",
) -> str:
    """
    Genera un documento HTML5 autocontenido con motor de física Force-Directed en Canvas 2D
    nativo (cero dependencias externas de CDN) y estética oscura tipo Obsidian Graph View:
    arrastre de nodos con el ratón, zoom con la rueda, buscador en vivo y panel de detalle
    al hacer clic sobre cualquier nodo o arista.
    """
    nodos_json = json.dumps(datos_grafo.get("nodes", []), ensure_ascii=False)
    aristas_json = json.dumps(datos_grafo.get("edges", []), ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>{titulo}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #090D16;
    color: #F8FAFC;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    overflow: hidden;
  }}
  #contenedor-principal {{
    position: relative;
    width: 100%;
    height: {altura_px}px;
    background: radial-gradient(circle at center, #111827 0%, #090D16 100%);
    border: 1px solid #1E293B;
    border-radius: 10px;
    overflow: hidden;
  }}
  canvas {{
    display: block;
    width: 100%;
    height: 100%;
    cursor: grab;
  }}
  canvas:active {{
    cursor: grabbing;
  }}
  .barra-superior {{
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    pointer-events: none;
    z-index: 10;
    gap: 8px;
  }}
  .leyenda {{
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 10px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 11px;
    pointer-events: auto;
  }}
  .item-leyenda {{
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .punto {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
    display: inline-block;
  }}
  .buscador-box {{
    pointer-events: auto;
    display: flex;
    gap: 6px;
  }}
  .buscador-box input {{
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid #475569;
    color: #F8FAFC;
    padding: 5px 9px;
    border-radius: 6px;
    font-size: 12px;
    width: 185px;
  }}
  .buscador-box button {{
    background: #1E293B;
    border: 1px solid #475569;
    color: #38BDF8;
    padding: 5px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
  }}
  #panel-detalle {{
    position: absolute;
    bottom: 10px;
    left: 10px;
    right: 10px;
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid #38BDF8;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.45;
    display: none;
    z-index: 10;
    max-height: 140px;
    overflow-y: auto;
  }}
</style>
</head>
<body>
<div id="contenedor-principal">
  <div class="barra-superior">
    <div class="leyenda">
      <div class="item-leyenda"><span class="punto" style="background:#22D3EE;box-shadow:0 0 6px #22D3EE"></span>Semilla RAG</div>
      <div class="item-leyenda"><span class="punto" style="background:#38BDF8"></span>CC-TLAX</div>
      <div class="item-leyenda"><span class="punto" style="background:#818CF8"></span>CPC-TLAX</div>
      <div class="item-leyenda"><span class="punto" style="background:#F87171"></span>CP-TLAX</div>
      <div class="item-leyenda"><span class="punto" style="background:#FB923C"></span>CPP-TLAX</div>
      <div class="item-leyenda"><span class="punto" style="background:#FBBF24"></span>CPEUM</div>
      <div class="item-leyenda"><span class="punto" style="background:#34D399"></span>LFT</div>
      <div class="item-leyenda"><span class="punto" style="background:#A855F7"></span>Norma Externa</div>
    </div>
    <div class="buscador-box">
      <input type="text" id="input-buscar" placeholder="Buscar nodo (ej. 123, 1470)..." oninput="filtrarNodos()"/>
      <button onclick="centrarVista()">Centrar</button>
    </div>
  </div>
  <canvas id="lienzo"></canvas>
  <div id="panel-detalle"></div>
</div>

<script>
// Motor vis.Network ligero nativo en Canvas 2D (sin dependencias externas)
const rawNodes = {nodos_json};
const rawEdges = {aristas_json};

const canvas = document.getElementById('lienzo');
const ctx = canvas.getContext('2d');
const panel = document.getElementById('panel-detalle');

let width = canvas.parentElement.clientWidth || 800;
let height = canvas.parentElement.clientHeight || {altura_px};
canvas.width = width;
canvas.height = height;

let camX = 0, camY = 0, camScale = 1.0;
let nodoSeleccionado = null;
let nodoHover = null;
let nodoArrastrado = null;
let arrastrandoFondo = false;
let lastMouseX = 0, lastMouseY = 0;
let filtroTexto = "";

const nodeMap = new Map();
const nodes = rawNodes.map((n, i) => {{
  const angle = (i / Math.max(1, rawNodes.length)) * Math.PI * 2;
  const radius = Math.min(width, height) * 0.28 * (0.4 + Math.random() * 0.6);
  const obj = {{
    ...n,
    x: width / 2 + Math.cos(angle) * radius,
    y: height / 2 + Math.sin(angle) * radius,
    vx: 0,
    vy: 0,
    r: Math.max(7, Math.min(22, n.size || 13))
  }};
  nodeMap.set(n.id, obj);
  return obj;
}});

const edges = rawEdges.map(e => ({{
  ...e,
  source: nodeMap.get(e.from),
  target: nodeMap.get(e.to)
}})).filter(e => e.source && e.target);

function simularFisica() {{
  const repulsion = 2400;
  const kSpring = 0.035;
  const longIdeal = 115;
  const gravedadCentro = 0.008;

  for (let i = 0; i < nodes.length; i++) {{
    const a = nodes[i];
    for (let j = i + 1; j < nodes.length; j++) {{
      const b = nodes[j];
      let dx = a.x - b.x;
      let dy = a.y - b.y;
      let dist2 = dx * dx + dy * dy + 1;
      if (dist2 < 90000) {{
        let dist = Math.sqrt(dist2);
        let f = repulsion / dist2;
        let fx = (dx / dist) * f;
        let fy = (dy / dist) * f;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      }}
    }}
  }}

  for (const e of edges) {{
    const a = e.source;
    const b = e.target;
    let dx = b.x - a.x;
    let dy = b.y - a.y;
    let dist = Math.sqrt(dx * dx + dy * dy) || 1;
    let f = (dist - longIdeal) * kSpring;
    let fx = (dx / dist) * f;
    let fy = (dy / dist) * f;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  }}

  for (const n of nodes) {{
    if (n === nodoArrastrado) continue;
    n.vx += (width / 2 - n.x) * gravedadCentro;
    n.vy += (height / 2 - n.y) * gravedadCentro;
    n.vx *= 0.82;
    n.vy *= 0.82;
    n.x += Math.max(-12, Math.min(12, n.vx));
    n.y += Math.max(-12, Math.min(12, n.vy));
  }}
}}

function pantallaAMundo(px, py) {{
  return {{
    x: (px - width / 2 - camX) / camScale + width / 2,
    y: (py - height / 2 - camY) / camScale + height / 2
  }};
}}

function dibujar() {{
  ctx.clearRect(0, 0, width, height);
  ctx.save();
  ctx.translate(width / 2 + camX, height / 2 + camY);
  ctx.scale(camScale, camScale);
  ctx.translate(-width / 2, -height / 2);

  // Dibujar aristas
  for (const e of edges) {{
    const a = e.source;
    const b = e.target;
    const esConectadaSel = nodoSeleccionado && (a === nodoSeleccionado || b === nodoSeleccionado);
    ctx.beginPath();
    if (e.dashes) ctx.setLineDash([5, 4]);
    else ctx.setLineDash([]);
    ctx.strokeStyle = esConectadaSel ? '#22D3EE' : (e.color || '#475569');
    ctx.lineWidth = esConectadaSel ? (e.width + 1.2) : (e.width || 1.3);
    ctx.globalAlpha = (filtroTexto && !coincideFiltro(a) && !coincideFiltro(b)) ? 0.15 : 0.85;
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();

    // Punta de flecha
    const ang = Math.atan2(b.y - a.y, b.x - a.x);
    const tx = b.x - Math.cos(ang) * (b.r + 3);
    const ty = b.y - Math.sin(ang) * (b.r + 3);
    ctx.beginPath();
    ctx.setLineDash([]);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.moveTo(tx, ty);
    ctx.lineTo(tx - 7 * Math.cos(ang - Math.PI / 6), ty - 7 * Math.sin(ang - Math.PI / 6));
    ctx.lineTo(tx - 7 * Math.cos(ang + Math.PI / 6), ty - 7 * Math.sin(ang + Math.PI / 6));
    ctx.closePath();
    ctx.fill();

    // Etiqueta de arista cuando hay pocos nodos o está seleccionada
    if ((nodes.length <= 25 || esConectadaSel) && e.label) {{
      const mx = (a.x + b.x) / 2;
      const my = (a.y + b.y) / 2;
      ctx.font = '9px Inter, sans-serif';
      ctx.fillStyle = '#94A3B8';
      ctx.textAlign = 'center';
      ctx.fillText(e.label, mx, my - 4);
    }}
  }}

  // Dibujar nodos
  ctx.setLineDash([]);
  for (const n of nodes) {{
    const activo = !filtroTexto || coincideFiltro(n);
    ctx.globalAlpha = activo ? 1.0 : 0.18;

    ctx.save();
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
    ctx.fillStyle = n.color || '#38BDF8';
    ctx.shadowColor = n.color || '#38BDF8';
    ctx.shadowBlur = (n === nodoSeleccionado || n === nodoHover || n.rol === 'semilla') ? 16 : 7;
    ctx.fill();
    ctx.lineWidth = (n === nodoSeleccionado || n.rol === 'semilla') ? 2.5 : 1.2;
    ctx.strokeStyle = (n === nodoSeleccionado) ? '#FFFFFF' : (n.border || '#0F172A');
    ctx.stroke();
    ctx.restore();

    // Etiqueta del nodo
    if (camScale > 0.55 || nodes.length <= 45 || n === nodoSeleccionado || n === nodoHover || n.rol === 'semilla') {{
      ctx.font = (n.rol === 'semilla' || n.rol === 'ley') ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#090D16';
      ctx.strokeText(n.label, n.x, n.y + n.r + 12);
      ctx.fillStyle = '#F8FAFC';
      ctx.fillText(n.label, n.x, n.y + n.r + 12);
    }}
  }}

  ctx.restore();
}}

function coincideFiltro(n) {{
  if (!filtroTexto) return true;
  return n.id.toLowerCase().includes(filtroTexto) ||
         n.label.toLowerCase().includes(filtroTexto) ||
         (n.title && n.title.toLowerCase().includes(filtroTexto));
}}

function buscarNodoEnPunto(mx, my) {{
  const m = pantallaAMundo(mx, my);
  for (let i = nodes.length - 1; i >= 0; i--) {{
    const n = nodes[i];
    const dx = m.x - n.x;
    const dy = m.y - n.y;
    if (dx * dx + dy * dy <= (n.r + 4) * (n.r + 4)) return n;
  }}
  return null;
}}

canvas.addEventListener('mousedown', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  lastMouseX = mx; lastMouseY = my;
  const tocado = buscarNodoEnPunto(mx, my);
  if (tocado) {{
    nodoArrastrado = tocado;
    nodoSeleccionado = tocado;
    panel.style.display = 'block';
    panel.innerHTML = '<strong>Nodo seleccionado: ' + tocado.id + '</strong><br/>' +
                      (tocado.title || '').replace(/\\n/g, '<br/>');
  }} else {{
    arrastrandoFondo = true;
    nodoSeleccionado = null;
    panel.style.display = 'none';
  }}
}});

window.addEventListener('mousemove', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  if (nodoArrastrado) {{
    const m = pantallaAMundo(mx, my);
    nodoArrastrado.x = m.x;
    nodoArrastrado.y = m.y;
    nodoArrastrado.vx = 0;
    nodoArrastrado.vy = 0;
  }} else if (arrastrandoFondo) {{
    camX += (mx - lastMouseX);
    camY += (my - lastMouseY);
  }} else {{
    nodoHover = buscarNodoEnPunto(mx, my);
  }}
  lastMouseX = mx; lastMouseY = my;
}});

window.addEventListener('mouseup', () => {{
  nodoArrastrado = null;
  arrastrandoFondo = false;
}});

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const factor = e.deltaY < 0 ? 1.12 : 0.89;
  camScale = Math.max(0.25, Math.min(3.5, camScale * factor));
}}, {{ passive: false }});

function centrarVista() {{
  camX = 0; camY = 0; camScale = 1.0;
}}

function filtrarNodos() {{
  filtroTexto = document.getElementById('input-buscar').value.toLowerCase().trim();
  if (filtroTexto) {{
    const primero = nodes.find(coincideFiltro);
    if (primero) {{
      nodoSeleccionado = primero;
      camScale = 1.25;
      camX = (width / 2 - primero.x) * camScale;
      camY = (height / 2 - primero.y) * camScale;
      panel.style.display = 'block';
      panel.innerHTML = '<strong>Nodo encontrado: ' + primero.id + '</strong><br/>' +
                        (primero.title || '').replace(/\\n/g, '<br/>');
    }}
  }}
}}

// Pre-estabilización rápida inicial
for (let i = 0; i < 65; i++) simularFisica();

function animar() {{
  simularFisica();
  dibujar();
  requestAnimationFrame(animar);
}}
animar();
</script>
</body>
</html>"""


def exportar_html_cerebro_obsidian(
    grafo: nx.MultiDiGraph,
    ruta_salida: Optional[Path] = None,
    max_nodos: int = 200,
) -> Path:
    """
    Genera y guarda en `knowledge_graph/visualizador_cerebro_lexis.html` el mapa
    interactivo tipo Obsidian para abrirlo directamente en cualquier navegador.
    """
    if ruta_salida is None:
        RUTA_KNOWLEDGE_GRAPH_DEFECTO.mkdir(parents=True, exist_ok=True)
        ruta_salida = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "visualizador_cerebro_lexis.html"
    else:
        ruta_salida = Path(ruta_salida)
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    datos = extraer_datos_cerebro_global(grafo, max_nodos_articulos=max_nodos)
    html = generar_html_obsidian(datos, altura_px=760)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html)
    return ruta_salida
