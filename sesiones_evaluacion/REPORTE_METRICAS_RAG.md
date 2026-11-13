# Reporte de Evaluación Cuantitativa RAG y GraphRAG — LEXIS

**Fecha de ejecución:** `2026-11-12T19:28:45`  
**Dataset Ground Truth:** `24` consultas jurídicas validadas en las 6 leyes (`k = 5`)

## 1. Comparativa de Arquitecturas de Recuperación (`k = 5`)

| Arquitectura Evaluada | Precision@5 | Recall@5 | Hit Rate@5 | MRR | Faithfulness (Fidelidad) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Solo Vectorial / Semántico** | 50.69% | 50.69% | 75.00% | 0.5903 | — |
| **2. Búsqueda Híbrida (Semántico + BM25 + RRF)** | 57.99% | 57.99% | 87.50% | 0.8750 | — |
| **3. Híbrido + GraphRAG (1-hop Grafo Jurídico)** | **72.22%** | **72.22%** | **91.67%** | **0.8819** | **100.00%** |

## 2. Desglose por Normativa (Arquitectura Híbrido + GraphRAG)

| Normativa | Consultas GT | Precision@5 | Recall@5 | Hit Rate@5 | MRR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Codigo Civil Tlaxcala** | 4 | 66.67% | 66.67% | 75.00% | 0.7500 |
| **Constitucion** | 4 | 75.00% | 75.00% | 75.00% | 0.7500 |
| **Código Penal Tlaxcala** | 4 | 79.17% | 79.17% | 100.00% | 0.7917 |
| **Ley Trabajo** | 4 | 79.17% | 79.17% | 100.00% | 1.0000 |
| **Procedimiento Civiles Tlaxcala** | 4 | 62.50% | 62.50% | 100.00% | 1.0000 |
| **Procedimiento Penal Tlaxcala** | 4 | 70.83% | 70.83% | 100.00% | 1.0000 |

## 3. Verificación de Fidelidad al Contexto (Faithfulness)

- **Respuestas generadas auditadas:** 16
- **Citas normativas verificadas contra contexto RAG + GraphRAG:** 29 / 29
- **Índice de Fidelidad (Faithfulness):** **100.00%** (0 alucinaciones normativas detectadas)
