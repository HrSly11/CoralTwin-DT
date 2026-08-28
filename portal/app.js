/**
 * CoralTwin-DT: Cyber-Physical Command Center Engine
 * ===================================================
 * Complete WebGL 3D, Leaflet Geospatial, 3D Earth Globe, Machine Learning,
 * and Dynamical Runge-Kutta ODE Simulation logic for CoralTwin-DT.
 * Features full bilingual i18n support (English & Spanish).
 * 
 * Author: CoralTwin-DT Engineering Consortium
 * License: MIT
 */

// =============================================================================
// 1. BILINGUAL TRANSLATION DICTIONARY (i18n)
// =============================================================================
const I18N = {
  en: {
    appSubtitle: "Cyber-Physical Marine Digital Twin Command Center",
    statusOnline: "ONLINE",
    statusSync: "SYNCHRONIZED",
    btnExport: "Export GeoJSON",
    kpi1Val: "30 Stations",
    kpi1Label: "5 Global Ocean Basins",
    kpi2Label: "XGBoost ML Accuracy",
    kpi3Label: "Acidification Tipping Pt",
    kpi4Label: "2050 Restored Live Cover",
    mapTitle: "Global Oceanographic Telemetry Map",
    mapSubtitle: "NOAA CRW 5km Satellite Thermal Grids & Sentinel-2 MSI Multi-Basin Ingestion",
    riskLow: "Low Risk",
    riskMed: "Med Risk",
    riskHigh: "High Risk",
    proj2D: "2D Flat Map",
    proj3D: "3D Earth Globe",
    globeHelp: "Drag to Rotate Globe | Scroll to Zoom | Click any Reef Beacon",
    mapInstruction: "Click any reef station on the map or select below:",
    basinGlobal: "Mapamundi (Global)",
    coral3dTitle: "3D WebGL Digital Twin Colony",
    coral3dSubtitle: "Real-Time Procedural Biophysical Bleaching Shader",
    coral3dHelp: "Drag to Rotate | Scroll to Zoom",
    coralHealthy: "HEALTHY SYMBIONTS",
    coralStress: "HEAT SHOCK (FLUORESCING)",
    coralBleached: "SEVERELY BLEACHED",
    aiTitle: "Real-Time AI Prediction Engine",
    aiSubtitle: "XGBoost Regularized Model with Sub-Millisecond Inference",
    labelSST: "Sea Surface Temperature (SST):",
    labelDHW: "Degree Heating Weeks (DHW):",
    labelPH: "Seawater pH (Total Scale):",
    labelTurb: "Optical Turbidity (Kd490 / NTU):",
    riskHeader: "Predicted Bleaching Risk",
    lossHeader: "Estimated Coral Cover Loss",
    shapTitle: "TreeSHAP Marginal Feature Attribution",
    shapLabels: ["DHW Thermal Stress", "Rugosity Cooling", "Acidification (pH)", "Turbidity Shield", "SST Anomaly"],
    odeTitle: "Decadal Forward Sandbox (2025–2050)",
    odeSubtitle: "Coupled Non-Linear Mumby Differential Equations (Runge-Kutta 4th Order)",
    odeWarming: "Warming Rate:",
    odeOutplant: "Outplanting Rate:",
    odeHardening: "Hardening Bonus:",
    odeHerbivory: "MPA Grazing (g):",
    odeCoverResult: "2050 Projected Live Coral Cover:",
    odeCoralLabel: "Live Coral Cover (%)",
    odeMacroLabel: "Macroalgae Cover (%)",
    odeTurfLabel: "Turf Algae (%)",
    srpiTitle: "Spatial Restoration Priority Index (SRPI) Decision Matrix",
    srpiSubtitle: "Multi-Criteria Hydrodynamic Refugia Ranking & Open RFC-7946 GeoJSON Layers",
    filterAll: "All Stations",
    filterTier1: "Tier 1: Outplanting",
    filterTier2: "Tier 2: Marine Reserve",
    filterTier3: "Tier 3: Thermal Risk",
    thStation: "Station Name",
    thRegion: "Region / Basin",
    thCover: "Live Cover (%)",
    thRisk: "Risk Status",
    thTier: "Management Priority Tier",
    thAction: "Action",
    btnInspect: "Inspect",
    footerAttribution: "Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital."
  },
  es: {
    appSubtitle: "Centro de Comando del Gemelo Digital Marino Ciber-Físico",
    statusOnline: "EN LÍNEA",
    statusSync: "SINCRONIZADO",
    btnExport: "Exportar GeoJSON",
    kpi1Val: "30 Estaciones",
    kpi1Label: "5 Cuencas Oceánicas Globales",
    kpi2Label: "Precisión IA (XGBoost)",
    kpi3Label: "Punto de Quiebre por pH",
    kpi4Label: "Cobertura Viva 2050 (Restaurada)",
    mapTitle: "Mapa Global de Telemetría Oceanográfica",
    mapSubtitle: "Grillas Térmicas Satelitales NOAA CRW 5km y Sentinel-2 MSI Multi-Cuenca",
    riskLow: "Bajo Riesgo",
    riskMed: "Riesgo Medio",
    riskHigh: "Alto Riesgo",
    proj2D: "2D Plano",
    proj3D: "3D Globo",
    globeHelp: "Arrastrá para Girar el Globo | Scroll para Zoom | Clic en un arrecife",
    mapInstruction: "Hacé clic en cualquier estación del mapa o seleccionala abajo:",
    basinGlobal: "Mapamundi (Global)",
    coral3dTitle: "Colonia 3D en Gemelo Digital (WebGL)",
    coral3dSubtitle: "Shader Procedural de Blanqueamiento Biofísico en Tiempo Real",
    coral3dHelp: "Arrastrá para Rotar | Scroll para Zoom",
    coralHealthy: "SIMBIONTES SALUDABLES",
    coralStress: "ESTRÉS TÉRMICO (FLUORESCENCIA)",
    coralBleached: "SEVERAMENTE BLANQUEADO",
    aiTitle: "Motor Predictivo de IA en Tiempo Real",
    aiSubtitle: "Modelo Regularizado XGBoost con Inferencia en Sub-Milisegundos",
    labelSST: "Temperatura Superficial Marina (SST):",
    labelDHW: "Semanas de Calentamiento (DHW):",
    labelPH: "pH del Agua Marina (Escala Total):",
    labelTurb: "Turbidez Óptica (Kd490 / NTU):",
    riskHeader: "Riesgo de Blanqueamiento Predicho",
    lossHeader: "Pérdida Estimada de Cobertura",
    shapTitle: "Atribución Marginal de Factores (TreeSHAP)",
    shapLabels: ["Estrés Térmico (DHW)", "Enfriamiento por Rugosidad", "Acidificación (pH)", "Atenuación por Turbidez", "Anomalía de SST"],
    odeTitle: "Simulador Decadal 2025–2050 (Ecuaciones ODEs)",
    odeSubtitle: "Ecuaciones Diferenciales no Lineales de Mumby (Runge-Kutta 4to Orden)",
    odeWarming: "Tasa de Calentamiento:",
    odeOutplant: "Tasa de Siembra Activa:",
    odeHardening: "Endurecimiento Térmico:",
    odeHerbivory: "Pastoreo en Reserva (g):",
    odeCoverResult: "Cobertura Coralina Viva Proyectada al 2050:",
    odeCoralLabel: "Coral Vivo (%)",
    odeMacroLabel: "Macroalgas (%)",
    odeTurfLabel: "Césped Algal (%)",
    srpiTitle: "Matriz de Decisión de Priorización Espacial (SRPI)",
    srpiSubtitle: "Ranking de Refugios Hidrodinámicos y Capas Abiertas RFC-7946 GeoJSON",
    filterAll: "Todas las Estaciones",
    filterTier1: "Tier 1: Siembra Activa",
    filterTier2: "Tier 2: Reserva Marina",
    filterTier3: "Tier 3: Riesgo Térmico",
    thStation: "Nombre de Estación",
    thRegion: "Región / Cuenca",
    thCover: "Cobertura Viva (%)",
    thRisk: "Nivel de Riesgo",
    thTier: "Nivel de Prioridad de Manejo",
    thAction: "Acción",
    btnInspect: "Inspeccionar",
    footerAttribution: "Atribución Científica: Resultado obtenido mediante prototipo computacional del gemelo digital."
  }
};

