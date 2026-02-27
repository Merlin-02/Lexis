# LEXIS: Sistema de Asistencia Legal Automatizada con IA ⚖️🤖

![Status](https://img.shields.io/badge/Status-En%20Desarrollo-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![NLP](https://img.shields.io/badge/AI-Procesamiento_de_Lenguaje_Natural-green)

## 📖 Descripción del Proyecto

El presente proyecto, denominado **LEXIS**, propone el desarrollo de un sistema de asistencia legal automatizada impulsado por inteligencia artificial. Concebido bajo los principios de accesibilidad, versatilidad y eficiencia, el sistema está capacitado para abordar problemáticas jurídicas recurrentes en los ámbitos **penal, civil y laboral**. 

La finalidad de LEXIS es democratizar el acceso a la información jurídica, reduciendo significativamente las brechas económicas, geográficas y de conocimiento, para dotar a la población de respuestas precisas, de fácil comprensión y en una etapa de primer contacto.

## 🎯 Objetivos

### Objetivo General
Desarrollar e implementar un sistema de asistencia legal automatizada basado en inteligencia artificial, con el propósito de proporcionar orientación jurídica accesible, precisa y de primer contacto, contribuyendo así a la reducción de las brechas en el acceso a la justicia.

### Objetivos Específicos
1. **Sistematización Legal:** Conformar un corpus legal especializado estructurando la normativa y jurisprudencia (con enfoque en la legislación mexicana vigente) para asegurar la precisión y actualización de la información.
2. **Desarrollo del Modelo:** Integrar un modelo de Inteligencia Artificial basado en algoritmos de Procesamiento de Lenguaje Natural (PLN), capaz de interpretar consultas en lenguaje cotidiano y generar respuestas jurídicas coherentes.
3. **Plataforma Accesible:** Implementar y validar una plataforma digital intuitiva, diseñada para mitigar las barreras de entrada técnicas y económicas para los usuarios.

## ⚙️ Arquitectura y Tecnologías Propuestas (PROTOTIPO)

* **Lenguaje Core:** Python 3.8+
* **Inteligencia Artificial (NLP):** Transformers (Hugging Face), spaCy, NLTK
* **Backend / API:** FastAPI / Flask
* **Frontend:** React / Vue.js / Streamlit
* **Base de Datos:** PostgreSQL / MongoDB

## 📂 Estructura del Repositorio (PROTOTIPO)

```text
LEXIS/
│
├── data/                  # Corpus legal estructurado (Leyes, códigos, jurisprudencia)
├── models/                # Modelos de NLP entrenados y pesos
├── notebooks/             # Jupyter notebooks para análisis exploratorio y pruebas de modelos
├── src/                   # Código fuente de la aplicación
│   ├── nlp_engine/        # Scripts de procesamiento de lenguaje natural
│   ├── api/               # Controladores y rutas de la API (Backend)
│   └── utils/             # Funciones auxiliares y de limpieza de texto
├── docs/                  # Documentación técnica y académica del proyecto
├── requirements.txt       # Dependencias del proyecto
└── README.md              # Este archivo
```

## 🚀 Instalación y Uso (Entorno de Desarrollo)

### 1. Clona este repositorio:
```bash
git clone https://github.com/Merlin-02/Lexis.git

cd LEXIS
```

### 2. Crea y activa un entorno virtual: (PROTOTIPO)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

### 4. Ejecuta el servidor de desarrollo:
```bash
uvicorn src.api.main:app --reload
```

## ⚠️ Aviso Legal y Limitación de Alcance

**LEXIS** es una herramienta tecnológica diseñada exclusivamente para fines de orientación e información jurídica de primer contacto. **Bajo ninguna circunstancia las respuestas generadas por este sistema de inteligencia artificial sustituyen el consejo, la representación o el diagnóstico formal de un profesional del derecho (abogado) debidamente acreditado.** En caso de requerir iniciar un proceso judicial o enfrentar una situación legal crítica, el sistema recomendará al usuario buscar asesoría legal profesional.

