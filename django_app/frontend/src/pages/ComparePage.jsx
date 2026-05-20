import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GitCompare, X, Plus } from 'lucide-react';
import { getCompanyFinancials } from '../services/api';
import HealthBadge from '../components/ui/HealthBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['var(--navy)', 'var(--gold)', 'var(--green)', 'var(--red)'];

const METRICS = [
  { label: 'Health Score',    key: 'overall_score',         source: 'score'    },
  { label: 'ROCE %',          key: 'roce_pct',              source: 'company'  },
  { label: 'ROE %',           key: 'roe_pct',               source: 'company'  },
  { label: 'Latest Revenue',  key: 'sales',                 source: 'pl_last'  },
  { label: 'Net Profit',      key: 'net_profit',            source: 'pl_last'  },
  { label: 'OPM %',           key: 'opm_pct',               source: 'pl_last'  },
  { label: 'Debt/Equity',     key: 'debt_to_equity',        source: 'bs_last'  },
  { label: 'EPS (₹)',         key: 'eps',                   source: 'pl_last'  },
  { label: 'Dividend %',      key: 'dividend_payout',       source: 'pl_last'  },
];

export default function ComparePage() {
  const [symbols,   setSymbols]   = useState(['', '']);
  const [data,      setData]      = useState({});
  const [loading,   setLoading]   = useState(false);
  const [compared,  setCompared]  = useState(false);
  const navigate = useNavigate();

  const handleCompare = async () => {
    const valid = symbols.filter(s => s.trim());
    if (valid.length < 2) {
      alert('Please enter at least 2 company symbols');
      return;
    }
    setLoading(true);
    setCompared(false);
    const results = {};
    await Promise.all(valid.map(async sym => {
      try {
        const res = await getCompanyFinancials(sym.toUpperCase().trim());
        results[sym.toUpperCase().trim()] = res.data;
      } catch (e) {
        results[sym.toUpperCase().trim()] = null;
      }
    }));
    setData(results);
    setLoading(false);
    setCompared(true);
  };

  const getValue = (compData, metric) => {
    if (!compData) return '—';
    const { source, key } = metric;
    try {
      if (source === 'score')   return compData.ml_score?.[key] ? parseFloat(compData.ml_score[key]).toFixed(1) : '—';
      if (source === 'company') return compData[key] ? `${compData[key]}%` : '—';
      if (source === 'pl_last') {
        const pl = compData.profit_loss;
        if (!pl?.length) return '—';
        const last = pl[pl.length - 1];
        return last[key] ? parseFloat(last[key]).toLocaleString() : '—';
      }
      if (source === 'bs_last') {
        const bs = compData.balance_sheet;
        if (!bs?.length) return '—';
        const last = bs[bs.length - 1];
        return last[key] ? parseFloat(last[key]).toFixed(2) : '—';
      }
    } catch { return '—'; }
    return '—';
  };

  // Build revenue chart data
  const validSymbols = symbols.filter(s => s.trim() && data[s.toUpperCase().trim()]);
  const revenueChartData = (() => {
    if (!validSymbols.length) return [];
    const yearMap = {};
    validSymbols.forEach(sym => {
      const pl = data[sym.toUpperCase().trim()]?.profit_loss || [];
      pl.forEach(row => {
        if (!yearMap[row.year_label]) yearMap[row.year_label] = { year: row.year_label };
        yearMap[row.year_label][sym.toUpperCase().trim()] = parseFloat(row.sales || 0);
      });
    });
    return Object.values(yearMap).slice(-10);
  })();

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--navy)' }}>
          ⚖️ Compare Companies
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Side by side financial comparison of up to 4 companies
        </p>
      </div>

      {/* Symbol Input */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          {symbols.map((sym, i) => (
            <div key={i} style={{ position: 'relative' }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
                              textTransform: 'uppercase', letterSpacing: '0.5px',
                              display: 'block', marginBottom: 4 }}>
                Company {i + 1}
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <input
                  value={sym}
                  onChange={e => {
                    const updated = [...symbols];
                    updated[i] = e.target.value.toUpperCase();
                    setSymbols(updated);
                  }}
                  placeholder={`e.g. TCS`}
                  className="input"
                  style={{ width: 140, textTransform: 'uppercase', fontWeight: 700 }}
                />
                {symbols.length > 2 && (
                  <button onClick={() => setSymbols(symbols.filter((_, j) => j !== i))}
                    style={{ background: 'none', border: 'none', cursor: 'pointer',
                             color: 'var(--red)', padding: 4 }}>
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}

          {symbols.length < 4 && (
            <button onClick={() => setSymbols([...symbols, ''])}
              style={{ display: 'flex', alignItems: 'center', gap: 4,
                       background: 'var(--bg)', border: '1px dashed var(--border)',
                       borderRadius: 8, padding: '8px 14px', cursor: 'pointer',
                       color: 'var(--text-muted)', fontSize: 13, marginTop: 20 }}>
              <Plus size={14} /> Add Company
            </button>
          )}

          <button className="btn-primary" onClick={handleCompare}
            style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 20 }}>
            <GitCompare size={14} /> Compare
          </button>
        </div>

        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>
          💡 Try: TCS, INFY, HCLTECH, WIPRO
        </div>
      </div>

      {loading && <LoadingSpinner message="Fetching company data..." />}

      {!loading && compared && (
        <>
          {/* Comparison Table */}
          <div className="card" style={{ marginBottom: 20, padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontWeight: 700 }}>Financial Comparison</span>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ minWidth: 140 }}>Metric</th>
                  {validSymbols.map((sym, i) => (
                    <th key={sym} style={{ color: COLORS[i] }}>
                      <button onClick={() => navigate(`/company/${sym.toUpperCase().trim()}`)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer',
                                 color: COLORS[i], fontWeight: 700, fontSize: 13 }}>
                        {sym.toUpperCase().trim()}
                      </button>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>
                        {data[sym.toUpperCase().trim()]?.company_name?.substring(0, 25)}
                      </div>
                      <div style={{ marginTop: 4 }}>
                        <HealthBadge label={data[sym.toUpperCase().trim()]?.ml_score?.health_label} />
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {METRICS.map(metric => (
                  <tr key={metric.key}>
                    <td style={{ fontWeight: 600, background: 'var(--bg)', color: 'var(--text)' }}>
                      {metric.label}
                    </td>
                    {validSymbols.map((sym, i) => (
                      <td key={sym} style={{ fontWeight: 500, color: COLORS[i] }}>
                        {getValue(data[sym.toUpperCase().trim()], metric)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Revenue Chart */}
          <div className="card">
            <h3 className="section-title">Revenue Trend Comparison (₹ Cr)</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={revenueChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `₹${v.toLocaleString()} Cr`} />
                <Legend />
                {validSymbols.map((sym, i) => (
                  <Line key={sym} dataKey={sym.toUpperCase().trim()}
                        stroke={COLORS[i]} strokeWidth={2}
                        dot={{ r: 3 }} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {!loading && !compared && (
        <div style={{
          background: 'var(--white)', borderRadius: 12, padding: '50px',
          textAlign: 'center', color: 'var(--text-muted)',
          border: '2px dashed var(--border)',
        }}>
          <GitCompare size={40} color="var(--border)" style={{ marginBottom: 16 }} />
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>
            Enter company symbols and click Compare
          </div>
          <div style={{ fontSize: 13 }}>
            Compare up to 4 companies side by side
          </div>
        </div>
      )}
    </div>
  );
}