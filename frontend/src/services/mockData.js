/**
 * Data Dragon & Demonstration Data for RiftTracker
 * 
 * IMPORTANT: This data represents interface demonstration values
 * clearly flagged as demo data for Phase 1 presentation.
 */

export const DDRAGON_VERSION = '14.20.1';
export const DDRAGON_CDN = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}`;

export const getProfileIconUrl = (iconId = 588) =>
  `${DDRAGON_CDN}/img/profileicon/${iconId}.png`;

export const getChampionIconUrl = (championName) =>
  `${DDRAGON_CDN}/img/champion/${championName}.png`;

export const getItemIconUrl = (itemId) =>
  `${DDRAGON_CDN}/img/item/${itemId}.png`;

export const SUMMONER_SPELL_MAP = {
  1: 'SummonerBoost',       // Cleanse
  3: 'SummonerExhaust',     // Exhaust
  4: 'SummonerFlash',       // Flash
  6: 'SummonerHaste',       // Ghost
  7: 'SummonerHeal',        // Heal
  11: 'SummonerSmite',      // Smite
  12: 'SummonerTeleport',   // Teleport
  13: 'SummonerMana',       // Clarity
  14: 'SummonerDot',        // Ignite
  21: 'SummonerBarrier',    // Barrier
  30: 'SummonerPoroRecall', // To the King!
  31: 'SummonerPoroThrow',  // Poro Toss
  32: 'SummonerSnowball',   // Mark / Dash
};

export const getSpellIconUrl = (spell) => {
  if (!spell && spell !== 0) return `${DDRAGON_CDN}/img/spell/SummonerFlash.png`;
  const name = typeof spell === 'number' ? (SUMMONER_SPELL_MAP[spell] || 'SummonerFlash') : spell;
  return `${DDRAGON_CDN}/img/spell/${name}.png`;
};

export const DEMO_SUMMONER_PROFILE = {
  isDemoData: true,
  gameName: 'Faker',
  tagLine: 'KR1',
  summonerLevel: 684,
  profileIconId: 588,
  region: {
    platformId: 'kr',
    name: 'Korea',
    cluster: 'asia',
  },
  tier: 'Grandmaster',
  rank: 'I',
  leaguePoints: 645,
  wins: 142,
  losses: 78,
  winRate: 64.5,
  ladderRank: 'Top 0.05%',
};

export const DEMO_SUMMARY_STATS = {
  isDemoData: true,
  matchesAnalyzed: 20,
  wins: 14,
  losses: 6,
  winRate: 70.0,
  averageKda: {
    ratio: 4.82,
    kills: 8.4,
    deaths: 2.6,
    assists: 9.1,
  },
  competitiveRank: 'Grandmaster 645 LP',
};

export const DEMO_TOP_CHAMPIONS = [
  {
    name: 'Ahri',
    title: 'La Mujer Zorro de Nueve Colas',
    iconName: 'Ahri',
    masteryLevel: 7,
    masteryPoints: 485200,
    matches: 8,
    wins: 6,
    losses: 2,
    winRate: 75.0,
    kda: 5.4,
    csPerMin: 8.9,
  },
  {
    name: 'Jinx',
    title: 'La Bala Perdida',
    iconName: 'Jinx',
    masteryLevel: 7,
    masteryPoints: 362400,
    matches: 5,
    wins: 4,
    losses: 1,
    winRate: 80.0,
    kda: 4.2,
    csPerMin: 9.3,
  },
  {
    name: 'Lee Sin',
    title: 'El Monje Ciego',
    iconName: 'LeeSin',
    masteryLevel: 7,
    masteryPoints: 590100,
    matches: 3,
    wins: 2,
    losses: 1,
    winRate: 66.7,
    kda: 3.8,
    csPerMin: 6.2,
  },
  {
    name: 'Aatrox',
    title: 'La Espada de los Oscuros',
    iconName: 'Aatrox',
    masteryLevel: 6,
    masteryPoints: 215300,
    matches: 2,
    wins: 1,
    losses: 1,
    winRate: 50.0,
    kda: 3.1,
    csPerMin: 8.4,
  },
  {
    name: 'Thresh',
    title: 'El Carcelero Implacable',
    iconName: 'Thresh',
    masteryLevel: 7,
    masteryPoints: 310800,
    matches: 2,
    wins: 1,
    losses: 1,
    winRate: 50.0,
    kda: 4.5,
    csPerMin: 1.4,
  },
];

export const DEMO_POSITION_DISTRIBUTION = [
  { name: 'Carril Central (MID)', value: 45, role: 'MID', color: '#0ac8b9' },
  { name: 'Tirador (BOT/ADC)', value: 25, role: 'ADC', color: '#c89b3c' },
  { name: 'Jungla (JGL)', value: 15, role: 'JGL', color: '#10b981' },
  { name: 'Carril Superior (TOP)', value: 10, role: 'TOP', color: '#9370db' },
  { name: 'Soporte (SUP)', value: 5, role: 'SUP', color: '#3b82f6' },
];

export const DEMO_ADVANCED_METRICS = {
  isDemoData: true,
  csPerMin: {
    value: 8.7,
    label: 'CS por Minuto',
    rating: 'S+',
    comparison: '+1.8 vs promedio regional',
  },
  visionScore: {
    value: 29.4,
    label: 'Puntaje de Visión',
    rating: 'A+',
    controlWardsBought: 3.8,
  },
  goldPerMatch: {
    value: 15420,
    label: 'Oro Promedio',
    goldPerMin: 485,
    rating: 'S',
  },
  objectiveParticipation: {
    value: 74,
    label: 'Participación en Objetivos',
    dragons: '78%',
    barons: '68%',
    towers: '82%',
  },
};

export const DEMO_MATCH_HISTORY = [
  {
    id: 'KR_7109283921',
    isVictory: true,
    queue: 'Ranked Solo/Duo',
    timeAgo: 'hace 45 min',
    duration: '28m 14s',
    champion: 'Ahri',
    championLevel: 16,
    spells: ['SummonerFlash', 'SummonerDot'],
    kills: 11,
    deaths: 2,
    assists: 9,
    kdaRatio: 10.0,
    killParticipation: 71,
    cs: 254,
    csPerMin: 9.0,
    goldEarned: 16200,
    items: [3089, 3157, 3020, 6655, 4645, 3135, 3364], // Rabadon, Zhonya, Sorc Shoes, Luden, Shadowflame, Void Staff, Oracle
    badge: 'MVP',
  },
  {
    id: 'KR_7109192844',
    isVictory: true,
    queue: 'Ranked Solo/Duo',
    timeAgo: 'hace 2 horas',
    duration: '32m 40s',
    champion: 'Jinx',
    championLevel: 17,
    spells: ['SummonerFlash', 'SummonerHaste'],
    kills: 14,
    deaths: 3,
    assists: 8,
    kdaRatio: 7.33,
    killParticipation: 68,
    cs: 312,
    csPerMin: 9.5,
    goldEarned: 18450,
    items: [3031, 3006, 3094, 3072, 3036, 3026, 3363], // IE, Berserkers, RFC, BT, LDR, GA, Blue Trinket
    badge: 'Triple Kill',
  },
  {
    id: 'KR_7108928311',
    isVictory: false,
    queue: 'Ranked Solo/Duo',
    timeAgo: 'hace 4 horas',
    duration: '24m 10s',
    champion: 'LeeSin',
    championLevel: 13,
    spells: ['SummonerFlash', 'SummonerSmite'],
    kills: 4,
    deaths: 5,
    assists: 6,
    kdaRatio: 2.0,
    killParticipation: 55,
    cs: 142,
    csPerMin: 5.9,
    goldEarned: 9800,
    items: [3078, 3047, 3053, 3065, 0, 0, 3364], // Trinity, Tabis, Steraks, Spirit Visage, Oracle
    badge: 'Ace',
  },
  {
    id: 'KR_7108549201',
    isVictory: true,
    queue: 'Ranked Solo/Duo',
    timeAgo: 'hace 6 horas',
    duration: '26m 52s',
    champion: 'Ahri',
    championLevel: 15,
    spells: ['SummonerFlash', 'SummonerTeleport'],
    kills: 8,
    deaths: 1,
    assists: 12,
    kdaRatio: 20.0,
    killParticipation: 74,
    cs: 238,
    csPerMin: 8.8,
    goldEarned: 14700,
    items: [6655, 3020, 3157, 4645, 3089, 0, 3364],
    badge: 'MVP',
  },
  {
    id: 'KR_7108392011',
    isVictory: false,
    queue: 'Ranked Solo/Duo',
    timeAgo: 'Ayer',
    duration: '35m 18s',
    champion: 'Aatrox',
    championLevel: 18,
    spells: ['SummonerFlash', 'SummonerTeleport'],
    kills: 7,
    deaths: 6,
    assists: 4,
    kdaRatio: 1.83,
    killParticipation: 48,
    cs: 295,
    csPerMin: 8.3,
    goldEarned: 15800,
    items: [3078, 3047, 3053, 3071, 3156, 3026, 3363],
    badge: null,
  },
];
