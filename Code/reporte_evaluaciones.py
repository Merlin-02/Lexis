#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reporte_evaluaciones.py — Procesamiento estadístico y generación de métricas
de pruebas de usabilidad y validación jurídica del sistema LEXIS (Etapa 5).

Procesa `sesiones_evaluacion/evaluaciones_consolidado.json` y `sesiones_evaluacion/usuarios.json`
y exporta `sesiones_evaluacion/resumen_metricas_usabilidad.json` junto con un reporte Markdown.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DIR_CODE = Path(__file__).resolve().parent
ROOT_DIR = DIR_CODE.parent
DIR_EVAL_DEFAULT = ROOT_DIR / "sesiones_evaluacion"


def _media(valores: List[float]) -> float:
    return round(sum(valores) / len(valores), 2) if valores else 0.0


def _desviacion_estandar(valores: List[float]) -> float:
    if len(valores) < 2:
        return 0.0
    m = sum(valores) / len(valores)
    var = sum((x - m) ** 2 for x in valores) / len(valores)
    return round(math.sqrt(var), 2)


def _inferir_area_normativa(resp: Dict[str, Any]) -> str:
    """Infiere la normativa o área jurídica a partir de los artículos recuperados o ley filtrada."""
    ley_f = (resp.get("ley_filtrada") or "").strip()
    if ley_f and ley_f.lower() != "automático":
        return ley_f

    arts = resp.get("articulos_recuperados") or []
    if arts and isinstance(arts[0], dict) and arts[0].get("documento"):
        return str(arts[0]["documento"])

    nodos = resp.get("nodos_grafo") or []
    mapa_slug = {
        "lft": "Ley Trabajo",
        "cp_tlax": "Código Penal Tlaxcala",
        "cc_tlax": "Codigo Civil Tlaxcala",
        "cpc_tlax": "Procedimiento Civiles Tlaxcala",
        "cpp_tlax": "Procedimiento Penal Tlaxcala",
        "cpeum": "Constitucion",
    }
    for n in nodos:
        partes = str(n).split(":")
        if len(partes) >= 2 and partes[1] in mapa_slug:
            return mapa_slug[partes[1]]
    return "General / Automático"