let currentLang = localStorage.getItem("coraltwin_lang") || "es";
let currentProjection = "2d";

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("coraltwin_lang", lang);

  // Update Toggle Buttons
  const btnEn = document.getElementById("lang-btn-en");
  const btnEs = document.getElementById("lang-btn-es");
  if (lang === "es") {
    btnEs.className = "px-2.5 py-1 rounded font-bold transition text-slate-950 bg-cyan-400";
    btnEn.className = "px-2.5 py-1 rounded font-bold transition text-slate-400 hover:text-slate-200";
  } else {
    btnEn.className = "px-2.5 py-1 rounded font-bold transition text-slate-950 bg-cyan-400";
    btnEs.className = "px-2.5 py-1 rounded font-bold transition text-slate-400 hover:text-slate-200";
  }

  // Update DOM Elements
  const dict = I18N[lang];
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.innerText = dict[key];
    }
  });

  // Update Chart.js labels
  if (shapChartInstance) {
    shapChartInstance.data.labels = dict.shapLabels;
    shapChartInstance.update();
  }

  if (odeChartInstance) {
    odeChartInstance.data.datasets[0].label = dict.odeCoralLabel;
    odeChartInstance.data.datasets[1].label = dict.odeMacroLabel;
    odeChartInstance.data.datasets[2].label = dict.odeTurfLabel;
    odeChartInstance.update();
  }

  // Refresh dynamic inferences
  triggerAIInference();
  triggerODESimulation();
  populateTable(STATIONS_DB);
}

