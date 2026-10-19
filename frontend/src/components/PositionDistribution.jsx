import React from 'react';
import { Compass, AlertCircle } from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import DemoBadge from './DemoBadge';

const ROLE_COLORS = {
  MID: '#0ac8b9',
  ADC: '#c89b3c',
  BOT: '#c89b3c',
  JUNGLE: '#10b981',
  JGL: '#10b981',
  TOP: '#9370db',
  SUPPORT: '#3b82f6',
  SUP: '#3b82f6',
  UNKNOWN: '#64748b',
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="recharts-custom-tooltip">
        <div className="tooltip-role">{data.name}</div>
        <div className="tooltip-value">
          {data.value}% ({data.matchesCount ?? 0} {data.matchesCount === 1 ? 'partida' : 'partidas'})
        </div>
        {data.winRate !== undefined && data.winRate !== null && (
          <div className="tooltip-subvalue">{data.winRate}% Tasa de Victoria</div>
        )}
      </div>
    );
  }
  return null;
};

export default function PositionDistribution({ positions = [], isDemoData = false }) {
  // Normalize backend RoleDistributionEntry objects or demo position objects
  const chartData = (positions || [])
    .map((item) => {
      const roleKey = (item.role || 'UNKNOWN').toUpperCase();
      const name = item.display_name || item.name || roleKey;
      const val = item.percentage !== undefined ? item.percentage : (item.value || 0);
      const color = item.color || ROLE_COLORS[roleKey] || '#64748b';
      const matchesCount = item.matches_count ?? item.matchesCount ?? 0;
      const winRate = item.win_rate ?? item.winRate ?? null;

      return {
        role: roleKey,
        name,
        value: Number(val),
        color,
        matchesCount,
        winRate,
      };
    })
    .filter((entry) => entry.value > 0);

  const hasData = chartData.length > 0;

  return (
    <section className="dashboard-panel" id="position-distribution-panel">
      <div className="panel-header">
        <div className="panel-title-wrapper">
          <Compass className="panel-icon" size={20} />
          <h3 className="panel-title">Distribución de Posiciones</h3>
        </div>
        {isDemoData && <DemoBadge compact />}
      </div>

      {!hasData ? (
        <div className="panel-empty-message" id="empty-positions-notice">
          <AlertCircle size={24} className="empty-icon-muted" />
          <p>Sin datos de distribución de carril en las partidas analizadas.</p>
        </div>
      ) : (
        <div className="position-chart-container">
          <div className="donut-chart-box">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="#060b13"
                  strokeWidth={2}
                >
                  {chartData.map((entry) => (
                    <Cell key={`cell-${entry.role}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend List */}
          <div className="position-legend-list" id="position-legend-list">
            {chartData.map((item) => (
              <div key={item.role} className="legend-item-row">
                <div className="legend-indicator">
                  <span
                    className="legend-color-dot"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="legend-name">{item.name}</span>
                </div>
                <span className="legend-percent">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
