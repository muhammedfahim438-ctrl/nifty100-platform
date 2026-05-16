// Main layout wrapper — Navbar + Sidebar + Content
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div>
      <Navbar />
      <div style={{ paddingTop: 'var(--navbar-height)' }}>
        <Sidebar />
        <main style={{
          marginLeft: 'var(--sidebar-width)',
          padding: '24px',
          minHeight: 'calc(100vh - var(--navbar-height))',
          background: 'var(--bg)',
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}