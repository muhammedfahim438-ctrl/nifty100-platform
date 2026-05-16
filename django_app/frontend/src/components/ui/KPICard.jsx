// KPI Card — shows a single metric
export default function KPICard({ label, value, color, icon: Icon }) {
  return (
    <div className="kpi-card" style={{
      borderLeftColor: color || 'var(--navy)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="kpi-value" style={{ color: color || 'var(--navy)' }}>
            {value}
          </div>
          <div className="kpi-label">{label}</div>
        </div>
        {Icon && (
          <div style={{
            width: 40, height: 40,
            background: color ? `${color}15` : 'var(--bg)',
            borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Icon size={20} color={color || 'var(--navy)'} />
          </div>
        )}
      </div>
    </div>
  );
}