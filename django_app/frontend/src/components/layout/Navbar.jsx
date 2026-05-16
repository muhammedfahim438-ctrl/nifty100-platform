// Navbar — Top navigation bar
import { Search } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/companies?search=${encodeURIComponent(query.trim())}`);
      setQuery('');
    }
  };

  return (
    <nav style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: 'var(--navbar-height)',
      background: 'var(--navy)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      zIndex: 1000,
      boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    }}>

      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32,
          background: 'var(--gold)',
          borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 900, fontSize: 16, color: 'var(--navy-dark)',
        }}>B</div>
        <span style={{
          color: 'white', fontWeight: 700, fontSize: 18, letterSpacing: '-0.5px'
        }}>
          B100 <span style={{ color: 'var(--gold)' }}>Intelligence</span>
        </span>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} style={{
        display: 'flex', alignItems: 'center',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: 8, padding: '6px 12px',
        gap: 8, width: 320,
      }}>
        <Search size={16} color="rgba(255,255,255,0.6)" />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search company or symbol..."
          style={{
            background: 'transparent', border: 'none', outline: 'none',
            color: 'white', fontSize: 13, width: '100%',
          }}
        />
      </form>

      {/* Right links */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
        <a href="http://127.0.0.1:8000/api/v1/docs/"
           target="_blank" rel="noreferrer"
           style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13,
                    textDecoration: 'none' }}>
          API Docs
        </a>
        <div style={{
          background: 'var(--gold)', color: 'var(--navy-dark)',
          padding: '5px 12px', borderRadius: 6,
          fontSize: 12, fontWeight: 700,
        }}>
          NIFTY 100
        </div>
      </div>
    </nav>
  );
}