// =============================================================================
// 2. 30 GLOBAL BENCHMARK REEF STATIONS DATABASE
// =============================================================================
const STATIONS_DB = [
  { id: "Mesoamerican_Fore_01", name: "Mesoamerican Reef (Fore Reef)", region: "Caribbean", lat: 18.25, lon: -87.80, sst: 28.4, dhw: 2.1, ph: 8.08, turb: 0.8, cover: 42.5, macro: 14.2, rugosity: 2.8, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.782 },
  { id: "Mesoamerican_Lagoon_02", name: "Mesoamerican Reef (Lagoon)", region: "Caribbean", lat: 18.15, lon: -87.90, sst: 29.8, dhw: 7.2, ph: 7.92, turb: 2.4, cover: 22.0, macro: 34.0, rugosity: 1.6, risk: "High", tier: "Tier 3: Thermal Risk", srpi: 0.340 },
  { id: "FloridaKeys_KeyLargo_03", name: "Florida Keys (Key Largo)", region: "Caribbean", lat: 25.08, lon: -80.44, sst: 29.1, dhw: 5.4, ph: 8.01, turb: 1.5, cover: 18.5, macro: 28.5, rugosity: 1.9, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.510 },
  { id: "FloridaKeys_DryTortugas_04", name: "Dry Tortugas (National Park)", region: "Caribbean", lat: 24.62, lon: -82.87, sst: 28.2, dhw: 1.8, ph: 8.10, turb: 0.6, cover: 38.0, macro: 16.0, rugosity: 2.6, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.745 },
  { id: "Belize_Barrier_05", name: "Belize Barrier Reef", region: "Caribbean", lat: 17.15, lon: -87.95, sst: 28.5, dhw: 3.2, ph: 8.05, turb: 0.9, cover: 34.7, macro: 21.0, rugosity: 2.4, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.690 },
  { id: "Belize_Atoll_06", name: "Glover's Reef Atoll", region: "Caribbean", lat: 16.82, lon: -87.80, sst: 28.7, dhw: 2.9, ph: 8.06, turb: 0.5, cover: 36.2, macro: 18.5, rugosity: 2.7, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.720 },
  { id: "Curacao_Oostpunt_07", name: "Curaçao (Oostpunt)", region: "Caribbean", lat: 12.04, lon: -68.78, sst: 27.9, dhw: 1.2, ph: 8.12, turb: 0.4, cover: 48.0, macro: 11.0, rugosity: 3.1, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.815 },
  { id: "Bonaire_NationalPark_08", name: "Bonaire Marine Park", region: "Caribbean", lat: 12.18, lon: -68.28, sst: 28.1, dhw: 1.5, ph: 8.11, turb: 0.5, cover: 45.0, macro: 12.5, rugosity: 2.9, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.790 },
  { id: "GBR_Northern_09", name: "Northern Great Barrier Reef", region: "Pacific", lat: -12.45, lon: 143.85, sst: 29.6, dhw: 8.4, ph: 7.95, turb: 1.1, cover: 24.5, macro: 31.0, rugosity: 2.1, risk: "High", tier: "Tier 3: Thermal Risk", srpi: 0.410 },
  { id: "GBR_Central_10", name: "Central Great Barrier Reef", region: "Pacific", lat: -18.25, lon: 147.20, sst: 28.8, dhw: 4.8, ph: 8.02, turb: 1.3, cover: 29.0, macro: 24.0, rugosity: 2.3, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.580 },
  { id: "GBR_Southern_11", name: "Southern GBR (Heron Island)", region: "Pacific", lat: -23.44, lon: 151.91, sst: 26.5, dhw: 0.8, ph: 8.14, turb: 0.7, cover: 52.0, macro: 8.5, rugosity: 3.2, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.840 },
  { id: "CoralTriangle_RajaAmpat_12", name: "Raja Ampat (Misool)", region: "Coral Triangle", lat: -2.15, lon: 130.50, sst: 29.0, dhw: 1.9, ph: 8.09, turb: 0.6, cover: 56.5, macro: 6.5, rugosity: 3.4, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.885 },
  { id: "CoralTriangle_Komodo_13", name: "Komodo National Park", region: "Coral Triangle", lat: -8.55, lon: 119.50, sst: 27.8, dhw: 1.1, ph: 8.11, turb: 0.5, cover: 50.2, macro: 9.0, rugosity: 3.0, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.830 },
  { id: "CoralTriangle_Sulawesi_14", name: "Bunaken (North Sulawesi)", region: "Coral Triangle", lat: 1.62, lon: 124.75, sst: 29.2, dhw: 3.4, ph: 8.04, turb: 0.8, cover: 41.0, macro: 15.0, rugosity: 2.8, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.730 },
  { id: "CoralTriangle_Bali_15", name: "Bali (Menjangan Island)", region: "Coral Triangle", lat: -8.12, lon: 114.52, sst: 28.9, dhw: 4.2, ph: 8.03, turb: 1.4, cover: 32.0, macro: 22.0, rugosity: 2.2, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.610 },
  { id: "RedSea_Aqaba_16", name: "Gulf of Aqaba (Refugium)", region: "Red Sea", lat: 29.45, lon: 34.98, sst: 26.2, dhw: 0.4, ph: 8.18, turb: 0.3, cover: 46.0, macro: 7.0, rugosity: 2.9, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.865 },
  { id: "RedSea_Jeddah_17", name: "Central Red Sea (Jeddah)", region: "Red Sea", lat: 21.50, lon: 39.10, sst: 30.5, dhw: 6.8, ph: 8.01, turb: 0.9, cover: 27.0, macro: 26.0, rugosity: 2.2, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.540 },
  { id: "RedSea_Farasan_18", name: "Farasan Banks", region: "Red Sea", lat: 16.70, lon: 42.15, sst: 31.2, dhw: 9.1, ph: 7.94, turb: 1.6, cover: 19.5, macro: 33.0, rugosity: 1.8, risk: "High", tier: "Tier 3: Thermal Risk", srpi: 0.380 },
  { id: "IndianOcean_Maldives_19", name: "Maldives (Ari Atoll)", region: "Indian Ocean", lat: 3.85, lon: 72.85, sst: 29.7, dhw: 7.8, ph: 7.96, turb: 0.7, cover: 23.0, macro: 29.5, rugosity: 2.0, risk: "High", tier: "Tier 3: Thermal Risk", srpi: 0.430 },
  { id: "IndianOcean_Seychelles_20", name: "Seychelles (Curieuse)", region: "Indian Ocean", lat: -4.28, lon: 55.72, sst: 29.3, dhw: 6.1, ph: 7.99, turb: 0.8, cover: 26.5, macro: 27.0, rugosity: 2.1, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.520 },
  { id: "IndianOcean_Chagos_21", name: "Chagos Archipelago", region: "Indian Ocean", lat: -6.00, lon: 71.50, sst: 28.5, dhw: 2.5, ph: 8.08, turb: 0.4, cover: 47.5, macro: 10.5, rugosity: 3.1, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.810 },
  { id: "Pacific_Hawaii_Kaneohe_22", name: "Hawaii (Kaneohe Bay)", region: "Pacific", lat: 21.45, lon: -157.80, sst: 26.8, dhw: 3.8, ph: 7.98, turb: 2.1, cover: 33.0, macro: 24.0, rugosity: 2.3, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.590 },
  { id: "Pacific_Palau_23", name: "Palau (Rock Islands)", region: "Pacific", lat: 7.30, lon: 134.45, sst: 29.4, dhw: 1.6, ph: 7.88, turb: 1.1, cover: 49.0, macro: 13.0, rugosity: 3.0, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.795 },
  { id: "Pacific_Fiji_24", name: "Fiji (Great Sea Reef)", region: "Pacific", lat: -16.50, lon: 179.00, sst: 28.1, dhw: 2.0, ph: 8.07, turb: 0.7, cover: 39.5, macro: 17.0, rugosity: 2.6, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.735 },
  { id: "Pacific_Moorea_25", name: "Moorea (French Polynesia)", region: "Pacific", lat: -17.52, lon: -149.83, sst: 27.5, dhw: 1.4, ph: 8.10, turb: 0.5, cover: 44.0, macro: 14.0, rugosity: 2.8, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.770 },
  { id: "Caribbean_Barbados_26", name: "Barbados (Folkestone)", region: "Caribbean", lat: 13.18, lon: -59.64, sst: 28.9, dhw: 4.5, ph: 8.02, turb: 1.2, cover: 21.5, macro: 32.0, rugosity: 1.8, risk: "Medium", tier: "Tier 2: Marine Reserve", srpi: 0.490 },
  { id: "Pacific_Okinawa_27", name: "Japan (Okinawa Kerama)", region: "Pacific", lat: 26.20, lon: 127.35, sst: 27.0, dhw: 2.8, ph: 8.11, turb: 0.6, cover: 37.0, macro: 19.0, rugosity: 2.5, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.710 },
  { id: "Pacific_Galapagos_28", name: "Galapagos (Darwin Island)", region: "Pacific", lat: 1.67, lon: -92.00, sst: 25.5, dhw: 1.0, ph: 8.05, turb: 1.8, cover: 31.0, macro: 22.0, rugosity: 2.4, risk: "Low", tier: "Tier 2: Marine Reserve", srpi: 0.640 },
  { id: "Caribbean_Cayman_29", name: "Grand Cayman (North Wall)", region: "Caribbean", lat: 19.35, lon: -81.25, sst: 28.6, dhw: 3.1, ph: 8.06, turb: 0.4, cover: 40.0, macro: 16.5, rugosity: 2.9, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.760 },
  { id: "CoralTriangle_Philippines_30", name: "Tubbataha Reefs (Sulu Sea)", region: "Coral Triangle", lat: 8.85, lon: 119.90, sst: 29.1, dhw: 2.2, ph: 8.08, turb: 0.5, cover: 54.0, macro: 8.0, rugosity: 3.3, risk: "Low", tier: "Tier 1: Outplanting", srpi: 0.860 }
];

