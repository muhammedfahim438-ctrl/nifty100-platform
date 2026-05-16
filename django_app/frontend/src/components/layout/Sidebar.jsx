// Sidebar — Left navigation
import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard, Building2, Search,
  GitCompare, TrendingUp, Activity, ChevronRight
} from 'lucide-react';

const navItems = [
  { path: '/',           label: 'Dashboard',    icon: LayoutDashboard },
  { path: '/companies',  label: 'Companies',    icon: Building2       },
  { path: '/screener',   label: 'Screener',     icon: Search          },
  { path: '/compare',    label: 'Compare',      icon: GitCompare      },
  { path: '/sectors',    label: 'Sectors',      icon: TrendingUp      },
  { path: '/scores',     label: 'Health Scores',icon: Activity        },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside style={{
      position: 'fixed',
      top: 'var(--navbar-height)',
      left: 0,
      width: 'var(--sidebar-width)',
      height: 'calc(100vh - var(--navbar-height))',
      background: 'var(--white)',
      borderRight: '1px solid var(--border)',
      overflowY: 'auto',
      zIndex: 900,
      paddingTop: 16,
    }}>

      {/* Nav Items */}
      <div style={{ padding: '0 12px' }}>
        <div style={{
          fontSize: 10, fontWeight: 700, color: 'var(--text-muted)',
          textTransform: 'uppercase', letterSpacing: 1,
          padding: '8px 8px 4px',
        }}>
          Main Menu
        </div>

        {navItems.map(({ path, label, icon: Icon }) => {
          const active = location.pathname === path ||
            (path !== '/' && location.pathname.startsWith(path));

          return (
            <Link key={path} to={path} style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex', alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 12px',
                borderRadius: 8,
                marginBottom: 2,
                background: active ? 'var(--navy)' : 'transparent',
                color: active ? 'white' : 'var(--text)',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => {
                if (!active) e.currentTarget.style.background = 'var(--bg)';
              }}
              onMouseLeave={e => {
                if (!active) e.currentTarget.style.background = 'transparent';
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Icon size={17} color={active ? 'var(--gold)' : 'var(--text-light)'} />
                  <span style={{ fontSize: 13, fontWeight: active ? 600 : 400 }}>
                    {label}
                  </span>
                </div>
                {active && <ChevronRight size={14} color="var(--gold)" />}
              </div>
            </Link>
          );
        })}
      </div>

      {/* Bottom Info */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        padding: '16px', borderTop: '1px solid var(--border)',
        background: 'var(--bg)',
      }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
          B100 Intelligence v1.0
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', textAlign: 'center', marginTop: 2 }}>
          92 Companies · 24 Sectors
        </div>
      </div>
    </aside>
  );
}