def generar_resumen_metricas(
    base_dir: Path = DIR_EVAL_DEFAULT,
    guardar_archivos: bool = True,
) -> Dict[str, Any]:
    """
    Calcula todas las métricas cuantitativas y cualitativas de usabilidad
    y validación jurídica a partir de los archivos consolidados.
    """
    base_dir = Path(base_dir)
    ruta_consolidado = base_dir / "evaluaciones_consolidado.json"
    ruta_usuarios = base_dir / "usuarios.json"

    consolidado: Dict[str, Any] = {"sesiones": {}}
    if ruta_consolidado.exists():
        with open(ruta_consolidado, "r", encoding="utf-8") as f:
            consolidado = json.load(f)

    usuarios: Dict[str, Any] = {}
    if ruta_usuarios.exists():
        with open(ruta_usuarios, "r", encoding="utf-8") as f:
            usuarios = json.load(f)

    # 1. Métricas de usuarios por perfil
    usuarios_area_juridica_tlax = 0
    usuarios_generales = 0
    usuarios_por_rol: Dict[str, int] = defaultdict(int)

    for u_data in usuarios.values():
        es_tlax = bool(u_data.get("es_area_juridica_tlaxcala", False))
        if es_tlax:
            usuarios_area_juridica_tlax += 1
        else:
            usuarios_generales += 1
        rol = u_data.get("rol", "Usuario General")
        usuarios_por_rol[rol] += 1

    # 2. Métricas de sesiones y respuestas evaluadas
    sesiones_dict = consolidado.get("sesiones", {})
    total_sesiones = len(sesiones_dict)
    sesiones_finalizadas = 0
    sesiones_activas = 0

    estrellas_globales_experiencia: List[float] = []
    comentarios_experiencia_lista: List[Dict[str, Any]] = []
    sugerencias_futuras_lista: List[Dict[str, Any]] = []

    total_respuestas_evaluadas = 0
    votos_like = 0
    votos_dislike = 0
    estrellas_respuestas: List[float] = []
    tiempos_respuesta: List[float] = []
    nodos_activados_conteo: List[float] = []
    observaciones_juridicas: List[Dict[str, Any]] = []

    desglose_por_perfil: Dict[str, Dict[str, Any]] = {
        "area_juridica_tlaxcala": {
            "respuestas": 0,
            "likes": 0,
            "dislikes": 0,
            "estrellas": [],
        },
        "usuario_general": {
            "respuestas": 0,
            "likes": 0,
            "dislikes": 0,
            "estrellas": [],
        },
    }

    desglose_por_normativa: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"respuestas": 0, "likes": 0, "dislikes": 0, "estrellas": [], "tiempos": [], "nodos": []}
    )

    for ses_id, ses in sesiones_dict.items():
        estado = ses.get("estado", "activa")
        if estado == "finalizada":
            sesiones_finalizadas += 1
        else:
            sesiones_activas += 1

        es_tlax_ses = bool(ses.get("es_area_juridica_tlaxcala", False))
        clave_perfil = "area_juridica_tlaxcala" if es_tlax_ses else "usuario_general"
        evaluador = ses.get("nombre_evaluador") or ses.get("username") or "Anónimo"
        rol_ses = ses.get("rol_usuario", "Usuario General")

        exp = ses.get("experiencia_final") or {}
        calif_exp = exp.get("calificacion_global_estrellas")
        if isinstance(calif_exp, (int, float)):
            estrellas_globales_experiencia.append(float(calif_exp))
        if (exp.get("comentarios_experiencia") or "").strip():
            comentarios_experiencia_lista.append(
                {
                    "sesion_id": ses_id,
                    "evaluador": evaluador,
                    "rol": rol_ses,
                    "es_area_juridica_tlaxcala": es_tlax_ses,
                    "calificacion_global_estrellas": calif_exp,
                    "comentario": exp["comentarios_experiencia"].strip(),
                }
            )
        if (exp.get("sugerencias_correccion_futura") or "").strip():
            sugerencias_futuras_lista.append(
                {
                    "sesion_id": ses_id,
                    "evaluador": evaluador,
                    "rol": rol_ses,
                    "sugerencia": exp["sugerencias_correccion_futura"].strip(),
                }
            )

        for resp in ses.get("respuestas_evaluadas", []):
            total_respuestas_evaluadas += 1
            voto = resp.get("voto")
            est = resp.get("estrellas_0_a_5")
            t_seg = resp.get("tiempo_respuesta_seg")
            nodos = resp.get("nodos_grafo") or []
            normativa = _inferir_area_normativa(resp)

            desglose_por_perfil[clave_perfil]["respuestas"] += 1
            desglose_por_normativa[normativa]["respuestas"] += 1
            desglose_por_normativa[normativa]["nodos"].append(float(len(nodos)))
            nodos_activados_conteo.append(float(len(nodos)))

            if voto == "like":
                votos_like += 1
                desglose_por_perfil[clave_perfil]["likes"] += 1
                desglose_por_normativa[normativa]["likes"] += 1
            elif voto == "dislike":
                votos_dislike += 1
                desglose_por_perfil[clave_perfil]["dislikes"] += 1
                desglose_por_normativa[normativa]["dislikes"] += 1

            if isinstance(est, (int, float)):
                est_f = float(est)
                estrellas_respuestas.append(est_f)
                desglose_por_perfil[clave_perfil]["estrellas"].append(est_f)
                desglose_por_normativa[normativa]["estrellas"].append(est_f)

            if isinstance(t_seg, (int, float)) and t_seg > 0:
                tiempos_respuesta.append(float(t_seg))
                desglose_por_normativa[normativa]["tiempos"].append(float(t_seg))

            corr = (resp.get("correccion_juridica") or "").strip()
            if corr:
                observaciones_juridicas.append(
                    {
                        "sesion_id": ses_id,
                        "id_mensaje": resp.get("id_mensaje", ""),
                        "evaluador": evaluador,
                        "rol": rol_ses,
                        "normativa": normativa,
                        "consulta": resp.get("consulta_origen", ""),
                        "voto": voto,
                        "estrellas": est,
                        "observacion_juridica": corr,
                    }
                )

    total_votos = votos_like + votos_dislike
    tasa_aprobacion_global = round((votos_like / total_votos) * 100, 2) if total_votos > 0 else 0.0

    resumen_perfiles = {}
    for k_p, d_p in desglose_por_perfil.items():
        v_tot = d_p["likes"] + d_p["dislikes"]
        resumen_perfiles[k_p] = {
            "total_respuestas_evaluadas": d_p["respuestas"],
            "likes": d_p["likes"],
            "dislikes": d_p["dislikes"],
            "porcentaje_aprobacion": round((d_p["likes"] / v_tot) * 100, 2) if v_tot > 0 else 0.0,
            "promedio_estrellas": _media(d_p["estrellas"]),
            "desviacion_estandar_estrellas": _desviacion_estandar(d_p["estrellas"]),
        }

    resumen_normativas = {}
    for norm_k, d_n in sorted(desglose_por_normativa.items()):
        v_tot = d_n["likes"] + d_n["dislikes"]
        resumen_normativas[norm_k] = {
            "total_consultas": d_n["respuestas"],
            "likes": d_n["likes"],
            "dislikes": d_n["dislikes"],
            "porcentaje_aprobacion": round((d_n["likes"] / v_tot) * 100, 2) if v_tot > 0 else 0.0,
            "promedio_estrellas": _media(d_n["estrellas"]),
            "desviacion_estandar_estrellas": _desviacion_estandar(d_n["estrellas"]),
            "tiempo_promedio_seg": _media(d_n["tiempos"]),
            "promedio_nodos_grafo": _media(d_n["nodos"]),
        }

    reporte = {
        "generado_en": datetime.now().isoformat(timespec="seconds"),
        "usuarios_registrados": {
            "total": len(usuarios),
            "area_juridica_tlaxcala": usuarios_area_juridica_tlax,
            "usuarios_generales": usuarios_generales,
            "por_rol": dict(usuarios_por_rol),
        },
        "sesiones": {
            "total": total_sesiones,
            "finalizadas": sesiones_finalizadas,
            "activas": sesiones_activas,
        },
        "metricas_globales_respuestas": {
            "total_respuestas_evaluadas": total_respuestas_evaluadas,
            "votos_like": votos_like,
            "votos_dislike": votos_dislike,
            "porcentaje_aprobacion_like": tasa_aprobacion_global,
            "promedio_estrellas_0_a_5": _media(estrellas_respuestas),
            "desviacion_estandar_estrellas": _desviacion_estandar(estrellas_respuestas),
            "tiempo_promedio_respuesta_seg": _media(tiempos_respuesta),
            "promedio_nodos_grafo_activados": _media(nodos_activados_conteo),
        },
        "experiencia_final_conversacion": {
            "total_encuestas_cierre": len(estrellas_globales_experiencia),
            "promedio_calificacion_global_estrellas": _media(estrellas_globales_experiencia),
            "desviacion_estandar_global": _desviacion_estandar(estrellas_globales_experiencia),
            "comentarios_experiencia": comentarios_experiencia_lista,
            "sugerencias_correccion_futura": sugerencias_futuras_lista,
        },
        "desglose_por_perfil_evaluador": resumen_perfiles,
        "desglose_por_normativa": resumen_normativas,
        "observaciones_juridicas_expertos": observaciones_juridicas,
    }

    if guardar_archivos:
        ruta_salida_json = base_dir / "resumen_metricas_usabilidad.json"
        with open(ruta_salida_json, "w", encoding="utf-8") as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2)

        ruta_salida_md = base_dir / "REPORTE_USABILIDAD.md"
        with open(ruta_salida_md, "w", encoding="utf-8") as f:
            f.write(formatear_reporte_markdown(reporte))

    return reporte