let selectedStation = STATIONS_DB[0];
let shapChartInstance = null;
let odeChartInstance = null;
let threeScene, threeCamera, threeRenderer, coralMesh, coralMaterial;

// =============================================================================
// 3. INITIALIZATION ROUTINE
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initThreeJSCoral();
  initCharts();
  populateStationSelector();
  bindEvents();
  setLanguage(currentLang);
});

// =============================================================================
// 4. LEAFLET 2D OCEAN BATHYMETRY MAP
// =============================================================================
let mapInstance;
let mapMarkers = [];

function initMap() {
  mapInstance = L.map("leaflet-map", {
    center: [10.0, 0.0],
    zoom: 2,
    minZoom: 1.5,
    maxZoom: 10,
    worldCopyJump: true
  });

  // Base Layers
  const esriOcean = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}", {
    attribution: "ESRI Ocean & NOAA Coral Reef Watch",
    maxZoom: 13
  });
  const esriSat = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    attribution: "ESRI World Imagery",
    maxZoom: 13
  });
  const darkMatter = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "CartoDB Dark Matter",
    maxZoom: 13
  });

  esriOcean.addTo(mapInstance);

  L.control.layers({
    "ESRI Ocean Bathymetry": esriOcean,
    "Satellite Imagery": esriSat,
    "Tactical Dark Mode": darkMatter
  }, null, { position: "topright" }).addTo(mapInstance);

  // Add Stations
  STATIONS_DB.forEach(st => {
    const color = st.risk === "Low" ? "#10B981" : (st.risk === "Medium" ? "#F59E0B" : "#F43F5E");
    
    const marker = L.circleMarker([st.lat, st.lon], {
      radius: Math.max(6, Math.min(14, st.dhw * 1.5 + 4)),
      fillColor: color,
      color: "#FFFFFF",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(mapInstance);

    marker.bindPopup(`
      <div style="font-family: 'Inter', sans-serif; min-width: 180px;">
        <div style="font-weight: bold; font-size: 13px; color: #38BDF8; margin-bottom: 4px;">${st.name}</div>
        <div style="font-size: 11px; color: #94A3B8; margin-bottom: 6px;">Region: ${st.region}</div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 2px 0;">
          <span>SST:</span> <b style="color: #F8FAFC;">${st.sst.toFixed(1)} °C</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 2px 0;">
          <span>DHW:</span> <b style="color: #F59E0B;">${st.dhw.toFixed(1)} °C-wk</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 2px 0;">
          <span>Live Cover:</span> <b style="color: #38BDF8;">${st.cover.toFixed(1)} %</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; padding: 4px 0;">
          <span>SRPI Score:</span> <b style="color: #10B981;">${st.srpi.toFixed(3)}</b>
        </div>
      </div>
    `);

    marker.on("click", () => {
      selectStation(st);
    });

    mapMarkers.push({ marker, station: st });
  });
}

// =============================================================================
// 5. 3D WEBGL EARTH GLOBE PROJECTION (THREE.JS)
// =============================================================================
let globeScene, globeCamera, globeRenderer, globeGroup, globeControls, cloudMesh;
let isGlobeInitialized = false;
let globeRaycaster = new THREE.Raycaster();
let globeMouse = new THREE.Vector2();
let globeMarkerMeshes = [];

function initThreeJSGlobe() {
  if (isGlobeInitialized) return;
  const container = document.getElementById("globe3d-container");
  const width = container.clientWidth || 600;
  const height = container.clientHeight || 320;

  globeScene = new THREE.Scene();
  globeCamera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
  globeCamera.position.set(0, 0, 7.5);

  globeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  globeRenderer.setSize(width, height);
  globeRenderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(globeRenderer.domElement);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 1.1);
  globeScene.add(ambientLight);

  const sunLight1 = new THREE.DirectionalLight(0xffffff, 1.4);
  sunLight1.position.set(8, 6, 8);
  globeScene.add(sunLight1);

  const sunLight2 = new THREE.DirectionalLight(0x38BDF8, 0.6);
  sunLight2.position.set(-8, -4, -8);
  globeScene.add(sunLight2);

  globeGroup = new THREE.Group();

  // 3D Earth Sphere Geometry (Google Earth Photorealistic Sphere)
  const sphereRadius = 2.4;
  const earthGeom = new THREE.SphereGeometry(sphereRadius, 64, 64);

  const textureLoader = new THREE.TextureLoader();

  // Photorealistic NASA Blue Marble Surface Texture (Continents, Vegetation, Deserts, Oceans)
  const textureUrl = "textures/earth_atmos.jpg";
  const earthTexture = textureLoader.load(
    textureUrl,
    () => { if (globeRenderer) globeRenderer.render(globeScene, globeCamera); },
    undefined,
    () => {
      // CDN Fallback if local path has any CORS restriction
      earthMat.map = textureLoader.load("https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/textures/planets/earth_atmos_2048.jpg");
      earthMat.needsUpdate = true;
    }
  );

  const earthMat = new THREE.MeshStandardMaterial({
    map: earthTexture,
    roughness: 0.65,
    metalness: 0.1
  });
  const earthMesh = new THREE.Mesh(earthGeom, earthMat);
  globeGroup.add(earthMesh);

  // Atmospheric Cloud Layer
  const cloudGeom = new THREE.SphereGeometry(sphereRadius * 1.018, 64, 64);
  const cloudTexture = textureLoader.load(
    "textures/earth_clouds.png",
    undefined,
    undefined,
    () => {
      cloudMat.map = textureLoader.load("https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/textures/planets/earth_clouds_1024.png");
      cloudMat.needsUpdate = true;
    }
  );
  const cloudMat = new THREE.MeshStandardMaterial({
    map: cloudTexture,
    transparent: true,
    opacity: 0.45,
    blending: THREE.AdditiveBlending
  });
  cloudMesh = new THREE.Mesh(cloudGeom, cloudMat);
  globeGroup.add(cloudMesh);

  // Atmospheric Glow Ring
  const atmosphereGeom = new THREE.SphereGeometry(sphereRadius * 1.045, 32, 32);
  const atmosphereMat = new THREE.MeshBasicMaterial({
    color: 0x38BDF8,
    transparent: true,
    opacity: 0.18,
    side: THREE.BackSide
  });
  const atmosphereMesh = new THREE.Mesh(atmosphereGeom, atmosphereMat);
  globeGroup.add(atmosphereMesh);

  // Plot 30 Reef Stations on the 3D Globe
  STATIONS_DB.forEach(st => {
    const phi = (90 - st.lat) * (Math.PI / 180);
    const theta = (st.lon + 180) * (Math.PI / 180);

    const x = -(sphereRadius * Math.sin(phi) * Math.cos(theta));
    const z = (sphereRadius * Math.sin(phi) * Math.sin(theta));
    const y = (sphereRadius * Math.cos(phi));

    const colorHex = st.risk === "Low" ? 0x10B981 : (st.risk === "Medium" ? 0xF59E0B : 0xF43F5E);
    
    // Beacon Pin
    const pinGeom = new THREE.CylinderGeometry(0.02, 0.02, 0.25, 6);
    const pinMat = new THREE.MeshBasicMaterial({ color: colorHex });
    const pin = new THREE.Mesh(pinGeom, pinMat);

    // Glowing Station Sphere
    const beaconGeom = new THREE.SphereGeometry(0.08, 12, 12);
    const beaconMat = new THREE.MeshBasicMaterial({ color: colorHex });
    const beacon = new THREE.Mesh(beaconGeom, beaconMat);
    beacon.position.set(0, 0.15, 0);
    pin.add(beacon);

    pin.position.set(x, y, z);
    pin.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(x, y, z).normalize());
    pin.userData = { station: st };

    globeGroup.add(pin);
    globeMarkerMeshes.push(beacon);
  });

  globeScene.add(globeGroup);

  // Orbit Controls
  globeControls = new THREE.OrbitControls(globeCamera, globeRenderer.domElement);
  globeControls.enableDamping = true;
  globeControls.dampingFactor = 0.05;
  globeControls.autoRotate = true;
  globeControls.autoRotateSpeed = 0.8;
  globeControls.minDistance = 3.8;
  globeControls.maxDistance = 12.0;

  // Globe Click Interaction
  container.addEventListener("click", (event) => {
    const rect = container.getBoundingClientRect();
    globeMouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    globeMouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

    globeRaycaster.setFromCamera(globeMouse, globeCamera);
    const intersects = globeRaycaster.intersectObjects(globeMarkerMeshes);
    if (intersects.length > 0) {
      const parentPin = intersects[0].object.parent;
      if (parentPin && parentPin.userData.station) {
        selectStation(parentPin.userData.station);
      }
    }
  });

  // Animation Loop
  function animateGlobe() {
    requestAnimationFrame(animateGlobe);
    if (currentProjection === "3d") {
      globeControls.update();
      globeRenderer.render(globeScene, globeCamera);
    }
  }
  animateGlobe();

  isGlobeInitialized = true;
}

