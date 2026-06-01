import React, { useState } from 'react';
import { 
  TrendingUp, 
  AlertTriangle, 
  DollarSign, 
  Layers, 
  Bell, 
  RefreshCw, 
  Cpu, 
  Database, 
  ShieldAlert, 
  Activity 
} from 'lucide-react';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [budgetLimit, setBudgetLimit] = useState(150.00);
  const [currentCost, setCurrentCost] = useState(112.45);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showNotification, setShowNotification] = useState(false);

  // Mock data for costs breakdown
  const costBreakdown = [
    { service: 'AWS Lambda', cost: 42.18, icon: Cpu, color: '#ff9900', percentage: 37 },
    { service: 'Amazon DynamoDB', cost: 35.50, icon: Database, color: '#3b82f6', percentage: 32 },
    { service: 'Amazon API Gateway', cost: 18.25, icon: Layers, color: '#10b981', percentage: 16 },
    { service: 'Amazon CloudWatch', cost: 11.80, icon: Activity, color: '#ec4899', percentage: 10 },
    { service: 'AWS SNS', cost: 4.72, icon: Bell, color: '#f59e0b', percentage: 5 },
  ];

  // Mock history logs
  const historyLogs = [
    { date: '2026-05-31', cost: 3.82, status: 'Normal' },
    { date: '2026-05-30', cost: 3.75, status: 'Normal' },
    { date: '2026-05-29', cost: 4.10, status: 'Normal' },
    { date: '2026-05-28', cost: 5.20, status: 'Normal' },
    { date: '2026-05-27', cost: 6.85, status: 'Spike Detected' },
  ];

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setShowNotification(true);
      setTimeout(() => setShowNotification(false), 3000);
    }, 800);
  };

  const handleBudgetChange = (e) => {
    setBudgetLimit(parseFloat(e.target.value) || 0);
  };

  return (
    <div style={styles.container}>
      {/* Top Banner / Toast Notification */}
      {showNotification && (
        <div style={styles.toast}>
          <RefreshCw size={16} className="pulse" style={{ marginRight: 8 }} />
          Fetched latest AWS Cost Explorer & DynamoDB metrics successfully.
        </div>
      )}

      {/* Header */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>AWS Cloud Cost Monitor</h1>
          <p style={styles.subtitle}>Real-time serverless billing intelligence dashboard</p>
        </div>
        <div style={styles.actions}>
          <button 
            style={{ ...styles.button, ...(isRefreshing ? styles.buttonActive : {}) }}
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw size={16} style={{ marginRight: 8, animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }} />
            {isRefreshing ? 'Syncing...' : 'Sync AWS Metrics'}
          </button>
        </div>
      </header>

      {/* Navigation tabs */}
      <div style={styles.tabsContainer}>
        <button 
          style={{ ...styles.tab, ...(activeTab === 'overview' ? styles.activeTab : {}) }}
          onClick={() => setActiveTab('overview')}
        >
          <TrendingUp size={16} style={{ marginRight: 8 }} />
          Cost Overview
        </button>
        <button 
          style={{ ...styles.tab, ...(activeTab === 'alerts' ? styles.activeTab : {}) }}
          onClick={() => setActiveTab('alerts')}
        >
          <AlertTriangle size={16} style={{ marginRight: 8 }} />
          Budget & Alerts
        </button>
      </div>

      {/* Main Grid content */}
      {activeTab === 'overview' && (
        <div>
          {/* Top KPI Cards Row */}
          <div style={styles.kpiRow}>
            <div className="glass-card" style={styles.kpiCard}>
              <div style={styles.kpiHeader}>
                <span style={styles.kpiLabel}>Month-to-Date Cost</span>
                <DollarSign size={20} color="#3b82f6" />
              </div>
              <div style={styles.kpiValue}>${currentCost.toFixed(2)}</div>
              <div style={{ ...styles.kpiFooter, color: '#10b981' }}>
                <span>↑ 12% vs last month</span>
              </div>
            </div>

            <div className="glass-card" style={styles.kpiCard}>
              <div style={styles.kpiHeader}>
                <span style={styles.kpiLabel}>Projected End of Month</span>
                <TrendingUp size={20} color="#10b981" />
              </div>
              <div style={styles.kpiValue}>${(currentCost * 1.15).toFixed(2)}</div>
              <div style={{ ...styles.kpiFooter, color: '#94a3b8' }}>
                <span>Calculated via regression</span>
              </div>
            </div>

            <div className="glass-card" style={styles.kpiCard}>
              <div style={styles.kpiHeader}>
                <span style={styles.kpiLabel}>Budget Threshold Limit</span>
                <ShieldAlert size={20} color={currentCost > budgetLimit ? '#ef4444' : '#f59e0b'} />
              </div>
              <div style={styles.kpiValue}>${budgetLimit.toFixed(2)}</div>
              <div style={{ 
                ...styles.kpiFooter, 
                color: currentCost > budgetLimit ? '#ef4444' : '#10b981'
              }}>
                <span>{currentCost > budgetLimit ? 'Budget breach alert triggered!' : 'Within budget margin'}</span>
              </div>
            </div>
          </div>

          {/* Detailed Content: Services & History */}
          <div style={styles.detailsGrid}>
            {/* Service Breakdown */}
            <div className="glass-card" style={styles.gridItem}>
              <h3 style={styles.sectionTitle}>Cost Breakdown by Service</h3>
              <div style={styles.breakdownList}>
                {costBreakdown.map((item, index) => (
                  <div key={index} style={styles.breakdownItem}>
                    <div style={styles.breakdownLabelRow}>
                      <div style={styles.serviceNameRow}>
                        <item.icon size={16} color={item.color} style={{ marginRight: 8 }} />
                        <span>{item.service}</span>
                      </div>
                      <span style={styles.serviceCost}>${item.cost.toFixed(2)}</span>
                    </div>
                    {/* Visual Progress Bar */}
                    <div style={styles.progressBarBackground}>
                      <div style={{ 
                        ...styles.progressBarFill, 
                        width: `${item.percentage}%`,
                        backgroundColor: item.color 
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Historical Logs */}
            <div className="glass-card" style={styles.gridItem}>
              <h3 style={styles.sectionTitle}>Aggregated Metric History</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={styles.table}>
                  <thead>
                    <tr style={styles.tableHeaderRow}>
                      <th style={styles.tableHeader}>Aggregated Date</th>
                      <th style={styles.tableHeader}>Daily Cost</th>
                      <th style={styles.tableHeader}>System Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyLogs.map((log, index) => (
                      <tr key={index} style={styles.tableRow}>
                        <td style={styles.tableCell}>{log.date}</td>
                        <td style={styles.tableCell}>${log.cost.toFixed(2)}</td>
                        <td style={styles.tableCell}>
                          <span style={{
                            ...styles.statusBadge,
                            backgroundColor: log.status === 'Normal' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            color: log.status === 'Normal' ? '#10b981' : '#ef4444'
                          }}>
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="glass-card" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h3 style={styles.sectionTitle}>Alert Threshold Configuration</h3>
          <p style={styles.descriptionText}>
            Configure your monthly budget alert threshold limit. If cumulative Month-to-Date costs
            cross this value, the alert checker Lambda function will trigger an email notification
            via AWS SNS.
          </p>

          <div style={styles.formGroup}>
            <label style={styles.formLabel}>Monthly Budget Limit (USD)</label>
            <div style={styles.inputWrapper}>
              <span style={styles.inputPrefix}>$</span>
              <input 
                type="number" 
                value={budgetLimit} 
                onChange={handleBudgetChange} 
                style={styles.formInput} 
              />
            </div>
          </div>

          <div style={styles.alertPreview}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
              <Bell size={18} color="#f59e0b" style={{ marginRight: 8 }} />
              <strong style={{ color: '#f8fafc' }}>Active Notification Policy:</strong>
            </div>
            <ul style={styles.bulletList}>
              <li>Monitors DynamoDB hourly aggregates for limits exceeded.</li>
              <li>Sends rich alerts to subscribers on standard cost breaches.</li>
              <li>Connected Topic: <code style={styles.codeSnippet}>aws-cost-alerts-topic</code></li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

// Styling Object using Inline JS styles for absolute ease of setup
const styles = {
  container: {
    padding: '40px 24px',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  toast: {
    position: 'fixed',
    top: '24px',
    right: '24px',
    background: 'rgba(59, 130, 246, 0.9)',
    color: '#fff',
    padding: '12px 20px',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    zIndex: 1000,
    display: 'flex',
    alignItems: 'center',
    fontSize: '0.875rem',
    fontWeight: 500,
    backdropFilter: 'blur(4px)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '16px',
    marginBottom: '32px',
  },
  title: {
    fontSize: '2.25rem',
    fontWeight: 800,
    letterSpacing: '-0.025em',
    background: 'linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    color: '#94a3b8',
    marginTop: '4px',
    fontSize: '1rem',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
  },
  button: {
    backgroundColor: '#3b82f6',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '10px 18px',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    transition: 'all 0.2s',
    boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.2)',
  },
  buttonActive: {
    backgroundColor: '#2563eb',
    opacity: 0.8,
  },
  tabsContainer: {
    display: 'flex',
    gap: '8px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    marginBottom: '32px',
    paddingBottom: '8px',
  },
  tab: {
    backgroundColor: 'transparent',
    color: '#94a3b8',
    border: 'none',
    padding: '8px 16px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    borderRadius: '6px',
    transition: 'all 0.2s',
  },
  activeTab: {
    color: '#3b82f6',
    backgroundColor: 'rgba(59, 130, 246, 0.08)',
    fontWeight: 600,
  },
  kpiRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    marginBottom: '32px',
  },
  kpiCard: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    minHeight: '140px',
  },
  kpiHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  kpiLabel: {
    color: '#94a3b8',
    fontSize: '0.875rem',
    fontWeight: 500,
  },
  kpiValue: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#f8fafc',
    margin: '8px 0',
  },
  kpiFooter: {
    fontSize: '0.75rem',
    fontWeight: 500,
    marginTop: '4px',
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '24px',
  },
  gridItem: {
    minHeight: '380px',
  },
  sectionTitle: {
    fontSize: '1.25rem',
    fontWeight: 700,
    marginBottom: '20px',
    color: '#f8fafc',
  },
  breakdownList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '18px',
  },
  breakdownItem: {
    display: 'flex',
    flexDirection: 'column',
  },
  breakdownLabelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '6px',
    fontSize: '0.875rem',
  },
  serviceNameRow: {
    display: 'flex',
    alignItems: 'center',
    color: '#e2e8f0',
  },
  serviceCost: {
    fontWeight: 600,
    color: '#f8fafc',
  },
  progressBarBackground: {
    height: '6px',
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: '3px',
    transition: 'width 0.4s ease',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '8px',
  },
  tableHeaderRow: {
    borderBottom: '1px solid rgba(255,255,255,0.08)',
  },
  tableHeader: {
    textAlign: 'left',
    color: '#94a3b8',
    fontWeight: 500,
    fontSize: '0.875rem',
    paddingBottom: '12px',
  },
  tableRow: {
    borderBottom: '1px solid rgba(255,255,255,0.04)',
  },
  tableCell: {
    padding: '14px 0',
    color: '#e2e8f0',
    fontSize: '0.875rem',
  },
  statusBadge: {
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  descriptionText: {
    color: '#94a3b8',
    fontSize: '0.875rem',
    lineHeight: 1.6,
    marginBottom: '24px',
  },
  formGroup: {
    marginBottom: '24px',
  },
  formLabel: {
    display: 'block',
    color: '#e2e8f0',
    fontSize: '0.875rem',
    fontWeight: 500,
    marginBottom: '8px',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputPrefix: {
    position: 'absolute',
    left: '12px',
    color: '#94a3b8',
    fontSize: '1rem',
  },
  formInput: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '8px',
    padding: '12px 12px 12px 28px',
    color: '#fff',
    fontSize: '1rem',
    width: '100%',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  alertPreview: {
    backgroundColor: 'rgba(245, 158, 11, 0.03)',
    border: '1px dashed rgba(245, 158, 11, 0.2)',
    borderRadius: '12px',
    padding: '16px',
    marginTop: '32px',
  },
  bulletList: {
    paddingLeft: '20px',
    color: '#94a3b8',
    fontSize: '0.85rem',
    lineHeight: 1.7,
  },
  codeSnippet: {
    fontFamily: 'monospace',
    backgroundColor: 'rgba(255,255,255,0.06)',
    padding: '2px 6px',
    borderRadius: '4px',
    color: '#f59e0b',
  }
};
