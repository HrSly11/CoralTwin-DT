"""
Launcher script para el servidor de Langflow en CoralTwin-DT.
Carga automáticamente las credenciales de .env y levanta el servidor en http://127.0.0.1:7860
"""
import os
import sys
import subprocess
from pathlib import Path

# Cargar variables de entorno desde .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file)
        print(f"[OK] Variables de entorno cargadas desde {env_file}")
    except ImportError:
        pass

os.environ["LANGFLOW_AUTO_LOGIN"] = "true"
os.environ["LANGFLOW_SKIP_AUTH_AUTO_LOGIN"] = "true"

host = os.getenv("LANGFLOW_HOST", "127.0.0.1")
port = os.getenv("LANGFLOW_PORT", "7860")

print("=" * 60)
print(f" Iniciando servidor de Langflow en http://{host}:{port}")
print(" Presiona Ctrl+C en esta consola para detener el servidor.")
print("=" * 60)

cmd = [sys.executable, "-m", "langflow", "run", "--host", host, "--port", port]
try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n[OK] Servidor de Langflow detenido.")
