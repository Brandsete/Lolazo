import React, { useState } from 'react';
import { Search, Globe, Hash, User, RefreshCw, Eye } from 'lucide-react';

const FALLBACK_REGIONS = [
  { platform_id: 'la1', name: 'Latin America North (LAN)', regional_cluster: 'americas' },
  { platform_id: 'la2', name: 'Latin America South (LAS)', regional_cluster: 'americas' },
  { platform_id: 'na1', name: 'North America (NA)', regional_cluster: 'americas' },
  { platform_id: 'euw1', name: 'Europe West (EUW)', regional_cluster: 'europe' },
  { platform_id: 'eun1', name: 'Europe Nordic & East (EUNE)', regional_cluster: 'europe' },
  { platform_id: 'kr', name: 'Korea (KR)', regional_cluster: 'asia' },
  { platform_id: 'br1', name: 'Brazil (BR)', regional_cluster: 'americas' },
  { platform_id: 'oc1', name: 'Oceania (OCE)', regional_cluster: 'sea' },
];

export default function SearchForm({
  regions = [],
  onSearch,
  isLoading,
  currentViewMode,
  onViewModeChange,
}) {
  const [gameName, setGameName] = useState('Faker');
  const [tagLine, setTagLine] = useState('KR1');
  const [selectedRegion, setSelectedRegion] = useState('kr');

  const regionList = regions.length > 0 ? regions : FALLBACK_REGIONS;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!gameName.trim()) return;

    // Clean tag if user typed '#'
    const cleanTag = tagLine.replace(/^#/, '').trim() || 'KR1';
    onSearch({
      gameName: gameName.trim(),
      tagLine: cleanTag,
      region: selectedRegion,
    });
  };

  const handlePresetSelect = (presetGameName, presetTag, presetRegion) => {
    setGameName(presetGameName);
    setTagLine(presetTag);
    setSelectedRegion(presetRegion);
    onSearch({
      gameName: presetGameName,
      tagLine: presetTag,
      region: presetRegion,
    });
  };

  return (
    <section className="search-section" id="search-section">
      <form onSubmit={handleSubmit} className="search-form-card" id="riot-search-form">
        <div className="search-inputs-grid">
          {/* Riot ID (Game Name) */}
          <div className="input-group">
            <label htmlFor="riot-id-input" className="input-label">
              <User size={14} className="input-icon" /> Riot ID (Nombre)
            </label>
            <input
              id="riot-id-input"
              type="text"
              className="text-input"
              placeholder="Ej: Faker, Caps, Josedeodo"
              value={gameName}
              onChange={(e) => setGameName(e.target.value)}
              required
            />
          </div>

          {/* Tagline */}
          <div className="input-group tag-input-group">
            <label htmlFor="tagline-input" className="input-label">
              <Hash size={14} className="input-icon" /> Etiqueta
            </label>
            <div className="tag-input-wrapper">
              <span className="tag-hash-prefix">#</span>
              <input
                id="tagline-input"
                type="text"
                className="text-input tag-field"
                placeholder="KR1, LAN, EUW"
                value={tagLine.replace(/^#/, '')}
                onChange={(e) => setTagLine(e.target.value.replace(/^#/, ''))}
                maxLength={6}
                required
              />
            </div>
          </div>

          {/* Region Selector */}
          <div className="input-group">
            <label htmlFor="region-select" className="input-label">
              <Globe size={14} className="input-icon" /> Región de Plataforma
            </label>
            <select
              id="region-select"
              className="select-input"
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
            >
              {regionList.map((reg) => (
                <option key={reg.platform_id} value={reg.platform_id}>
                  {reg.platform_id.toUpperCase()} — {reg.name} ({reg.regional_cluster})
                </option>
              ))}
            </select>
          </div>

          {/* Submit Button */}
          <div className="search-action-wrapper">
            <button
              type="submit"
              className="btn btn-primary btn-search"
              id="search-submit-btn"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw size={16} className="spin-animation" /> Buscando...
                </>
              ) : (
                <>
                  <Search size={16} /> Buscar Invocador
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick test presets and view-mode toggles */}
        <div className="search-extras-row">
          <div className="search-presets">
            <span className="presets-label">Perfiles de prueba:</span>
            <button
              type="button"
              className="preset-chip"
              onClick={() => handlePresetSelect('Faker', 'KR1', 'kr')}
            >
              Faker #KR1 (KR)
            </button>
            <button
              type="button"
              className="preset-chip"
              onClick={() => handlePresetSelect('Caps', 'EUW', 'euw1')}
            >
              Caps #EUW (EUW)
            </button>
            <button
              type="button"
              className="preset-chip"
              onClick={() => handlePresetSelect('Josedeodo', 'LAN', 'la1')}
            >
              Josedeodo #LAN (LAN)
            </button>
          </div>

          {/* State Simulation Bar for Requirement 9 */}
          <div className="state-simulation-toggle" id="state-simulation-controls">
            <span className="simulation-label">
              <Eye size={13} /> Estados UI:
            </span>
            <button
              type="button"
              className={`mode-btn ${currentViewMode === 'normal' ? 'active' : ''}`}
              onClick={() => onViewModeChange('normal')}
              title="Ver dashboard completo con datos demo"
            >
              Normal
            </button>
            <button
              type="button"
              className={`mode-btn ${currentViewMode === 'loading' ? 'active' : ''}`}
              onClick={() => onViewModeChange('loading')}
              title="Ver animación de carga / skeleton"
            >
              Cargando
            </button>
            <button
              type="button"
              className={`mode-btn ${currentViewMode === 'empty' ? 'active' : ''}`}
              onClick={() => onViewModeChange('empty')}
              title="Ver estado de invocador no encontrado"
            >
              Sin Datos
            </button>
            <button
              type="button"
              className={`mode-btn ${currentViewMode === 'error' ? 'active' : ''}`}
              onClick={() => onViewModeChange('error')}
              title="Ver estado de error en consulta"
            >
              Error
            </button>
            <button
              type="button"
              className={`mode-btn ${currentViewMode === 'partial' ? 'active' : ''}`}
              onClick={() => onViewModeChange('partial')}
              title="Ver estado con datos parciales"
            >
              Parcial
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
