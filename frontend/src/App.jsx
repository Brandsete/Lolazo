import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  TrendingUp,
  Gamepad2,
  Sword,
  Award,
} from 'lucide-react';

import Header from './components/Header';
import SearchForm from './components/SearchForm';
import ProfileCard from './components/ProfileCard';
import StatCard from './components/StatCard';
import TopChampions from './components/TopChampions';
import PositionDistribution from './components/PositionDistribution';
import AdvancedMetrics from './components/AdvancedMetrics';
import MatchHistory from './components/MatchHistory';
import DemoBadge from './components/DemoBadge';
import {
  LoadingSkeleton,
  ErrorState,
  EmptyState,
  PartialDataBanner,
} from './components/StatusIndicators';

import {
  fetchBackendHealth,
  fetchSupportedRegions,
  fetchRiotStatus,
  fetchCompletePlayerData,
} from './services/api';

import {
  DEMO_SUMMONER_PROFILE,
  DEMO_SUMMARY_STATS,
  DEMO_TOP_CHAMPIONS,
  DEMO_POSITION_DISTRIBUTION,
  DEMO_ADVANCED_METRICS,
  DEMO_MATCH_HISTORY,
} from './services/mockData';

export default function App() {
  // Backend & API connectivity state
  const [backendHealth, setBackendHealth] = useState(null);
  const [regions, setRegions] = useState([]);
  const [riotStatus, setRiotStatus] = useState(null);

  // Active query parameters
  const [searchParams, setSearchParams] = useState({
    gameName: 'Faker',
    tagLine: 'KR1',
    region: 'kr',
  });

  // Track last executed search to prevent duplicate requests
  const lastExecutedSearchRef = useRef(null);

  // Ref to hold active AbortController and cancel in-flight queries
  const abortControllerRef = useRef(null);

  // UI state modes: 'normal' | 'loading' | 'empty' | 'error' | 'partial'
  const [viewMode, setViewMode] = useState('normal');
  const [isSearching, setIsSearching] = useState(false);
  const [showPartialNotice, setShowPartialNotice] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Mode flag: true if displaying demo/simulated fallback data
  const [isDemoMode, setIsDemoMode] = useState(true);

  // Real backend player data states
  const [profileData, setProfileData] = useState(DEMO_SUMMONER_PROFILE);
  const [statsData, setStatsData] = useState(null);
  const [championsData, setChampionsData] = useState(null);
  const [rolesData, setRolesData] = useState(null);
  const [matchesData, setMatchesData] = useState(null);

  // Initial backend check on mount
  const checkBackendServices = useCallback(async () => {
    try {
      const [health, regData, rStatus] = await Promise.allSettled([
        fetchBackendHealth(),
        fetchSupportedRegions(),
        fetchRiotStatus(),
      ]);

      if (health.status === 'fulfilled') {
        setBackendHealth(health.value);
      }
      if (regData.status === 'fulfilled') {
        setRegions(regData.value.regions || []);
      }
      if (rStatus.status === 'fulfilled') {
        setRiotStatus(rStatus.value);
      }
    } catch (err) {
      console.warn('Advertencia en conexión de backend inicial:', err);
    }
  }, []);

  useEffect(() => {
    checkBackendServices();

    // Clean up any ongoing request on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [checkBackendServices]);

  /**
   * Search handler connecting directly to FastAPI endpoints
   * Supports manual retry, request deduplication, and cancellation
   */
  const handleSearch = async (
    { gameName, tagLine, region },
    forceRetry = false
  ) => {
    const cleanName = gameName.trim();
    const cleanTag = tagLine.replace(/^#/, '').trim();
    const cleanRegion = region.trim().toLowerCase();

    if (!cleanName) return;

    // Deduplication check: prevent identical in-flight or repeated queries unless retrying
    const queryKey = `${cleanName.toLowerCase()}#${cleanTag.toLowerCase()}@${cleanRegion}`;
    if (
      !forceRetry &&
      isSearching &&
      lastExecutedSearchRef.current === queryKey
    ) {
      return;
    }

    // Cancel any pending in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    lastExecutedSearchRef.current = queryKey;
    setSearchParams({ gameName: cleanName, tagLine: cleanTag, region: cleanRegion });
    setIsSearching(true);
    setViewMode('loading');
    setErrorMessage('');

    try {
      const result = await fetchCompletePlayerData(
        cleanName,
        cleanTag,
        cleanRegion,
        { queue: 'ranked', matches: 20, matchCount: 10 },
        controller.signal
      );

      // Validate core response: must contain valid puuid and game_name
      if (!result.profile || !result.profile.puuid) {
        throw new Error('Respuesta inválida del servidor: falta identificador PUUID');
      }

      // Attach region display name if known from backend /api/regions
      const regionObj = regions.find((r) => r.platform_id.toLowerCase() === cleanRegion) || {
        name: cleanRegion.toUpperCase(),
        regional_cluster: result.profile.regional_cluster,
      };

      const enrichedProfile = {
        ...result.profile,
        region: {
          platformId: result.profile.region,
          name: regionObj.name,
          cluster: result.profile.regional_cluster,
        },
        isDemoData: false,
      };

      setProfileData(enrichedProfile);
      setStatsData(result.stats);
      setChampionsData(result.champions);
      setRolesData(result.roles);
      setMatchesData(result.matches);
      setIsDemoMode(false);

      // Check if partial data occurred (e.g. stats endpoint had errors or 0 matches)
      const hasErrorsInSubrequests = Boolean(
        result.errors.stats ||
        result.errors.champions ||
        result.errors.roles ||
        result.errors.matches
      );

      if (hasErrorsInSubrequests) {
        setShowPartialNotice(true);
        setViewMode('partial');
      } else {
        setViewMode('normal');
      }
    } catch (err) {
      // Ignore user-initiated aborts
      if (err.name === 'AbortError') {
        return;
      }

      console.error('Error al consultar jugador:', err);

      if (err.status === 404) {
        // Player not found
        setViewMode('empty');
      } else if (err.status === 401 || err.status === 403) {
        // RIOT_API_KEY invalid, placeholder, or expired
        const regionObj = regions.find((r) => r.platform_id.toLowerCase() === cleanRegion) || {
          platformId: cleanRegion,
          name: cleanRegion.toUpperCase(),
          cluster: 'americas',
        };

        // Fallback to simulated demo profile with explicit partial indicator
        setProfileData({
          ...DEMO_SUMMONER_PROFILE,
          gameName: cleanName,
          tagLine: cleanTag,
          region: {
            platformId: cleanRegion,
            name: regionObj.name,
            cluster: regionObj.regional_cluster || 'americas',
          },
          isDemoData: true,
        });
        setStatsData(null);
        setChampionsData(null);
        setRolesData(null);
        setMatchesData(null);
        setIsDemoMode(true);
        setShowPartialNotice(true);
        setViewMode('partial');
      } else {
        // General network or server error
        setErrorMessage(
          err.detail ||
          err.message ||
          `No se pudo obtener información para ${cleanName}#${cleanTag} (${cleanRegion.toUpperCase()}). Verifica que FastAPI esté ejecutándose en http://127.0.0.1:8000.`
        );
        setViewMode('error');
      }
    } finally {
      setIsSearching(false);
    }
  };

  /**
   * Reset to initial simulated demonstration state
   */
  const handleResetSearch = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    lastExecutedSearchRef.current = null;
    setSearchParams({ gameName: 'Faker', tagLine: 'KR1', region: 'kr' });
    setProfileData(DEMO_SUMMONER_PROFILE);
    setStatsData(null);
    setChampionsData(null);
    setRolesData(null);
    setMatchesData(null);
    setIsDemoMode(true);
    setViewMode('normal');
    setErrorMessage('');
  };

  // ---------------------------------------------------------------------------
  // Dynamic Metric Card Calculations (with null-safety and no invented numbers)
  // ---------------------------------------------------------------------------

  // Card 1: Win Rate (WR)
  const winRateVal = statsData
    ? `${statsData.win_rate}%`
    : profileData?.solo_rank
    ? `${profileData.solo_rank.win_rate}%`
    : isDemoMode
    ? `${DEMO_SUMMARY_STATS.winRate}%`
    : 'N/D';

  const winRateSub = statsData
    ? `${statsData.wins} Victorias - ${statsData.losses} Derrotas`
    : profileData?.solo_rank
    ? `${profileData.solo_rank.wins}V - ${profileData.solo_rank.losses}D`
    : isDemoMode
    ? `${DEMO_SUMMARY_STATS.wins} Victorias - ${DEMO_SUMMARY_STATS.losses} Derrotas`
    : '0 partidas clasificatorias';

  const winRateProg = statsData
    ? statsData.win_rate
    : profileData?.solo_rank
    ? profileData.solo_rank.win_rate
    : isDemoMode
    ? DEMO_SUMMARY_STATS.winRate
    : null;

  const winRateTrend = statsData
    ? `Muestra: ${statsData.matches_analyzed} partidas (${statsData.queue_filter})`
    : profileData?.solo_rank
    ? 'Clasificatoria Solo/Duo'
    : isDemoMode
    ? '+4.2% vs temporada anterior'
    : null;

  // Card 2: Analyzed Matches
  const matchesVal = statsData
    ? `${statsData.matches_analyzed}`
    : profileData?.solo_rank
    ? `${profileData.solo_rank.wins + profileData.solo_rank.losses}`
    : isDemoMode
    ? `${DEMO_SUMMARY_STATS.matchesAnalyzed}`
    : '0';

  const matchesSub = statsData
    ? `De ${statsData.matches_requested} solicitadas`
    : profileData?.solo_rank
    ? 'Total en temporada clasificatoria'
    : isDemoMode
    ? 'Muestra de partidas recientes'
    : 'Sin partidas registradas';

  const matchesProg = statsData && statsData.matches_requested > 0
    ? (statsData.matches_analyzed / statsData.matches_requested) * 100
    : isDemoMode
    ? 100
    : 0;

  const matchesTrend = statsData
    ? `Filtro: ${statsData.queue_filter.toUpperCase()}`
    : 'Filtro: Ranked Solo/Duo';

  // Card 3: Average KDA
  const kdaVal = statsData?.kda
    ? statsData.kda.perfect_kda
      ? 'Perfecto'
      : `${statsData.kda.kda_ratio}:1`
    : isDemoMode
    ? `${DEMO_SUMMARY_STATS.averageKda.ratio}:1`
    : 'N/D';

  const kdaSub = statsData?.kda
    ? `${statsData.kda.kills_avg} / ${statsData.kda.deaths_avg} / ${statsData.kda.assists_avg}`
    : isDemoMode
    ? `${DEMO_SUMMARY_STATS.averageKda.kills} / ${DEMO_SUMMARY_STATS.averageKda.deaths} / ${DEMO_SUMMARY_STATS.averageKda.assists}`
    : 'Sin datos de KDA';

  const kdaProg = statsData?.kda
    ? Math.min(100, (statsData.kda.kda_ratio / 6) * 100)
    : isDemoMode
    ? 78
    : null;

  const kdaTrend = statsData?.kda
    ? statsData.kda.perfect_kda
      ? '0 muertes registradas'
      : `Total: ${statsData.kda.total_kills}A / ${statsData.kda.total_deaths}M / ${statsData.kda.total_assists}As`
    : isDemoMode
    ? '71% Participación en asesinatos'
    : null;

  // Card 4: Competitive Rank
  const rankVal = profileData?.solo_rank
    ? `${profileData.solo_rank.tier} ${profileData.solo_rank.rank}`
    : isDemoMode
    ? DEMO_SUMMARY_STATS.competitiveRank
    : 'UNRANKED';

  const rankSub = profileData?.solo_rank
    ? `${profileData.solo_rank.league_points} LP`
    : isDemoMode
    ? 'Temporada 2026 - Split 1'
    : 'Sin clasificar';

  const rankProg = profileData?.solo_rank
    ? Math.min(100, Math.max(10, profileData.solo_rank.league_points))
    : isDemoMode
    ? 92
    : null;

  const rankTrend = profileData?.flex_rank
    ? `Flex: ${profileData.flex_rank.tier} ${profileData.flex_rank.rank} (${profileData.flex_rank.league_points} LP)`
    : isDemoMode
    ? 'Top 0.05% Regional'
    : 'Flex: Sin clasificar';

  return (
    <div className="app-container" id="app-root">
      {/* 1. Header with Title & Live Status */}
      <Header backendHealth={backendHealth} riotStatus={riotStatus} />

      {/* 2. Search Form (Riot ID, Tag, Region Selector, View Modes) */}
      <SearchForm
        regions={regions}
        onSearch={handleSearch}
        isLoading={isSearching}
        currentViewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Demonstration notice disclaimer when in demo mode */}
      {isDemoMode && <DemoBadge />}

      {/* 9. Partial Data Banner (when in 'partial' or normal mode with notice) */}
      {(viewMode === 'partial' || (viewMode === 'normal' && showPartialNotice && isDemoMode)) && (
        <PartialDataBanner onDismiss={() => setShowPartialNotice(false)} />
      )}

      {/* Main Dynamic View Area based on viewMode */}
      <main className="dashboard-main" id="dashboard-main">
        {/* Loading Skeleton Mode */}
        {viewMode === 'loading' && <LoadingSkeleton />}

        {/* Error State Mode */}
        {viewMode === 'error' && (
          <ErrorState
            title="Error al consultar estadísticas"
            message={
              errorMessage ||
              `No se pudo obtener información para ${searchParams.gameName}#${searchParams.tagLine}. Verifica la conexión con el backend de FastAPI.`
            }
            onRetry={() => handleSearch(searchParams, true)}
          />
        )}

        {/* Empty State Mode */}
        {viewMode === 'empty' && (
          <EmptyState
            gameName={searchParams.gameName}
            tagLine={searchParams.tagLine}
            onReset={handleResetSearch}
          />
        )}

        {/* Normal and Partial Modes: Full Dashboard View */}
        {(viewMode === 'normal' || viewMode === 'partial') && (
          <div className="dashboard-content-layout">
            {/* 3. Player Profile Card */}
            <ProfileCard profile={profileData} />

            {/* 4. Key Metric Cards (Winrate, matches, KDA, rank) */}
            <section
              className="grid-4-metrics"
              id="summary-metrics-grid"
              aria-label="Métricas Principales"
            >
              <StatCard
                id="metric-card-winrate"
                title="Tasa de Victoria (WR)"
                value={winRateVal}
                subvalue={winRateSub}
                icon={TrendingUp}
                variant="cyan"
                progressPercent={winRateProg}
                trend={winRateTrend}
              />

              <StatCard
                id="metric-card-matches"
                title="Partidas Analizadas"
                value={matchesVal}
                subvalue={matchesSub}
                icon={Gamepad2}
                variant="gold"
                progressPercent={matchesProg}
                trend={matchesTrend}
              />

              <StatCard
                id="metric-card-kda"
                title="KDA Promedio"
                value={kdaVal}
                subvalue={kdaSub}
                icon={Sword}
                variant="purple"
                progressPercent={kdaProg}
                trend={kdaTrend}
              />

              <StatCard
                id="metric-card-rank"
                title="Rango Competitivo"
                value={rankVal}
                subvalue={rankSub}
                icon={Award}
                variant="gold"
                progressPercent={rankProg}
                trend={rankTrend}
              />
            </section>

            {/* Split Row: 5. Top Champions & 6. Position Distribution */}
            <div className="grid-split-layout">
              {/* 5. Top 5 Most Played Champions */}
              <TopChampions
                champions={
                  championsData?.champions ||
                  (isDemoMode ? DEMO_TOP_CHAMPIONS : [])
                }
                isDemoData={isDemoMode}
              />

              {/* 6. Position Distribution Donut Chart */}
              <PositionDistribution
                positions={
                  rolesData?.roles ||
                  (isDemoMode ? DEMO_POSITION_DISTRIBUTION : [])
                }
                isDemoData={isDemoMode}
              />
            </div>

            {/* 8. Advanced Performance Metrics (CS/min, Vision, Gold, Objectives) */}
            <AdvancedMetrics
              stats={statsData}
              metrics={isDemoMode ? DEMO_ADVANCED_METRICS : null}
              isDemoData={isDemoMode}
            />

            {/* 7. Recent Match History */}
            <MatchHistory
              matches={
                matchesData?.matches ||
                (isDemoMode ? DEMO_MATCH_HISTORY : [])
              }
              isDemoData={isDemoMode}
            />
          </div>
        )}
      </main>

      {/* 10. Responsive Footer */}
      <footer className="app-footer" id="main-footer">
        <p>
          RiftTracker &bull; League of Legends Stats Platform &bull; Construido con FastAPI, React & Data Dragon
        </p>
      </footer>
    </div>
  );
}
