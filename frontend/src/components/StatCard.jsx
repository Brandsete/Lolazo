import React from 'react';

export default function StatCard({
  id,
  title,
  value,
  subvalue,
  icon: Icon,
  variant = 'default',
  progressPercent = null,
  trend = null,
}) {
  return (
    <div className={`metric-card metric-card-${variant}`} id={id}>
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {Icon && (
          <div className="metric-icon-box">
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="metric-body">
        <div className="metric-primary-value">{value}</div>
        {subvalue && <div className="metric-subvalue">{subvalue}</div>}
      </div>

      {progressPercent !== null && (
        <div className="metric-progress-wrapper">
          <div className="metric-progress-bar">
            <div
              className={`metric-progress-fill fill-${variant}`}
              style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
            />
          </div>
        </div>
      )}

      {trend && (
        <div className="metric-footer">
          <span className="metric-trend">{trend}</span>
        </div>
      )}
    </div>
  );
}