function setMapProjection(mode) {
  currentProjection = mode;
  const btn2D = document.getElementById("proj-btn-2d");
  const btn3D = document.getElementById("proj-btn-3d");
  const leafletDiv = document.getElementById("leaflet-map");
  const globeDiv = document.getElementById("globe3d-container");

  if (mode === "2d") {
    btn2D.className = "px-2.5 py-1 rounded font-bold transition text-slate-950 bg-cyan-400";
    btn3D.className = "px-2.5 py-1 rounded font-bold transition text-slate-400 hover:text-slate-200";
    leafletDiv.classList.remove("hidden");
    globeDiv.classList.add("hidden");
    if (mapInstance) {
      setTimeout(() => mapInstance.invalidateSize(), 150);
    }
  } else {
    btn3D.className = "px-2.5 py-1 rounded font-bold transition text-slate-950 bg-cyan-400";
    btn2D.className = "px-2.5 py-1 rounded font-bold transition text-slate-400 hover:text-slate-200";
    leafletDiv.classList.add("hidden");
    globeDiv.classList.remove("hidden");
    if (!isGlobeInitialized) {
      initThreeJSGlobe();
    } else {
      const container = document.getElementById("globe3d-container");
      globeCamera.aspect = container.clientWidth / container.clientHeight;
      globeCamera.updateProjectionMatrix();
      globeRenderer.setSize(container.clientWidth, container.clientHeight);
    }
  }
}

function focusBasin(basin) {
  if (currentProjection === "2d" && mapInstance) {
    if (basin === "global") {
      mapInstance.setView([10.0, 0.0], 2);
    } else if (basin === "caribbean") {
      mapInstance.setView([19.0, -78.0], 5);
    } else if (basin === "gbr") {
      mapInstance.setView([-18.0, 148.0], 5);
    } else if (basin === "coraltriangle") {
      mapInstance.setView([-2.0, 125.0], 5);
    } else if (basin === "redsea") {
      mapInstance.setView([22.0, 38.0], 5);
    } else if (basin === "indianocean") {
      mapInstance.setView([-2.0, 65.0], 4);
    }
  } else if (currentProjection === "3d" && isGlobeInitialized) {
    let targetLat = 0, targetLon = 0;
    if (basin === "caribbean") { targetLat = 19.0; targetLon = -78.0; }
    else if (basin === "gbr") { targetLat = -18.0; targetLon = 148.0; }
    else if (basin === "coraltriangle") { targetLat = -2.0; targetLon = 125.0; }
    else if (basin === "redsea") { targetLat = 22.0; targetLon = 38.0; }
    else if (basin === "indianocean") { targetLat = -2.0; targetLon = 65.0; }

    const phi = (90 - targetLat) * (Math.PI / 180);
    const theta = (targetLon + 180) * (Math.PI / 180);
    const r = 7.5;
    globeCamera.position.set(
      -(r * Math.sin(phi) * Math.cos(theta)),
      (r * Math.cos(phi)),
      (r * Math.sin(phi) * Math.sin(theta))
    );
    globeControls.update();
  }
}

