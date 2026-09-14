import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styles from './LoginPage.module.css';
import { IntelliSplashCursor } from '../../components/effects/IntelliSplashCursor';

export default function LoginPage() {
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate login success and redirect to app
    navigate('/app');
  };

  return (
    <div className={styles.authContainer}>
      <IntelliSplashCursor color="#7c3aed" />
      <div className={styles.authCard}>
        <h2 className={styles.title}>Sign In to Intelli-CA</h2>
        <form onSubmit={handleLogin}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Email Address</label>
            <input type="email" className={styles.input} placeholder="admin@intelli-ca.com" required />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Password</label>
            <input type="password" className={styles.input} placeholder="••••••••" required />
          </div>
          <button type="submit" className={styles.submitBtn}>Sign In</button>
        </form>
        <div className={styles.links}>
          <div style={{ marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Don't have an account? </span>
            <Link to="/signup" style={{ color: 'var(--color-primary)', fontWeight: 500 }}>Sign Up</Link>
          </div>
          <Link to="/" style={{ color: 'var(--color-text-secondary)' }}>← Back to Home</Link>
        </div>
      </div>
    </div>
  );
}
