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
    statusOnline: "CONNECTING",
    statusSync: "BASELINE",
    btnExport: "Export GeoJSON",
    kpi1Val: "25 Stations",
    kpi1Label: "5 Global Ocean Basins",
    kpi2Label: "XGBoost ML Accuracy",
    kpi3Label: "Acidification Tipping Pt",
    kpi4Label: "2050 Restored Live Cover",
    mapTitle: "Global Oceanographic Telemetry Map",
    mapSubtitle: "NOAA CRW 5km SST/DHW with deterministic baseline features",
    tierRestoration: "Tier 1: Restoration",
    tierConservation: "Tier 2: Conservation",
    tierMonitoring: "Tier 3: Monitoring",
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
    aiSubtitle: "Server inference from synchronized station state",
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
    filterTier1: "Tier 1: Restoration",
    filterTier2: "Tier 2: Conservation",
    filterTier3: "Tier 3: Monitoring",
    thStation: "Station Name",
    thRegion: "Region / Basin",
    thCover: "Live Cover (%)",
    thSrpi: "SRPI Score",
    thTier: "Management Priority Tier",
    thAction: "Action",
    btnInspect: "Inspect",
    btnAIAudit: "AI Audit & Benchmark",
    auditModalTitle: "AI Engine Audit, EDA & Spatial Cross-Validation",
    auditModalSubtitle: "Rigorous 5-Fold Spatially-Stratified CV, Hyperparameters, Confusion Matrix & Statistical Analysis",
    auditTabBenchmark: "1. Model Benchmark & CV",
    auditTabConfusion: "2. Confusion Matrix",
    auditTabEDA: "3. Exploratory Analysis (EDA)",
    auditTabHyperparams: "4. Hyperparameters & Protocol",
    auditMetricRecords: "Harmonized Total Dataset",
    auditMetricCV: "Validation Protocol",
    auditMetricAccuracy: "Production Accuracy",
    auditMetricLatency: "Inference Latency",
    auditTableTitle: "Multi-Architecture Benchmark Comparison (5-Fold Cross-Validation)",
    confusionTitle: "Out-of-Fold Confusion Matrix (XGBoost Classifier)",
    confusionSubtitle: "Evaluated across 12,492 harmonized out-of-fold station-stratified samples",
    footerAttribution: "Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital."
  },
  es: {
    appSubtitle: "Centro de Comando del Gemelo Digital Marino Ciber-Físico",
    statusOnline: "CONECTANDO",
    statusSync: "LÍNEA BASE",
    btnExport: "Exportar GeoJSON",
    kpi1Val: "25 Estaciones",
    kpi1Label: "5 Cuencas Oceánicas Globales",
    kpi2Label: "Precisión IA (XGBoost)",
    kpi3Label: "Punto de Quiebre por pH",
    kpi4Label: "Cobertura Viva 2050 (Restaurada)",
    mapTitle: "Mapa Global de Telemetría Oceanográfica",
    mapSubtitle: "NOAA CRW 5km SST/DHW con variables de línea base deterministas",
    tierRestoration: "Tier 1: Restauración",
    tierConservation: "Tier 2: Conservación",
    tierMonitoring: "Tier 3: Monitoreo",
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
    aiSubtitle: "Inferencia del servidor desde el estado sincronizado",
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
    filterTier1: "Tier 1: Restauración",
    filterTier2: "Tier 2: Conservación",
    filterTier3: "Tier 3: Monitoreo",
    thStation: "Nombre de Estación",
    thRegion: "Región / Cuenca",
    thCover: "Cobertura Viva (%)",
    thSrpi: "Puntaje SRPI",
    thTier: "Nivel de Prioridad de Manejo",
    thAction: "Acción",
    btnInspect: "Inspeccionar",
    btnAIAudit: "Auditoría & Benchmark IA",
    auditModalTitle: "Auditoría del Motor de IA, EDA y Validación Cruzada",
    auditModalSubtitle: "Evaluación formal 5-Fold Spatially-Stratified CV, Hiperparámetros, Matriz de Confusión y Análisis Estadístico",
    auditTabBenchmark: "1. Benchmark & Validación Cruzada",
    auditTabConfusion: "2. Matriz de Confusión",
    auditTabEDA: "3. Análisis Exploratorio (EDA)",
    auditTabHyperparams: "4. Hiperparámetros & Protocolo",
    auditMetricRecords: "Dataset Total Armonizado",
    auditMetricCV: "Protocolo de Validación",
    auditMetricAccuracy: "Precisión de Producción",
    auditMetricLatency: "Latencia de Inferencia",
    auditTableTitle: "Tabla Comparativa de Modelos Multiarquitectura (Validación Cruzada 5-Fold)",
    confusionTitle: "Matriz de Confusión Out-of-Fold (XGBoost Classifier)",
    confusionSubtitle: "Evaluación sobre las 12,492 muestras del test out-of-fold estratificado por estación",
    footerAttribution: "Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital."
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
  updateStationCount();
}

