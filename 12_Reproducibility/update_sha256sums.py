"""
12_Reproducibility/update_sha256sums.py
=======================================
Updates `verify_release.sh` (with strict LF line endings) and recomputes
`SHA256SUMS` across all required release artifacts for CoralTwin-DT v2.1.0.
"""

import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
PUB_DIR = r"c:\Users\Harry\Documents\CICLO 8\ING SOFT II\GRUPO28_RodríguezSandoval\publicacion"

VERIFY_RELEASE_SH = """#!/usr/bin/env bash
# =============================================================================
# CoralTwin-DT v2.1.0 — Clean Release & Reproducibility Verification Script
# =============================================================================
# Validates:
#   1. Pinned SHA-256 digest in Dockerfile
#   2. Python environment & core scientific dependencies
#   3. Existence and non-emptiness of all FASE 1–FASE 8 & BLOQUE 1–6 deliverables
#   4. Reference & banned-string audit (0 orphans, 0 uncited, 0 banned terms)
#   5. End-to-end consistency report (0 discrepancies) & pipeline log (v4)
#   6. Cryptographic SHA-256 checksums against SHA256SUMS
# =============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "============================================================================="
echo " CoralTwin-DT v2.1.0 Release Verification"
echo " Workspace: $ROOT_DIR"
echo "============================================================================="

echo "[1/6] Checking Dockerfile pinned SHA-256 digest..."
if ! grep -q "^FROM python:3.11-slim@sha256:[0-9a-f]\\{64\\}" Dockerfile; then
    echo "ERROR: Dockerfile does not contain a pinned 64-hex SHA-256 digest!"
    exit 1
fi
grep "^FROM " Dockerfile

echo "[2/6] Verifying Python environment and required packages..."
python -c "
import docx, pandas, xgboost, shap, torch, sklearn, scipy
print('  Python packages verified:', {
    'python-docx': docx.__version__,
    'pandas': pandas.__version__,
    'xgboost': xgboost.__version__,
    'shap': shap.__version__,
    'torch': torch.__version__,
    'scikit-learn': sklearn.__version__,
    'scipy': scipy.__version__,
})
"

echo "[3/6] Verifying existence of all required v2.1.0 scripts, datasets, figures, and manuscript files..."
REQUIRED_FILES=(
    "01_Data/calibrate_generator_to_noaa.py"
    "03_Data/calibrate_generator_to_noaa.py"
    "03_Data/final_dataset.csv"
    "03_Data/final_dataset_noaa_calibrated.csv"
    "07_Scenarios_and_Simulations/s4_factor_isolation.py"
    "08_GIS_and_Remote_Sensing/srpi_sensitivity.py"
    "09_Results/audit_references.py"
    "09_Results/build_manuscript_numbers.py"
    "09_Results/build_v3_docx.py"
    "09_Results/build_consistency_report.py"
    "results/noaa_calibration_metrics.csv"
    "results/noaa_calibration_summary.json"
    "results/s4_factor_isolation.csv"
    "results/s4_factor_isolation_variants.csv"
    "results/s4_factor_isolation_shapley.csv"
    "results/s4_factor_isolation_anova_sobol.csv"
    "results/srpi_sensitivity.csv"
    "results/srpi_bootstrap_10000.csv"
    "results/srpi_loso_sensitivity.csv"
    "results/references_audit.csv"
    "references_audit.csv"
    "results/manuscript_numbers.json"
    "results/pipeline_execution_log_v4.json"
    "figures/fig_noaa_calibration_v3.png"
    "Grupo28B_RodriguezSandoval_HarrySly_corregido.docx"
    "Grupo28B_RodriguezSandoval_HarrySly_corregido_v2.docx"
    "Grupo28B_RodriguezSandoval_HarrySly_v3.docx"
    "Grupo28B_RodriguezSandoval_HarrySly_v3_trackchanges_report.md"
    "response_to_reviewer_v3.md"
    "consistency_report.md"
    "Dockerfile"
    "SHA256SUMS"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [[ ! -s "$f" ]]; then
        echo "ERROR: Missing or empty required artifact: $f"
        exit 1
    fi
done
echo "  All ${#REQUIRED_FILES[@]} required artifacts exist and are non-empty."

echo "[4/6] Verifying citation & banned-string audit on Grupo28B_RodriguezSandoval_HarrySly_v3.docx..."
python 09_Results/audit_references.py
python -c "
import json
with open('results/references_audit_summary.json', encoding='utf-8') as f:
    s = json.load(f)
assert s['orphan_citations_count'] == 0, f'Orphan citations found: {s}'
assert s['uncited_references_count'] == 0, f'Uncited references found: {s}'
for k, v in s['banned_terms_occurrences'].items():
    assert v == 0, f'Banned string {k} has count {v}'
print('  Audit assertions passed: 0 orphans, 0 uncited, 0 banned strings.')
"

echo "[5/6] Verifying consistency_report.md (0 discrepancies) and pipeline execution log (results/pipeline_execution_log_v4.json)..."
python 09_Results/build_consistency_report.py
python -c "
import json
with open('results/pipeline_execution_log_v4.json', encoding='utf-8') as f:
    log = json.load(f)
assert log['all_steps_succeeded'] is True, 'Pipeline did not succeed on all steps!'
print(f\\"  Pipeline log verified: {log['total_steps']} steps succeeded in {log['total_elapsed_seconds']}s.\\")
"

echo "[6/6] Verifying cryptographic checksums against SHA256SUMS..."
python -c "
import hashlib, sys
with open('SHA256SUMS', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
for line in lines:
    expected_hash, rel_path = line.split(None, 1)
    rel_path = rel_path.lstrip('*')
    h = hashlib.sha256()
    with open(rel_path, 'rb') as fp:
        for chunk in iter(lambda: fp.read(65536), b''):
            h.update(chunk)
    actual_hash = h.hexdigest()
    if actual_hash != expected_hash:
        print(f'ERROR: SHA-256 mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}')
        sys.exit(1)
print(f'  All {len(lines)} SHA-256 checksums in SHA256SUMS matched bit-for-bit.')
"

echo "============================================================================="
echo " VERIFICATION PASSED: CoralTwin-DT v2.1.0 is 100% reproducible and verified."
echo "============================================================================="
"""

