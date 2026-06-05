import { useState, useEffect, useMemo } from 'react';
import './App.css';

function App() {
  // --- Form Input States ---
  const [monthlyIncome, setMonthlyIncome] = useState(5000);
  const [loanAmount, setLoanAmount] = useState(120000);
  const [existingDebt, setExistingDebt] = useState(15000); // Annual debt
  const [creditScore, setCreditScore] = useState(700);
  const [employmentStatus, setEmploymentStatus] = useState('Employed');
  const [educationLevel, setEducationLevel] = useState('Graduate');
  
  // Advanced States
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loanTerm, setLoanTerm] = useState(30); // years
  const [employmentDuration, setEmploymentDuration] = useState(3); // years
  const [savingsAmount, setSavingsAmount] = useState(25000);

  // --- UI States ---
  const [activeTab, setActiveTab] = useState('calculator'); // 'calculator' | 'history'
  const [loading, setLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking'); // 'checking' | 'connected' | 'disconnected'

  // --- Client-side Live Financial Ratios ---
  const annualIncome = useMemo(() => monthlyIncome * 12, [monthlyIncome]);
  
  const dti = useMemo(() => {
    if (annualIncome <= 0) return 0;
    return (existingDebt / annualIncome) * 100;
  }, [existingDebt, annualIncome]);

  const lti = useMemo(() => {
    if (annualIncome <= 0) return 0;
    return loanAmount / annualIncome;
  }, [loanAmount, annualIncome]);

  const incomeCoverage = useMemo(() => {
    if (existingDebt <= 0) return 99.0;
    return annualIncome / existingDebt;
  }, [annualIncome, existingDebt]);

  const checkHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        setApiStatus('connected');
      } else {
        setApiStatus('disconnected');
      }
    } catch (err) {
      console.error("Health check error:", err);
      setApiStatus('disconnected');
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        setHistory(data.history || []);
        if (data.error) {
          console.warn("History DB Warning:", data.error);
        }
      }
    } catch (err) {
      console.error("Fetch history error:", err);
    }
  };

  // --- Check API Health on Mount ---
  useEffect(() => {
    let isMounted = true;
    const init = async () => {
      if (isMounted) {
        await checkHealth();
        await fetchHistory();
      }
    };
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  // --- Form Submission ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setPredictionResult(null);

    const payload = {
      monthly_income: parseFloat(monthlyIncome),
      loan_amount: parseFloat(loanAmount),
      existing_debt: parseFloat(existingDebt),
      credit_score: parseInt(creditScore),
      employment_status: employmentStatus,
      education_level: educationLevel,
      loan_term: showAdvanced ? parseInt(loanTerm) : null,
      employment_duration: showAdvanced ? parseFloat(employmentDuration) : null,
      savings_amount: showAdvanced ? parseFloat(savingsAmount) : null,
    };

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to analyze risk');
      }

      const data = await res.json();
      setPredictionResult(data);
      
      // Refresh history log after successful predict
      fetchHistory();
    } catch (err) {
      console.error("Analysis error:", err);
      setError(err.message || 'An unexpected error occurred. Is the API server running?');
    } finally {
      setLoading(false);
    }
  };

  // --- Dynamic Color Class for Credit Score ---
  const getFicoClass = (score) => {
    if (score >= 740) return 'excellent';
    if (score >= 670) return 'good';
    if (score >= 580) return 'fair';
    return 'poor';
  };

  const getFicoLabel = (score) => {
    if (score >= 740) return '⭐ Excellent (740 – 850)';
    if (score >= 670) return '👍 Good (670 – 739)';
    if (score >= 580) return '⚠️ Fair (580 – 669)';
    return '🚨 Poor (300 – 579)';
  };

  // --- Filtered History ---
  const filteredHistory = useMemo(() => {
    return history.filter(item => {
      const matchesSearch = item.loan_id?.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            item.approval_status?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesFilter = statusFilter === 'All' || item.approval_status === statusFilter;
      
      return matchesSearch && matchesFilter;
    });
  }, [history, searchQuery, statusFilter]);

  // --- Stats calculations ---
  const historyStats = useMemo(() => {
    if (history.length === 0) return { rate: 0, avgScore: 0, total: 0 };
    const approved = history.filter(h => h.approval_status === 'Approved').length;
    const rate = (approved / history.length) * 100;
    const avgScore = history.reduce((sum, h) => sum + (h.credit_score || 0), 0) / history.length;
    return {
      rate: rate.toFixed(1),
      avgScore: Math.round(avgScore),
      total: history.length
    };
  }, [history]);

  // Confidence ring circle configuration
  const circleRadius = 35;
  const circleCircumference = 2 * Math.PI * circleRadius;
  const confidencePercent = predictionResult ? predictionResult.probability * 100 : 0;
  const strokeDashoffset = circleCircumference - (confidencePercent / 100) * circleCircumference;

  return (
    <div className="app-container">
      {/* Navbar */}
      <header className="app-nav">
        <div className="nav-brand">
          <span className="brand-icon">🏦</span>
          <h2>VaultRisk</h2>
          <span className="brand-tag">AI Engine v2.0</span>
        </div>
        <div className="nav-status">
          <div className="status-indicator">
            <span className={`status-dot ${apiStatus === 'checking' ? 'loading' : ''} ${apiStatus === 'disconnected' ? 'danger' : ''}`}></span>
            <span>API: {apiStatus === 'connected' ? 'Connected' : apiStatus === 'checking' ? 'Connecting...' : 'Offline'}</span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="tabs-container">
        <button 
          className={`tab-btn ${activeTab === 'calculator' ? 'active' : ''}`}
          onClick={() => setActiveTab('calculator')}
        >
          🔍 Eligibility Engine
        </button>
        <button 
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('history');
            fetchHistory();
          }}
        >
          📜 Decision History
        </button>
      </div>

      {activeTab === 'calculator' ? (
        <div className="dashboard-grid">
          {/* Form Side */}
          <div className="glass-card">
            <h3 className="card-title">
              <span className="card-title-icon">📝</span> Financial & Applicant Details
            </h3>

            <form onSubmit={handleSubmit} className="form-grid">
              {/* Income & Loan Amount */}
              <div className="form-row">
                <div className="input-group">
                  <label htmlFor="monthly-income">Monthly Income</label>
                  <div className="input-wrapper">
                    <span className="input-prefix">$</span>
                    <input 
                      id="monthly-income"
                      type="number" 
                      className="has-prefix"
                      value={monthlyIncome} 
                      onChange={(e) => setMonthlyIncome(Math.max(0, parseFloat(e.target.value) || 0))}
                      min="500"
                      max="100000"
                      step="100"
                      required
                    />
                  </div>
                  <span className="input-hint">Annualized: ${(monthlyIncome * 12).toLocaleString()}</span>
                </div>

                <div className="input-group">
                  <label htmlFor="loan-amount">Requested Loan</label>
                  <div className="input-wrapper">
                    <span className="input-prefix">$</span>
                    <input 
                      id="loan-amount"
                      type="number" 
                      className="has-prefix"
                      value={loanAmount} 
                      onChange={(e) => setLoanAmount(Math.max(0, parseFloat(e.target.value) || 0))}
                      min="5000"
                      max="2000000"
                      step="1000"
                      required
                    />
                  </div>
                  <span className="input-hint">Total borrowing limit requested</span>
                </div>
              </div>

              {/* Existing Debt & Credit Score */}
              <div className="form-row">
                <div className="input-group">
                  <label htmlFor="existing-debt">Existing Annual Debt</label>
                  <div className="input-wrapper">
                    <span className="input-prefix">$</span>
                    <input 
                      id="existing-debt"
                      type="number" 
                      className="has-prefix"
                      value={existingDebt} 
                      onChange={(e) => setExistingDebt(Math.max(0, parseFloat(e.target.value) || 0))}
                      min="0"
                      max="500000"
                      step="500"
                      required
                    />
                  </div>
                  <span className="input-hint">All monthly debt cards/obligations x 12</span>
                </div>

                <div className="input-group slider-container">
                  <div className="slider-header">
                    <label htmlFor="credit-score">Credit Score (FICO)</label>
                    <span className={`slider-val-badge ${getFicoClass(creditScore)}`}>
                      {creditScore}
                    </span>
                  </div>
                  <input 
                    id="credit-score"
                    type="range" 
                    className="range-input" 
                    min="300" 
                    max="850" 
                    value={creditScore}
                    onChange={(e) => setCreditScore(parseInt(e.target.value))}
                  />
                  <span className="input-hint" style={{ textAlign: 'right' }}>
                    {getFicoLabel(creditScore)}
                  </span>
                </div>
              </div>

              {/* Employment & Education */}
              <div className="form-row">
                <div className="input-group">
                  <label>Employment Status</label>
                  <div className="selector-cards">
                    {['Employed', 'Self-Employed', 'Unemployed'].map((status) => (
                      <button
                        key={status}
                        type="button"
                        className={`selector-card ${employmentStatus === status ? 'active' : ''}`}
                        onClick={() => setEmploymentStatus(status)}
                      >
                        {status}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="input-group">
                  <label>Education Level</label>
                  <div className="selector-cards">
                    {['Graduate', 'Not Graduate'].map((level) => (
                      <button
                        key={level}
                        type="button"
                        className={`selector-card ${educationLevel === level ? 'active' : ''}`}
                        onClick={() => setEducationLevel(level)}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Advanced Settings Toggle */}
              <div 
                className="advanced-toggle"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                {showAdvanced ? '⚙️ Hide Advanced Risk Variables' : '⚙️ Show Advanced Risk Variables'}
              </div>

              {showAdvanced && (
                <div className="advanced-fields">
                  <div className="form-row">
                    <div className="input-group">
                      <label htmlFor="loan-term">Loan Term (Years)</label>
                      <div className="input-wrapper">
                        <input 
                          id="loan-term"
                          type="number" 
                          value={loanTerm} 
                          onChange={(e) => setLoanTerm(Math.max(1, parseInt(e.target.value) || 0))}
                          min="1"
                          max="40"
                          required
                        />
                      </div>
                    </div>

                    <div className="input-group">
                      <label htmlFor="employment-duration">Job Duration (Years)</label>
                      <div className="input-wrapper">
                        <input 
                          id="employment-duration"
                          type="number" 
                          value={employmentDuration} 
                          onChange={(e) => setEmploymentDuration(Math.max(0, parseFloat(e.target.value) || 0))}
                          min="0"
                          max="50"
                          step="0.5"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="input-group">
                    <label htmlFor="savings-amount">Cash Savings & Assets</label>
                    <div className="input-wrapper">
                      <span className="input-prefix">$</span>
                      <input 
                        id="savings-amount"
                        type="number" 
                        className="has-prefix"
                        value={savingsAmount} 
                        onChange={(e) => setSavingsAmount(Math.max(0, parseFloat(e.target.value) || 0))}
                        min="0"
                        max="10000000"
                        step="500"
                        required
                      />
                    </div>
                    <span className="input-hint">Direct reserve reserves, deposits and liquid assets</span>
                  </div>
                </div>
              )}

              {/* Live Indicators Block */}
              <div style={{ marginTop: '0.5rem' }}>
                <span className="input-hint" style={{ fontWeight: '600', textTransform: 'uppercase', fontSize: '0.72rem', letterSpacing: '0.05em' }}>
                  📊 Client-Side Live Ratios
                </span>
                <div className="live-indicators">
                  <div className="indicator-box">
                    <span className="label">Debt-to-Income</span>
                    <span className="value">{dti.toFixed(1)}%</span>
                    <span className={`badge ${dti <= 35 ? 'safe' : dti <= 45 ? 'warning' : 'danger'}`}>
                      {dti <= 35 ? 'Safe' : dti <= 45 ? 'Borderline' : 'Too High'}
                    </span>
                  </div>
                  <div className="indicator-box">
                    <span className="label">Loan-to-Income</span>
                    <span className="value">{lti.toFixed(1)}x</span>
                    <span className={`badge ${lti <= 3 ? 'safe' : lti <= 5 ? 'warning' : 'danger'}`}>
                      {lti <= 3 ? 'Conservative' : lti <= 5 ? 'High' : 'Exceeds 5x'}
                    </span>
                  </div>
                  <div className="indicator-box">
                    <span className="label">Income Cover</span>
                    <span className="value">{incomeCoverage.toFixed(1)}x</span>
                    <span className="badge safe">Multiples</span>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading || apiStatus === 'disconnected'}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    <span>Running AI Scoring Models...</span>
                  </>
                ) : (
                  <>
                    <span>🔍 Check Loan Eligibility</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Results Side */}
          <div className="glass-card">
            <h3 className="card-title">
              <span className="card-title-icon">⚡</span> Decision Analysis Panel
            </h3>

            {error && (
              <div className="result-hero rejected" style={{ textAlign: 'left', padding: '1.25rem' }}>
                <span className="result-icon">⚠️</span>
                <h2 style={{ fontSize: '1.2rem', color: 'var(--color-rejected)' }}>System Diagnostics Warning</h2>
                <p style={{ fontSize: '0.85rem' }}>{error}</p>
                <button 
                  onClick={checkHealth}
                  style={{ 
                    marginTop: '1rem', 
                    padding: '0.4rem 0.8rem', 
                    background: 'rgba(255,255,255,0.08)', 
                    border: '1px solid var(--border-light)', 
                    borderRadius: '4px',
                    color: 'white',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  Retry API Connection
                </button>
              </div>
            )}

            {!predictionResult && !error && (
              <div className="empty-state">
                <span className="empty-state-icon">📊</span>
                <h4>Awaiting Evaluation</h4>
                <p>Fill out the financial profile and trigger the eligibility engine to generate a decision tree risk report.</p>
              </div>
            )}

            {predictionResult && !error && (
              <div className="results-container">
                {/* Result Status card */}
                <div className={`result-hero ${predictionResult.status === 'Approved' ? 'approved' : 'rejected'}`}>
                  <span className="result-icon">
                    {predictionResult.status === 'Approved' ? '✅' : '❌'}
                  </span>
                  <h2>Loan {predictionResult.status}</h2>
                  
                  {/* Circular Confidence Graph */}
                  <div className="confidence-ring-container">
                    <svg width="90" height="90" viewBox="0 0 90 90">
                      {/* Background circle */}
                      <circle 
                        cx="45" cy="45" r={circleRadius} 
                        fill="transparent" 
                        stroke="rgba(255,255,255,0.03)" 
                        strokeWidth="8"
                      />
                      {/* Highlighted path */}
                      <circle 
                        cx="45" cy="45" r={circleRadius} 
                        fill="transparent" 
                        stroke={predictionResult.status === 'Approved' ? 'var(--color-approved)' : 'var(--color-rejected)'} 
                        strokeWidth="8"
                        strokeDasharray={circleCircumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        transform="rotate(-90 45 45)"
                        style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
                      />
                    </svg>
                    <span className="confidence-value">
                      {Math.round(confidencePercent)}%
                    </span>
                  </div>
                  
                  <span className="result-meta">
                    {predictionResult.status === 'Approved' ? 'Approval Confidence Probability' : 'Repayment Failure Risk Metric'}
                  </span>
                  <span className="result-meta" style={{ fontSize: '0.72rem', opacity: 0.7 }}>
                    Application ID: {predictionResult.loan_id}
                  </span>
                </div>

                {/* Score Breakdowns */}
                <div className="analysis-grid">
                  {/* Strengths */}
                  <div>
                    <h4 className="analysis-section-title">⭐ Approval Strengths</h4>
                    <div className="factors-container">
                      {predictionResult.strengths?.length > 0 ? (
                        predictionResult.strengths.map((s, idx) => (
                          <div key={idx} className="factor-item strength">
                            <span className="icon">✓</span>
                            <span>{s}</span>
                          </div>
                        ))
                      ) : (
                        <span className="input-hint">No primary strengths logged in the decision logs.</span>
                      )}
                    </div>
                  </div>

                  {/* Risks */}
                  <div style={{ marginTop: '0.5rem' }}>
                    <h4 className="analysis-section-title">⚠️ Identified Risk Factors</h4>
                    <div className="factors-container">
                      {predictionResult.risk_factors?.length > 0 ? (
                        predictionResult.risk_factors.map((w, idx) => (
                          <div key={idx} className="factor-item risk">
                            <span className="icon">⚠</span>
                            <span>{w}</span>
                          </div>
                        ))
                      ) : (
                        <div className="factor-item strength">
                          <span className="icon">✓</span>
                          <span>No critical risk flags triggered</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div style={{ marginTop: '0.5rem' }}>
                    <h4 className="analysis-section-title">💡 Actionable Mitigations</h4>
                    <div className="factors-container">
                      {predictionResult.recommendations?.length > 0 ? (
                        predictionResult.recommendations.map((r, idx) => (
                          <div key={idx} className="factor-item recommendation">
                            <span className="icon">➔</span>
                            <span>{r}</span>
                          </div>
                        ))
                      ) : (
                        <div className="factor-item strength">
                          <span className="icon">✓</span>
                          <span>Applicant profile is optimized. Ready for manual review fallback.</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* History Dashboard Tab */
        <div className="glass-card history-section">
          <h3 className="card-title">
            <span className="card-title-icon">📜</span> Recent Risk Audits Log
          </h3>

          {/* Stats Summary Panel */}
          <div className="stats-row">
            <div className="stat-card">
              <span className="label">Total Audits</span>
              <span className="value">{historyStats.total}</span>
            </div>
            <div className="stat-card">
              <span className="label">AI Approval Rate</span>
              <span className="value">{historyStats.rate}%</span>
            </div>
            <div className="stat-card">
              <span className="label">Average FICO Credit</span>
              <span className="value">{historyStats.avgScore}</span>
            </div>
            <div className="stat-card">
              <span className="label">Connection Mode</span>
              <span className="value" style={{ fontSize: '1rem', marginTop: '0.3rem', color: 'var(--accent-secondary)' }}>
                Active DB Backend
              </span>
            </div>
          </div>

          <div className="history-header">
            {/* Status Filter tab group */}
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {['All', 'Approved', 'Rejected'].map((status) => (
                <button
                  key={status}
                  className={`tab-btn ${statusFilter === status ? 'active' : ''}`}
                  onClick={() => setStatusFilter(status)}
                  style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
                >
                  {status}
                </button>
              ))}
            </div>

            {/* Search filter input */}
            <div className="search-input-wrapper">
              <span className="search-icon">🔍</span>
              <input 
                type="text" 
                placeholder="Search Loan ID or status..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {filteredHistory.length > 0 ? (
            <div className="history-table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Loan ID</th>
                    <th>Credit Score</th>
                    <th>Annual Income</th>
                    <th>Loan Amount</th>
                    <th>Status Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '600', fontFamily: 'var(--font-display)' }}>
                        {item.loan_id || `APP-RAND-${idx}`}
                      </td>
                      <td>
                        <span className={`slider-val-badge ${getFicoClass(item.credit_score)}`} style={{ fontSize: '0.8rem', padding: '0.1rem 0.4rem' }}>
                          {item.credit_score}
                        </span>
                      </td>
                      <td>${(item.annual_income || 0).toLocaleString()}</td>
                      <td>${(item.loan_amount || 0).toLocaleString()}</td>
                      <td>
                        <span className={`badge-status ${item.approval_status === 'Approved' ? 'approved' : 'rejected'}`}>
                          {item.approval_status === 'Approved' ? 'Approved' : 'Rejected'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <span className="empty-state-icon" style={{ fontSize: '2rem' }}>📭</span>
              <p>No matching applications located in the transaction logs database.</p>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <div>
          <span>VaultRisk Platform // Decision Tree Neural System v2.0.0</span>
        </div>
        <div className="footer-links">
          <span>Secure AES-256 Logs</span>
          <span>&bull;</span>
          <span>Compliance Guard</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
