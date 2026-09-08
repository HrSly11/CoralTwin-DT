(function (root, factory) {
  "use strict";

  const api = factory();
  root.CoralTwinAPI = api;
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  const DEFAULT_STALE_THRESHOLD_MS = 24 * 60 * 60 * 1000;
  const BASELINE_FEATURE_NAMES = [
    "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks", "pH_total",
    "Aragonite_Saturation_Omega", "Turbidity_NTU", "PAR_umol_m2_s",
    "Structural_Rugosity", "Live_Coral_Cover_Pct",
  ];
  const PRIORITY_TIER_DEFINITIONS = {
    Tier_1_High_Priority_Restoration: { key: "Tier 1", label: "Tier 1: Restoration", color: "#F43F5E" },
    Tier_2_Secondary_Conservation: { key: "Tier 2", label: "Tier 2: Conservation", color: "#10B981" },
    Tier_3_Low_Monitoring: { key: "Tier 3", label: "Tier 3: Monitoring", color: "#38BDF8" },
  };

  class TwinAPIError extends Error {
    constructor(message, details) {
      super(message);
      this.name = "TwinAPIError";
      this.code = details && details.code ? details.code : "api_error";
      this.path = details && details.path ? details.path : null;
      this.status = details && details.status != null ? details.status : null;
      if (details && details.cause) this.cause = details.cause;
    }
  }

  function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function finiteNumber(value, description) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new TwinAPIError(description + " must be a finite number", { code: "invalid_payload" });
    }
    return value;
  }

  function timestamp(value, description) {
    if (typeof value !== "string" || Number.isNaN(Date.parse(value))) {
      throw new TwinAPIError(description + " must be an ISO timestamp", { code: "invalid_payload" });
    }
    return value;
  }

  function observationValue(value) {
    if (value === null) return null;
    if (!isObject(value)) {
      throw new TwinAPIError("observation must be an object or null", { code: "invalid_payload" });
    }
    const result = {
      value: finiteNumber(value.value, "observation value"),
      observed_at: timestamp(value.observed_at, "observation observed_at"),
      dataset_id: value.dataset_id === undefined || value.dataset_id === null ? null : String(value.dataset_id),
    };
    if (value.source !== undefined) result.source = String(value.source);
    if (value.product !== undefined) result.product = String(value.product);
    if (value.unit !== undefined) result.unit = String(value.unit);
    return result;
  }

  function stationId(value) {
    const id = value.station_id !== undefined ? value.station_id : value.id;
    if (typeof id !== "string" || id.length === 0) {
      throw new TwinAPIError("station station_id must be a non-empty string", { code: "invalid_payload" });
    }
    return id;
  }

  function optionalNumber(value) {
    return value === null || value === undefined ? null : finiteNumber(value, "baseline feature");
  }

  function normalizeBaseline(raw) {
    if (raw === null || raw === undefined) {
      return { status: "missing", source: "static_baseline", source_date: null, features: {} };
    }
    if (!isObject(raw)) {
      throw new TwinAPIError("baseline must be an object", { code: "invalid_payload" });
    }
    const rawFeatures = isObject(raw.features) ? raw.features : {};
    const features = {};
    BASELINE_FEATURE_NAMES.forEach(function (name) {
      if (rawFeatures[name] !== undefined) features[name] = optionalNumber(rawFeatures[name]);
    });
    return {
      status: raw.status === undefined ? "ok" : String(raw.status),
      source: raw.source === undefined ? "static_baseline" : String(raw.source),
      source_date: raw.source_date === null || raw.source_date === undefined ? null : String(raw.source_date),
      features: features,
    };
  }

  function mapBaselineFeatures(baseline) {
    const features = baseline && isObject(baseline.features) ? baseline.features : {};
    return {
      depth: optionalNumber(features.Depth_m),
      baseline_sst: optionalNumber(features.SST_degC),
      sst_anomaly: optionalNumber(features.SST_Anomaly_degC),
      baseline_dhw: optionalNumber(features.DHW_degC_weeks),
      ph: optionalNumber(features.pH_total),
      aragonite: optionalNumber(features.Aragonite_Saturation_Omega),
      turb: optionalNumber(features.Turbidity_NTU),
      par: optionalNumber(features.PAR_umol_m2_s),
      rugosity: optionalNumber(features.Structural_Rugosity),
      cover: optionalNumber(features.Live_Coral_Cover_Pct),
    };
  }

  function normalizeDecision(raw) {
    if (raw === null || raw === undefined) return { status: "unavailable" };
    if (!isObject(raw)) {
      throw new TwinAPIError("decision must be an object or null", { code: "invalid_payload" });
    }
    const status = raw.status === undefined ? "unavailable" : String(raw.status);
    if (status !== "available") {
      const unavailable = { status: status };
      if (raw.reason !== undefined && raw.reason !== null) unavailable.reason = String(raw.reason);
      return unavailable;
    }
    const textFields = ["station_name", "region", "reef_zone", "priority_tier", "source"];
    const numericFields = ["macroalgae_cover_pct", "bleaching_severity_pct", "coral_cover_loss_pct", "srpi"];
    const decision = { status: "available" };
    textFields.forEach(function (field) {
      if (typeof raw[field] !== "string" || raw[field].length === 0) {
        throw new TwinAPIError("decision " + field + " must be a non-empty string", { code: "invalid_payload" });
      }
      if (field === "priority_tier" && !PRIORITY_TIER_DEFINITIONS[raw[field]]) {
        throw new TwinAPIError("decision priority_tier is not a known canonical tier", { code: "invalid_payload" });
      }
      decision[field] = raw[field];
    });
    numericFields.forEach(function (field) {
      decision[field] = finiteNumber(raw[field], "decision " + field);
    });
    return decision;
  }

  function mapDecisionFeatures(decision) {
    const normalized = normalizeDecision(decision);
    if (normalized.status !== "available") {
      return { region: null, reef_zone: null, tier: null, srpi: null, macro: null };
    }
    return {
      region: normalized.region,
      reef_zone: normalized.reef_zone,
      tier: PRIORITY_TIER_DEFINITIONS[normalized.priority_tier].key,
      srpi: normalized.srpi,
      macro: normalized.macroalgae_cover_pct,
    };
  }

  function decisionExportFeatures(decision) {
    const normalized = normalizeDecision(decision);
    if (normalized.status !== "available") return {};
    return {
      bleaching_severity_pct: normalized.bleaching_severity_pct,
      coral_cover_loss_pct: normalized.coral_cover_loss_pct,
      management_tier: normalized.priority_tier,
      management_tier_display: PRIORITY_TIER_DEFINITIONS[normalized.priority_tier].key,
      srpi_priority_score: normalized.srpi,
      decision_source: normalized.source,
    };
  }

  function telemetryExportFeatures(station) {
    const value = isObject(station) ? station : {};
    const sst = observationValue(value.sst_observation === undefined ? null : value.sst_observation);
    const dhw = observationValue(value.dhw_observation === undefined ? null : value.dhw_observation);
    const baseline = normalizeBaseline(value.baseline);
    const features = baseline.features || {};
    return {
      sea_surface_temp_degC: sst ? sst.value : null,
      degree_heating_weeks: dhw ? dhw.value : null,
      sst_telemetry_status: sst ? "available" : "missing",
      dhw_telemetry_status: dhw ? "available" : "missing",
      sst_source: sst ? sst.source : null,
      sst_dataset_id: sst ? sst.dataset_id : null,
      sst_observed_at: sst ? sst.observed_at : null,
      dhw_source: dhw ? dhw.source : null,
      dhw_dataset_id: dhw ? dhw.dataset_id : null,
      dhw_observed_at: dhw ? dhw.observed_at : null,
      baseline_sst_degC: optionalNumber(features.SST_degC),
      baseline_dhw_degC_weeks: optionalNumber(features.DHW_degC_weeks),
      baseline_source: baseline.source,
      baseline_source_date: baseline.source_date,
    };
  }

  function priorityPresentation(decision) {
    const normalized = normalizeDecision(decision);
    if (normalized.status !== "available") {
      return { tier: null, label: "N/A", color: "#64748B", available: false };
    }
    const presentation = PRIORITY_TIER_DEFINITIONS[normalized.priority_tier];
    if (!presentation) return { tier: null, label: "N/A", color: "#64748B", available: false };
    return { tier: presentation.key, label: presentation.label, color: presentation.color, available: true };
  }

  function needsMarkerRefresh(previousIds, stations) {
    const currentIds = Array.isArray(stations) ? stations.map(function (station) { return station.id; }) : [];
    if (!Array.isArray(previousIds) || previousIds.length !== currentIds.length) return true;
    return previousIds.some(function (id, index) { return id !== currentIds[index]; });
  }

  function overlayObservations(station, state) {
    const result = Object.assign({}, station);
    if (state && state.sst !== null && state.sst !== undefined) result.sst = state.sst;
    if (state && state.dhw !== null && state.dhw !== undefined) result.dhw = state.dhw;
    return result;
  }

  function normalizeStationList(payload) {
    if (!isObject(payload) || !Array.isArray(payload.stations)) {
      throw new TwinAPIError("stations payload must contain an array", { code: "invalid_payload" });
    }
    if (!Number.isInteger(payload.count) || payload.count !== payload.stations.length) {
      throw new TwinAPIError("stations payload count does not match its array", { code: "invalid_payload" });
    }
    const retrievedAt = timestamp(payload.retrieved_at, "stations retrieved_at");
    const stations = payload.stations.map(function (raw) {
      if (!isObject(raw)) {
        throw new TwinAPIError("station entry must be an object", { code: "invalid_payload" });
      }
      const id = stationId(raw);
      const name = raw.name !== undefined ? raw.name : raw.station_name;
      if (typeof name !== "string" || name.length === 0) {
        throw new TwinAPIError("station name must be a non-empty string", { code: "invalid_payload" });
      }
      const latitude = raw.latitude !== undefined ? raw.latitude : raw.lat;
      const longitude = raw.longitude !== undefined ? raw.longitude : raw.lon;
      const station = {
        id: id,
        name: name,
        lat: finiteNumber(latitude, "station latitude"),
        lon: finiteNumber(longitude, "station longitude"),
        sst: raw.sst === undefined ? null : raw.sst,
        dhw: raw.dhw === undefined ? null : raw.dhw,
      };
      if (raw.baseline !== undefined) {
        station.baseline = normalizeBaseline(raw.baseline);
        station.baseline_fields = mapBaselineFeatures(station.baseline);
      }
      if (raw.decision !== undefined) {
        station.decision = normalizeDecision(raw.decision);
        Object.assign(station, mapDecisionFeatures(station.decision));
      }
      const legacyFields = raw.decision === undefined
        ? ["region", "reef_zone", "tier", "cover", "ph", "turb", "macro", "rugosity"]
        : ["cover", "ph", "turb", "rugosity"];
      legacyFields.forEach(function (key) {
        if (raw[key] !== undefined) station[key] = raw[key];
      });
      return station;
    });
    return { stations: stations, count: payload.count, retrieved_at: retrievedAt };
  }

  function classifyFreshness(observation, now, staleThresholdMs) {
    if (observation === null || observation === undefined) {
      return { status: "missing", observed_at: null, age_ms: null };
    }
    const observedAt = typeof observation === "string" ? observation : observation.observed_at;
    if (typeof observedAt !== "string" || Number.isNaN(Date.parse(observedAt))) {
      return { status: "invalid", observed_at: observedAt || null, age_ms: null };
    }
    const nowValue = now instanceof Date ? now.getTime() : new Date(now || Date.now()).getTime();
    const observedValue = Date.parse(observedAt);
    const age = Math.max(0, nowValue - observedValue);
    const threshold = staleThresholdMs === undefined ? DEFAULT_STALE_THRESHOLD_MS : staleThresholdMs;
    if (typeof threshold !== "number" || !Number.isFinite(threshold) || threshold < 0) {
      throw new TwinAPIError("stale threshold must be a non-negative number", { code: "invalid_payload" });
    }
    return { status: age <= threshold ? "fresh" : "stale", observed_at: observedAt, age_ms: age };
  }

  function normalizeStationState(payload, requestedStationId, options) {
    if (!isObject(payload)) {
      throw new TwinAPIError("station state payload must be an object", { code: "invalid_payload" });
    }
    const stationMetadata = isObject(payload.station) ? payload.station : payload;
    const id = stationId(stationMetadata);
    if (requestedStationId !== undefined && id !== requestedStationId) {
      throw new TwinAPIError("station state does not match requested station", { code: "invalid_payload" });
    }
    const retrievedAt = payload.retrieved_at === undefined
      ? new Date().toISOString()
      : timestamp(payload.retrieved_at, "state retrieved_at");
    const nested = isObject(payload.latest_state) ? payload.latest_state : (isObject(payload.observations) ? payload.observations : payload);
    const sst = observationValue(nested.sst === undefined ? null : nested.sst);
    const dhw = observationValue(nested.dhw === undefined ? null : nested.dhw);
    const normalized = {};
    Object.keys(payload).forEach(function (key) { normalized[key] = payload[key]; });
    normalized.station_id = id;
    if (isObject(payload.station)) normalized.station = payload.station;
    normalized.retrieved_at = retrievedAt;
    normalized.sst = sst;
    normalized.dhw = dhw;
    if (payload.baseline !== undefined) {
      normalized.baseline = normalizeBaseline(payload.baseline);
      normalized.baseline_fields = mapBaselineFeatures(normalized.baseline);
    }
    if (payload.decision !== undefined) {
      normalized.decision = normalizeDecision(payload.decision);
      Object.assign(normalized, mapDecisionFeatures(normalized.decision));
    }
    delete normalized.risk;
    const freshnessOptions = options || {};
    normalized.freshness = {
      sst: classifyFreshness(sst, freshnessOptions.now, freshnessOptions.staleThresholdMs),
      dhw: classifyFreshness(dhw, freshnessOptions.now, freshnessOptions.staleThresholdMs),
    };
    return normalized;
  }

  function normalizeResponseObject(payload, description) {
    if (!isObject(payload)) {
      throw new TwinAPIError(description + " must be an object", { code: "invalid_payload" });
    }
    return payload;
  }

  function joinUrl(baseUrl, path) {
    if (!baseUrl) return path;
    return String(baseUrl).replace(/\/$/, "") + path;
  }

  class TwinAPIClient {
    constructor(options) {
      const config = options || {};
      this.baseUrl = config.baseUrl || "";
      this.fetch = config.fetch || (typeof fetch === "function" ? fetch.bind(typeof globalThis === "object" ? globalThis : null) : null);
      this.now = config.now || function () { return new Date(); };
      this.staleThresholdMs = config.staleThresholdMs === undefined ? DEFAULT_STALE_THRESHOLD_MS : config.staleThresholdMs;
    }

    async request(path, options) {
      if (!this.fetch) {
        throw new TwinAPIError("Fetch is unavailable", { code: "offline", path: path });
      }
      let response;
      try {
        response = await this.fetch(joinUrl(this.baseUrl, path), options || {});
      } catch (error) {
        throw new TwinAPIError("API request failed while offline", { code: "offline", path: path, cause: error });
      }
      if (!response || typeof response.ok !== "boolean") {
        throw new TwinAPIError("API response is malformed", { code: "invalid_payload", path: path });
      }
      if (!response.ok) {
        throw new TwinAPIError("API request returned HTTP " + response.status, {
          code: "http_error", path: path, status: response.status,
        });
      }
      let body;
      try {
        body = await response.json();
      } catch (error) {
        throw new TwinAPIError("API response is not valid JSON", { code: "invalid_payload", path: path, cause: error });
      }
      return body;
    }

    async listStations() {
      return normalizeStationList(await this.request("/api/stations"));
    }

    async getStationState(stationIdValue) {
      if (typeof stationIdValue !== "string" || stationIdValue.length === 0) {
        throw new TwinAPIError("station id must be a non-empty string", { code: "invalid_payload", path: "/api/stations" });
      }
      const encodedId = encodeURIComponent(stationIdValue);
      return normalizeStationState(
        await this.request("/api/stations/" + encodedId + "/state"),
        stationIdValue,
        { now: this.now(), staleThresholdMs: this.staleThresholdMs },
      );
    }

    async sync(stationIdValue) {
      const requestOptions = { method: "POST" };
      if (stationIdValue !== undefined) {
        if (typeof stationIdValue !== "string" || stationIdValue.length === 0) {
          throw new TwinAPIError("station id must be a non-empty string", { code: "invalid_payload", path: "/api/sync" });
        }
        requestOptions.headers = { "Content-Type": "application/json" };
        requestOptions.body = JSON.stringify({ station_id: stationIdValue });
      }
      return normalizeResponseObject(await this.request("/api/sync", requestOptions), "sync response");
    }

    async latestSyncRun() {
      const payload = await this.request("/api/sync-runs/latest");
      return payload === null ? null : normalizeResponseObject(payload, "sync run response");
    }
  }

  return {
    DEFAULT_STALE_THRESHOLD_MS: DEFAULT_STALE_THRESHOLD_MS,
    TwinAPIClient: TwinAPIClient,
    TwinApiClient: TwinAPIClient,
    TwinAPIError: TwinAPIError,
    classifyFreshness: classifyFreshness,
    normalizeStationList: normalizeStationList,
    normalizeStations: normalizeStationList,
    normalizeStationState: normalizeStationState,
    normalizeBaseline: normalizeBaseline,
    mapBaselineFeatures: mapBaselineFeatures,
    overlayObservations: overlayObservations,
    normalizeDecision: normalizeDecision,
    mapDecisionFeatures: mapDecisionFeatures,
    decisionExportFeatures: decisionExportFeatures,
    telemetryExportFeatures: telemetryExportFeatures,
    priorityPresentation: priorityPresentation,
    needsMarkerRefresh: needsMarkerRefresh,
    BASELINE_FEATURE_NAMES: BASELINE_FEATURE_NAMES,
  };
});
