import React from 'react';
import { Shield, Activity, KeyRound, Zap } from 'lucide-react';

export default function Header({ backendHealth, riotStatus }) {
  const isOnline = backendHealth?.status === 'healthy';
  const isKeyConfigured = riotStatus?.is_configured === true;

  return (
    <header className="app-header" id="main-header">
      <div className="brand-wrapper">
        <div className="brand-logo-icon" id="brand-logo">
          <Shield size={24} strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="brand-title" id="app-title">
            RiftTracker — LOL STATISTICS API
          </h1>
          <p className="brand-tagline">
            Analítica de Rendimiento y Estadísticas Oficiales de League of Legends
          </p>
        </div>
      </div>

      <div className="header-status-group" id="header-status-group">
        {/* Backend Connectivity Status */}
        <span
          className={`status-pill ${isOnline ? 'online' : 'offline'}`}
          id="status-pill-backend"
          title={`Backend FastAPI en ${backendHealth?.service || '127.0.0.1:8000'}`}
        >
          <Activity size={13} />
          {isOnline ? 'Backend Online' : 'Backend Desconectado'}
        </span>

        {/* Riot Games API Status */}
        <span
          className={`status-pill ${isKeyConfigured ? 'online' : 'warning'}`}
          id="status-pill-riot"
          title={riotStatus?.message || 'Estado de Riot API Key'}
        >
          <KeyRound size={13} />
          {isKeyConfigured ? 'Riot API Configurada' : 'Riot API: Placeholder'}
        </span>

        <span className="status-pill phase" id="status-pill-phase">
          <Zap size={13} /> Frontend Fase 1
        </span>
      </div>
    </header>
  );
}
