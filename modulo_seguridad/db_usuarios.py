# modulo_seguridad/db_usuarios.py
"""Gestión de usuarios, hash de contraseñas y roles para CoralTwin-DT"""
import bcrypt
import datetime

def hash_contraseña(contraseña: str) -> str:
    """Genera hash seguro con bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(contraseña.encode('utf-8'), salt).decode('utf-8')

def verificar_contraseña(contraseña: str, hash_almacenado: str) -> bool:
    """Valida la contraseña contra su hash"""
    try:
        return bcrypt.checkpw(contraseña.encode('utf-8'), hash_almacenado.encode('utf-8'))
    except Exception:
        return False

# Usuarios predeterminados para demostración y evaluación inmediata
USUARIOS_DEMO = {
    "admin": {
        "id_usuario": 1,
        "usuario": "admin",
        "nombre_completo": "Dra. Sofía Alarcón",
        "correo": "admin@coraltwin.org",
        "contraseña_hash": hash_contraseña("AdminCoral2026!"),
        "rol": "administrador",
        "institucion": "NOAA / Coral Reef Watch Consortium",
        "idioma_preferido": "es",
        "tema": "claro"
    },
    "investigador": {
        "id_usuario": 2,
        "usuario": "investigador",
        "nombre_completo": "Dr. Mateo Valdivia",
        "correo": "mvaldivia@oceanresearch.org",
        "contraseña_hash": hash_contraseña("InvestigaCoral123!"),
        "rol": "investigador_marino",
        "institucion": "Instituto de Ciencias del Mar y Limnología",
        "idioma_preferido": "es",
        "tema": "claro"
    },
    "gestor": {
        "id_usuario": 3,
        "usuario": "gestor",
        "nombre_completo": "Lic. Elena Morales",
        "correo": "emorales@coralrestoration.org",
        "contraseña_hash": hash_contraseña("GestionCoral123!"),
        "rol": "gestor_conservacion",
        "institucion": "Red de Áreas Marinas Protegidas del Caribe",
        "idioma_preferido": "es",
        "tema": "claro"
    },
    "consultor": {
        "id_usuario": 4,
        "usuario": "consultor",
        "nombre_completo": "Biól. Lucas Benítez",
        "correo": "lbenitez@ecotour.org",
        "contraseña_hash": hash_contraseña("ConsultaCoral123!"),
        "rol": "consultor_publico",
        "institucion": "Observatorio Ciudadano de Biodiversidad Marina",
        "idioma_preferido": "es",
        "tema": "claro"
    }
}

def buscar_usuario(identificador: str):
    """Busca un usuario por username o correo electrónico"""
    id_lower = identificador.lower().strip()
    for user_key, datos in USUARIOS_DEMO.items():
        if user_key.lower() == id_lower or datos["correo"].lower() == id_lower:
            return datos
    return None

def actualizar_ultimo_acceso(id_usuario: int):
    """Registra marca de tiempo del último acceso"""
    for _, datos in USUARIOS_DEMO.items():
        if datos["id_usuario"] == id_usuario:
            datos["ultimo_acceso"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
