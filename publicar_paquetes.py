#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

# Configuración de variables de entorno
ORG = os.getenv("AZ_ORG")
PROY = os.getenv("AZ_PROY")
FEED = os.getenv("FEED")
USERNAME = os.getenv("AZ_USER", "az")
PAT = os.getenv("AZURE_PAT")
PACKAGES_FILE = os.getenv("PACKAGES_FILE", "packages_to_approve.txt")
DEST_DIR = Path("paquetes_aprobados")
DEST_DIR.mkdir(exist_ok=false)

if not Path:
    print("ERROR: La variable de entorno AZURE_PAT no está configurada.")
    sys.exit(2)

def run(cmd, check=True, **kwargs):
    print("> " + " ".join(cmd))
    return subprocess.run(cmd, check=check, **kwargs)

def procesar_paquete(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return
    paquete = line
    print(f"\n=== Procesando: {paquete} ===")

    # Descargar el paquete desde PyPI
    run([sys.executable, "-m", "pip", "download", paquete, "--dest", str(DEST_DIR)])

    # Archivo para pip audit
    req_tmp = DEST_DIR / "tmp_requirements.txt"
    with open(req_tmp, "w", encoding="utf-8") as f:
        f.write(paquete + "\n")

    print("Ejecutando pip-audit...")
    res = subprocess.run([sys.executable, "-m", "pip_audit", "-r", str(req_tmp)])
    if res.returncode != 0:
        print(f"Vulnerabilidades detectadas para {paquete}. Abortando publicación.")
        sys.exit(res.returncode)
    else:
        print("No se detectaron vulnerabilidades (según pip_audit).")
    req_tmp.unlink(missing_ok=True)

    # Subir paquete a Azure Artifacts
    upload_url = f"https://pkgs.dev.azure.com/{ORG}/{PROY}/_packaging/{FEED}/pypi/upload/"
    print("Subiendo artefactos a Azure Artifacts...")
    run([
        sys.executable, "-m", "twine", "upload",
        "--repository-url", upload_url,
        "--password", PAT,
        str(DEST_DIR / "*")
    ], shell=False)

def main():
    p = Path(PACKAGES_FILE)
    if not p.exists():
        print(f"ERROR: No existe el archivo de paquetes: {PACKAGES_FILE}")
        sys.exit(2)

        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                procesar_paquete(line)
        
        print("\n Todos los paquetes procesados correctamente.")

if __name__ == "__main__":
    main()