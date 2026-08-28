# Zenodo Repository Metadata & DOI Archiving Specification

**Archive Target:** Zenodo Open-Science Repository (CERN / OpenAIRE)  
**Project:** CoralTwin-DT (Cyber-Physical Environmental Digital Twin)  
**Release Tag:** `v1.0.0`  
**Target DOI Placeholder:** `10.5281/zenodo.10275001`  
**License:** Open Access (MIT License)  

---

## 1. Zenodo Deposit Metadata (JSON / Form Specification)

```json
{
  "title": "CoralTwin-DT: A Cyber-Physical Digital Twin Coupling Machine Learning and Dynamical Biophysics for Coral Reef Restoration Prioritization under Thermal Stress and Ocean Acidification",
  "upload_type": "software",
  "publication_date": "2026-08-27",
  "creators": [
    {
      "name": "CoralTwin-DT Doctoral Research Consortium",
      "affiliation": "Computational Oceanography & Ecological Informatics Laboratory",
      "orcid": "0000-0002-1825-0097"
    }
  ],
  "description": "<p><strong>CoralTwin-DT</strong> is an open-source, cyber-physical digital twin engineered to model, forecast, and spatially prioritize coral reef restoration and conservation interventions under compounding marine heatwaves (MHWs) and ocean acidification.</p><p>The repository contains the complete 14-module codebase, harmonized spatio-temporal datasets (N = 15,000 observations across 30 global benchmark stations), serialized machine learning models (XGBoost, Random Forest, Deep MLP, LSTM), TreeSHAP game-theoretic explainability routines, coupled Mumby ordinary differential equations (ODEs) forward decadal simulations (2025–2050), and open RFC-7946 GeoJSON spatial prioritization layers.</p><p><em>Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.</em></p>",
  "access_right": "open",
  "license": "MIT",
  "keywords": [
    "Digital Twin",
    "Coral Bleaching",
    "Ocean Acidification",
    "Degree Heating Weeks",
    "XGBoost",
    "TreeSHAP",
    "Ecological Informatics",
    "Restoration Ecology",
    "Marine Protected Areas",
    "Sentinel-2",
    "NOAA Coral Reef Watch",
    "Mumby Differential Model",
    "Spatial Prioritization",
    "FAIR Data"
  ],
  "related_identifiers": [
    {
      "identifier": "https://github.com/HrSly11/CoralTwin-DT",
      "relation": "isSupplementTo",
      "scheme": "url"
    }
  ],
  "version": "1.0.0",
  "language": "eng"
}
```

---

## 2. Zenodo Direct Archival Instructions

To archive a release snapshot on Zenodo:
1. Navigate to [https://zenodo.org/account/settings/github/](https://zenodo.org/account/settings/github/).
2. Enable the toggle switch for repository `HrSly11/CoralTwin-DT`.
3. Create an official Release on GitHub using tag `v1.0.0`.
4. Zenodo will automatically archive the repository zip, assign a persistent DOI, and index the software in OpenAIRE.
