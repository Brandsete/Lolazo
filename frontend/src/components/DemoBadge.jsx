import React from 'react';
import { AlertTriangle, Sparkles } from 'lucide-react';

export default function DemoBadge({ compact = false }) {
  if (compact) {
    return (
      <span className="demo-pill-badge" id="demo-pill-badge" title="Muestra provisional para visualización de componentes">
        <Sparkles size={12} /> DATOS DEMO
      </span>
    );
  }

  return (
    <aside className="demo-disclaimer-banner" id="demo-disclaimer-banner" aria-label="Aviso de datos de demostración">
      <div className="demo-banner-content">
        <AlertTriangle size={18} className="demo-icon" />
        <div>
          <strong>Modo Demostración Activo (Fase 1):</strong> Las métricas y partidas visualizadas a continuación
          corresponden a datos de prueba para validar los componentes gráficos, Data Dragon y la interfaz. En la
          Fase 2 se conectarán en vivo con las consultas de invocador de Riot Games API.
        </div>
      </div>
    </aside>
  );
}
