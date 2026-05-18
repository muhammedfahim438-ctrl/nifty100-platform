import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { getCompany, getCompanyFinancials } from '../../services/api';
import HealthBadge from '../../components/ui/HealthBadge';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import { ArrowLeft, ExternalLink } from 'lucide-react';

const TABS = ['Overview', 'Financials', 'Balance Sheet', 'Cash Flow', 'Health Score', 'Documents'];

export default function CompanyDetailPage() {
  const { symbol } = useParams();
  const navigate   = useNavigate();
  const [activeTab,   setActiveTab]   = useState('Overview');
  const [company,     setCompany]     = useState(null);
  const [financials,  setFinancials]  = useState(null);
  const [loading,     setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([getCompany(symbol), getCompanyFinancials(symbol)])
      .then(([compRes, finRes]) => {
        setCompany(compRes.data);
        setFinancials(finRes.data);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <LoadingSpinner message={`Loading ${symbol}...`} />;
  if (!company) return <div className="card">Company not found.</div>;

  const score = financials?.ml_score;
  const pl    = financials?.profit_loss || [];
  const bs    = financials?.balance_sheet || [];
  const cf    = financials?.cash_flow || [];
  const pros  = financials?.pros || [];
  const cons  = financials?.cons || [];
  const docs  = financials?.documents || [];

  // Chart data
  const plChartData = pl.slice(-10).map(row => ({
    year       : row.year_label,
    Revenue    : parseFloat(row.sales || 0),
    'Net Profit': parseFloat(row.net_profit || 0),
    'OPM %'    : parseFloat(row.opm_pct || 0),
  }));

  const bsChartData = bs.slice(-10).map(row => ({
    year      : row.year_label,
    Borrowings: parseFloat(row.borrowings || 0),
    Reserves  : parseFloat(row.reserves || 0),
    'D/E'     : parseFloat(row.debt_to_equity || 0),
  }));

  const cfChartData = cf.slice(-10).map(row => ({
    year       : row.year_label,
    Operating  : parseFloat(row.operating_activity || 0),
    Investing  : parseFloat(row.investing_activity || 0),
    Financing  : parseFloat(row.financing_activity || 0),
    'Free CF'  : parseFloat(row.free_cash_flow || 0),
  }));

  const radarData = score ? [
    { metric: 'Profitability', value: parseFloat(score.profitability_score || 0) },
    { metric: 'Growth',        value: parseFloat(score.growth_score || 0)        },
    { metric: 'Leverage',      value: parseFloat(score.leverage_score || 0)      },
    { metric: 'Cash Flow',     value: parseFloat(score.cashflow_score || 0)      },
    { metric: 'Dividends',     value: parseFloat(score.dividend_score || 0)      },
    { metric: 'Trend',         value: parseFloat(score.trend_score || 0)         },
  ] : [];

  return (
    <div>
      {/* Back button */}
      <button onClick={() => navigate('/companies')}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'none', border: 'none', color: 'var(--text-muted)',
          cursor: 'pointer', fontSize: 13, marginBottom: 16,
        }}>
        <ArrowLeft size={16} /> Back to Companies
      </button>

      {/* Company Header */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between',
                      alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--navy)' }}>
                {symbol}
              </h1>
              {score && <HealthBadge label={score.health_label} />}
            </div>
            <p style={{ color: 'var(--text)', fontSize: 15, fontWeight: 500, marginBottom: 4 }}>
              {company.company_name}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
              {company.sector_name}
            </p>

            {/* Links */}
            <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
              {company.website && (
                <a href={company.website} target="_blank" rel="noreferrer"
                   style={{ display: 'flex', alignItems: 'center', gap: 4,
                            color: 'var(--navy)', fontSize: 12, textDecoration: 'none',
                            border: '1px solid var(--border)', borderRadius: 6,
                            padding: '4px 10px' }}>
                  <ExternalLink size={12} /> Website
                </a>
              )}
              {company.nse_url && (
                <a href={company.nse_url} target="_blank" rel="noreferrer"
                   style={{ display: 'flex', alignItems: 'center', gap: 4,
                            color: 'var(--navy)', fontSize: 12, textDecoration: 'none',
                            border: '1px solid var(--border)', borderRadius: 6,
                            padding: '4px 10px' }}>
                  <ExternalLink size={12} /> NSE
                </a>
              )}
              {company.bse_url && (
                <a href={company.bse_url} target="_blank" rel="noreferrer"
                   style={{ display: 'flex', alignItems: 'center', gap: 4,
                            color: 'var(--navy)', fontSize: 12, textDecoration: 'none',
                            border: '1px solid var(--border)', borderRadius: 6,
                            padding: '4px 10px' }}>
                  <ExternalLink size={12} /> BSE
                </a>
              )}
            </div>
          </div>

          {/* Key Ratios */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)',
                        gap: 12, minWidth: 300 }}>
            {[
              { label: 'ROCE %',      value: company.roce_pct      ? `${company.roce_pct}%`  : '—' },
              { label: 'ROE %',       value: company.roe_pct       ? `${company.roe_pct}%`   : '—' },
              { label: 'Face Value',  value: company.face_value    ? `₹${company.face_value}`: '—' },
              { label: 'Book Value',  value: company.book_value    ? `₹${company.book_value}`: '—' },
              { label: 'Health Score',value: score?.overall_score  ? parseFloat(score.overall_score).toFixed(1) : '—' },
              { label: 'Sector',      value: company.sector_name   || '—' },
            ].map(({ label, value }) => (
              <div key={label} style={{
                background: 'var(--bg)', borderRadius: 8, padding: '10px 12px',
              }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)',
                              textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {label}
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--navy)', marginTop: 2 }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 20,
        borderBottom: '2px solid var(--border)', paddingBottom: 0,
      }}>
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 16px', background: 'none', border: 'none',
              cursor: 'pointer', fontSize: 13, fontWeight: activeTab === tab ? 700 : 400,
              color: activeTab === tab ? 'var(--navy)' : 'var(--text-muted)',
              borderBottom: activeTab === tab ? '2px solid var(--navy)' : '2px solid transparent',
              marginBottom: -2, transition: 'all 0.15s',
            }}>
            {tab}
          </button>
        ))}
      </div>

      {/* ── TAB: OVERVIEW ── */}
      {activeTab === 'Overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* About */}
          <div className="card">
            <h3 className="section-title">About</h3>
            <p style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.7 }}>
              {company.about_company
                ? company.about_company.replace(/\\n/g,'').substring(0, 600) + '...'
                : 'No description available.'}
            </p>
          </div>

          {/* Pros & Cons */}
          <div className="card">
            <h3 className="section-title">Pros & Cons</h3>
            {pros.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--green)',
                              marginBottom: 8, textTransform: 'uppercase' }}>
                  ✅ Pros
                </div>
                {pros.map((p, i) => (
                  <div key={i} style={{
                    fontSize: 13, color: 'var(--text)', padding: '6px 0',
                    borderBottom: '1px solid var(--border)',
                    paddingLeft: 12, borderLeft: '3px solid var(--green)',
                    marginBottom: 6,
                  }}>{p.text}</div>
                ))}
              </div>
            )}
            {cons.length > 0 && (
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--red)',
                              marginBottom: 8, textTransform: 'uppercase' }}>
                  ❌ Cons
                </div>
                {cons.map((c, i) => (
                  <div key={i} style={{
                    fontSize: 13, color: 'var(--text)', padding: '6px 0',
                    paddingLeft: 12, borderLeft: '3px solid var(--red)',
                    marginBottom: 6,
                  }}>{c.text}</div>
                ))}
              </div>
            )}
            {pros.length === 0 && cons.length === 0 && (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                No pros & cons available.
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: FINANCIALS ── */}
      {activeTab === 'Financials' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Revenue & Profit Chart */}
          <div className="card">
            <h3 className="section-title">Revenue & Net Profit Trend (₹ Cr)</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={plChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `₹${v.toLocaleString()} Cr`} />
                <Legend />
                <Bar dataKey="Revenue"     fill="var(--navy)"  radius={[4,4,0,0]} />
                <Bar dataKey="Net Profit"  fill="var(--green)" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* OPM% Chart */}
          <div className="card">
            <h3 className="section-title">Operating Profit Margin % Trend</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={plChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(v) => `${v}%`} />
                <Line dataKey="OPM %" stroke="var(--gold)"
                      strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* P&L Table */}
          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <h3 className="section-title" style={{ margin: 0 }}>
                Profit & Loss (₹ Cr)
              </h3>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {pl.slice(-8).map(r => <th key={r.year_label}>{r.year_label}</th>)}
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'Revenue',        key: 'sales'            },
                  { label: 'Expenses',       key: 'expenses'         },
                  { label: 'Oper. Profit',   key: 'operating_profit' },
                  { label: 'OPM %',          key: 'opm_pct'          },
                  { label: 'Net Profit',     key: 'net_profit'       },
                  { label: 'EPS (₹)',        key: 'eps'              },
                  { label: 'Dividend %',     key: 'dividend_payout'  },
                ].map(({ label, key }) => (
                  <tr key={key}>
                    <td style={{ fontWeight: 600, color: 'var(--text)',
                                 background: 'var(--bg)', minWidth: 130 }}>
                      {label}
                    </td>
                    {pl.slice(-8).map(r => {
                      const val = parseFloat(r[key] || 0);
                      const isNegative = val < 0;
                      return (
                        <td key={r.year_label}
                          style={{ color: isNegative ? 'var(--red)' : 'var(--text)',
                                   textAlign: 'right' }}>
                          {r[key] ? parseFloat(r[key]).toLocaleString() : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── TAB: BALANCE SHEET ── */}
      {activeTab === 'Balance Sheet' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Chart */}
          <div className="card">
            <h3 className="section-title">Borrowings vs Reserves (₹ Cr)</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={bsChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `₹${v.toLocaleString()} Cr`} />
                <Legend />
                <Bar dataKey="Borrowings" fill="var(--red)"   radius={[4,4,0,0]} />
                <Bar dataKey="Reserves"   fill="var(--green)" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Table */}
          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <h3 className="section-title" style={{ margin: 0 }}>Balance Sheet (₹ Cr)</h3>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {bs.slice(-8).map(r => <th key={r.year_label}>{r.year_label}</th>)}
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'Equity Capital', key: 'equity_capital'    },
                  { label: 'Reserves',       key: 'reserves'          },
                  { label: 'Borrowings',     key: 'borrowings'        },
                  { label: 'Total Assets',   key: 'total_assets'      },
                  { label: 'Fixed Assets',   key: 'fixed_assets'      },
                  { label: 'Investments',    key: 'investments'       },
                  { label: 'Debt / Equity',  key: 'debt_to_equity'    },
                ].map(({ label, key }) => (
                  <tr key={key}>
                    <td style={{ fontWeight: 600, color: 'var(--text)',
                                 background: 'var(--bg)', minWidth: 130 }}>
                      {label}
                    </td>
                    {bs.slice(-8).map(r => (
                      <td key={r.year_label} style={{ textAlign: 'right' }}>
                        {r[key] ? parseFloat(r[key]).toLocaleString() : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── TAB: CASH FLOW ── */}
      {activeTab === 'Cash Flow' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <h3 className="section-title">Cash Flow Trend (₹ Cr)</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={cfChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `₹${v.toLocaleString()} Cr`} />
                <Legend />
                <Bar dataKey="Operating"  fill="var(--green)" radius={[4,4,0,0]} />
                <Bar dataKey="Investing"  fill="var(--red)"   radius={[4,4,0,0]} />
                <Bar dataKey="Financing"  fill="var(--gold)"  radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <h3 className="section-title" style={{ margin: 0 }}>Cash Flow Statement (₹ Cr)</h3>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {cf.slice(-8).map(r => <th key={r.year_label}>{r.year_label}</th>)}
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'Operating CF',  key: 'operating_activity' },
                  { label: 'Investing CF',  key: 'investing_activity' },
                  { label: 'Financing CF',  key: 'financing_activity' },
                  { label: 'Net Cash Flow', key: 'net_cash_flow'      },
                  { label: 'Free CF',       key: 'free_cash_flow'     },
                ].map(({ label, key }) => (
                  <tr key={key}>
                    <td style={{ fontWeight: 600, color: 'var(--text)',
                                 background: 'var(--bg)', minWidth: 130 }}>
                      {label}
                    </td>
                    {cf.slice(-8).map(r => {
                      const val = parseFloat(r[key] || 0);
                      return (
                        <td key={r.year_label}
                          style={{ textAlign: 'right',
                                   color: val < 0 ? 'var(--red)' : 'var(--text)' }}>
                          {r[key] ? parseFloat(r[key]).toLocaleString() : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── TAB: HEALTH SCORE ── */}
      {activeTab === 'Health Score' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* Score Cards */}
          <div className="card">
            <h3 className="section-title">Score Breakdown</h3>
            {score ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  { label: 'Overall Score',    value: score.overall_score,       weight: '100%', color: 'var(--navy)' },
                  { label: 'Profitability',    value: score.profitability_score, weight: '25%',  color: 'var(--green)' },
                  { label: 'Growth',           value: score.growth_score,        weight: '20%',  color: 'var(--gold)' },
                  { label: 'Leverage',         value: score.leverage_score,      weight: '20%',  color: 'var(--red)' },
                  { label: 'Cash Flow',        value: score.cashflow_score,      weight: '15%',  color: '#8b5cf6' },
                  { label: 'Dividends',        value: score.dividend_score,      weight: '10%',  color: '#ec4899' },
                  { label: 'Trend',            value: score.trend_score,         weight: '10%',  color: '#06b6d4' },
                ].map(({ label, value, weight, color }) => (
                  <div key={label}>
                    <div style={{ display: 'flex', justifyContent: 'space-between',
                                  marginBottom: 4, fontSize: 13 }}>
                      <span style={{ color: 'var(--text)', fontWeight: 500 }}>
                        {label} <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                          ({weight})
                        </span>
                      </span>
                      <span style={{ fontWeight: 700, color }}>
                        {value ? parseFloat(value).toFixed(1) : '—'}
                      </span>
                    </div>
                    <div style={{
                      height: 6, background: 'var(--border)', borderRadius: 3
                    }}>
                      <div style={{
                        height: 6, borderRadius: 3, background: color,
                        width: `${Math.min(parseFloat(value || 0), 100)}%`,
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No health score available.</p>
            )}
          </div>

          {/* Radar Chart */}
          <div className="card">
            <h3 className="section-title">Score Radar</h3>
            {radarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
                  <Radar dataKey="value" stroke="var(--navy)"
                         fill="var(--navy)" fillOpacity={0.25} />
                  <Tooltip formatter={(v) => v.toFixed(1)} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No radar data available.</p>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: DOCUMENTS ── */}
      {activeTab === 'Documents' && (
        <div className="card">
          <h3 className="section-title">Annual Reports</h3>
          {docs.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Annual Report</th>
                </tr>
              </thead>
              <tbody>
                {docs.map(doc => (
                  <tr key={doc.year}>
                    <td style={{ fontWeight: 600 }}>{doc.year}</td>
                    <td>
                      {doc.annual_report ? (
                        <a href={doc.annual_report} target="_blank" rel="noreferrer"
                          style={{ color: 'var(--navy)', textDecoration: 'none',
                                   display: 'flex', alignItems: 'center', gap: 4,
                                   fontSize: 13 }}>
                          <ExternalLink size={13} /> Download PDF
                        </a>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Not available</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No annual reports available.</p>
          )}
        </div>
      )}
    </div>
  );
}