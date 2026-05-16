// Loading spinner component
export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '60px 20px', gap: 16,
    }}>
      <div className="spinner" />
      <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{message}</div>
    </div>
  );
}