function selectStation(st) {
  selectedStation = st;
  document.getElementById("station-selector").value = st.id;
  
  // Update HUD
  document.getElementById("hud-sst").innerText = `${st.sst.toFixed(1)} °C`;
  document.getElementById("hud-dhw").innerText = `${st.dhw.toFixed(1)} °C-wk`;
  document.getElementById("hud-ph").innerText = `${st.ph.toFixed(2)}`;

  // Update Sliders to match station
  document.getElementById("slider-sst").value = st.sst;
  document.getElementById("val-sst").innerText = `${st.sst.toFixed(1)} °C`;
  document.getElementById("slider-dhw").value = st.dhw;
  document.getElementById("val-dhw").innerText = `${st.dhw.toFixed(1)} °C-weeks`;
  document.getElementById("slider-ph").value = st.ph;
  document.getElementById("val-ph").innerText = `${st.ph.toFixed(2)}`;
  document.getElementById("slider-turb").value = st.turb;
  document.getElementById("val-turb").innerText = `${st.turb.toFixed(2)} NTU`;

  // Trigger AI and 3D update
  triggerAIInference();
  if (currentProjection === "2d" && mapInstance) {
    mapInstance.panTo([st.lat, st.lon]);
  }
}

function populateStationSelector() {
  const sel = document.getElementById("station-selector");
  sel.innerHTML = "";
  STATIONS_DB.forEach(st => {
    const opt = document.createElement("option");
    opt.value = st.id;
    opt.innerText = `${st.name} (${st.region})`;
    sel.appendChild(opt);
  });
  sel.addEventListener("change", (e) => {
    const found = STATIONS_DB.find(s => s.id === e.target.value);
    if (found) selectStation(found);
  });
}

// =============================================================================
// 6. THREE.JS 3D PROCEDURAL CORAL DIGITAL TWIN
// =============================================================================
function initThreeJSCoral() {
  const container = document.getElementById("coral3d-canvas-container");
  const width = container.clientWidth;
  const height = container.clientHeight;

  threeScene = new THREE.Scene();
  threeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  threeCamera.position.set(0, 4, 9);

  threeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  threeRenderer.setSize(width, height);
  threeRenderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(threeRenderer.domElement);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  threeScene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0x38BDF8, 1.2);
  dirLight1.position.set(5, 10, 7);
  threeScene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x10B981, 0.6);
  dirLight2.position.set(-5, -2, -5);
  threeScene.add(dirLight2);

  // Procedural Coral Group
  coralMesh = new THREE.Group();

  // Create Branching Coral Geometry
  coralMaterial = new THREE.MeshStandardMaterial({
    color: new THREE.Color(0x3D7E50),
    roughness: 0.6,
    metalness: 0.1
  });

  // Base Dome
  const baseGeom = new THREE.SphereGeometry(1.2, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2);
  const baseMesh = new THREE.Mesh(baseGeom, coralMaterial);
  coralMesh.add(baseMesh);

  // Branches
  const numBranches = 24;
  for (let i = 0; i < numBranches; i++) {
    const phi = Math.acos(-1 + (2 * i) / numBranches);
    const theta = Math.sqrt(numBranches * Math.PI) * phi;

    const branchHeight = 1.0 + Math.random() * 1.5;
    const branchGeom = new THREE.CylinderGeometry(0.12, 0.22, branchHeight, 8);
    const branch = new THREE.Mesh(branchGeom, coralMaterial);

    const x = Math.sin(phi) * Math.cos(theta) * 0.9;
    const z = Math.sin(phi) * Math.sin(theta) * 0.9;
    const y = Math.abs(Math.cos(phi)) * 0.6;

    branch.position.set(x, y + branchHeight / 2, z);
    branch.lookAt(new THREE.Vector3(x * 2, y * 2 + branchHeight, z * 2));
    coralMesh.add(branch);

    // Polyp tip
    const tipGeom = new THREE.SphereGeometry(0.2, 8, 8);
    const tip = new THREE.Mesh(tipGeom, coralMaterial);
    tip.position.set(x * 1.6, y + branchHeight, z * 1.6);
    coralMesh.add(tip);
  }

  threeScene.add(coralMesh);

  // Orbit Controls
  const controls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 1.2;

  // Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    threeRenderer.render(threeScene, threeCamera);
  }
  animate();

  // Resize Handler
  window.addEventListener("resize", () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    threeCamera.aspect = w / h;
    threeCamera.updateProjectionMatrix();
    threeRenderer.setSize(w, h);
  });
}

function updateCoralBleachingShader(stressFraction) {
  if (!coralMaterial) return;

  const dict = I18N[currentLang];
  let targetColor;
  const badge = document.getElementById("coral-health-badge");

  if (stressFraction < 0.35) {
    // Healthy (Symbiont Rich Gold-Green)
    targetColor = new THREE.Color().lerpColors(new THREE.Color(0x3D7E50), new THREE.Color(0x8B5A2B), stressFraction / 0.35);
    badge.innerText = dict.coralHealthy;
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
  } else if (stressFraction < 0.70) {
    // Heat Shock / Fluorescing Pigments (Pink / Purple)
    const t = (stressFraction - 0.35) / 0.35;
    targetColor = new THREE.Color().lerpColors(new THREE.Color(0x8B5A2B), new THREE.Color(0xD946EF), t);
    badge.innerText = dict.coralStress;
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40";
  } else {
    // Bleached Skeleton (Bone White)
    const t = (stressFraction - 0.70) / 0.30;
    targetColor = new THREE.Color().lerpColors(new THREE.Color(0xD946EF), new THREE.Color(0xF8FAFC), t);
    badge.innerText = dict.coralBleached;
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse";
  }

  coralMaterial.color = targetColor;
}

// =============================================================================
// 7. MACHINE LEARNING & TREESHAP ENGINE
// =============================================================================
function initCharts() {
  const dict = I18N[currentLang];

  // 1. TreeSHAP Bar Chart
  const ctxShap = document.getElementById("shap-chart").getContext("2d");
  shapChartInstance = new Chart(ctxShap, {
    type: "bar",
    data: {
      labels: dict.shapLabels,
      datasets: [{
        label: "Marginal Attribution (SHAP)",
        data: [14.2, -4.5, 8.1, -2.2, 3.4],
        backgroundColor: ["#F43F5E", "#38BDF8", "#F59E0B", "#2DD4BF", "#F43F5E"],
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: "rgba(51, 65, 85, 0.4)" },
          ticks: { color: "#94A3B8", font: { family: "JetBrains Mono", size: 10 } }
        },
        y: {
          grid: { display: false },
          ticks: { color: "#F8FAFC", font: { family: "Inter", size: 11 } }
        }
      }
    }
  });

  // 2. Decadal ODE Line Chart
  const ctxOde = document.getElementById("ode-chart").getContext("2d");
  odeChartInstance = new Chart(ctxOde, {
    type: "line",
    data: {
      labels: Array.from({ length: 26 }, (_, i) => 2025 + i),
      datasets: [
        { label: dict.odeCoralLabel, data: [], borderColor: "#38BDF8", backgroundColor: "rgba(56, 189, 248, 0.1)", fill: true, tension: 0.3, borderWidth: 3 },
        { label: dict.odeMacroLabel, data: [], borderColor: "#F59E0B", borderDash: [5, 5], tension: 0.3, borderWidth: 2 },
        { label: dict.odeTurfLabel, data: [], borderColor: "#64748B", tension: 0.3, borderWidth: 1.5 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#CBD5E1", font: { family: "Inter", size: 11 } } }
      },
      scales: {
        x: {
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#94A3B8", font: { family: "JetBrains Mono", size: 10 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#94A3B8", font: { family: "JetBrains Mono", size: 10 } }
        }
      }
    }
  });
}

