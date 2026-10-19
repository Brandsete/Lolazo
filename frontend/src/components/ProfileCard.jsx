import React from 'react';
import { Award, Globe2, ShieldCheck, Flame } from 'lucide-react';
import { getProfileIconUrl } from '../services/mockData';
import DemoBadge from './DemoBadge';

export default function ProfileCard({ profile }) {
  if (!profile) return null;

  // Normalize FastAPI models vs demo state fields
  const gameName = profile.game_name || profile.gameName || 'Invocador';
  const tagLine = profile.tag_line || profile.tagLine || '';
  const summonerLevel = profile.summoner_level ?? profile.summonerLevel ?? 1;
  const iconUrl =
    profile.profile_icon_url ||
    getProfileIconUrl(profile.profile_icon_id ?? profile.profileIconId ?? 29);

  const platformId = (
    profile.region && typeof profile.region === 'string'
      ? profile.region
      : profile.region?.platformId || 'la1'
  ).toUpperCase();

  const cluster = (
    profile.regional_cluster ||
    profile.region?.cluster ||
    'americas'
  ).toUpperCase();

  const regionName = profile.region?.name || platformId;

  // Competitive rank resolution (solo_rank from FastAPI PlayerProfileResponse)
  const soloRank = profile.solo_rank;
  const isRanked = Boolean(soloRank && soloRank.tier);

  const tier = isRanked ? soloRank.tier : (profile.tier || 'UNRANKED');
  const rank = isRanked ? soloRank.rank : (profile.rank || '');
  const lp = isRanked ? soloRank.league_points : (profile.leaguePoints ?? 0);
  const wins = isRanked ? soloRank.wins : (profile.wins ?? 0);
  const losses = isRanked ? soloRank.losses : (profile.losses ?? 0);
  const winRate = isRanked ? soloRank.win_rate : (profile.winRate ?? null);

  const ladderText = isRanked
    ? `Top Competitivo (${tier})`
    : (profile.ladderRank || 'Sin Clasificar');

  const isDemo = Boolean(profile.isDemoData);

  return (
    <article className="profile-card" id="player-profile-card">
      <div className="profile-main-layout">
        {/* Summoner Avatar & Level */}
        <div className="profile-avatar-wrapper">
          <div className="avatar-frame">
            <img
              src={iconUrl}
              alt={`Icono de invocador ${gameName}`}
              className="summoner-icon-img"
              loading="lazy"
              onError={(e) => {
                e.target.src = getProfileIconUrl(29);
              }}
            />
            <span className="summoner-level-badge" id="summoner-level-badge">
              {summonerLevel}
            </span>
          </div>
        </div>

        {/* Identity & Region Info */}
        <div className="profile-identity">
          <div className="name-and-tag">
            <h2 className="summoner-game-name" id="summoner-game-name">
              {gameName}
            </h2>
            {tagLine && (
              <span className="summoner-tagline" id="summoner-tagline">
                #{tagLine}
              </span>
            )}
            {isDemo && <DemoBadge compact />}
          </div>

          <div className="profile-meta-pills">
            <span className="meta-pill" id="profile-region-pill">
              <Globe2 size={13} />
              {regionName} ({platformId})
            </span>
            <span className="meta-pill cluster" id="profile-cluster-pill">
              <ShieldCheck size={13} />
              Clúster: {cluster}
            </span>
            <span className="meta-pill ladder" id="profile-ladder-pill">
              <Flame size={13} />
              {ladderText}
            </span>
          </div>
        </div>

        {/* Competitive Rank Banner */}
        <div className="profile-rank-summary" id="profile-rank-summary">
          <div className="rank-tier-emblem">
            <Award size={36} className="rank-icon-lucide" />
          </div>
          <div className="rank-details">
            <div className="rank-tier-name">
              {tier} {rank}
            </div>
            <div className="rank-lp">
              {isRanked ? `${lp} LP` : 'Sin Clasificar'}
            </div>
            <div className="rank-record">
              {isRanked ? (
                <>
                  <span className="wins-count">{wins}V</span>{' '}
                  <span className="losses-count">{losses}D</span> &bull;{' '}
                  <span className="winrate-pct">
                    {winRate !== null ? `${winRate}% WR` : 'N/D'}
                  </span>
                </>
              ) : (
                <span className="unranked-label">0 partidas clasificatorias</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
