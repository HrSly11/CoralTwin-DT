# config.py
"""
Configuración central del sistema CoralTwin-DT:
Gemelo Digital de Arrecifes de Coral bajo Estrés Térmico y Acidificación Oceánica
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Rutas del Proyecto
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "03_Data"
MODELS_DIR = BASE_DIR / "06_AI_and_Modeling" / "machine_learning" / "saved_models"
GEOSPATIAL_DIR = BASE_DIR / "08_GIS_and_Remote_Sensing" / "geospatial_outputs"
OPERATIONAL_DIR = BASE_DIR / "operational" / "data"

FINAL_DATASET_CSV = DATA_DIR / "final_dataset.csv"
CORALTWIN_DB = OPERATIONAL_DIR / "coraltwin.db"
SPATIAL_RANKING_CSV = GEOSPATIAL_DIR / "spatial_restoration_priority_ranking.csv"
GEOJSON_ZONES = GEOSPATIAL_DIR / "priority_restoration_zones.geojson"

# Configuración de Base de Datos
DB_TIPO = os.getenv("DB_TIPO", "sqlite")
DB_SQLITE_PATH = os.getenv("CORALTWIN_DB_PATH", str(CORALTWIN_DB))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PUERTO = os.getenv("DB_PUERTO", "5432")
DB_NOMBRE = os.getenv("DB_NOMBRE", "coraltwin")
DB_USUARIO = os.getenv("DB_USUARIO", "postgres")
DB_CONTRASEÑA = os.getenv("DB_CONTRASEÑA", "")

# Configuración de la Aplicación
TITULO_SISTEMA_ES = "CoralTwin-DT — Gemelo Digital de Arrecifes de Coral"
TITULO_SISTEMA_EN = "CoralTwin-DT — Digital Twin of Coral Reefs"
SUBTITULO_ES = "Priorización de Restauración y Conservación bajo Estrés Térmico y Acidificación"
SUBTITULO_EN = "Restoration and Conservation Prioritization under Thermal Stress and Ocean Acidification"

IDIOMA_POR_DEFECTO = os.getenv("IDIOMA_POR_DEFECTO", "es")
TEMA_POR_DEFECTO = os.getenv("TEMA_POR_DEFECTO", "claro")

# Umbrales Científicos NOAA y Biogeoquímicos
UMBRAL_DHW_WATCH = 1.0       # °C-semanas
UMBRAL_DHW_WARNING = 4.0     # Riesgo de blanqueamiento significativo
UMBRAL_DHW_ALERT1 = 8.0      # Blanqueamiento masivo severo
UMBRAL_DHW_ALERT2 = 12.0     # Mortalidad coralina catastrófica

PH_LINEA_BASE = 8.10
PH_CRITICO_ACIDIFICACION = 7.80
OMEGA_ARAGONITA_CRITICO = 3.0

# Metadatos Científicos
ATTRIBUTION_TEXT = "Resultado obtenido mediante prototipo computacional del gemelo digital CoralTwin-DT."
TARGET_JOURNAL = "Ecological Informatics (Q1)"
VERSION = "1.0.0"