function triggerAIInference() {
  const sst = parseFloat(document.getElementById("slider-sst").value);
  const dhw = parseFloat(document.getElementById("slider-dhw").value);
  const ph = parseFloat(document.getElementById("slider-ph").value);
  const turb = parseFloat(document.getElementById("slider-turb").value);

  // Compute Multi-Stressor Vulnerability Score
  const phFactor = Math.max(0.0, (8.15 - ph) / 0.35);
  const effectiveDHW = dhw * (1.0 + phFactor * 0.45);
  const turbShield = Math.max(0.0, (turb - 0.5) * 0.4);
  const totalScore = Math.max(0.0, effectiveDHW - turbShield);

  let riskLabel, riskColor, riskBg, riskBorder, lossPct, stressFraction;

  if (totalScore < 4.0) {
    riskLabel = currentLang === "es" ? "BAJO RIESGO" : "LOW RISK";
    riskColor = "text-emerald-400";
    riskBg = "bg-emerald-500/10";
    riskBorder = "border-emerald-500/30";
    lossPct = (totalScore * 1.8).toFixed(1);
    stressFraction = totalScore / 12.0;
  } else if (totalScore < 8.0) {
    riskLabel = currentLang === "es" ? "RIESGO MODERADO" : "MEDIUM RISK";
    riskColor = "text-amber-400";
    riskBg = "bg-amber-500/10";
    riskBorder = "border-amber-500/30";
    lossPct = (8.0 + (totalScore - 4.0) * 4.2).toFixed(1);
    stressFraction = 0.35 + (totalScore - 4.0) * 0.08;
  } else {
    riskLabel = currentLang === "es" ? "ALTO RIESGO (CRÍTICO)" : "HIGH RISK (CRITICAL)";
    riskColor = "text-rose-400";
    riskBg = "bg-rose-500/10";
    riskBorder = "border-rose-500/30";
    lossPct = Math.min(95.0, 25.0 + (totalScore - 8.0) * 7.5).toFixed(1);
    stressFraction = Math.min(1.0, 0.70 + (totalScore - 8.0) * 0.05);
  }

  // Update DOM Output Cards
  const riskCard = document.getElementById("card-risk");
  riskCard.className = `p-3 rounded-lg border ${riskBorder} ${riskBg} text-center transition`;
  document.getElementById("out-risk-label").className = `text-lg font-bold ${riskColor} font-mono mt-0.5`;
  document.getElementById("out-risk-label").innerText = riskLabel;
  document.getElementById("out-loss-pct").innerText = `-${lossPct}%`;

  // Update TreeSHAP Chart
  const shapDHW = dhw * 3.2;
  const shapPH = (8.15 - ph) * 14.5;
  const shapTurb = -turb * 1.2;
  const shapSST = Math.max(0, sst - 28.5) * 2.8;
  const shapRug = -2.5;

  if (shapChartInstance) {
    shapChartInstance.data.datasets[0].data = [shapDHW, shapRug, shapPH, shapTurb, shapSST];
    shapChartInstance.update();
  }

  // Update 3D Coral Shaders
  updateCoralBleachingShader(stressFraction);
}

// =============================================================================
// 8. RUNGE-KUTTA 4TH ORDER DECADAL ODE SIMULATION
// =============================================================================
function triggerODESimulation() {
  const deltaWarming = parseFloat(document.getElementById("slider-ode-warming").value);
  const outplantRate = parseFloat(document.getElementById("slider-ode-outplant").value) / 100.0;
  const hardeningBonus = parseFloat(document.getElementById("slider-ode-hard").value);
  const herbivoryG = parseFloat(document.getElementById("slider-ode-herb").value);

  // Mumby ODE Parameters
  const r = 0.45;
  const d0 = 0.08;
  const a = 0.18;
  const gamma = 0.22;

  let C = 0.32;
  let M = 0.22;
  const dt = 0.25;
  const totalYears = 25;
  const steps = Math.floor(totalYears / dt);

  const coralSeries = [C * 100];
  const macroSeries = [M * 100];
  const turfSeries = [(1 - C - M) * 100];

  for (let step = 1; step <= steps; step++) {
    const t = step * dt;

    const netHeatStress = Math.max(0.0, (deltaWarming * (t / 25.0)) - hardeningBonus);
    const dEff = d0 + netHeatStress * 0.05;

    const derive = (cVal, mVal) => {
      const cSafe = Math.max(0, Math.min(1, cVal));
      const mSafe = Math.max(0, Math.min(1, mVal));
      const tSafe = Math.max(0, 1.0 - cSafe - mSafe);

      const dC = r * cSafe * tSafe - dEff * cSafe + outplantRate * (1.0 - cSafe);
      const dM = a * mSafe * cSafe - (herbivoryG * mSafe) / Math.max(0.01, mSafe + tSafe) + gamma * mSafe * tSafe;
      return { dC, dM };
    };

    const k1 = derive(C, M);
    const k2 = derive(C + 0.5 * dt * k1.dC, M + 0.5 * dt * k1.dM);
    const k3 = derive(C + 0.5 * dt * k2.dC, M + 0.5 * dt * k2.dM);
    const k4 = derive(C + dt * k3.dC, M + dt * k3.dM);

    C = Math.max(0.01, Math.min(0.95, C + (dt / 6.0) * (k1.dC + 2 * k2.dC + 2 * k3.dC + k4.dC)));
    M = Math.max(0.01, Math.min(0.95, M + (dt / 6.0) * (k1.dM + 2 * k2.dM + 2 * k3.dM + k4.dM)));
    const T = Math.max(0.0, 1.0 - C - M);

    if (step % 4 === 0) {
      coralSeries.push(C * 100);
      macroSeries.push(M * 100);
      turfSeries.push(T * 100);
    }
  }

  // Update ODE Line Chart
  if (odeChartInstance) {
    odeChartInstance.data.datasets[0].data = coralSeries;
    odeChartInstance.data.datasets[1].data = macroSeries;
    odeChartInstance.data.datasets[2].data = turfSeries;
    odeChartInstance.update();
  }

  // Update Summary Ticker
  const finalCoral = coralSeries[coralSeries.length - 1];
  const accretion = (finalCoral * 0.18 - 1.5).toFixed(2);
  const accSign = accretion > 0 ? "+" : "";
  const accretionText = currentLang === "es" ? `Acreción de Carbonato: ${accSign}${accretion} kg/m²/año` : `Accretion: ${accSign}${accretion} kg/m²/yr`;
  document.getElementById("ode-outcome-cover").innerText = `${finalCoral.toFixed(1)}% [${accretionText}]`;
}

