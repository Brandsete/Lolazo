/**
 * RiftTracker Centralized HTTP API Service Layer
 * Connects the React frontend with the FastAPI backend.
 *
 * Configures the base URL from import.meta.env.VITE_API_BASE_URL or falls back to
 * the Vite development proxy ('/api' -> http://127.0.0.1:8000).
 */

const RAW_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const API_BASE_URL = RAW_BASE.replace(/\/+$/, '');

/**
 * Common HTTP request handler with uniform error parsing and abort signal support
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const { signal, headers = {}, ...rest } = options;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...headers,
      },
      signal,
      ...rest,
    });

    if (!response.ok) {
      let errorData = null;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText || `HTTP Error ${response.status}` };
      }

      const errorMessage =
        (errorData && (errorData.detail || errorData.message)) ||
        `Error HTTP ${response.status}: Consulta fallida`;

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = errorData;
      error.errorType = errorData?.error_type || 'HTTP_ERROR';
      throw error;
    }

    return await response.json();
  } catch (err) {
    // If the request was deliberately aborted by AbortController, rethrow as AbortError
    if (err.name === 'AbortError') {
      throw err;
    }
    // Network or other fetch errors
    if (!err.status) {
      err.status = 0;
      err.detail = err.message || 'No se pudo conectar con el servidor backend';
    }
    throw err;
  }
}

/**
 * 1. Health check endpoint: GET /api/health
 */
export async function fetchBackendHealth(signal) {
  return apiFetch('/health', { signal });
}

/**
 * 2. Supported platform regions: GET /api/regions
 */
export async function fetchSupportedRegions(cluster = null, signal) {
  const query = cluster ? `?cluster=${encodeURIComponent(cluster)}` : '';
  return apiFetch(`/regions${query}`, { signal });
}

/**
 * 3. Riot API status endpoint: GET /api/riot/status
 * Informs whether the RIOT_API_KEY is configured in backend without leaking it.
 */
export async function fetchRiotStatus(signal) {
  return apiFetch('/riot/status', { signal });
}

/**
 * 4. Player profile & competitive ranks: GET /api/players/{game_name}/{tag_line}?region={region}
 */
export async function fetchPlayerProfile(gameName, tagLine, region, signal) {
  const cleanName = encodeURIComponent(gameName.trim());
  const cleanTag = encodeURIComponent(tagLine.replace(/^#/, '').trim());
  const cleanRegion = encodeURIComponent(region.trim());

  return apiFetch(`/players/${cleanName}/${cleanTag}?region=${cleanRegion}`, { signal });
}

/**
 * 5. Player consolidated statistical analysis: GET /api/players/{game_name}/{tag_line}/stats
 */
export async function fetchPlayerStats(
  gameName,
  tagLine,
  region,
  { queue = 'ranked', matches = 20 } = {},
  signal
) {
  const cleanName = encodeURIComponent(gameName.trim());
  const cleanTag = encodeURIComponent(tagLine.replace(/^#/, '').trim());
  const cleanRegion = encodeURIComponent(region.trim());
  const cleanQueue = encodeURIComponent(queue);
  const cleanMatches = encodeURIComponent(matches);

  return apiFetch(
    `/players/${cleanName}/${cleanTag}/stats?region=${cleanRegion}&queue=${cleanQueue}&matches=${cleanMatches}`,
    { signal }
  );
}

/**
 * 6. Top champions played breakdown: GET /api/players/{game_name}/{tag_line}/champions
 */
export async function fetchPlayerChampions(
  gameName,
  tagLine,
  region,
  { matches = 20 } = {},
  signal
) {
  const cleanName = encodeURIComponent(gameName.trim());
  const cleanTag = encodeURIComponent(tagLine.replace(/^#/, '').trim());
  const cleanRegion = encodeURIComponent(region.trim());
  const cleanMatches = encodeURIComponent(matches);

  return apiFetch(
    `/players/${cleanName}/${cleanTag}/champions?region=${cleanRegion}&matches=${cleanMatches}`,
    { signal }
  );
}

/**
 * 7. Position / Role distribution: GET /api/players/{game_name}/{tag_line}/roles
 */
export async function fetchPlayerRoles(
  gameName,
  tagLine,
  region,
  { matches = 20 } = {},
  signal
) {
  const cleanName = encodeURIComponent(gameName.trim());
  const cleanTag = encodeURIComponent(tagLine.replace(/^#/, '').trim());
  const cleanRegion = encodeURIComponent(region.trim());
  const cleanMatches = encodeURIComponent(matches);

  return apiFetch(
    `/players/${cleanName}/${cleanTag}/roles?region=${cleanRegion}&matches=${cleanMatches}`,
    { signal }
  );
}

/**
 * 8. Recent matches history: GET /api/players/{game_name}/{tag_line}/matches
 */
export async function fetchPlayerMatches(
  gameName,
  tagLine,
  region,
  { count = 10 } = {},
  signal
) {
  const cleanName = encodeURIComponent(gameName.trim());
  const cleanTag = encodeURIComponent(tagLine.replace(/^#/, '').trim());
  const cleanRegion = encodeURIComponent(region.trim());
  const cleanCount = encodeURIComponent(count);

  return apiFetch(
    `/players/${cleanName}/${cleanTag}/matches?region=${cleanRegion}&count=${cleanCount}`,
    { signal }
  );
}

/**
 * 9. Match detail by ID: GET /api/matches/{match_id}?region={region}
 */
export async function fetchMatchDetail(matchId, region, signal) {
  const cleanMatchId = encodeURIComponent(matchId.trim());
  const cleanRegion = encodeURIComponent(region.trim());

  return apiFetch(`/matches/${cleanMatchId}?region=${cleanRegion}`, { signal });
}

/**
 * 10. Consolidated Player Data Fetcher
 * Queries profile, overall stats, champions, roles, and match history concurrently.
 * Returns structured results with status indicators.
 */
export async function fetchCompletePlayerData(
  gameName,
  tagLine,
  region,
  { queue = 'ranked', matches = 20, matchCount = 10 } = {},
  signal
) {
  // First query the profile to resolve the player and verify existence
  const profile = await fetchPlayerProfile(gameName, tagLine, region, signal);

  // If profile exists, query stats, champions, roles, and matches in parallel
  const [statsResult, championsResult, rolesResult, matchesResult] = await Promise.allSettled([
    fetchPlayerStats(gameName, tagLine, region, { queue, matches }, signal),
    fetchPlayerChampions(gameName, tagLine, region, { matches }, signal),
    fetchPlayerRoles(gameName, tagLine, region, { matches }, signal),
    fetchPlayerMatches(gameName, tagLine, region, { count: matchCount }, signal),
  ]);

  return {
    profile,
    stats: statsResult.status === 'fulfilled' ? statsResult.value : null,
    champions: championsResult.status === 'fulfilled' ? championsResult.value : null,
    roles: rolesResult.status === 'fulfilled' ? rolesResult.value : null,
    matches: matchesResult.status === 'fulfilled' ? matchesResult.value : null,
    errors: {
      stats: statsResult.status === 'rejected' ? statsResult.reason : null,
      champions: championsResult.status === 'rejected' ? championsResult.reason : null,
      roles: rolesResult.status === 'rejected' ? rolesResult.reason : null,
      matches: matchesResult.status === 'rejected' ? matchesResult.reason : null,
    },
  };
}
