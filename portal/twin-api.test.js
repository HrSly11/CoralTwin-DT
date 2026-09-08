"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  TwinAPIClient,
  TwinAPIError,
  classifyFreshness,
  normalizeStationList,
  normalizeStationState,
  mapBaselineFeatures,
  normalizeBaseline,
  overlayObservations,
  normalizeDecision,
  mapDecisionFeatures,
  decisionExportFeatures,
  telemetryExportFeatures,
  priorityPresentation,
  needsMarkerRefresh,
} = require("./twin-api.js");

const NOW = new Date("2026-08-29T12:00:00Z");
const PRIORITY_DISPLAY = {
  Tier_1_High_Priority_Restoration: "Tier 1",
  Tier_2_Secondary_Conservation: "Tier 2",
  Tier_3_Low_Monitoring: "Tier 3",
};

function response(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Bad Gateway",
    async json() {
      return body;
    },
  };
}

function stationList() {
  return {
    count: 1,
    retrieved_at: "2026-08-29T12:00:00Z",
    stations: [{ station_id: "station-01", name: "Mesoamerican_Fore_01", latitude: 18.25, longitude: -87.8 }],
  };
}

function statePayload() {
  return {
    station_id: "station-01",
    retrieved_at: "2026-08-29T12:00:00Z",
    sst: { value: 29.4, observed_at: "2026-08-29T11:00:00Z", dataset_id: "noaacrwsstDaily", source: "noaa_crw_erddap" },
    dhw: null,
  };
}

function decisionPayload(overrides = {}) {
  return Object.assign({
    status: "available",
    station_name: "Mesoamerican_Fore_01",
    region: "Caribbean",
    reef_zone: "fore reef",
    macroalgae_cover_pct: 18.5,
    bleaching_severity_pct: 7.25,
    coral_cover_loss_pct: 4.5,
    srpi: 0.812,
    priority_tier: "Tier_1_High_Priority_Restoration",
    source: "processed_decision_csv",
  }, overrides);
}

test("normalizes decision snapshots and maps their operational fields", () => {
  const decision = normalizeDecision(decisionPayload());

  assert.deepEqual(decision, decisionPayload());
  assert.deepEqual(mapDecisionFeatures(decision), {
    region: "Caribbean",
    reef_zone: "fore reef",
    tier: "Tier 1",
    srpi: 0.812,
    macro: 18.5,
  });
  assert.equal(decision.priority_tier, "Tier_1_High_Priority_Restoration");
});

test("exports authoritative decision tiers and provenance without misleading null risk fields", () => {
  [
    "Tier_1_High_Priority_Restoration",
    "Tier_2_Secondary_Conservation",
    "Tier_3_Low_Monitoring",
  ].forEach((tier) => {
    const exported = decisionExportFeatures(decisionPayload({ priority_tier: tier }));
    assert.equal(exported.management_tier, tier);
    assert.equal(exported.management_tier_display, PRIORITY_DISPLAY[tier]);
    assert.equal(exported.decision_source, "processed_decision_csv");
    assert.equal(exported.coral_cover_loss_pct, 4.5);
  });
  assert.deepEqual(decisionExportFeatures({ status: "unavailable", reason: "offline" }), {});
});

