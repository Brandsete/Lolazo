import React from 'react';
import { Target, Coins, Eye, Crosshair, ShieldAlert } from 'lucide-react';
import DemoBadge from './DemoBadge';

export default function AdvancedMetrics({ stats, metrics, isDemoData = false }) {
  // Support either FastAPI PlayerOverallStatsResponse (stats) or legacy demo object (metrics)
  const isFromStats = Boolean(stats);

  // 1. CS Per Min
  const csVal = isFromStats
    ? (stats.cs_per_min ?? null)
    : (metrics?.csPerMin?.value ?? null);
  const csTotal = isFromStats ? stats.total_cs : null;
  const csGrade = csVal !== null
    ? (csVal >= 9.0 ? 'S+' : csVal >= 8.0 ? 'S' : csVal >= 7.0 ? 'A' : csVal >= 5.5 ? 'B' : 'C')
    : (metrics?.csPerMin?.rating || 'N/D');

  // 2. Vision Score
  const visionVal = isFromStats
    ? (stats.vision?.average_vision_score ?? null)
    : (metrics?.visionScore?.value ?? null);
  const visionTotal = isFromStats ? stats.vision?.total_vision_score : null;
  const visionGrade = visionVal !== null
    ? (visionVal >= 30 ? 'S+' : visionVal >= 25 ? 'S' : visionVal >= 18 ? 'A' : visionVal >= 10 ? 'B' : 'C')
    : (metrics?.visionScore?.rating || 'N/D');

  // 3. Gold per Match
  const goldVal = isFromStats
    ? (stats.gold?.average_gold ?? null)
    : (metrics?.goldPerMatch?.value ?? null);
  const goldPerMin = isFromStats
    ? (stats.gold?.gold_per_min ?? null)
    : (metrics?.goldPerMatch?.goldPerMin ?? null);
  const goldGrade = goldPerMin !== null
    ? (goldPerMin >= 500 ? 'S+' : goldPerMin >= 440 ? 'S' : goldPerMin >= 360 ? 'A' : 'B')
    : (metrics?.goldPerMatch?.rating || 'N/D');

  // 4. Objectives Participation
  const objectives = isFromStats ? stats.objectives : null;
  const objAvailable = isFromStats
    ? Boolean(objectives?.is_available)
    : Boolean(metrics?.objectiveParticipation);

  const dragonPart = isFromStats
    ? (objectives?.dragon_participation !== null && objectives?.dragon_participation !== undefined
        ? `${objectives.dragon_participation}%`
        : 'N/D')
    : (metrics?.objectiveParticipation?.dragons || 'N/D');

  const baronPart = isFromStats
    ? (objectives?.baron_participation !== null && objectives?.baron_participation !== undefined
        ? `${objectives.baron_participation}%`
        : 'N/D')
    : (metrics?.objectiveParticipation?.barons || 'N/D');

  const turretPart = isFromStats
    ? (objectives?.turret_participation !== null && objectives?.turret_participation !== undefined
        ? `${objectives.turret_participation}%`
        : 'N/D')
    : (metrics?.objectiveParticipation?.towers || 'N/D');

  // Calculate composite objective percentage if numbers available
  let overallObjPercent = null;
  if (isFromStats) {
    if (objAvailable) {
      const parts = [
        objectives?.dragon_participation,
        objectives?.baron_participation,
        objectives?.turret_participation,
      ].filter((v) => typeof v === 'number');

      if (parts.length > 0) {
        overallObjPercent = Math.round(parts.reduce((a, b) => a + b, 0) / parts.length);
      }
    }
  } else if (metrics?.objectiveParticipation?.value) {
    overallObjPercent = metrics.objectiveParticipation.value;
  }

  return (
    <section className="dashboard-panel" id="advanced-metrics-panel">
      <div className="panel-header">
        <div className="panel-title-wrapper">
          <Crosshair className="panel-icon" size={20} />
          <h3 className="panel-title">Métricas Avanzadas de Rendimiento</h3>
        </div>
        {isDemoData && <DemoBadge compact />}
      </div>

      <div className="advanced-metrics-grid" id="advanced-metrics-grid">
        {/* 1. CS por Minuto */}
        <div className="advanced-metric-card" id="metric-cs-per-min">
          <div className="adv-header">
            <span className="adv-label">
              <Target size={15} /> CS por Minuto
            </span>
            <span className={`tier-grade-badge ${csVal !== null ? 'grade-s' : 'grade-muted'}`}>
              {csGrade}
            </span>
          </div>
          <div className="adv-main-value">
            {csVal !== null ? csVal : 'N/D'}
          </div>
          <div className="adv-meta-text">
            {csTotal !== null
              ? `${csTotal} súbditos totales`
              : (metrics?.csPerMin?.comparison || 'No disponible')}
          </div>
          <div className="adv-progress-bar">
            <div
              className="adv-progress-fill fill-cyan"
              style={{ width: `${csVal !== null ? Math.min(100, (csVal / 10) * 100) : 0}%` }}
            />
          </div>
        </div>

        {/* 2. Visión Promedio */}
        <div className="advanced-metric-card" id="metric-vision-score">
          <div className="adv-header">
            <span className="adv-label">
              <Eye size={15} /> Puntuación de Visión
            </span>
            <span className={`tier-grade-badge ${visionVal !== null ? 'grade-a' : 'grade-muted'}`}>
              {visionGrade}
            </span>
          </div>
          <div className="adv-main-value">
            {visionVal !== null ? visionVal : 'N/D'}
          </div>
          <div className="adv-meta-text">
            {visionTotal !== null
              ? `${visionTotal} puntos acumulados`
              : (metrics?.visionScore?.controlWardsBought
                  ? `${metrics.visionScore.controlWardsBought} Wards de Control / partida`
                  : 'Sin datos de visión')}
          </div>
          <div className="adv-progress-bar">
            <div
              className="adv-progress-fill fill-gold"
              style={{ width: `${visionVal !== null ? Math.min(100, (visionVal / 40) * 100) : 0}%` }}
            />
          </div>
        </div>

        {/* 3. Oro Promedio */}
        <div className="advanced-metric-card" id="metric-average-gold">
          <div className="adv-header">
            <span className="adv-label">
              <Coins size={15} /> Oro Promedio
            </span>
            <span className={`tier-grade-badge ${goldVal !== null ? 'grade-s' : 'grade-muted'}`}>
              {goldGrade}
            </span>
          </div>
          <div className="adv-main-value">
            {goldVal !== null ? Math.round(goldVal).toLocaleString('es-ES') : 'N/D'}
          </div>
          <div className="adv-meta-text">
            {goldPerMin !== null
              ? `${goldPerMin} oro / minuto`
              : 'Sin datos de economía'}
          </div>
          <div className="adv-progress-bar">
            <div
              className="adv-progress-fill fill-gold"
              style={{ width: `${goldPerMin !== null ? Math.min(100, (goldPerMin / 600) * 100) : 0}%` }}
            />
          </div>
        </div>

        {/* 4. Participación en Objetivos */}
        <div className="advanced-metric-card" id="metric-objective-participation">
          <div className="adv-header">
            <span className="adv-label">
              <Target size={15} /> Participación en Objetivos
            </span>
            <span className={`adv-percentage-badge ${objAvailable ? '' : 'badge-disabled'}`}>
              {objAvailable && overallObjPercent !== null
                ? `${overallObjPercent}%`
                : 'No disponible'}
            </span>
          </div>

          {!objAvailable ? (
            <div className="objective-unavailable-notice">
              <ShieldAlert size={14} />
              <span>{objectives?.notes || 'Datos de equipo no disponibles para el modo consultado'}</span>
            </div>
          ) : (
            <div className="objective-stats-row">
              <div className="objective-sub-stat">
                <span className="obj-name">Dragones:</span>{' '}
                <span className="obj-val">{dragonPart}</span>
              </div>
              <div className="objective-sub-stat">
                <span className="obj-name">Barones:</span>{' '}
                <span className="obj-val">{baronPart}</span>
              </div>
              <div className="objective-sub-stat">
                <span className="obj-name">Torres:</span>{' '}
                <span className="obj-val">{turretPart}</span>
              </div>
            </div>
          )}

          <div className="adv-progress-bar">
            <div
              className="adv-progress-fill fill-green"
              style={{ width: `${overallObjPercent !== null ? overallObjPercent : 0}%` }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
