import React from 'react';
import { AlertCircle, UserX, RefreshCw, AlertTriangle, Layers } from 'lucide-react';

/**
 * 1. Loading Skeleton Indicator
 */
export function LoadingSkeleton() {
  return (
    <div className="skeleton-container" id="loading-skeleton" aria-busy="true">
      {/* Profile Skeleton */}
      <div className="skeleton-card skeleton-profile">
        <div className="skeleton-avatar pulse-anim" />
        <div className="skeleton-info-block">
          <div className="skeleton-line pulse-anim line-title" />
          <div className="skeleton-line pulse-anim line-subtitle" />
          <div className="skeleton-pills-row">
            <div className="skeleton-pill pulse-anim" />
            <div className="skeleton-pill pulse-anim" />
          </div>
        </div>
      </div>

      {/* Metric Cards Skeleton */}
      <div className="grid-4-metrics">
        {[1, 2, 3, 4].map((n) => (
          <div key={`sk-metric-${n}`} className="skeleton-card skeleton-metric pulse-anim" />
        ))}
      </div>

      {/* Main Content Skeleton */}
      <div className="grid-split-layout">
        <div className="skeleton-card skeleton-panel pulse-anim" style={{ height: 350 }} />
        <div className="skeleton-card skeleton-panel pulse-anim" style={{ height: 350 }} />
      </div>
    </div>
  );
}

/**
 * 2. Error State Indicator
 */
export function ErrorState({ title = 'Error en la Consulta', message, onRetry }) {
  return (
    <section className="status-indicator-card error-card" id="error-indicator-card">
      <div className="status-icon-wrapper error-icon">
        <AlertCircle size={36} />
      </div>
      <h3 className="status-heading">{title}</h3>
      <p className="status-message">
        {message || 'No fue posible conectar con el servidor backend o la API de Riot Games. Verifica que el servidor FastAPI esté iniciado en http://127.0.0.1:8000.'}
      </p>
      {onRetry && (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onRetry}
          id="btn-retry-error"
        >
          <RefreshCw size={14} /> Reintentar Operación
        </button>
      )}
    </section>
  );
}

/**
 * 3. Empty / No Results Found State Indicator
 */
export function EmptyState({ gameName = '', tagLine = '', onReset }) {
  return (
    <section className="status-indicator-card empty-card" id="empty-state-card">
      <div className="status-icon-wrapper empty-icon">
        <UserX size={36} />
      </div>
      <h3 className="status-heading">Invocador No Encontrado</h3>
      <p className="status-message">
        {gameName ? (
          <>
            No se encontraron registros para <strong>{gameName}#{tagLine}</strong> en la región seleccionada.
          </>
        ) : (
          'No hay resultados que mostrar con los criterios ingresados.'
        )}
      </p>
      <div className="tips-box">
        <strong>Consejos de Búsqueda de Riot Games:</strong>
        <ul>
          <li>Verifica que hayas incluido el <strong>Riot ID</strong> exacto junto a su etiqueta (ej. <code>Faker#KR1</code>).</li>
          <li>Asegúrate de seleccionar la <strong>Región de Plataforma</strong> correcta (LAN, LAS, NA, EUW, KR, etc.).</li>
          <li>Las cuentas de Riot Games ahora requieren el formato <em>Nombre#Etiqueta</em> en lugar del antiguo nombre de invocador.</li>
        </ul>
      </div>
      {onReset && (
        <button
          type="button"
          className="btn btn-primary"
          onClick={onReset}
          id="btn-reset-empty-search"
        >
          Restablecer a Perfil de Prueba
        </button>
      )}
    </section>
  );
}

/**
 * 4. Partial Data Indicator Banner
 */
export function PartialDataBanner({ onDismiss }) {
  return (
    <div className="partial-data-banner" id="partial-data-banner">
      <div className="partial-banner-inner">
        <AlertTriangle size={18} className="partial-icon" />
        <div className="partial-text">
          <strong>Aviso de Datos Parciales:</strong> Algunas estadísticas se calcularon sobre un subconjunto
          de partidas debido al límite de la caché o cuota de desarrollo de Riot Games API.
        </div>
      </div>
      {onDismiss && (
        <button
          type="button"
          className="btn-dismiss"
          onClick={onDismiss}
          title="Ocultar aviso"
        >
          &times;
        </button>
      )}
    </div>
  );
}