// =============================================================================
// 2. OPERATIONAL STATIONS (loaded from the canonical API registry)
// =============================================================================
let STATIONS_DB = [];
let selectedStation = null;
const twinApiClient = new CoralTwinAPI.TwinAPIClient();
let operationalConnectionState = "connecting";
let stationStates = Object.create(null);
let shapChartInstance = null;
let odeChartInstance = null;
let threeScene, threeCamera, threeRenderer, coralMesh, coralMaterial;

// =============================================================================
// 3. INITIALIZATION ROUTINE
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initThreeJSCoral();
  initCharts();
  populateStationSelector();
  bindEvents();
  setLanguage(currentLang);
  loadOperationalStations();
});

function numberOrNull(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatValue(value, digits, suffix) {
  const numeric = numberOrNull(value);
  return numeric === null ? "N/A" : `${numeric.toFixed(digits)}${suffix || ""}`;
}

function sourceTimestamp(observation) {
  if (!observation || !observation.observed_at) return "No observation";
  const source = observation.source || observation.dataset_id || "source unavailable";
  return `${source} · ${observation.observed_at}`;
}

function mapApiStation(station) {
  const baseline = station.baseline || { status: "missing", source: "static_baseline", source_date: null, features: {} };
  const fields = station.baseline_fields || CoralTwinAPI.mapBaselineFeatures(baseline);
  const decision = CoralTwinAPI.normalizeDecision(station.decision);
  const decisionFields = CoralTwinAPI.mapDecisionFeatures(decision);
  const sst = station.sst || null;
  const dhw = station.dhw || null;
  return {
    id: station.id,
    name: station.name,
    region: decisionFields.region || station.region || "N/A",
    reef_zone: decisionFields.reef_zone,
    lat: station.lat,
    lon: station.lon,
    sst: sst ? sst.value : fields.baseline_sst,
    dhw: dhw ? dhw.value : fields.baseline_dhw,
    ph: fields.ph,
    turb: fields.turb,
    cover: fields.cover,
    rugosity: fields.rugosity,
    depth: fields.depth,
    macro: decisionFields.macro,
    tier: decisionFields.tier,
    srpi: decisionFields.srpi,
    decision: decision,
    baseline: baseline,
    baseline_fields: fields,
    sst_observation: sst,
    dhw_observation: dhw,
    inference: null,
    latest_sync_run: null,
    retrieved_at: station.retrieved_at || null,
  };
}

function setConnectionState(state) {
  operationalConnectionState = state;
  const status = document.getElementById("connection-status");
  if (status) {
    status.innerText = state.toUpperCase();
    status.className = `font-bold ${state === "live" ? "text-emerald-400" : state === "partial" || state === "stale" ? "text-amber-400" : state === "offline" ? "text-rose-400" : "text-slate-400"}`;
  }
}

function updateStationCount() {
  const count = document.getElementById("station-count");
  if (count) count.innerText = `${STATIONS_DB.length} ${currentLang === "es" ? "Estaciones" : "Stations"}`;
}

async function loadOperationalStations() {
  setConnectionState("connecting");
  try {
    const payload = await twinApiClient.listStations();
    STATIONS_DB = payload.stations.map(mapApiStation);
    STATIONS_DB.forEach(station => { station.retrieved_at = payload.retrieved_at; });
    selectedStation = STATIONS_DB[0] || null;
    stationStates = Object.create(null);
    STATIONS_DB.forEach(station => { stationStates[station.id] = station; });
    const hasNoaaObservation = STATIONS_DB.some(station => station.sst_observation || station.dhw_observation);
    setConnectionState(STATIONS_DB.length === 0 || !hasNoaaObservation ? "no-data" : "live");
    updateStationCount();
    initMap();
    if (isGlobeInitialized) refreshGlobeMarkers();
    populateStationSelector();
    populateTable(STATIONS_DB);
    if (selectedStation) {
      renderStationState(selectedStation);
      await refreshStationState(selectedStation.id);
    }
  } catch (error) {
    setConnectionState("offline");
    updateStationCount();
    if (!mapInstance) initMap();
    populateStationSelector();
    populateTable(STATIONS_DB);
  }
}

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
    const priority = CoralTwinAPI.priorityPresentation(st.decision);
    const color = priority.color;
    
    const marker = L.circleMarker([st.lat, st.lon], {
      radius: Math.max(6, Math.min(14, (numberOrNull(st.dhw) || 0) * 1.5 + 4)),
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
          <span>SST:</span> <b style="color: #F8FAFC;">${formatValue(st.sst, 1, " °C")}</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 2px 0;">
          <span>DHW:</span> <b style="color: #F59E0B;">${formatValue(st.dhw, 1, " °C-wk")}</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 2px 0;">
          <span>Live Cover:</span> <b style="color: #38BDF8;">${formatValue(st.cover, 1, " %")}</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; padding: 4px 0;">
          <span>Priority:</span> <b style="color: ${color};">${priority.label}</b>
        </div>
        <div style="font-size: 11px; display: flex; justify-content: space-between; padding: 4px 0;">
          <span>SRPI Score:</span> <b style="color: #10B981;">${formatValue(st.srpi, 3)}</b>
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
let globeMarkerIds = [];
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

  // Plot canonical reef stations on the 3D Globe
  refreshGlobeMarkers();

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

function refreshGlobeMarkers() {
  if (!globeGroup) return;
  const nextIds = STATIONS_DB.map(st => st.id);
  if (!CoralTwinAPI.needsMarkerRefresh(globeMarkerIds, STATIONS_DB)) return;
  globeMarkerMeshes.forEach(beacon => {
    if (beacon.parent && beacon.parent.parent === globeGroup) globeGroup.remove(beacon.parent);
  });
  globeMarkerMeshes = [];
  const sphereRadius = 2.4;
  STATIONS_DB.forEach(st => {
    const phi = (90 - st.lat) * (Math.PI / 180);
    const theta = (st.lon + 180) * (Math.PI / 180);

    const x = -(sphereRadius * Math.sin(phi) * Math.cos(theta));
    const z = (sphereRadius * Math.sin(phi) * Math.sin(theta));
    const y = (sphereRadius * Math.cos(phi));

    const colorHex = parseInt(CoralTwinAPI.priorityPresentation(st.decision).color.slice(1), 16);

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
  globeMarkerIds = nextIds;
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
  if (!st) return;
  selectedStation = st;
  document.getElementById("station-selector").value = st.id;
  renderStationState(st);
  if (currentProjection === "2d" && mapInstance) {
    mapInstance.panTo([st.lat, st.lon]);
  }
  refreshStationState(st.id);
}

function renderStationState(st) {
  const sstInput = document.getElementById("slider-sst");
  const dhwInput = document.getElementById("slider-dhw");
  const phInput = document.getElementById("slider-ph");
  const turbInput = document.getElementById("slider-turb");
  const sst = numberOrNull(st.sst);
  const dhw = numberOrNull(st.dhw);
  const ph = numberOrNull(st.ph);
  const turb = numberOrNull(st.turb);
  document.getElementById("hud-sst").innerText = formatValue(sst, 1, " °C");
  document.getElementById("hud-dhw").innerText = formatValue(dhw, 1, " °C-wk");
  document.getElementById("hud-ph").innerText = formatValue(ph, 2);
  document.getElementById("hud-sst-meta").innerText = sourceTimestamp(st.sst_observation);
  document.getElementById("hud-dhw-meta").innerText = sourceTimestamp(st.dhw_observation);
  if (sst !== null) { sstInput.value = sst; document.getElementById("val-sst").innerText = formatValue(sst, 1, " °C"); }
  else document.getElementById("val-sst").innerText = "N/A";
  if (dhw !== null) { dhwInput.value = dhw; document.getElementById("val-dhw").innerText = formatValue(dhw, 1, " °C-weeks"); }
  else document.getElementById("val-dhw").innerText = "N/A";
  if (ph !== null) { phInput.value = ph; document.getElementById("val-ph").innerText = formatValue(ph, 2); }
  else document.getElementById("val-ph").innerText = "N/A";
  if (turb !== null) { turbInput.value = turb; document.getElementById("val-turb").innerText = formatValue(turb, 2, " NTU"); }
  else document.getElementById("val-turb").innerText = "N/A";
  triggerAIInference();
}

function mergeStationState(st, state) {
  const merged = Object.assign({}, st);
  if (state.station) {
    merged.name = state.station.name || merged.name;
    merged.lat = state.station.latitude;
    merged.lon = state.station.longitude;
  }
  if (state.sst) { merged.sst = state.sst.value; merged.sst_observation = state.sst; }
  if (state.dhw) { merged.dhw = state.dhw.value; merged.dhw_observation = state.dhw; }
  if (state.baseline) {
    merged.baseline = state.baseline;
    merged.baseline_fields = state.baseline_fields || CoralTwinAPI.mapBaselineFeatures(state.baseline);
    Object.assign(merged, merged.baseline_fields);
  }
  if (state.decision !== undefined) {
    merged.decision = CoralTwinAPI.normalizeDecision(state.decision);
    Object.assign(merged, CoralTwinAPI.mapDecisionFeatures(merged.decision));
  }
  merged.inference = state.inference || null;
  merged.latest_sync_run = state.latest_sync_run || null;
  merged.retrieved_at = state.retrieved_at || merged.retrieved_at;
  return merged;
}

async function refreshStationState(stationId) {
  const previous = stationStates[stationId];
  if (!previous) return;
  try {
    const state = await twinApiClient.getStationState(stationId);
    const merged = mergeStationState(previous, state);
    stationStates[stationId] = merged;
    const index = STATIONS_DB.findIndex(st => st.id === stationId);
    if (index >= 0) STATIONS_DB[index] = merged;
    if (selectedStation && selectedStation.id === stationId) {
      selectedStation = merged;
      renderStationState(merged);
    }
    const freshness = Object.values(state.freshness || {});
    const nextStatus = freshness.some(item => item.status === "stale")
      ? "stale"
      : freshness.length > 0 && freshness.every(item => item.status === "missing") ? "no-data" : "live";
    setConnectionState(nextStatus);
  } catch (error) {
    setConnectionState(error.code === "offline" ? "offline" : "partial");
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
  sel.onchange = (e) => {
    const found = STATIONS_DB.find(s => s.id === e.target.value);
    if (found) selectStation(found);
  };
}

// =============================================================================
// 6. THREE.JS 3D HIGH-RESOLUTION ORGANIC CORAL DIGITAL TWIN
// =============================================================================
let planktonParticles;

function initThreeJSCoral() {
  const container = document.getElementById("coral3d-canvas-container");
  const width = container.clientWidth || 500;
  const height = container.clientHeight || 280;

  threeScene = new THREE.Scene();
  threeCamera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
  threeCamera.position.set(0, 3.2, 7.8);

  threeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  threeRenderer.setSize(width, height);
  threeRenderer.setPixelRatio(window.devicePixelRatio);
  threeRenderer.toneMapping = THREE.ACESFilmicToneMapping;
  threeRenderer.toneMappingExposure = 1.1;
  container.appendChild(threeRenderer.domElement);

  // Deep Underwater Lighting
  const ambientLight = new THREE.AmbientLight(0xdcf8c6, 0.7);
  threeScene.add(ambientLight);

  const sunLight = new THREE.DirectionalLight(0x38bdf8, 1.3);
  sunLight.position.set(6, 12, 6);
  threeScene.add(sunLight);

  const bounceLight = new THREE.DirectionalLight(0x10b981, 0.5);
  bounceLight.position.set(-5, -4, -5);
  threeScene.add(bounceLight);

  const innerLight = new THREE.PointLight(0x5eead4, 0.8, 6);
  innerLight.position.set(0, 1.2, 0);
  threeScene.add(innerLight);

  coralMesh = new THREE.Group();

  // High-Quality Subsurface-Simulating Material
  coralMaterial = new THREE.MeshStandardMaterial({
    color: new THREE.Color(0x3D7E50), // Healthy Symbiodiniaceae Golden Green
    roughness: 0.82,
    metalness: 0.05,
    flatShading: false
  });

  // 1. Organic Base Carbonate Rock (Reef Substrate)
  const rockGeom = new THREE.DodecahedronGeometry(1.4, 2);
  const pos = rockGeom.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const vx = pos.getX(i);
    const vy = pos.getY(i);
    const vz = pos.getZ(i);
    const noise = 1.0 + (Math.sin(vx * 3.0) + Math.cos(vz * 3.0)) * 0.08;
    pos.setXYZ(i, vx * noise, Math.min(0.4, vy * 0.6), vz * noise);
  }
  rockGeom.computeVertexNormals();
  const rockMesh = new THREE.Mesh(rockGeom, coralMaterial);
  rockMesh.position.set(0, -0.2, 0);
  coralMesh.add(rockMesh);

  // 2. High-Resolution Branching Splines (Acropora Staghorn Morphology)
  const numMainBranches = 14;
  for (let i = 0; i < numMainBranches; i++) {
    const angle = (i / numMainBranches) * Math.PI * 2 + ((i % 3) * 0.15);
    const spread = 0.7 + (i % 3) * 0.25;
    const height = 1.8 + (i % 4) * 0.35;

    const p0 = new THREE.Vector3(Math.cos(angle) * 0.2, 0.1, Math.sin(angle) * 0.2);
    const p1 = new THREE.Vector3(Math.cos(angle) * spread * 0.45, height * 0.4, Math.sin(angle) * spread * 0.45);
    const p2 = new THREE.Vector3(Math.cos(angle + 0.1) * spread * 0.85, height * 0.75, Math.sin(angle + 0.1) * spread * 0.85);
    const p3 = new THREE.Vector3(Math.cos(angle) * (spread + 0.2), height, Math.sin(angle) * (spread + 0.2));

    const curve = new THREE.CatmullRomCurve3([p0, p1, p2, p3]);
    const branchGeom = new THREE.TubeGeometry(curve, 28, 0.14, 16, false);
    const branchMesh = new THREE.Mesh(branchGeom, coralMaterial);
    coralMesh.add(branchMesh);

    // Apical Axial Polyp at Tip
    const tipGeom = new THREE.SphereGeometry(0.13, 16, 16);
    const tipMesh = new THREE.Mesh(tipGeom, coralMaterial);
    tipMesh.position.copy(p3);
    coralMesh.add(tipMesh);

    // Radial Corallites (Pólipos incrustados en la corteza)
    for (let c = 1; c <= 5; c++) {
      const u = c / 6.0;
      const point = curve.getPoint(u);
      const tangent = curve.getTangent(u);
      
      const normal = new THREE.Vector3(Math.cos(angle + c), 0.2, Math.sin(angle + c)).normalize();
      const coralliteGeom = new THREE.ConeGeometry(0.05, 0.12, 10);
      const corallite = new THREE.Mesh(coralliteGeom, coralMaterial);
      corallite.position.copy(point).add(normal.clone().multiplyScalar(0.12));
      corallite.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
      coralMesh.add(corallite);
    }

    // Secondary Bifurcation (Brote secundario)
    if (i % 2 === 0) {
      const subP0 = curve.getPoint(0.55);
      const subAngle = angle + 0.55;
      const subP1 = subP0.clone().add(new THREE.Vector3(Math.cos(subAngle) * 0.4, 0.45, Math.sin(subAngle) * 0.4));
      const subCurve = new THREE.CatmullRomCurve3([subP0, subP1]);
      const subGeom = new THREE.TubeGeometry(subCurve, 12, 0.09, 12, false);
      const subMesh = new THREE.Mesh(subGeom, coralMaterial);
      coralMesh.add(subMesh);

      const subTip = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 12), coralMaterial);
      subTip.position.copy(subP1);
      coralMesh.add(subTip);
    }
  }

  threeScene.add(coralMesh);

  // 3. Floating Marine Plankton Particles in Water Column
  const planktonCount = 45;
  const planktonGeom = new THREE.BufferGeometry();
  const planktonPos = new Float32Array(planktonCount * 3);
  for (let p = 0; p < planktonCount * 3; p += 3) {
    planktonPos[p] = (Math.random() - 0.5) * 6;
    planktonPos[p + 1] = Math.random() * 4 - 0.5;
    planktonPos[p + 2] = (Math.random() - 0.5) * 6;
  }
  planktonGeom.setAttribute("position", new THREE.BufferAttribute(planktonPos, 3));
  const planktonMat = new THREE.PointsMaterial({
    color: 0x6fffe9,
    size: 0.04,
    transparent: true,
    opacity: 0.65
  });
  planktonParticles = new THREE.Points(planktonGeom, planktonMat);
  threeScene.add(planktonParticles);

  // Orbit Controls
  const controls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 1.0;
  controls.minDistance = 4.0;
  controls.maxDistance = 14.0;

  // Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    controls.update();

    // Drift plankton gently
    if (planktonParticles) {
      const pPositions = planktonParticles.geometry.attributes.position.array;
      for (let i = 1; i < pPositions.length; i += 3) {
        pPositions[i] += 0.003;
        if (pPositions[i] > 3.5) pPositions[i] = -0.5;
      }
      planktonParticles.geometry.attributes.position.needsUpdate = true;
    }

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
  const badge = document.getElementById("coral-health-badge");
  if (!Number.isFinite(stressFraction)) {
    coralMaterial.color = new THREE.Color(0x64748B);
    badge.innerText = "INFERENCE UNAVAILABLE";
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/20 text-slate-300 border border-slate-500/40";
    return;
  }
  let targetColor;

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
  const inference = selectedStation && selectedStation.inference;
  const available = inference && inference.status === "ok";
  const label = available ? inference.classification : "N/A";
  const loss = available ? numberOrNull(inference.coral_cover_loss_pct) : null;
  const riskLabel = label === "N/A" ? "N/A" : `${label.toUpperCase()} RISK`;
  const riskColor = label === "High" ? "text-rose-400" : label === "Medium" ? "text-amber-400" : label === "Low" ? "text-emerald-400" : "text-slate-400";
  const riskBg = label === "High" ? "bg-rose-500/10" : label === "Medium" ? "bg-amber-500/10" : "bg-slate-500/10";
  const riskBorder = label === "High" ? "border-rose-500/30" : label === "Medium" ? "border-amber-500/30" : "border-slate-500/30";
  const riskCard = document.getElementById("card-risk");
  riskCard.className = `p-3 rounded-lg border ${riskBorder} ${riskBg} text-center transition`;
  document.getElementById("out-risk-label").className = `text-lg font-bold ${riskColor} font-mono mt-0.5`;
  document.getElementById("out-risk-label").innerText = riskLabel;
  document.getElementById("out-loss-pct").innerText = loss === null ? "N/A" : `-${loss.toFixed(1)}%`;
  if (shapChartInstance) {
    shapChartInstance.data.datasets[0].data = available && Array.isArray(inference.shap_values)
      ? inference.shap_values : [null, null, null, null, null];
    shapChartInstance.update();
  }
  updateCoralBleachingShader(available ? (label === "High" ? 0.85 : label === "Medium" ? 0.5 : 0.1) : null);
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
    const priority = CoralTwinAPI.priorityPresentation(st.decision);
    const tierText = priority.available ? priority.label : "N/A";
    const tierClass = priority.available
      ? "border-current"
      : "bg-slate-500/20 text-slate-400 border-slate-500/30";
    const tierStyle = priority.available ? `color: ${priority.color};` : "";

    tr.innerHTML = `
      <td class="py-2.5 px-4 font-semibold text-slate-200">${st.name}</td>
      <td class="py-2.5 px-4 text-slate-400">${st.region}</td>
      <td class="py-2.5 px-4 text-cyan-300 font-bold">${formatValue(st.cover, 1, "%")}</td>
      <td class="py-2.5 px-4 text-amber-400">${formatValue(st.dhw, 1)}</td>
      <td class="py-2.5 px-4 text-teal-300">${formatValue(st.ph, 2)}</td>
      <td class="py-2.5 px-4 font-mono" style="${tierStyle}">${formatValue(st.srpi, 3)}</td>
      <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] border ${tierClass}" style="${tierStyle}">● ${tierText}</span></td>
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
        ...CoralTwinAPI.telemetryExportFeatures(st),
        seawater_pH: st.ph,
        reef_zone: st.reef_zone,
        macroalgae_cover_pct: st.macro,
        ...CoralTwinAPI.decisionExportFeatures(st.decision)
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
  // Synchronized telemetry inputs are display-only; inference is refreshed by station selection.

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
        const filtered = STATIONS_DB.filter(s => CoralTwinAPI.priorityPresentation(s.decision).tier === tier);
        populateTable(filtered);
      }
    });
  });

  // Export GeoJSON Button
  document.getElementById("btn-export-geojson").addEventListener("click", exportGeoJSON);

  // Close modal on ESC key
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAIAuditModal();
  });
}

// =============================================================================
// 11. AI AUDIT, EDA & BENCHMARK MODAL CONTROLS
// =============================================================================
function openAIAuditModal() {
  const modal = document.getElementById("ai-audit-modal");
  if (modal) {
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }
}

function closeAIAuditModal() {
  const modal = document.getElementById("ai-audit-modal");
  if (modal) {
    modal.classList.add("hidden");
    document.body.style.overflow = "";
  }
}

function switchAuditTab(tab) {
  const tabs = ["benchmark", "confusion", "eda", "hyperparams"];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const content = document.getElementById(`tab-content-${t}`);
    if (t === tab) {
      if (btn) {
        btn.className = "px-4 py-2.5 border-b-2 border-cyan-400 text-cyan-300 font-bold transition flex items-center gap-2";
      }
      if (content) content.classList.remove("hidden");
    } else {
      if (btn) {
        btn.className = "px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center gap-2";
      }
      if (content) content.classList.add("hidden");
    }
  });
}
