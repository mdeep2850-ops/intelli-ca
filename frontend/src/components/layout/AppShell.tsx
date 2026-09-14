import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Files, 
  Calculator, 
  Users, 
  BarChart3, 
  ShieldCheck, 
  Settings,
  Menu,
  X,
  Bell,
  Search,
  UserCircle
} from 'lucide-react';
import styles from './AppShell.module.css';

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  const getPageTitle = () => {
    const path = location.pathname.split('/').pop() || '';
    if (path === 'ai') return 'AI Workspace';
    return path.charAt(0).toUpperCase() + path.slice(1);
  };

  return (
    <div className={styles.layout}>
      {/* Sidebar Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
          style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 40 }}
        />
      )}

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${sidebarOpen ? styles.open : ''}`}>
        <div className={styles.logo}>
          INTELLI-CA
          <button className={styles.mobileToggle} onClick={toggleSidebar} style={{ marginLeft: 'auto' }}>
            <X size={24} />
          </button>
        </div>
        <nav className={styles.nav}>
          <NavItem to="/app/dashboard" icon={<LayoutDashboard size={20} />} label="Dashboard" />
          <NavItem to="/app/ai" icon={<MessageSquare size={20} />} label="AI Workspace" />
          <NavItem to="/app/documents" icon={<Files size={20} />} label="Documents" />
          <NavItem to="/app/tools" icon={<Calculator size={20} />} label="Financial Tools" />
          <NavItem to="/app/clients" icon={<Users size={20} />} label="Clients" />
          <NavItem to="/app/reports" icon={<BarChart3 size={20} />} label="Reports" />
          <NavItem to="/app/compliance" icon={<ShieldCheck size={20} />} label="Compliance" />
        </nav>
        <div className={styles.footer}>
          <NavItem to="/app/settings" icon={<Settings size={20} />} label="Settings" />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={styles.main}>
        <header className={styles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button className={styles.mobileToggle} onClick={toggleSidebar}>
              <Menu size={24} />
            </button>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{getPageTitle()}</h1>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ position: 'relative', display: 'none' }} className="md:block">
              {/* Future global search placeholder */}
              <Search size={18} style={{ position: 'absolute', left: '0.5rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
              <input 
                type="text" 
                placeholder="Search..." 
                style={{ 
                  padding: '0.5rem 0.5rem 0.5rem 2rem', 
                  borderRadius: 'var(--radius-md)', 
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-base)',
                  color: 'var(--color-text-primary)'
                }} 
              />
            </div>
            <button style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
              <Bell size={20} />
            </button>
            <button style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
              <UserCircle size={24} />
            </button>
          </div>
        </header>
        
        <div className={styles.content}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink 
      to={to} 
      className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  );
}
