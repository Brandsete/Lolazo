import React from 'react';
import { Swords, Coins, AlertCircle } from 'lucide-react';
import { getChampionIconUrl } from '../services/mockData';
import DemoBadge from './DemoBadge';

export default function TopChampions({ champions = [], isDemoData = false }) {
  const hasChampions = Array.isArray(champions) && champions.length > 0;

  return (
    <section className="dashboard-panel" id="top-champions-panel">
      <div className="panel-header">
        <div className="panel-title-wrapper">
          <Swords className="panel-icon" size={20} />
          <h3 className="panel-title">Campeones Más Jugados</h3>
        </div>
        <div className="panel-actions">
          {isDemoData && <DemoBadge compact />}
        </div>
      </div>

      {!hasChampions ? (
        <div className="panel-empty-message" id="empty-champions-notice">
          <AlertCircle size={24} className="empty-icon-muted" />
          <p>No se registraron partidas con campeones en la muestra consultada.</p>
        </div>
      ) : (
        <div className="top-champions-list" id="top-champions-list">
          {champions.slice(0, 5).map((champ, index) => {
            const name = champ.champion_name || champ.name || 'Desconocido';
            const iconUrl =
              champ.champion_icon_url ||
              getChampionIconUrl(champ.champion_name || champ.iconName || name);

            const winRate = champ.win_rate ?? champ.winRate ?? 0;
            const wins = champ.wins ?? 0;
            const losses = champ.losses ?? 0;
            const matchesCount =
              champ.matches_played ?? champ.matches ?? wins + losses;
            const kda = champ.kda_ratio ?? champ.kda ?? 0;
            const cs = champ.cs_per_min ?? champ.csPerMin ?? 0;
            const goldMin = champ.gold_per_min ?? champ.goldPerMin ?? null;

            return (
              <div
                key={`${name}-${index}`}
                className="champion-row-card"
                id={`champion-row-${name.toLowerCase().replace(/[^a-z0-9]/g, '')}`}
              >
                {/* Rank index */}
                <span className="champion-rank-number">#{index + 1}</span>

                {/* Champion Data Dragon Avatar */}
                <div className="champion-avatar-box">
                  <img
                    src={iconUrl}
                    alt={name}
                    className="champion-img"
                    loading="lazy"
                    onError={(e) => {
                      e.target.src = getChampionIconUrl('Ahri');
                    }}
                  />
                  {champ.masteryLevel && (
                    <span className="mastery-badge">M{champ.masteryLevel}</span>
                  )}
                </div>

                {/* Champion Info */}
                <div className="champion-identity">
                  <h4 className="champion-name">{name}</h4>
                  {champ.masteryPoints ? (
                    <span className="champion-mastery-pts">
                      {(champ.masteryPoints / 1000).toFixed(0)}k pts maestría
                    </span>
                  ) : goldMin !== null ? (
                    <span className="champion-mastery-pts">
                      <Coins size={11} /> {goldMin} oro / min
                    </span>
                  ) : (
                    <span className="champion-mastery-pts">
                      {matchesCount} partidas
                    </span>
                  )}
                </div>

                {/* Performance Stats */}
                <div className="champion-stats-group">
                  <div className="stat-col winrate-col">
                    <span className="stat-main-text">{winRate}% WR</span>
                    <span className="stat-sub-text">
                      {wins}V - {losses}D ({matchesCount} {matchesCount === 1 ? 'partida' : 'partidas'})
                    </span>
                    <div className="mini-progress-bar">
                      <div
                        className="mini-progress-fill"
                        style={{ width: `${Math.min(100, Math.max(0, winRate))}%` }}
                      />
                    </div>
                  </div>

                  <div className="stat-col kda-col">
                    <span className="stat-main-text">{kda}:1 KDA</span>
                    <span className="stat-sub-text">{cs} CS/min</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
