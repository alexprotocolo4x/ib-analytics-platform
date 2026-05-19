import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface KPIs {
  total_lots: number;
  revenue_bruto: number;
  pago_ib: number;
  margen_neto: number;
  pnl_total: number;
  profit_factor: number;
  win_rate: number;
  cuentas_activas: number;
  cuentas_totales: number;
  total_deals: number;
  total_swap: number;
  total_commission: number;
  gross_profit: number;
  gross_loss: number;
  avg_profit_per_trade: number;
}

export interface AccountMetrics {
  login: string;
  total_lots: number;
  total_deals: number;
  pnl: number;
  revenue: number;
  profit_factor: number;
  win_rate: number;
  swap: number;
  commission: number;
  status: string;
}

export interface UploadStatus {
  deals_loaded: boolean;
  deals_count: number;
  accounts_loaded: boolean;
  accounts_count: number;
  ready_for_analysis: boolean;
}

// Upload MT5 HTML
export const uploadMT5HTML = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/upload/mt5-html', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// Upload accounts Excel
export const uploadAccountsExcel = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/upload/accounts-excel', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// Get upload status
export const getUploadStatus = async (): Promise<UploadStatus> => {
  const response = await api.get('/api/upload/status');
  return response.data;
};

// Get KPIs
export const getKPIs = async (): Promise<KPIs> => {
  const response = await api.get('/api/analytics/kpis');
  return response.data.kpis;
};

// Get accounts metrics
export const getAccountsMetrics = async (): Promise<AccountMetrics[]> => {
  const response = await api.get('/api/analytics/accounts');
  return response.data.accounts;
};

// Clear data
export const clearData = async () => {
  const response = await api.delete('/api/upload/clear');
  return response.data;
};

export default api;
