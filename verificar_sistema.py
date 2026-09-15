# ==========================================================
# SCRIPT DE VERIFICACIÓN AUTOMÁTICA DEL SISTEMA CORALTWIN-DT
# Revisa estructura de módulos, sintaxis Python y dependencias
# Ejecutar: python verificar_sistema.py
# ==========================================================
import os
import sys
import ast
from pathlib import Path

# Configurar encoding seguro para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

class Colores:
    OK = "✅"
    FALLA = "❌"
    ADVERTENCIA = "⚠️"
    INFO = "ℹ️"
    RESET = ""

ESTRUCTURA_ESPERADA = {
    "archivos_raiz": [
        "app.py",
        "config.py",
        "requirements.txt",
        "verificar_sistema.py",
        "INSTALACION.md"
    ],
    "modulo_seguridad": [
        "__init__.py",
        "auth.py",
        "roles_permisos.py",
        "db_usuarios.py",
        "decoradores.py"
    ],
    "modulo_base_datos": [
        "__init__.py",
        "conexion.py",
        "repositorio_arrecifes.py"
    ],
    "modulo_simulacion": [
        "__init__.py",
        "motor_biofisico.py",
        "escenarios_ipcc.py",
        "intervenciones.py",
        "evaluacion_hipotesis.py"
    ],
    "modulo_ia": [
        "__init__.py",
        "inferencia.py",
        "explicabilidad.py",
        "analisis_exploratorio.py"
    ],
    "modulo_visualizacion_3d": [
        "__init__.py",
        "mapa_arrecifes.py",
        "arrecife_3d.py"
    ],
    "modulo_reportes": [
        "__init__.py",
        "reporte_pdf.py",
        "reporte_word.py",
        "reporte_excel.py",
        "generador.py"
    ],
    "modulo_chatbot": [
        "__init__.py",
        "asistente_ecologico.py",
        "interfaz_chat.py"
    ],
    "modulo_idioma": [
        "__init__.py",
        "textos_es.py",
        "textos_en.py"
    ],
    "utilidades": [
        "__init__.py",
        "validadores.py"
    ]
}

resultados = {"existen": [], "faltan": [], "sintaxis_ok": [], "sintaxis_error": []}

def revisar_archivos():
    print(f"\n{Colores.INFO} REVISANDO ESTRUCTURA DE ARCHIVOS CORALTWIN-DT\n")
    for archivo in ESTRUCTURA_ESPERADA["archivos_raiz"]:
        if Path(archivo).exists():
            resultados["existen"].append(archivo)
            print(f"  {Colores.OK} {archivo}")
        else:
            resultados["faltan"].append(archivo)
            print(f"  {Colores.FALLA} {archivo} — FALTANTE")

    for carpeta, archivos in ESTRUCTURA_ESPERADA.items():
        if carpeta == "archivos_raiz":
            continue
        print(f"\n📁 {carpeta}/")
        for arch in archivos:
            ruta = Path(carpeta) / arch
            if ruta.exists():
                resultados["existen"].append(str(ruta))
                print(f"  {Colores.OK} {arch}")
            else:
                resultados["faltan"].append(str(ruta))
                print(f"  {Colores.FALLA} {arch} — FALTANTE")

def revisar_sintaxis():
    print(f"\n{Colores.INFO} REVISANDO SINTAXIS DE ARCHIVOS PYTHON\n")
    archivos_py = list(Path(".").rglob("*.py"))
    # Excluir carpetas temporales o virtuales
    archivos_filtrados = [p for p in archivos_py if not any(part.startswith(".") or part == "venv" or part == "build" for part in p.parts)]
    
    for ruta in archivos_filtrados:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                codigo = f.read()
            ast.parse(codigo, filename=str(ruta))
            resultados["sintaxis_ok"].append(str(ruta))
            print(f"  {Colores.OK} {ruta}")
        except SyntaxError as e:
            resultados["sintaxis_error"].append({"archivo": str(ruta), "error": str(e)})
            print(f"  {Colores.FALLA} {ruta} -> {e}")

def revisar_dependencias():
    print(f"\n{Colores.INFO} VERIFICANDO DEPENDENCIAS PRINCIPALES\n")
    paquetes_clave = [
        "streamlit", "pandas", "numpy", "scikit-learn", "xgboost",
        "plotly", "reportlab", "docx", "openpyxl", "bcrypt", "scipy"
    ]
    for paquete in paquetes_clave:
        try:
            if paquete == "docx":
                import docx
            elif paquete == "scikit-learn":
                import sklearn
            else:
                __import__(paquete.replace("-", "_"))
            print(f"  {Colores.OK} {paquete}")
        except ImportError:
            print(f"  {Colores.ADVERTENCIA} {paquete} — NO INSTALADO")

def resumen():
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN DE VERIFICACIÓN — CORALTWIN-DT")
    print(f"{'='*60}")
    print(f"{Colores.OK} Archivos presentes:     {len(resultados['existen'])}")
    print(f"{Colores.FALLA} Archivos faltantes:     {len(resultados['faltan'])}")
    print(f"{Colores.OK} Sintaxis correcta:      {len(resultados['sintaxis_ok'])}")
    print(f"{Colores.FALLA} Errores de sintaxis:    {len(resultados['sintaxis_error'])}")
    
    if len(resultados['faltan']) == 0 and len(resultados['sintaxis_error']) == 0:
        print(f"\n{Colores.OK}{Colores.OK} SISTEMA VERIFICADO — TODO OPERATIVO {Colores.OK}")
        print("\n🚀 Para iniciar la aplicación: streamlit run app.py")
    else:
        print(f"\n{Colores.ADVERTENCIA} Corregir los elementos marcados antes de iniciar.")

if __name__ == "__main__":
    revisar_archivos()
    revisar_sintaxis()
    revisar_dependencias()
    resumen()
