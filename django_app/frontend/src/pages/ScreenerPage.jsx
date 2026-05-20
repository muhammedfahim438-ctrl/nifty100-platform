import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, SlidersHorizontal } from 'lucide-react';
import { getSectors, screenCompanies } from '../services/api';
import HealthBadge from '../components/ui/HealthBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function ScreenerPage() {
  const [sectors,      setSectors]      = useState([]);
  const [results,      setResults]      = useState([]);
  const [loading,      setLoading]      = useState(false);
  const [searched,     setSearched]     = useState(false);
  const [filters,      setFilters]      = useState({
    min_score   : '',
    health_label: '',
    sector      : '',
  });
  const navigate = useNavigate();

  useEffect(() => {
    getSectors().then(res => {
      const data = Array.isArray(res.data) ? res.data : res.data.results || [];
      setSectors(data);
    });
  }, []);

  const handleFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleScreen = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const params = {};
      if (filters.min_score)    params.min_score    = filters.min_score;
      if (filters.health_label) params.health_label = filters.health_label;
      if (filters.sector)       params.sector       = filters.sector;

      const res = await screenCompanies(params);
      const data = res.data?.results || res.data || [];
      setResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFilters({ min_score: '', health_label: '', sector: '' });
    setResults([]);
    setSearched(false);
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--navy)' }}>
          🔍 Company Screener
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Filter companies by financial criteria
        </p>
      </div>

      {/* Filter Panel */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <SlidersHorizontal size={18} color="var(--navy)" />
          <span style={{ fontWeight: 700, color: 'var(--navy)' }}>Filter Criteria</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>

          {/* Min Health Score */}
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-light)',
                            textTransform: 'uppercase', letterSpacing: '0.5px',
                            display: 'block', marginBottom: 6 }}>
              Min Health Score
            </label>
            <input
              type="number" min="0" max="100"
              value={filters.min_score}
              onChange={e => handleFilter('min_score', e.target.value)}
              placeholder="e.g. 60"
              className="input"
            />
          </div>

          {/* Health Label */}
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-light)',
                            textTransform: 'uppercase', letterSpacing: '0.5px',
                            display: 'block', marginBottom: 6 }}>
              Health Label
            </label>
            <select className="select" style={{ width: '100%' }}
                    value={filters.health_label}
                    onChange={e => handleFilter('health_label', e.target.value)}>
              <option value="">Any Label</option>
              {['EXCELLENT','GOOD','AVERAGE','WEAK','POOR'].map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>

          {/* Sector */}
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-light)',
                            textTransform: 'uppercase', letterSpacing: '0.5px',
                            display: 'block', marginBottom: 6 }}>
              Sector
            </label>
            <select className="select" style={{ width: '100%' }}
                    value={filters.sector}
                    onChange={e => handleFilter('sector', e.target.value)}>
              <option value="">All Sectors</option>
              {sectors.map(s => (
                <option key={s.sector_id} value={s.sector_name}>{s.sector_name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn-primary" onClick={handleScreen}
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Search size={14} /> Screen Companies
          </button>
          <button onClick={handleClear}
                  style={{ background: 'none', border: '1px solid var(--border)',
                           borderRadius: 8, padding: '8px 16px', fontSize: 13,
                           cursor: 'pointer', color: 'var(--text-muted)' }}>
            Clear Filters
          </button>
        </div>
      </div>

      {/* Results */}
      {loading && <LoadingSpinner message="Screening companies..." />}

      {!loading && searched && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 600 }}>
              {results.length} {results.length === 1 ? 'company' : 'companies'} found
            </span>
          </div>

          {results.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Symbol</th>
                  <th>Company Name</th>
                  <th>Sector</th>
                  <th>Health Score</th>
                  <th>Label</th>
                </tr>
              </thead>
              <tbody>
                {results.map((c, i) => (
                  <tr key={c.symbol} style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/company/${c.symbol}`)}>
                    <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                    <td style={{ fontWeight: 700, color: 'var(--navy)' }}>{c.symbol}</td>
                    <td style={{ color: 'var(--text)' }}>{c.company_name}</td>
                    <td>
                      <span style={{ background: 'var(--bg)', padding: '2px 8px',
                                     borderRadius: 20, fontSize: 11, color: 'var(--text-light)' }}>
                        {c.sector_name || '—'}
                      </span>
                    </td>
                    <td style={{
                      fontWeight: 700,
                      color: c.overall_score >= 70 ? 'var(--green)' :
                             c.overall_score >= 50 ? 'var(--yellow)' : 'var(--red)',
                    }}>
                      {c.overall_score ? parseFloat(c.overall_score).toFixed(1) : '—'}
                    </td>
                    <td><HealthBadge label={c.health_label} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No companies match your criteria. Try relaxing the filters.
            </div>
          )}
        </div>
      )}

      {!loading && !searched && (
        <div style={{
          background: 'var(--white)', borderRadius: 12, padding: '40px',
          textAlign: 'center', color: 'var(--text-muted)', border: '2px dashed var(--border)',
        }}>
          <SlidersHorizontal size={32} color="var(--border)" style={{ marginBottom: 12 }} />
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
            Set your filters and click "Screen Companies"
          </div>
          <div style={{ fontSize: 13 }}>
            Find companies matching your specific financial criteria
          </div>
        </div>
      )}
    </div>
  );
}