test("exports live telemetry provenance separately from baseline values", () => {
  const baseline = { status: "available", source: "processed_harmonized_csv", source_date: "2026-08-28", features: { SST_degC: 27.1, DHW_degC_weeks: 1.2 } };
  const sstObservation = { value: 29.4, observed_at: "2026-08-29T11:00:00Z", source: "noaa_crw_erddap", dataset_id: "noaacrwsstDaily" };
  const dhwObservation = { value: 3.4, observed_at: "2026-08-29T11:00:00Z", source: "noaa_crw_erddap", dataset_id: "noaacrwdhwDaily" };
  const live = telemetryExportFeatures({
    sst_observation: sstObservation, dhw_observation: dhwObservation,
    baseline,
  });
  assert.deepEqual(live, {
    sea_surface_temp_degC: 29.4, degree_heating_weeks: 3.4,
    sst_telemetry_status: "available", dhw_telemetry_status: "available",
    sst_source: "noaa_crw_erddap", sst_dataset_id: "noaacrwsstDaily", sst_observed_at: "2026-08-29T11:00:00Z",
    dhw_source: "noaa_crw_erddap", dhw_dataset_id: "noaacrwdhwDaily", dhw_observed_at: "2026-08-29T11:00:00Z",
    baseline_sst_degC: 27.1, baseline_dhw_degC_weeks: 1.2,
    baseline_source: "processed_harmonized_csv", baseline_source_date: "2026-08-28",
  });
  const partial = telemetryExportFeatures({ sst_observation: sstObservation, baseline });
  assert.equal(partial.degree_heating_weeks, null);
  assert.equal(partial.dhw_telemetry_status, "missing");
  assert.equal(partial.baseline_dhw_degC_weeks, 1.2);
  const none = telemetryExportFeatures({ baseline });
  assert.equal(none.sea_surface_temp_degC, null);
  assert.equal(none.sst_telemetry_status, "missing");
  assert.equal(none.baseline_sst_degC, 27.1);
});

test("keeps unavailable decisions explicit and rejects malformed available snapshots", () => {
  assert.deepEqual(normalizeDecision({ status: "unavailable", reason: "baseline missing" }), {
    status: "unavailable",
    reason: "baseline missing",
  });
  assert.throws(() => normalizeDecision(decisionPayload({ srpi: "high" })), TwinAPIError);
  assert.throws(() => normalizeDecision(decisionPayload({ priority_tier: "Tier_9_Unknown" })), TwinAPIError);
  assert.deepEqual(priorityPresentation(normalizeDecision(null)), {
    tier: null,
    label: "N/A",
    color: "#64748B",
    available: false,
  });
});

test("presents truthful SRPI tiers and detects post-load globe marker refresh", () => {
  assert.deepEqual(priorityPresentation(normalizeDecision(decisionPayload({ priority_tier: "Tier_1_High_Priority_Restoration" }))), {
    tier: "Tier 1",
    label: "Tier 1: Restoration",
    color: "#F43F5E",
    available: true,
  });
  assert.deepEqual(priorityPresentation(normalizeDecision(decisionPayload({ priority_tier: "Tier_2_Secondary_Conservation" }))), {
    tier: "Tier 2",
    label: "Tier 2: Conservation",
    color: "#10B981",
    available: true,
  });
  assert.equal(priorityPresentation(normalizeDecision(decisionPayload({ priority_tier: "Tier_3_Low_Monitoring" }))).label, "Tier 3: Monitoring");
  assert.equal(needsMarkerRefresh([], [{ id: "station-01" }]), true);
  assert.equal(needsMarkerRefresh(["station-01"], [{ id: "station-01" }]), false);
});

test("carries decision snapshots through station list and detail normalization", () => {
  const list = stationList();
  list.stations[0].region = "stale legacy region";
  list.stations[0].tier = "Tier 1";
  list.stations[0].decision = decisionPayload({ priority_tier: "Tier_3_Low_Monitoring", region: "Pacific" });
  const normalizedList = normalizeStationList(list);
  assert.equal(normalizedList.stations[0].decision.priority_tier, "Tier_3_Low_Monitoring");
  assert.equal(normalizedList.stations[0].tier, "Tier 3");
  assert.equal(normalizedList.stations[0].region, "Pacific");

  const state = statePayload();
  state.decision = decisionPayload({ macroalgae_cover_pct: 33.1 });
  const normalizedState = normalizeStationState(state, "station-01", { now: NOW });
  assert.equal(normalizedState.decision.macroalgae_cover_pct, 33.1);
  assert.equal(normalizedState.macro, 33.1);
});