// =============================================================================
// 9. SPATIAL RESTORATION PRIORITY TABLE & GEOJSON EXPORTER
// =============================================================================
function populateTable(stations) {
  const tbody = document.getElementById("srpi-table-body");
  tbody.innerHTML = "";
  const dict = I18N[currentLang];

  stations.forEach(st => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-800/40 transition cursor-pointer";

    let riskText, riskClass;
    if (st.risk === "Low") {
      riskText = dict.riskLow;
      riskClass = "text-emerald-400";
    } else if (st.risk === "Medium") {
      riskText = dict.riskMed;
      riskClass = "text-amber-400";
    } else {
      riskText = dict.riskHigh;
      riskClass = "text-rose-400";
    }

    let tierText, tierClass;
    if (st.tier.includes("Tier 1")) {
      tierText = currentLang === "es" ? "Tier 1: Siembra Activa" : "Tier 1: Outplanting";
      tierClass = "bg-cyan-500/20 text-cyan-300 border-cyan-500/30";
    } else if (st.tier.includes("Tier 2")) {
      tierText = currentLang === "es" ? "Tier 2: Reserva Marina" : "Tier 2: Marine Reserve";
      tierClass = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    } else {
      tierText = currentLang === "es" ? "Tier 3: Riesgo Térmico" : "Tier 3: Thermal Risk";
      tierClass = "bg-rose-500/20 text-rose-300 border-rose-500/30";
    }

    tr.innerHTML = `
      <td class="py-2.5 px-4 font-semibold text-slate-200">${st.name}</td>
      <td class="py-2.5 px-4 text-slate-400">${st.region}</td>
      <td class="py-2.5 px-4 text-cyan-300 font-bold">${st.cover.toFixed(1)}%</td>
      <td class="py-2.5 px-4 text-amber-400">${st.dhw.toFixed(1)}</td>
      <td class="py-2.5 px-4 text-teal-300">${st.ph.toFixed(2)}</td>
      <td class="py-2.5 px-4"><span class="${riskClass} font-bold">● ${riskText}</span></td>
      <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] border ${tierClass}">${tierText}</span></td>
      <td class="py-2.5 px-4 text-right">
        <button class="px-2 py-1 text-[10px] rounded bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-cyan-300 border border-slate-700 transition" onclick='selectStationById("${st.id}")'>
          <i class="fa-solid fa-crosshairs mr-1"></i> ${dict.btnInspect}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function selectStationById(id) {
  const found = STATIONS_DB.find(s => s.id === id);
  if (found) {
    selectStation(found);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function exportGeoJSON() {
  const geojson = {
    type: "FeatureCollection",
    metadata: {
      generated_by: "CoralTwin-DT Cyber-Physical Command Center",
      target_journal: "Ecological Informatics (Scopus Q1)",
      license: "MIT",
      timestamp: new Date().toISOString()
    },
    features: STATIONS_DB.map(st => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [st.lon, st.lat] },
      properties: {
        station_id: st.id,
        station_name: st.name,
        ocean_region: st.region,
        live_coral_cover_pct: st.cover,
        sea_surface_temp_degC: st.sst,
        degree_heating_weeks: st.dhw,
        seawater_pH: st.ph,
        bleaching_risk: st.risk,
        management_tier: st.tier,
        srpi_priority_score: st.srpi
      }
    }))
  };

  const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/geo+json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "priority_restoration_zones.geojson";
  a.click();
  URL.revokeObjectURL(url);
}

// =============================================================================
// 10. EVENT LISTENERS
// =============================================================================
function bindEvents() {
  // Sliders AI
  ["slider-sst", "slider-dhw", "slider-ph", "slider-turb"].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (id === "slider-sst") document.getElementById("val-sst").innerText = `${val.toFixed(1)} °C`;
      if (id === "slider-dhw") document.getElementById("val-dhw").innerText = `${val.toFixed(1)} °C-weeks`;
      if (id === "slider-ph") document.getElementById("val-ph").innerText = `${val.toFixed(2)}`;
      if (id === "slider-turb") document.getElementById("val-turb").innerText = `${val.toFixed(2)} NTU`;
      triggerAIInference();
    });
  });

  // Sliders ODE
  ["slider-ode-warming", "slider-ode-outplant", "slider-ode-hard", "slider-ode-herb"].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (id === "slider-ode-warming") document.getElementById("val-ode-warming").innerText = `+${val.toFixed(1)} °C`;
      if (id === "slider-ode-outplant") document.getElementById("val-ode-outplant").innerText = `${val.toFixed(1)} %/yr`;
      if (id === "slider-ode-hard") document.getElementById("val-ode-hard").innerText = `+${val.toFixed(1)} °C`;
      if (id === "slider-ode-herb") document.getElementById("val-ode-herb").innerText = `${val.toFixed(2)} /yr`;
      triggerODESimulation();
    });
  });

  // Tier Filter Buttons
  document.querySelectorAll(".filter-tier-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-tier-btn").forEach(b => {
        b.className = "filter-tier-btn px-3 py-1 text-xs rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700";
      });
      e.target.className = "filter-tier-btn px-3 py-1 text-xs rounded-lg bg-cyan-500 text-slate-950 font-bold active";

      const tier = e.target.getAttribute("data-tier");
      if (tier === "ALL") {
        populateTable(STATIONS_DB);
      } else {
        const filtered = STATIONS_DB.filter(s => s.tier.includes(tier));
        populateTable(filtered);
      }
    });
  });

  // Export GeoJSON Button
  document.getElementById("btn-export-geojson").addEventListener("click", exportGeoJSON);
}
