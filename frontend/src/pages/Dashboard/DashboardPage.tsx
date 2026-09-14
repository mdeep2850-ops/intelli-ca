
import { Link } from 'react-router-dom';
import { Bot, FileText, Calculator, ArrowRight } from 'lucide-react';
import styles from './DashboardPage.module.css';

export default function DashboardPage() {
  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.heroSection}>
        <h1 className={styles.heroTitle}>Welcome to Intelli-CA</h1>
        <p className={styles.heroSubtitle}>
          Your Agentic AI platform for financial intelligence and automated workflows.
        </p>
        
        <Link to="/app/ai" className={styles.ctaButton}>
          <span>Open AI Workspace</span>
          <ArrowRight size={18} />
        </Link>
      </div>

      <div className={styles.featuresSection}>
        <div className={styles.featureCard}>
          <div className={styles.featureIconWrapper}>
            <FileText size={24} className={styles.featureIcon} />
          </div>
          <h3>Document Intelligence</h3>
          <p>Upload Profit & Loss statements, Balance Sheets, and other financial records securely.</p>
        </div>

        <div className={styles.featureCard}>
          <div className={styles.featureIconWrapper}>
            <Calculator size={24} className={styles.featureIcon} />
          </div>
          <h3>Deterministic Calculations</h3>
          <p>Financial metrics are calculated strictly by reliable Python tools, ensuring mathematical accuracy.</p>
        </div>

        <div className={styles.featureCard}>
          <div className={styles.featureIconWrapper}>
            <Bot size={24} className={styles.featureIcon} />
          </div>
          <h3>Agentic Reasoning</h3>
          <p>Intelli-CA dynamically routes your requests to the correct capabilities and synthesizes professional reports.</p>
        </div>
      </div>
    </div>
  );
}
