import { useState, useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import { 
  uploadMT5HTML, 
  uploadAccountsExcel, 
  getKPIs, 
  getAccountsMetrics,
  getUploadStatus,
  KPIs,
  AccountMetrics 
} from '../services/api';
import './Dashboard.css';

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [accounts, setAccounts] = useState<AccountMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState({
    deals: false,
    accounts: false
  });

  const checkStatus = async () => {
    try {
      const status = await getUploadStatus();
      setUploadStatus({
        deals: status.deals_loaded,
        accounts: status.accounts_loaded
      });
      
      // Si ambos están listos, cargar datos
      if (status.ready_for_analysis) {
        await loadAnalytics();
      }
    } catch (err) {
      console.error('Error checking status:', err);
    }
  };

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [kpisData, accountsData] = await Promise.all([
        getKPIs(),
        getAccountsMetrics()
      ]);
      
      setKpis(kpisData);
      setAccounts(accountsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando análisis');
    } finally {
      setLoading(false);
    }
  };

  const handleMT5Upload = async (file: File) => {
    await uploadMT5HTML(file);
    await checkStatus();
  };

  const handleAccountsUpload = async (file: File) => {
    await uploadAccountsExcel(file);
    await checkStatus();
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="brand">
          <h1 className="brand-logo">IB Analytics</h1>
          <p className="brand-sub">TAG MARKETS</p>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Upload Section */}
        <section className="upload-section">
          <h2 className="section-title">1. Cargar Datos</h2>
          
          <div className="upload-grid">
            <FileUpload
              onUpload={handleMT5Upload}
              accept="text/html"
              label="MT5 Administrator Deals"
              description="Export HTML de MT5 con los deals del período"
              icon="📄"
            />
            
            <FileUpload
              onUpload={handleAccountsUpload}
              accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              label="Excel de Cuentas"
              description="Archivo Excel con columna 'Login' y los números de cuenta"
              icon="📊"
            />
          </div>

          {/* Status */}
          <div className="upload-status-bar">
            <div className={`status-item ${uploadStatus.deals ? 'ready' : ''}`}>
              {uploadStatus.deals ? '✅' : '⏳'} Deals: {uploadStatus.deals ? 'Cargado' : 'Pendiente'}
            </div>
            <div className={`status-item ${uploadStatus.accounts ? 'ready' : ''}`}>
              {uploadStatus.accounts ? '✅' : '⏳'} Cuentas: {uploadStatus.accounts ? 'Cargadas' : 'Pendiente'}
            </div>
          </div>
        </section>

        {/* Analytics Section */}
        {uploadStatus.deals && uploadStatus.accounts && (
          <>
            {loading && (
              <div className="loading-message">
                <div className="spinner-large"></div>
                <p>Calculando métricas...</p>
              </div>
            )}

            {error && (
              <div className="error-message">
                ❌ {error}
              </div>
            )}

            {kpis && !loading && (
              <>
                {/* KPIs Section */}
                <section className="kpis-section">
                  <h2 className="section-title">2. Métricas Principales</h2>
                  
                  <div className="kpi-grid">
                    <div className="kpi-card highlight">
                      <div className="kpi-label">Lotes Totales</div>
                      <div className="kpi-value gold">{kpis.total_lots.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                      <div className="kpi-sub">{kpis.total_deals.toLocaleString()} deals</div>
                    </div>

                    <div className="kpi-card">
                      <div className="kpi-label">Revenue Bruto</div>
                      <div className="kpi-value">${kpis.revenue_bruto.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                      <div className="kpi-sub">$25 × lotes</div>
                    </div>

                    <div className="kpi-card">
                      <div className="kpi-label">Pago al IB</div>
                      <div className="kpi-value">${kpis.pago_ib.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                      <div className="kpi-sub">$17 × lotes</div>
                    </div>

                    <div className="kpi-card highlight">
                      <div className="kpi-label">Margen Neto Broker</div>
                      <div className="kpi-value green">${kpis.margen_neto.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                      <div className="kpi-sub">Revenue - Pago IB</div>
                    </div>

                    <div className="kpi-card">
                      <div className="kpi-label">P&L Clientes</div>
                      <div className={`kpi-value ${kpis.pnl_total < 0 ? 'red' : 'green'}`}>
                        ${kpis.pnl_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="kpi-sub">
                        {kpis.pnl_total < 0 ? 'Clientes perdieron' : 'Clientes ganaron'}
                      </div>
                    </div>

                    <div className="kpi-card">
                      <div className="kpi-label">Profit Factor</div>
                      <div className="kpi-value">{kpis.profit_factor.toFixed(2)}</div>
                      <div className="kpi-sub">Objetivo: &lt; 1.00</div>
                    </div>

                    <div className="kpi-card">
                      <div className="kpi-label">Win Rate</div>
                      <div className="kpi-value">{kpis.win_rate.toFixed(1)}%</div>
                      <div className="kpi-sub">Trades ganadores</div>
                    </div>

                    <div className="kpi-card">
                      <div className="kpi-label">Cuentas Activas</div>
                      <div className="kpi-value">
                        {kpis.cuentas_activas} <span style={{ color: 'var(--text-muted)', fontSize: '18px' }}>/ {kpis.cuentas_totales}</span>
                      </div>
                      <div className="kpi-sub">Con trades</div>
                    </div>
                  </div>
                </section>

                {/* Accounts Table */}
                <section className="accounts-section">
                  <h2 className="section-title">3. Detalle por Cuenta</h2>
                  
                  <div className="table-card">
                    <table>
                      <thead>
                        <tr>
                          <th>Cuenta</th>
                          <th>Lotes</th>
                          <th>Deals</th>
                          <th>P&L</th>
                          <th>Revenue</th>
                          <th>PF</th>
                          <th>Win %</th>
                          <th>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {accounts.map((acc) => (
                          <tr key={acc.login}>
                            <td className="td-name">{acc.login}</td>
                            <td>{acc.total_lots.toFixed(2)}</td>
                            <td>{acc.total_deals}</td>
                            <td className={acc.pnl < 0 ? 'value-negative' : 'value-positive'}>
                              ${acc.pnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className="value-gold">
                              ${acc.revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td>{acc.profit_factor.toFixed(2)}</td>
                            <td>{acc.win_rate.toFixed(1)}%</td>
                            <td>
                              <span className={`status-badge ${acc.status}`}>
                                {acc.status === 'active' ? 'Activa' : 'Inactiva'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
