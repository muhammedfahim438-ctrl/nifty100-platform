import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity } from 'lucide-react';
import { getHealthScores } from '../services/api';
import HealthBadge from '../components/ui/HealthBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function HealthScoresPage() {
  const [scores,   setScores]   = useState([]);
  const [filter,   setFilter]   = useState('');
  const [loading,  setLoading]  = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getHealthScores().then(res => {
      const data = Array.isArray(res.data) ? res.data : res.data.results || [];
      setScores(data);
    }).finally(() => setLoading(false));
  }, []);

  const labels    = ['EXCELLENT','GOOD','AVERAGE','WEAK','POOR'];
  const filtered  = filter ? scores.filter(s => s.health_label === filter) : scores;

  const labelColors = {
    EXCELLENT: { bg: '#DCFCE7', color: '#15803D' },
    GOOD:      { bg: '#D1FAE5', color: '#047857' },
    AVERAGE:   { bg: '#FEF9C3', color: '#854D0E' },
    WEAK:      { bg: '#FFEDD5', color: '#9A3412' },
    POOR:      { bg: '#FEE2E2', color: '#991B1B' },
  };

  const counts = labels.reduce((acc, l) => {
    acc[l] = scores.filter(s => s.health_label === l).length;
    return acc;
  }, {});

  if (loading) return <LoadingSpinner message="Loading health scores..." />;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--navy)' }}>
          🏥 Financial Health Scorecard
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          ML-generated health scores for all 92 Nifty 100 companies
        </p>
      </div>

      {/* Label Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 12, marginBottom: 24 }}>
        {labels.map(l => {
          const style = labelColors[l];
          const active = filter === l;
          return (
            <button key={l} onClick={() => setFilter(active ? '' : l)}
              style={{
                background: active ? style.color : style.bg,
                color: active ? 'white' : style.color,
                border: `2px solid ${active ? style.color : 'transparent'}`,
                borderRadius: 12, padding: '14px 8px', cursor: 'pointer',
                textAlign: 'center', transition: 'all 0.2s',
              }}>
              <div style={{ fontSize: 22, fontWeight: 800 }}>{counts[l] || 0}</div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
                            letterSpacing: '0.5px', marginTop: 2 }}>{l}</div>
            </button>
          );
        })}
      </div>

      {/* Filter indicator */}
      {filter && (
        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Showing {filtered.length} {filter} companies
          </span>
          <button onClick={() => setFilter('')}
            style={{ fontSize: 12, color: 'var(--navy)', background: 'none',
                     border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
            Show all
          </button>
        </div>
      )}

      {/* Scores Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}>#</th>
              <th>Symbol</th>
              <th>Company</th>
              <th>Overall</th>
              <th>Label</th>
              <th>Profitability</th>
              <th>Growth</th>
              <th>Leverage</th>
              <th>Cash Flow</th>
              <th>Dividends</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s, i) => (
              <tr key={s.symbol} style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/company/${s.symbol}`)}>
                <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                <td style={{ fontWeight: 700, color: 'var(--navy)' }}>{s.symbol}</td>
                <td style={{ color: 'var(--text)', fontSize: 12, maxWidth: 180 }}>
                  <div style={{ whiteSpace: 'nowrap', overflow: 'hidden',
                                textOverflow: 'ellipsis', maxWidth: 180 }}>
                    {s.company_name}
                  </div>
                </td>
                <td style={{
                  fontWeight: 800, fontSize: 15,
                  color: s.overall_score >= 70 ? 'var(--green)' :
                         s.overall_score >= 50 ? 'var(--yellow)' : 'var(--red)',
                }}>
                  {s.overall_score ? parseFloat(s.overall_score).toFixed(1) : '—'}
                </td>
                <td><HealthBadge label={s.health_label} /></td>
                {['profitability_score','growth_score','leverage_score',
                  'cashflow_score','dividend_score','trend_score'].map(key => (
                  <td key={key} style={{ color: 'var(--text-light)', fontSize: 12 }}>
                    {s[key] ? parseFloat(s[key]).toFixed(0) : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}