import React, { useState, useEffect, useCallback } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { 
  TrendingUp, 
  AlertTriangle, 
  DollarSign, 
  Layers, 
  Bell, 
  RefreshCw, 
  CheckCircle, 
  XCircle
} from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

// Vibrant Shades of Silver, Chrome, and Metallic tones
const SERVICE_COLORS = {
  EC2: '#ffffff',       // Pure White / Glowing Chrome
  S3: '#d4d4d8',        // Platinum Silver
  Lambda: '#a1a1aa',    // Sleek Steel
  RDS: '#71717a',       // Slate Metal
  CloudFront: '#3f3f46', // Dark Charcoal
  Unknown: '#27272a'    // Deep Gunmetal
};

export default function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // State for metrics & configurations
  const [summaryData, setSummaryData] = useState({
    mtd_total: 0,
    projected_month_end: 0,
    threshold: 50,
    percent_used: 0,
    top_service: 'None',
    service_totals: {}
  });

  const [chartData, setChartData] = useState([]);
  const [serviceNames, setServiceNames] = useState([]);
  
  // Alert Config State
  const [thresholdInput, setThresholdInput] = useState('50.00');
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [configSaving, setConfigSaving] = useState(false);
  const [configMessage, setConfigMessage] = useState(null);

  // Fetch Dashboard Data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Summary
      const summaryRes = await fetch(`${API_BASE_URL}/summary`);
      if (!summaryRes.ok) {
        throw new Error(`Summary API returned status ${summaryRes.status}`);
      }
      const summary = await summaryRes.json();
      setSummaryData(summary);
      setThresholdInput(summary.threshold.toString());

      // 2. Fetch Metrics (last 30 days)
      const metricsRes = await fetch(`${API_BASE_URL}/metrics?days=30`);
      if (!metricsRes.ok) {
        throw new Error(`Metrics API returned status ${metricsRes.status}`);
      }
      const metrics = await metricsRes.json();

      // Transform raw lists to Recharts suitable format
      const formattedChartData = metrics.dates.map((date, index) => {
        const item = { date };
        Object.keys(metrics.services).forEach(svc => {
          item[svc] = metrics.services[svc][index];
        });
        return item;
      });

      setChartData(formattedChartData);
      setServiceNames(Object.keys(metrics.services));
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Dashboard Fetch Error:", err);
      
      // Local In-Browser High-Fidelity Simulation Fallback
      console.warn("API Server is unreachable. Falling back to local in-browser simulation mode!");
      
      const today = new Date();
      const dates = [];
      const services = ["EC2", "S3", "Lambda", "RDS", "CloudFront"];
      const servicesData = {
        EC2: [],
        S3: [],
        Lambda: [],
        RDS: [],
        CloudFront: []
      };
      
      let mtdTotal = 0;
      const serviceTotals = { EC2: 0, S3: 0, Lambda: 0, RDS: 0, CloudFront: 0 };
      
      // Generate 30 days of data deterministically
      for (let i = 29; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(today.getDate() - i);
        const dateStr = d.toISOString().split('T')[0];
        dates.push(dateStr);
        
        // Simple deterministic values based on date index
        const isWeekend = d.getDay() === 0 || d.getDay() === 6;
        const seedValue = d.getDate();
        
        const ec2 = parseFloat(((72 + (isWeekend ? 0 : (seedValue % 10 + 5))) * 0.0464 * (0.95 + (seedValue % 5) * 0.02)).toFixed(4));
        const s3 = parseFloat((50 + (seedValue * 0.15) * (0.023 / 30) * (0.95 + (seedValue % 3) * 0.02)).toFixed(4));
        const lamb = parseFloat((((isWeekend ? 200000 : 900000) + (seedValue * 10000)) * 0.0000002).toFixed(4));
        const rds = parseFloat((24 * 0.017 * (0.98 + (seedValue % 4) * 0.01)).toFixed(4));
        const cf = parseFloat(((isWeekend ? 100 : 400) * 0.0085 * (0.95 + (seedValue % 6) * 0.02)).toFixed(4));
        
        servicesData.EC2.push(ec2);
        servicesData.S3.push(s3);
        servicesData.Lambda.push(lamb);
        servicesData.RDS.push(rds);
        servicesData.CloudFront.push(cf);
        
        // Sum MTD costs for current month dates
        if (d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear()) {
          mtdTotal += (ec2 + s3 + lamb + rds + cf);
          serviceTotals.EC2 += ec2;
          serviceTotals.S3 += s3;
          serviceTotals.Lambda += lamb;
          serviceTotals.RDS += rds;
          serviceTotals.CloudFront += cf;
        }
      }
      
      const daysElapsed = today.getDate() || 1;
      const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
      const projected = (mtdTotal / daysElapsed) * daysInMonth;
      
      let topService = "EC2";
      let topCost = serviceTotals.EC2;
      services.forEach(svc => {
        if (serviceTotals[svc] > topCost) {
          topCost = serviceTotals[svc];
          topService = svc;
        }
      });
      
      setSummaryData(prev => {
        const threshold = prev.threshold || 50.00;
        const percentUsed = threshold > 0 ? (mtdTotal / threshold) * 100 : 0;
        return {
          mtd_total: mtdTotal,
          projected_month_end: projected,
          threshold: threshold,
          percent_used: parseFloat(percentUsed.toFixed(2)),
          top_service: topService,
          service_totals: {
            EC2: parseFloat(serviceTotals.EC2.toFixed(2)),
            S3: parseFloat(serviceTotals.S3.toFixed(2)),
            Lambda: parseFloat(serviceTotals.Lambda.toFixed(2)),
            RDS: parseFloat(serviceTotals.RDS.toFixed(2)),
            CloudFront: parseFloat(serviceTotals.CloudFront.toFixed(2))
          },
          local_demo_mode: true
        };
      });
      
      const formattedChartData = dates.map((date, index) => {
        const item = { date };
        services.forEach(svc => {
          item[svc] = servicesData[svc][index];
        });
        return item;
      });
      
      setChartData(formattedChartData);
      setServiceNames(services);
      setLastUpdated(new Date().toLocaleTimeString() + " (Offline Mode)");
      setError("Docker Desktop could not be reached. Local simulation enabled.");
    } finally {
      setLoading(false);
    }
  }, []);


  // Save Alert Configuration
  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setConfigSaving(true);
    setConfigMessage(null);

    const nextThreshold = parseFloat(thresholdInput) || 0;

    // If in Offline Simulation Mode, handle save instantly in-browser
    if (summaryData.local_demo_mode) {
      setTimeout(() => {
        setConfigMessage({ type: 'success', text: 'Alert configurations saved successfully (Simulation Mode)!' });
        setSummaryData(prev => {
          const nextPercent = nextThreshold > 0 ? (prev.mtd_total / nextThreshold) * 100 : 0;
          return {
            ...prev,
            threshold: nextThreshold,
            percent_used: parseFloat(nextPercent.toFixed(2)),
            local_demo_mode: true
          };
        });
        setConfigSaving(false);
      }, 600);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          monthly_threshold: nextThreshold,
          alerts_enabled: alertsEnabled
        })
      });

      if (!response.ok) {
        throw new Error(`Config API returned status ${response.status}`);
      }

      setConfigMessage({ type: 'success', text: 'Alert configurations saved successfully!' });
      
      // Update local state metrics to match saved thresholds
      setSummaryData(prev => {
        const nextPercent = nextThreshold > 0 ? (prev.mtd_total / nextThreshold) * 100 : 0;
        return {
          ...prev,
          threshold: nextThreshold,
          percent_used: parseFloat(nextPercent.toFixed(2))
        };
      });
    } catch (err) {
      console.error("Config Save Error:", err);
      setConfigMessage({ type: 'error', text: err.message || 'Failed to update configuration.' });
    } finally {
      setConfigSaving(false);
      // Auto clear message after 4 seconds
      setTimeout(() => setConfigMessage(null), 4000);
    }
  };

  // Initial fetch and 5-minute interval setup
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // 5 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  // Premium glowing silver progress bar intensity
  const getBudgetIntensity = (percent) => {
    if (percent < 70) return 'bg-gradient-to-r from-zinc-600 via-zinc-400 to-zinc-200 shadow-[0_0_8px_rgba(255,255,255,0.3)]';
    if (percent <= 90) return 'bg-gradient-to-r from-zinc-400 via-zinc-200 to-white shadow-[0_0_12px_rgba(255,255,255,0.5)]';
    return 'bg-gradient-to-r from-zinc-300 via-white to-white shadow-[0_0_15px_rgba(255,255,255,0.8)] animate-pulse';
  };

  return (
    <div className="min-h-screen bg-black text-zinc-100 flex flex-col font-sans selection:bg-zinc-700 selection:text-white relative">
      
      {/* Dynamic Cyber Grid & Animated Blur Radial Lights */}
      <div className="cyber-grid" />
      <div className="fixed top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-zinc-700/5 blur-[130px] pointer-events-none -z-10 floating-blur-1" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-zinc-500/5 blur-[120px] pointer-events-none -z-10 floating-blur-2" />

      {/* 1. Header Bar */}
      <header className="border-b border-zinc-900/80 bg-black/40 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-white shadow-[0_0_12px_#ffffff] animate-pulse" />
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-500 bg-clip-text text-transparent text-glow-silver">
                AWS Cost Monitor
              </h1>
              <p className="text-xs text-zinc-500 font-semibold tracking-wider mt-0.5 uppercase">
                Serverless Cost Intelligence Portal
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {lastUpdated && (
              <span className="text-xs text-zinc-500 font-mono font-medium tracking-wide">
                SYNCED: {lastUpdated}
              </span>
            )}
            <button
              onClick={fetchData}
              disabled={loading}
              className="flex items-center text-xs font-bold px-4 py-2 rounded-xl border border-zinc-800 bg-gradient-to-b from-zinc-900 to-zinc-950 hover:from-zinc-800 hover:to-zinc-900 text-zinc-200 hover:text-white transition-all shadow-[0_4px_12px_rgba(0,0,0,0.5)] hover:shadow-[0_4px_15px_rgba(255,255,255,0.05)] active:scale-95"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-2 ${loading ? 'animate-spin' : ''}`} />
              REFRESH
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        
        {/* Error Banner / Demo Mode Banner */}
        {error && !summaryData.local_demo_mode && (
          <div className="flex items-center gap-3 p-4 rounded-2xl border border-rose-500/20 bg-rose-500/10 text-rose-200 text-sm animate-pulse">
            <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <div className="flex-1">
              <strong>API Error:</strong> {error}. Make sure your API backend is active and REACT_APP_API_URL is configured.
            </div>
            <button onClick={fetchData} className="underline font-semibold hover:text-white">Retry</button>
          </div>
        )}

        {summaryData.local_demo_mode && (
          <div className="flex items-center gap-3 p-4 rounded-2xl border border-zinc-800 bg-zinc-950/80 backdrop-blur-md text-zinc-300 text-sm shadow-xl">
            <AlertTriangle className="w-5 h-5 text-zinc-400 flex-shrink-0 animate-bounce" />
            <div className="flex-1">
              <strong>Offline Mode Enabled:</strong> Local database container is not running. Streaming browser-simulated cost projections.
            </div>
            <button 
              onClick={() => {
                setSummaryData(prev => ({ ...prev, local_demo_mode: false }));
                fetchData();
              }} 
              className="underline text-xs font-extrabold text-white tracking-wider hover:text-zinc-300 transition-colors uppercase ml-4"
            >
              Retry Live Link
            </button>
          </div>
        )}

        {/* 2. Top Row — 4 Metric Cards */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {loading ? (
            // Premium Skeletons
            Array(4).fill(0).map((_, idx) => (
              <div key={idx} className="h-32 rounded-2xl border border-zinc-900 bg-zinc-950/50 animate-pulse p-6 flex flex-col justify-between">
                <div className="h-4 bg-zinc-800 rounded w-1/2"></div>
                <div className="h-8 bg-zinc-800 rounded w-3/4 my-2"></div>
                <div className="h-3 bg-zinc-800 rounded w-1/3"></div>
              </div>
            ))
          ) : (
            <>
              {/* Card 1: MTD Spend */}
              <div className="silver-card p-6 flex flex-col justify-between min-h-[128px]">
                <div className="flex justify-between items-center text-zinc-400 text-sm font-semibold tracking-wide uppercase">
                  <span>Month-to-Date Spend</span>
                  <DollarSign className="w-5 h-5 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.4)]" />
                </div>
                <div className="text-3xl font-extrabold tracking-tight text-white my-1 text-glow-silver">
                  ${summaryData.mtd_total.toFixed(2)}
                </div>
                <div className="text-xs text-zinc-500 font-medium">
                  Accrued cost this month
                </div>
              </div>

              {/* Card 2: Projected Spend */}
              <div className="silver-card p-6 flex flex-col justify-between min-h-[128px]">
                <div className="flex justify-between items-center text-zinc-400 text-sm font-semibold tracking-wide uppercase">
                  <span>Projected Month-End</span>
                  <TrendingUp className="w-5 h-5 text-zinc-300 drop-shadow-[0_0_8px_rgba(200,200,200,0.3)]" />
                </div>
                <div className="text-3xl font-extrabold tracking-tight text-white my-1 text-glow-silver">
                  ${summaryData.projected_month_end.toFixed(2)}
                </div>
                <div className="text-xs text-zinc-500 font-medium">
                  Linear projection estimate
                </div>
              </div>

              {/* Card 3: Top Service */}
              <div className="silver-card p-6 flex flex-col justify-between min-h-[128px]">
                <div className="flex justify-between items-center text-zinc-400 text-sm font-semibold tracking-wide uppercase">
                  <span>Top Contributor</span>
                  <Layers className="w-5 h-5 text-zinc-400" />
                </div>
                <div className="text-2xl font-extrabold tracking-tight text-white my-1 truncate text-glow-silver">
                  {summaryData.top_service}
                </div>
                <div className="text-xs text-zinc-500 font-medium">
                  Cost: ${((summaryData.service_totals[summaryData.top_service]) || 0).toFixed(2)}
                </div>
              </div>

              {/* Card 4: Budget Used */}
              <div className="silver-card p-6 flex flex-col justify-between min-h-[128px]">
                <div className="flex justify-between items-center text-zinc-400 text-sm font-semibold tracking-wide uppercase">
                  <span>Monthly Budget Used</span>
                  <AlertTriangle className={`w-5 h-5 ${summaryData.percent_used > 90 ? 'text-white drop-shadow-[0_0_8px_white] animate-bounce' : 'text-zinc-400'}`} />
                </div>
                <div className="my-1 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold tracking-tight text-white text-glow-silver">
                    {summaryData.percent_used}%
                  </span>
                  <span className="text-xs text-zinc-500 font-medium">
                    of ${summaryData.threshold}
                  </span>
                </div>
                {/* Visual dynamic progress bar in silver/white gradient */}
                <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden mt-1">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${getBudgetIntensity(summaryData.percent_used)}`}
                    style={{ width: `${Math.min(summaryData.percent_used, 100)}%` }}
                  />
                </div>
              </div>
            </>
          )}
        </section>

        {/* 3. Daily Costs Chart Section */}
        <section className="silver-card p-6 flex flex-col gap-4 shadow-2xl">
          <div>
            <h3 className="text-lg font-bold text-white tracking-wide">Daily AWS Cost Breakdown</h3>
            <p className="text-xs text-zinc-500 font-medium">Chronological daily cost distribution stacked across all mock resource channels</p>
          </div>

          <div className="h-80 w-full mt-4">
            {loading ? (
              <div className="w-full h-full bg-zinc-950/40 rounded-xl border border-dashed border-zinc-800 flex items-center justify-center animate-pulse">
                <span className="text-sm text-zinc-600 font-semibold tracking-wide">Plotting data pipeline...</span>
              </div>
            ) : chartData.length === 0 ? (
              <div className="w-full h-full bg-zinc-950/40 rounded-xl border border-dashed border-zinc-800 flex items-center justify-center">
                <span className="text-sm text-zinc-600 font-semibold tracking-wide">No chronological cost metrics logged in this window.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#18181b" opacity={0.5} />
                  <XAxis 
                    dataKey="date" 
                    stroke="#71717a" 
                    fontSize={10} 
                    fontWeight={500}
                    tickFormatter={(tick) => tick.substring(5)}  // Show MM-DD format
                  />
                  <YAxis 
                    stroke="#71717a" 
                    fontSize={10} 
                    fontWeight={500}
                    tickFormatter={(tick) => `$${tick}`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#09090b', 
                      borderColor: '#27272a', 
                      borderRadius: '16px',
                      color: '#f4f4f5',
                      fontSize: '12px',
                      fontWeight: '500',
                      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.9)'
                    }} 
                    itemStyle={{ padding: '2px 0' }}
                  />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px', color: '#a1a1aa', fontWeight: '500' }} />
                  {serviceNames.map((svc) => (
                    <Line
                      key={svc}
                      type="monotone"
                      dataKey={svc}
                      name={svc}
                      stroke={SERVICE_COLORS[svc] || SERVICE_COLORS.Unknown}
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5, stroke: '#000000', strokeWidth: 2 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        {/* 4. Alert Config Panel (Bottom Card) */}
        <section className="max-w-2xl w-full mx-auto">
          <div className="silver-card p-6 flex flex-col gap-6">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 tracking-wide">
                <Bell className="w-5 h-5 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.4)]" />
                Notification Configurations
              </h3>
              <p className="text-xs text-zinc-500 font-medium mt-1">
                Configure your monthly budget warnings. An automated alert is sent via SNS if spend breaches target rates.
              </p>
            </div>

            <form onSubmit={handleSaveConfig} className="flex flex-col gap-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Threshold input */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Monthly Budget (USD)</label>
                  <div className="relative flex items-center">
                    <span className="absolute left-4 text-zinc-500 font-mono font-bold">$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={thresholdInput}
                      onChange={(e) => setThresholdInput(e.target.value)}
                      className="w-full pl-8 pr-4 py-2.5 text-sm bg-zinc-950/80 border border-zinc-800 focus:border-zinc-500 rounded-xl focus:outline-none text-white font-mono font-semibold transition-colors"
                    />
                  </div>
                </div>

                {/* Enabled Toggle */}
                <div className="flex flex-col justify-end gap-2">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Alerts Mode Status</label>
                  <button
                    type="button"
                    onClick={() => setAlertsEnabled(!alertsEnabled)}
                    className={`flex items-center justify-between px-4 py-2.5 border rounded-xl transition-all active:scale-95 ${
                      alertsEnabled 
                        ? 'border-zinc-700 bg-zinc-900/60 text-white shadow-[0_0_15px_rgba(255,255,255,0.03)]' 
                        : 'border-zinc-800 bg-zinc-950 text-zinc-600'
                    }`}
                  >
                    <span className="text-xs font-bold uppercase tracking-wider">
                      {alertsEnabled ? 'Alerts Enabled' : 'Alerts Blocked'}
                    </span>
                    <div className={`w-8 h-4 rounded-full p-0.5 transition-colors ${alertsEnabled ? 'bg-white' : 'bg-zinc-800'}`}>
                      <div className={`w-3 h-3 rounded-full bg-black transition-transform ${alertsEnabled ? 'translate-x-4' : 'translate-x-0'}`} />
                    </div>
                  </button>
                </div>
              </div>

              {/* Status Message block */}
              {configMessage && (
                <div className={`flex items-center gap-2 p-3 rounded-xl border text-xs font-semibold ${
                  configMessage.type === 'success' 
                    ? 'border-zinc-800 bg-zinc-950 text-white' 
                    : 'border-rose-500/20 bg-rose-500/10 text-rose-300'
                }`}>
                  {configMessage.type === 'success' ? (
                    <CheckCircle className="w-4 h-4 flex-shrink-0 text-white drop-shadow-[0_0_8px_white]" />
                  ) : (
                    <XCircle className="w-4 h-4 flex-shrink-0" />
                  )}
                  <span>{configMessage.text}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={configSaving}
                className="w-full flex items-center justify-center text-sm font-bold py-3 px-4 rounded-xl bg-white hover:bg-zinc-200 text-black transition-all disabled:opacity-50 shadow-xl shadow-white/10 hover:shadow-white/20 active:scale-98"
              >
                {configSaving ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    APPLYING SETTINGS...
                  </>
                ) : (
                  'APPLY ALARM CONFIGURATIONS'
                )}
              </button>
            </form>
          </div>
        </section>

      </main>

      {/* Footer info */}
      <footer className="border-t border-zinc-900 bg-black py-8 px-6 text-center">
        <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">
          AWS Cloud Cost Monitoring Portal • Design: Platinum Carbon Custom
        </span>
      </footer>

    </div>
  );
}
