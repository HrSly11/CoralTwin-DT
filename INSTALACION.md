# 🪸 GUÍA DE INSTALACIÓN Y PUESTA EN MARCHA — CORALTWIN-DT

Sistema de Gemelo Digital de Arrecifes de Coral bajo Estrés Térmico y Acidificación Oceánica para la Priorización de Restauración y Conservación.

---

## 📋 Requisitos Previos

- **Python:** 3.10 o superior (verificado con Python 3.11 de 64-bit)
- **Navegador Web:** Chrome, Edge, Firefox, Brave o Safari
- **Memoria RAM:** Mínimo 4 GB (8 GB recomendado)

---

## 🚀 Paso 1: Acceder al Proyecto

```bash
cd CoralTwin-DT
```

---

## 📦 Paso 2: Verificar Dependencias

El sistema utiliza las librerías científicas del entorno global (`streamlit`, `pandas`, `numpy`, `scikit-learn`, `xgboost`, `plotly`, `reportlab`, `python-docx`, `openpyxl`, `bcrypt`, `scipy`).

Si necesita instalar o actualizar:
```bash
pip install -r requirements.txt
```

---

## 🧪 Paso 3: Diagnóstico Automático del Sistema

Ejecute el script de verificación integral para validar estructura, sintaxis y módulos:

```bash
python verificar_sistema.py
```

Debe mostrar todos los indicadores en verde ✅.

---

## 🎯 Paso 4: Iniciar la Aplicación Web

```bash
streamlit run app.py
```

Para forzar un puerto específico (por ejemplo, el puerto 8503 si 8501 y 8502 están en uso por los otros dos gemelos):

```bash
streamlit run app.py --server.port 8503
```

El navegador abrirá automáticamente la aplicación en `http://localhost:8503`.

---

## 👤 Credenciales de Acceso por Defecto

| Rol | Usuario | Contraseña | Capacidades |
|---|---|---|---|
| 👑 **Administrador** | `admin` | `AdminCoral2026!` | Acceso irrestricto, configuración y sincronización |
| 🔬 **Investigador Marino** | `investigador` | `InvestigaCoral123!` | Simulación biofísica ODEs, modelos IA y evaluación de hipótesis |
| 🛡️ **Gestor de AMP** | `gestor` | `GestionCoral123!` | Priorización espacial SRPI y carteras de restauración |
| 🌍 **Consultor Público** | `consultor` | `ConsultaCoral123!` | Visualización 3D, mapa de estaciones y reportes ejecutivos |

---

## 🛠️ Solución de Problemas Frecuentes

| Síntoma | Diagnóstico | Solución |
|---|---|---|
| Puerto 8501 ocupado | Otro gemelo está ejecutándose en 8501 | Ejecutar con `--server.port 8503` |
| Caracteres extraños en terminal Windows | Problema de página de código cp1252 | Ejecutar `$env:PYTHONIOENCODING="utf-8"` en PowerShell |
| Modelos de IA no cargan | Falta paquete `joblib` o `xgboost` | Ejecutar `pip install joblib xgboost` |
