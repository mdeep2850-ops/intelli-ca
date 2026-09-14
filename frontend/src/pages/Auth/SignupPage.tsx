import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styles from './SignupPage.module.css';
import { IntelliSplashCursor } from '../../components/effects/IntelliSplashCursor';

export default function SignupPage() {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.fullName.trim()) newErrors.fullName = 'Full Name is required';
    if (!formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Valid Email is required';
    if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      // Simulate signup success and redirect to login
      navigate('/login');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className={styles.authContainer}>
      <IntelliSplashCursor color="#7c3aed" />
      <div className={styles.authCard}>
        <h2 className={styles.title}>Create an Intelli-CA Account</h2>
        <form onSubmit={handleSignup}>
          
          <div className={styles.formGroup}>
            <label className={styles.label}>Full Name</label>
            <input 
              type="text" 
              name="fullName"
              className={`${styles.input} ${errors.fullName ? styles.inputError : ''}`} 
              placeholder="Jane Doe" 
              value={formData.fullName}
              onChange={handleChange}
            />
            {errors.fullName && <div className={styles.errorText}>{errors.fullName}</div>}
          </div>
          
          <div className={styles.formGroup}>
            <label className={styles.label}>Email Address</label>
            <input 
              type="email" 
              name="email"
              className={`${styles.input} ${errors.email ? styles.inputError : ''}`} 
              placeholder="admin@intelli-ca.com" 
              value={formData.email}
              onChange={handleChange}
            />
            {errors.email && <div className={styles.errorText}>{errors.email}</div>}
          </div>
          
          <div className={styles.formGroup}>
            <label className={styles.label}>Password</label>
            <input 
              type="password" 
              name="password"
              className={`${styles.input} ${errors.password ? styles.inputError : ''}`} 
              placeholder="••••••••" 
              value={formData.password}
              onChange={handleChange}
            />
            {errors.password && <div className={styles.errorText}>{errors.password}</div>}
          </div>
          
          <div className={styles.formGroup}>
            <label className={styles.label}>Confirm Password</label>
            <input 
              type="password" 
              name="confirmPassword"
              className={`${styles.input} ${errors.confirmPassword ? styles.inputError : ''}`} 
              placeholder="••••••••" 
              value={formData.confirmPassword}
              onChange={handleChange}
            />
            {errors.confirmPassword && <div className={styles.errorText}>{errors.confirmPassword}</div>}
          </div>
          
          <button type="submit" className={styles.submitBtn}>Sign Up</button>
        </form>
        
        <div className={styles.links}>
          <div>
            <span style={{ color: 'var(--color-text-secondary)' }}>Already have an account? </span>
            <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 500 }}>Sign In</Link>
          </div>
          <Link to="/" style={{ color: 'var(--color-text-secondary)' }}>← Back to Home</Link>
        </div>
      </div>
    </div>
  );
}
