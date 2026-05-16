// Health Label Badge — color coded
export default function HealthBadge({ label }) {
  const styles = {
    EXCELLENT: { bg: '#DCFCE7', color: '#15803D' },
    GOOD:      { bg: '#D1FAE5', color: '#047857' },
    AVERAGE:   { bg: '#FEF9C3', color: '#854D0E' },
    WEAK:      { bg: '#FFEDD5', color: '#9A3412' },
    POOR:      { bg: '#FEE2E2', color: '#991B1B' },
    UNKNOWN:   { bg: '#F3F4F6', color: '#6B7280' },
  };

  const style = styles[label] || styles.UNKNOWN;

  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 20,
      fontSize: 11,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      background: style.bg,
      color: style.color,
    }}>
      {label || 'UNKNOWN'}
    </span>
  );
}