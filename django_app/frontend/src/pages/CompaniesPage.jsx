import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Filter } from 'lucide-react';
import { getCompanies, getSectors, getHealthScores } from '../services/api';
import HealthBadge from '../components/ui/HealthBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function CompaniesPage() {
  const [companies,  setCompanies]  = useState([]);
  const [sectors,    setSectors]    = useState([]);
  const [scores,     setScores]     = useState({});
  const [loading,    setLoading]    = useState(true);
  const [search,     setSearch]     = useState('');
  const [sector,     setSector]     = useState('');
  const [label,      setLabel]      = useState('');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const q = searchParams.get('search') || '';
    setSearch(q);

    Promise.all([getCompanies({ search: q }), getSectors(), getHealthScores()])
      .then(([compRes, secRes, scoreRes]) => {
        const companiesData = Array.isArray(compRes.data)
          ? compRes.data : compRes.data.results || [];
        const sectorsData = Array.isArray(secRes.data)
          ? secRes.data : secRes.data.results || [];
        const scoresData = Array.isArray(scoreRes.data)
          ? scoreRes.data : scoreRes.data.results || [];

        // Build scores lookup map
        const scoreMap = {};
        scoresData.forEach(s => { scoreMap[s.symbol] = s; });

        setCompanies(companiesData);
        setSectors(sectorsData);
        setScores(scoreMap);
      })
      .finally(() => setLoading(false));
  }, [searchParams]);

  // Filter companies
  const filtered = companies.filter(c => {
    const matchSearch = !search ||
      c.symbol.toLowerCase().includes(search.toLowerCase()) ||
      (c.company_name || '').toLowerCase().includes(search.toLowerCase());
    const matchSector = !sector || c.sector_name === sector;
    const score = scores[c.symbol];
    const matchLabel = !label || (score && score.health_label === label);
    return matchSearch && matchSector && matchLabel;
  });

  const handleSearch = (e) => {
    e.preventDefault();
    setLoading(true);
    getCompanies({ search }).then(res => {
      const data = Array.isArray(res.data) ? res.data : res.data.results || [];
      setCompanies(data);
      setLoading(false);
    });
  };

  if (loading) return <LoadingSpinner message="Loading companies..." />;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--navy)' }}>
          All Companies
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          {filtered.length} of {companies.length} companies
        </p>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: 20, padding: 16 }}>
        <form onSubmit={handleSearch}
          style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>

          {/* Search */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            border: '1px solid var(--border)', borderRadius: 8,
            padding: '7px 12px', flex: 1, minWidth: 200,
            background: 'white',
          }}>
            <Search size={15} color="var(--text-muted)" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search symbol or company name..."
              style={{
                border: 'none', outline: 'none', fontSize: 13,
                color: 'var(--text)', width: '100%', background: 'transparent',
              }}
            />
          </div>

          {/* Sector filter */}
          <select className="select" value={sector}
                  onChange={e => setSector(e.target.value)}
                  style={{ minWidth: 160 }}>
            <option value="">All Sectors</option>
            {sectors.map(s => (
              <option key={s.sector_id} value={s.sector_name}>
                {s.sector_name}
              </option>
            ))}
          </select>

          {/* Label filter */}
          <select className="select" value={label}
                  onChange={e => setLabel(e.target.value)}
                  style={{ minWidth: 140 }}>
            <option value="">All Labels</option>
            {['EXCELLENT','GOOD','AVERAGE','WEAK','POOR'].map(l => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>

          <button type="submit" className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Filter size={14} /> Filter
          </button>

          {(search || sector || label) && (
            <button type="button"
              onClick={() => { setSearch(''); setSector(''); setLabel(''); }}
              style={{
                background: 'none', border: 'none', color: 'var(--text-muted)',
                fontSize: 13, cursor: 'pointer', textDecoration: 'underline',
              }}>
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}>#</th>
              <th>Symbol</th>
              <th>Company Name</th>
              <th>Sector</th>
              <th>Health Score</th>
              <th>Label</th>
              <th>ROCE %</th>
              <th>ROE %</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c, i) => {
              const score = scores[c.symbol];
              const overallScore = score?.overall_score;
              const healthLabel  = score?.health_label || c.health_label;

              return (
                <tr key={c.symbol}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/company/${c.symbol}`)}>
                  <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                  <td>
                    <span style={{
                      fontWeight: 700, color: 'var(--navy)',
                      fontSize: 13,
                    }}>
                      {c.symbol}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text)', maxWidth: 240 }}>
                    <div style={{
                      whiteSpace: 'nowrap', overflow: 'hidden',
                      textOverflow: 'ellipsis', maxWidth: 220,
                    }}>
                      {c.company_name}
                    </div>
                  </td>
                  <td>
                    <span style={{
                      background: 'var(--bg)', padding: '2px 8px',
                      borderRadius: 20, fontSize: 11, color: 'var(--text-light)',
                    }}>
                      {c.sector_name || '—'}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 700,
                      color: overallScore >= 70 ? 'var(--green)' :
                             overallScore >= 50 ? 'var(--yellow)' :
                             overallScore ? 'var(--red)' : 'var(--text-muted)',
                    }}>
                      {overallScore ? parseFloat(overallScore).toFixed(1) : '—'}
                    </span>
                  </td>
                  <td>
                    <HealthBadge label={healthLabel} />
                  </td>
                  <td style={{ color: 'var(--text-light)' }}>
                    {c.roce_pct ? `${c.roce_pct}%` : '—'}
                  </td>
                  <td style={{ color: 'var(--text-light)' }}>
                    {c.roe_pct ? `${c.roe_pct}%` : '—'}
                  </td>
                </tr>
              );
            })}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{
                  textAlign: 'center', padding: '40px',
                  color: 'var(--text-muted)',
                }}>
                  No companies found matching your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}