test("normalizes station lists without inventing missing observations", () => {
  const normalized = normalizeStationList(stationList());

  assert.equal(normalized.count, 1);
  assert.deepEqual(normalized.stations[0], {
    id: "station-01",
    name: "Mesoamerican_Fore_01",
    lat: 18.25,
    lon: -87.8,
    sst: null,
    dhw: null,
  });
  assert.equal(normalized.retrieved_at, "2026-08-29T12:00:00Z");
});

test("maps every baseline feature to a deterministic legacy field", () => {
  const baseline = normalizeBaseline({
    status: "ok",
    source: "static_baseline",
    source_date: "2024-01-01",
    features: {
      Depth_m: 12.5,
      SST_degC: 28.1,
      SST_Anomaly_degC: 0.4,
      DHW_degC_weeks: 1,
      pH_total: 8.1,
      Aragonite_Saturation_Omega: 3.8,
      Turbidity_NTU: 0.7,
      PAR_umol_m2_s: 1000,
      Structural_Rugosity: 2.5,
      Live_Coral_Cover_Pct: 35,
    },
  });

  assert.deepEqual(mapBaselineFeatures(baseline), {
    depth: 12.5, baseline_sst: 28.1, sst_anomaly: 0.4, baseline_dhw: 1,
    ph: 8.1, aragonite: 3.8, turb: 0.7, par: 1000, rugosity: 2.5, cover: 35,
  });
});

test("overlays only actual NOAA observations and retains prior values for missing products", () => {
  const station = { id: "station-01", sst: { value: 28 }, dhw: { value: 2 } };
  const updated = overlayObservations(station, { sst: { value: 29 }, dhw: null });

  assert.deepEqual(updated, { id: "station-01", sst: { value: 29 }, dhw: { value: 2 } });
});

test("normalizes state with explicit null products and classifies stale timestamps", () => {
  const state = normalizeStationState(statePayload(), "station-01", { now: NOW, staleThresholdMs: 30 * 60 * 1000 });

  assert.equal(state.station_id, "station-01");
  assert.equal(state.sst.value, 29.4);
  assert.equal(state.dhw, null);
  assert.equal(state.freshness.sst.status, "stale");
  assert.equal(state.freshness.dhw.status, "missing");
  assert.equal(classifyFreshness(state.sst, NOW, 2 * 60 * 60 * 1000).status, "fresh");
});

test("uses same-origin endpoints and supports optional sync station body", async () => {
  const calls = [];
  const client = new TwinAPIClient({
    fetch: async (url, options = {}) => {
      calls.push({ url, options });
      if (url === "/api/stations") return response(stationList());
      if (url === "/api/stations/station-01/state") return response(statePayload());
      if (url === "/api/sync") return response({ status: "accepted" });
      return response({ run_id: 7, status: "success" });
    },
    now: () => NOW,
  });

  await client.listStations();
  await client.getStationState("station-01");
  await client.sync("station-01");
  await client.sync();
  await client.latestSyncRun();

  assert.deepEqual(calls.map((call) => call.url), [
    "/api/stations",
    "/api/stations/station-01/state",
    "/api/sync",
    "/api/sync",
    "/api/sync-runs/latest",
  ]);
  assert.equal(JSON.parse(calls[2].options.body).station_id, "station-01");
  assert.equal(calls[3].options.body, undefined);
});

test("turns transport failures into structured offline errors", async () => {
  const client = new TwinAPIClient({ fetch: async () => { throw new TypeError("network down"); } });

  await assert.rejects(
    client.listStations(),
    (error) => error instanceof TwinAPIError && error.code === "offline" && error.path === "/api/stations",
  );
});

test("turns non-2xx responses and malformed payloads into explicit errors", async () => {
  const httpClient = new TwinAPIClient({ fetch: async () => response({ detail: "upstream unavailable" }, 502) });
  await assert.rejects(httpClient.listStations(), (error) => error.code === "http_error" && error.status === 502);

  const invalidClient = new TwinAPIClient({ fetch: async () => response({ stations: "not-an-array" }) });
  await assert.rejects(invalidClient.listStations(), (error) => error.code === "invalid_payload");
});
