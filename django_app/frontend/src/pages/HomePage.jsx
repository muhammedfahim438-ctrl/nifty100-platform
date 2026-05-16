import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Building2, TrendingUp, Activity, ChevronRight } from 'lucide-react';
import { getSectors, getHealthScores } from '../services/api';
import KPICard from '../components/ui/KPICard';
import HealthBadge from '../components/ui/HealthBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function HomePage() {
  const [query, setQuery]       = useState('');
  const [topCompanies, setTop]  = useState([]);
  const [sectors, setSectors]   = useState([]);
  const [stats, setStats]       = useState({});
  const [loading, setLoading]   = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getHealthScores(), getSectors()])
      .then(([scoresRes, sectorsRes]) => {
        const scores = Array.isArray(scoresRes.data) 
  ? scoresRes.data 
  : scoresRes.data.results || [];
        setTop(scores.slice(0, 10));
const sectorsData = Array.isArray(sectorsRes.data) 
  ? sectorsRes.data 
  : sectorsRes.data.results || [];
setSectors(sectorsData.slice(0, 12));
        const total   = scores.length;
        const good    = scores.filter(s => s.overall_score >= 70).length;
        const avg     = scores.reduce((a, b) => a + (parseFloat(b.overall_score) || 0), 0) / total;

        setStats({ total, good, avg: avg.toFixed(1) });
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) navigate(`/companies?search=${encodeURIComponent(query.trim())}`);
  };

  if (loading) return <LoadingSpinner message="Loading B100 Intelligence..." />;

  return (
    <div>

      {/* Hero Section */}
      <div style={{
        background: 'linear-gradient(135deg, var(--navy) 0%, var(--navy-light) 100%)',
        borderRadius: 16, padding: '40px 32px', marginBottom: 24, color: 'white',
      }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>
          B100 <span style={{ color: 'var(--gold)' }}>Intelligence</span>
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: 24, fontSize: 15 }}>
          Complete financial intelligence for India's top 100 listed companies
        </p>

        {/* Search */}
        <form onSubmit={handleSearch} style={{
          display: 'flex', gap: 8, maxWidth: 520,
        }}>
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center',
            background: 'white', borderRadius: 10, padding: '10px 16px', gap: 10,
          }}>
            <Search size={18} color="var(--text-muted)" />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search company name or symbol (e.g. TCS, Reliance)..."
              style={{
                border: 'none', outline: 'none', fontSize: 14,
                color: 'var(--text)', width: '100%', background: 'transparent',
              }}
            />
          </div>
          <button type="submit" className="btn-gold" style={{ padding: '10px 20px' }}>
            Search
          </button>
        </form>

        {/* Quick links */}
        <div style={{ display: 'flex', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
          {['TCS', 'RELIANCE', 'HDFCBANK', 'INFY', 'BAJFINANCE'].map(sym => (
            <button key={sym} onClick={() => navigate(`/company/${sym}`)}
              style={{
                background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)',
                color: 'white', padding: '4px 12px', borderRadius: 20,
                fontSize: 12, cursor: 'pointer', fontWeight: 600,
              }}>
              {sym}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 16, marginBottom: 24,
      }}>
        <KPICard label="Companies Tracked" value={stats.total}
                 color="var(--navy)"  icon={Building2} />
        <KPICard label="Avg Health Score"  value={stats.avg}
                 color="var(--gold)"  icon={Activity} />
        <KPICard label="GOOD+ Companies"   value={stats.good}
                 color="var(--green)" icon={TrendingUp} />
      </div>

      {/* Top Companies + Sectors */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>

        {/* Top 10 Companies */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 className="section-title" style={{ margin: 0 }}>🏆 Top Companies by Health Score</h2>
            <button onClick={() => navigate('/companies')}
              style={{ fontSize: 12, color: 'var(--navy)', cursor: 'pointer',
                       background: 'none', border: 'none', fontWeight: 600 }}>
              View All →
            </button>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Company</th>
                <th>Score</th>
                <th>Label</th>
              </tr>
            </thead>
            <tbody>
              {topCompanies.map((c, i) => (
                <tr key={c.symbol} style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/company/${c.symbol}`)}>
                  <td style={{ color: 'var(--text-muted)', width: 30 }}>{i + 1}</td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{c.symbol}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.company_name}</div>
                  </td>
                  <td style={{ fontWeight: 700, color: 'var(--navy)' }}>
                    {parseFloat(c.overall_score).toFixed(1)}
                  </td>
                  <td><HealthBadge label={c.health_label} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Sectors */}
        <div className="card">
          <h2 className="section-title">🏭 Browse by Sector</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {sectors.map(s => (
              <button key={s.sector_id}
                onClick={() => navigate(`/sectors?name=${s.sector_name}`)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)',
                  background: 'var(--bg)', cursor: 'pointer', textAlign: 'left',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = 'var(--navy)';
                  e.currentTarget.style.color = 'white';
                  e.currentTarget.style.borderColor = 'var(--navy)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = 'var(--bg)';
                  e.currentTarget.style.color = 'var(--text)';
                  e.currentTarget.style.borderColor = 'var(--border)';
                }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{s.sector_name}</span>
                <ChevronRight size={14} color="var(--text-muted)" />
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}