import React from 'react';
import { History, Clock, Flame, AlertCircle } from 'lucide-react';
import {
  getChampionIconUrl,
  getItemIconUrl,
  getSpellIconUrl,
} from '../services/mockData';
import DemoBadge from './DemoBadge';

/**
 * Format game duration in minutes and seconds
 */
function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0m 0s';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

/**
 * Format timestamp (epoch in ms) to relative human readable string
 */
function formatTimeAgo(epochMs) {
  if (!epochMs) return 'Reciente';
  const now = Date.now();
  const diffSec = Math.floor((now - epochMs) / 1000);

  if (diffSec < 60) return 'Hace un momento';
  if (diffSec < 3600) return `Hace ${Math.floor(diffSec / 60)} min`;
  if (diffSec < 86400) return `Hace ${Math.floor(diffSec / 3600)} horas`;
  if (diffSec < 172800) return 'Ayer';
  return `Hace ${Math.floor(diffSec / 86400)} días`;
}

export default function MatchHistory({ matches = [], isDemoData = false }) {
  const hasMatches = Array.isArray(matches) && matches.length > 0;

  return (
    <section className="dashboard-panel" id="match-history-panel">
      <div className="panel-header">
        <div className="panel-title-wrapper">
          <History className="panel-icon" size={20} />
          <h3 className="panel-title">Historial de Partidas Recientes</h3>
        </div>
        {isDemoData && <DemoBadge compact />}
      </div>

      {!hasMatches ? (
        <div className="panel-empty-message" id="empty-matches-notice">
          <AlertCircle size={24} className="empty-icon-muted" />
          <p>No se encontraron partidas recientes para este invocador.</p>
        </div>
      ) : (
        <div className="match-cards-list" id="match-cards-list">
          {matches.map((match, idx) => {
            // Normalize FastAPI PlayerMatchSummary vs legacy demo structure
            const matchId = match.match_id || match.id || `match-${idx}`;
            const isVictory = match.is_victory !== undefined ? match.is_victory : match.isVictory;
            const queueName = match.queue_name || match.queue || 'Partida Normal';

            const durationText = match.game_duration_seconds
              ? formatDuration(match.game_duration_seconds)
              : (match.duration || '20m 0s');

            const timeAgoText = match.game_creation
              ? formatTimeAgo(match.game_creation)
              : (match.timeAgo || 'Reciente');

            const champName = match.champion_name || match.champion || 'Unknown';
            const champIcon =
              match.champion_icon_url || getChampionIconUrl(champName);
            const champLevel = match.champion_level || match.championLevel || 1;

            const spells = match.summoner_spells || match.spells || [];
            const items = match.items || [];
            const kills = match.kills ?? 0;
            const deaths = match.deaths ?? 0;
            const assists = match.assists ?? 0;
            const kdaRatio = match.kda_ratio !== undefined ? match.kda_ratio : (match.kdaRatio ?? 0);

            const cs = match.total_cs !== undefined ? match.total_cs : (match.cs ?? 0);
            const csPerMin = match.cs_per_min !== undefined ? match.cs_per_min : (match.csPerMin ?? 0);
            const gold = match.gold_earned !== undefined ? match.gold_earned : (match.goldEarned ?? 0);
            const killPart = match.kill_participation !== undefined ? match.kill_participation : match.killParticipation;

            return (
              <article
                key={matchId}
                className={`match-row-card ${isVictory ? 'victory' : 'defeat'}`}
                id={`match-card-${matchId.replace(/[^a-zA-Z0-9_-]/g, '')}`}
              >
                {/* Outcome Strip */}
                <div className="outcome-strip">
                  <span className="outcome-label">
                    {isVictory ? 'Victoria' : 'Derrota'}
                  </span>
                  <span className="queue-type">{queueName}</span>
                  <div className="match-time-meta">
                    <Clock size={11} /> {durationText} &bull; {timeAgoText}
                  </div>
                </div>

                {/* Champion & Spells */}
                <div className="champ-spells-block">
                  <div className="match-champ-avatar">
                    <img
                      src={champIcon}
                      alt={champName}
                      className="match-champ-img"
                      loading="lazy"
                      onError={(e) => {
                        e.target.src = getChampionIconUrl('Ahri');
                      }}
                    />
                    <span className="match-champ-lvl">{champLevel}</span>
                  </div>

                  <div className="match-spells-column">
                    {spells.slice(0, 2).map((spell, sIdx) => (
                      <img
                        key={`spell-${matchId}-${sIdx}`}
                        src={getSpellIconUrl(spell)}
                        alt={`Hechizo ${sIdx + 1}`}
                        className="match-spell-img"
                        loading="lazy"
                      />
                    ))}
                  </div>
                </div>

                {/* KDA & Kill Participation */}
                <div className="kda-block">
                  <div className="kda-score-text">
                    <span className="kda-kills">{kills}</span> /{' '}
                    <span className="kda-deaths">{deaths}</span> /{' '}
                    <span className="kda-assists">{assists}</span>
                  </div>
                  <div className="kda-ratio-text">
                    <strong>{kdaRatio}:1</strong> KDA
                  </div>
                  {killPart !== null && killPart !== undefined ? (
                    <div className="kp-badge">
                      <Flame size={11} /> {killPart}% P. Asesinatos
                    </div>
                  ) : (
                    <div className="kp-badge kp-badge-muted">
                      Visión: {match.vision_score ?? 'N/D'}
                    </div>
                  )}
                </div>

                {/* CS and Gold */}
                <div className="economy-block">
                  <div className="cs-text">
                    <strong>{cs}</strong> CS ({csPerMin}/m)
                  </div>
                  <div className="gold-text">
                    {gold.toLocaleString('es-ES')} Oro
                  </div>
                  {match.badge && (
                    <span
                      className={`performance-pill badge-${match.badge.toLowerCase().replace(/\s+/g, '')}`}
                    >
                      {match.badge}
                    </span>
                  )}
                </div>

                {/* Items Grid (6 items + 1 trinket) */}
                <div className="items-inventory-grid">
                  {items.slice(0, 6).map((itemId, i) => (
                    <div key={`item-${matchId}-${i}`} className="item-slot">
                      {itemId > 0 ? (
                        <img
                          src={getItemIconUrl(itemId)}
                          alt={`Objeto ${itemId}`}
                          className="item-img"
                          loading="lazy"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="item-empty-slot" />
                      )}
                    </div>
                  ))}
                  {/* Trinket Slot */}
                  <div className="item-slot trinket-slot">
                    {items[6] > 0 ? (
                      <img
                        src={getItemIconUrl(items[6])}
                        alt="Baratija"
                        className="item-img"
                        loading="lazy"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="item-empty-slot" />
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
