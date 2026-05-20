import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { TrendingUp, ChevronRight, ArrowLeft } from 'lucide-react';
import { getSectors, getCompanies, getHealthScores } from '../services/api';
import HealthBadge from '../components/ui/HealthBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function SectorsPage() {
  const [sectors,    setSectors]    = useState([]);
  const [companies,  setCompanies]  = useState([]);
  const [scores,     setScores]     = useState({});
  const [loading,    setLoading]    = useState(true);
  const [searchParams] = useSearchParams();
  const selectedSector = searchParams.get('name');
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getSectors(), getCompanies(), getHealthScores()])
      .then(([secRes, compRes, scoreRes]) => {
        const sectorsData  = Array.isArray(secRes.data)   ? secRes.data   : secRes.data.results   || [];
        const companiesData= Array.isArray(compRes.data)  ? compRes.data  : compRes.data.results  || [];
        const scoresData   = Array.isArray(scoreRes.data) ? scoreRes.data : scoreRes.data.results || [];

        const scoreMap = {};
        scoresData.forEach(s => { scoreMap[s.symbol] = s; });

        setSectors(sectorsData);
        setCompanies(companiesData);
        setScores(scoreMap);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading sectors..." />;

  // If a sector is selected show detail view
  if (selectedSector) {
    const sectorCompanies = companies.filter(c => c.sector_name === selectedSector);
    const withScores = sectorCompanies.map(c => ({
      ...c,
      score: scores[c.symbol],
    })).sort((a, b) => {
      const aScore = parseFloat(a.score?.overall_score || 0);
      const bScore = parseFloat(b.score?.overall_score || 0);
      return bScore - aScore;
    });

    const avgScore = withScores.reduce((sum, c) =>
      sum + parseFloat(c.score?.overall_score || 0), 0) / withScores.length;

    return (
      <div>
        {/* Back */}
        <button onClick={() => navigate('/sectors')}
          style={{ display: 'flex', alignItems: 'center', gap: 6,
                   background: 'none', border: 'none', color: 'var(--text-muted)',
                   cursor: 'pointer', fontSize: 13, marginBottom: 16 }}>
          <ArrowLeft size={16} /> Back to Sectors
        </button>

        {/* Sector Header */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--navy)' }}>
                {selectedSector}
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
                {withScores.length} companies in this sector
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--navy)' }}>
                {avgScore.toFixed(1)}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Avg Health Score</div>
            </div>
          </div>
        </div>

        {/* Companies Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Symbol</th>
                <th>Company Name</th>
                <th>Health Score</th>
                <th>Label</th>
                <th>ROCE %</th>
                <th>ROE %</th>
              </tr>
            </thead>
            <tbody>
              {withScores.map((c, i) => (
                <tr key={c.symbol} style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/company/${c.symbol}`)}>
                  <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                  <td style={{ fontWeight: 700, color: 'var(--navy)' }}>{c.symbol}</td>
                  <td style={{ color: 'var(--text)' }}>{c.company_name}</td>
                  <td style={{
                    fontWeight: 700,
                    color: c.score?.overall_score >= 70 ? 'var(--green)' :
                           c.score?.overall_score >= 50 ? 'var(--yellow)' : 'var(--red)',
                  }}>
                    {c.score?.overall_score
                      ? parseFloat(c.score.overall_score).toFixed(1) : '—'}
                  </td>
                  <td><HealthBadge label={c.score?.health_label} /></td>
                  <td style={{ color: 'var(--text-light)' }}>
                    {c.roce_pct ? `${c.roce_pct}%` : '—'}
                  </td>
                  <td style={{ color: 'var(--text-light)' }}>
                    {c.roe_pct ? `${c.roe_pct}%` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // Sector list view
  const sectorStats = sectors.map(s => {
    const sectorCompanies = companies.filter(c => c.sector_name === s.sector_name);
    const sectorScores = sectorCompanies
      .map(c => parseFloat(scores[c.symbol]?.overall_score || 0))
      .filter(v => v > 0);
    const avgScore = sectorScores.length
      ? sectorScores.reduce((a, b) => a + b, 0) / sectorScores.length : 0;

    return { ...s, count: sectorCompanies.length, avgScore };
  }).sort((a, b) => b.avgScore - a.avgScore);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--navy)' }}>
          🏭 Sectors
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          {sectors.length} sectors covering all Nifty 100 companies
        </p>
      </div>

      {/* Sector Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
        {sectorStats.map(s => {
          const scoreColor = s.avgScore >= 70 ? 'var(--green)' :
                             s.avgScore >= 50 ? 'var(--yellow)' : 'var(--red)';
          return (
            <button key={s.sector_id}
              onClick={() => navigate(`/sectors?name=${s.sector_name}`)}
              style={{
                background: 'var(--white)', borderRadius: 12,
                padding: '20px', border: '1px solid var(--border)',
                cursor: 'pointer', textAlign: 'left',
                boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                e.currentTarget.style.borderColor = 'var(--navy)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.06)';
                e.currentTarget.style.borderColor = 'var(--border)';
              }}>
              <div style={{ display: 'flex', justifyContent: 'space-between',
                            alignItems: 'flex-start', marginBottom: 12 }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--navy)' }}>
                  {s.sector_name}
                </div>
                <ChevronRight size={16} color="var(--text-muted)" />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between',
                            alignItems: 'center' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {s.count} companies
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <TrendingUp size={14} color={scoreColor} />
                  <span style={{ fontWeight: 700, color: scoreColor, fontSize: 14 }}>
                    {s.avgScore.toFixed(1)}
                  </span>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ height: 4, background: 'var(--border)',
                            borderRadius: 2, marginTop: 10 }}>
                <div style={{
                  height: 4, borderRadius: 2, background: scoreColor,
                  width: `${Math.min(s.avgScore, 100)}%`,
                }} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}