def formatear_reporte_markdown(reporte: Dict[str, Any]) -> str:
    """Genera un informe estructurado en formato Markdown con tablas estadísticas."""
    u = reporte["usuarios_registrados"]
    s = reporte["sesiones"]
    m = reporte["metricas_globales_respuestas"]
    e = reporte["experiencia_final_conversacion"]

    lineas = [
        "# Reporte de Pruebas de Usabilidad y Validación Jurídica — LEXIS (Etapa 5)",
        "",
        f"**Fecha de corte:** `{reporte['generado_en']}`",
        "",
        "## 1. Resumen Ejecutivo de Participación y Desempeño",
        "",
        "| Indicador | Valor |",
        "| :--- | :--- |",
        f"| **Usuarios registrados totales** | {u['total']} ({u['area_juridica_tlaxcala']} área jurídica Tlaxcala / {u['usuarios_generales']} usuarios generales) |",
        f"| **Sesiones registradas** | {s['total']} ({s['finalizadas']} finalizadas / {s['activas']} en curso) |",
        f"| **Consultas jurídicas evaluadas** | {m['total_respuestas_evaluadas']} |",
        f"| **Tasa de aprobación (Like vs. Dislike)** | **{m['porcentaje_aprobacion_like']}%** ({m['votos_like']} Like / {m['votos_dislike']} Dislike) |",
        f"| **Calificación promedio por respuesta (0–5 estrellas)** | **{m['promedio_estrellas_0_a_5']} / 5.00** (DE: ±{m['desviacion_estandar_estrellas']}) |",
        f"| **Calificación global de experiencia al cierre (0–5 estrellas)** | **{e['promedio_calificacion_global_estrellas']} / 5.00** (DE: ±{e['desviacion_estandar_global']}) |",
        f"| **Tiempo promedio de respuesta (RAG + GraphRAG + LLM)** | **{m['tiempo_promedio_respuesta_seg']} s** |",
        f"| **Promedio de nodos del grafo jurídico activados por consulta** | **{m['promedio_nodos_grafo_activados']} nodos** |",
        "",
        "## 2. Desglose por Perfil de Evaluador",
        "",
        "| Perfil de Usuario | Consultas Evaluadas | Likes | Dislikes | % Aprobación | Promedio Estrellas (0–5) | Desv. Estándar |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    nombres_perfil = {
        "area_juridica_tlaxcala": "Abogados / Estudiantes de Derecho o afín (Tlaxcala)",
        "usuario_general": "Usuarios Generales / Ciudadanos",
    }
    for k_p, datos_p in reporte["desglose_por_perfil_evaluador"].items():
        lineas.append(
            f"| {nombres_perfil.get(k_p, k_p)} | {datos_p['total_respuestas_evaluadas']} | "
            f"{datos_p['likes']} | {datos_p['dislikes']} | {datos_p['porcentaje_aprobacion']}% | "
            f"{datos_p['promedio_estrellas']} / 5.0 | ±{datos_p['desviacion_estandar_estrellas']} |"
        )

    lineas.extend(
        [
            "",
            "## 3. Desglose por Normativa / Materia Jurídica",
            "",
            "| Normativa / Materia | Consultas | Likes | Dislikes | % Aprobación | Estrellas (0–5) | Tiempo Prom. (s) | Nodos Grafo Prom. |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    for norm_k, datos_n in reporte["desglose_por_normativa"].items():
        lineas.append(
            f"| **{norm_k}** | {datos_n['total_consultas']} | {datos_n['likes']} | {datos_n['dislikes']} | "
            f"{datos_n['porcentaje_aprobacion']}% | {datos_n['promedio_estrellas']} (±{datos_n['desviacion_estandar_estrellas']}) | "
            f"{datos_n['tiempo_promedio_seg']} s | {datos_n['promedio_nodos_grafo']} |"
        )

    lineas.extend(
        [
            "",
            "## 4. Retroalimentación y Observaciones Jurídicas (Licenciados en Derecho y Evaluadores)",
            "",
        ]
    )
    for obs in reporte["observaciones_juridicas_expertos"]:
        lineas.append(
            f"- **[{obs['normativa']}]** *{obs['evaluador']} ({obs['rol']})* — Calificación: `{obs['voto'].upper()}` ({obs['estrellas']}/5 estrellas): "
            f"\"{obs['observacion_juridica']}\" *(Consulta: \"{obs['consulta']}\")*"
        )

    lineas.extend(
        [
            "",
            "## 5. Comentarios de Experiencia Final y Sugerencias de Mejora",
            "",
        ]
    )
    for com in e["comentarios_experiencia"]:
        lineas.append(
            f"- **{com['evaluador']}** (*{com['rol']}*, `{com['calificacion_global_estrellas']}/5 estrellas`): \"{com['comentario']}\""
        )

    if e["sugerencias_correccion_futura"]:
        lineas.append("")
        lineas.append("### Sugerencias para trabajo futuro registradas al cierre:")
        for sug in e["sugerencias_correccion_futura"]:
            lineas.append(f"- **{sug['evaluador']}** (*{sug['rol']}*): \"{sug['sugerencia']}\"")

    lineas.append("")
    return "\n".join(lineas)


if __name__ == "__main__":
    rep = generar_resumen_metricas()
    print(formatear_reporte_markdown(rep))