SHA256_FILES = [
    "01_Data/calibrate_generator_to_noaa.py",
    "03_Data/calibrate_generator_to_noaa.py",
    "03_Data/final_dataset.csv",
    "03_Data/final_dataset_noaa_calibrated.csv",
    "07_Scenarios_and_Simulations/s4_factor_isolation.py",
    "08_GIS_and_Remote_Sensing/srpi_sensitivity.py",
    "09_Results/audit_references.py",
    "09_Results/build_manuscript_numbers.py",
    "09_Results/build_v3_docx.py",
    "09_Results/build_consistency_report.py",
    "results/noaa_calibration_metrics.csv",
    "results/noaa_calibration_summary.json",
    "results/s4_factor_isolation.csv",
    "results/s4_factor_isolation_variants.csv",
    "results/s4_factor_isolation_shapley.csv",
    "results/s4_factor_isolation_anova_sobol.csv",
    "results/srpi_sensitivity.csv",
    "results/srpi_bootstrap_10000.csv",
    "results/srpi_loso_sensitivity.csv",
    "results/references_audit.csv",
    "references_audit.csv",
    "results/manuscript_numbers.json",
    "results/pipeline_execution_log_v3.json",
    "results/pipeline_execution_log_v4.json",
    "figures/fig_noaa_calibration_v3.png",
    "Grupo28B_RodriguezSandoval_HarrySly_corregido.docx",
    "Grupo28B_RodriguezSandoval_HarrySly_corregido_v2.docx",
    "Grupo28B_RodriguezSandoval_HarrySly_v3.docx",
    "Grupo28B_RodriguezSandoval_HarrySly_v3_trackchanges_report.md",
    "response_to_reviewer_v3.md",
    "consistency_report.md",
    "Dockerfile",
    "verify_release.sh",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    v_path = os.path.join(PROJECT_ROOT, "verify_release.sh")
    with open(v_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(VERIFY_RELEASE_SH)

    lines = []
    for rel in SHA256_FILES:
        abs_p = os.path.join(PROJECT_ROOT, rel)
        digest = sha256_file(abs_p)
        lines.append(f"{digest}  {rel}")

    sha_content = "\n".join(lines) + "\n"
    sha_path = os.path.join(PROJECT_ROOT, "SHA256SUMS")
    with open(sha_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(sha_content)

    if os.path.exists(PUB_DIR):
        with open(os.path.join(PUB_DIR, "verify_release.sh"), "w", encoding="utf-8", newline="\n") as f:
            f.write(VERIFY_RELEASE_SH)
        with open(os.path.join(PUB_DIR, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
            f.write(sha_content)

    print(f"Updated verify_release.sh and SHA256SUMS ({len(lines)} artifacts).")


if __name__ == "__main__":
    main()
