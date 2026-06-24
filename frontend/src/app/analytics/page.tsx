"use client";

import { useQuery } from '@tanstack/react-query';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import { Download, Activity, AlertTriangle, Users, FileText } from 'lucide-react';
import * as React from 'react';
import { useState } from 'react';
import { format, subDays } from 'date-fns';

import apiClient from '@/lib/apiClient';

const fetcher = async (url: string, role: string, startDate?: Date, endDate?: Date) => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate.toISOString());
  if (endDate) params.append('end_date', endDate.toISOString());
  
  const endpoint = `/api/analytics${url}${params.toString() ? `?${params.toString()}` : ''}`;
  
  const res = await apiClient.get(endpoint, {
    headers: {
      'X-User-Role': role,
    }
  });
  
  return res.data;
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function AnalyticsDashboard() {
  const [role, setRole] = useState<string>("Admin");
  const [startDate, setStartDate] = useState<Date | undefined>(subDays(new Date(), 30));
  const [endDate, setEndDate] = useState<Date | undefined>(new Date());

  const { data: overview, isLoading: loadingOverview } = useQuery({ 
    queryKey: ['overview', role, startDate, endDate], 
    queryFn: () => fetcher('/overview', role, startDate, endDate), 
    refetchInterval: 30000 
  });
  const { data: fraud, isLoading: loadingFraud } = useQuery({ 
    queryKey: ['fraud', role, startDate, endDate], 
    queryFn: () => fetcher('/fraud', role, startDate, endDate), 
    refetchInterval: 30000 
  });
  const { data: funnel, isLoading: loadingFunnel } = useQuery({ 
    queryKey: ['funnel', role, startDate, endDate], 
    queryFn: () => fetcher('/investigations', role, startDate, endDate), 
    refetchInterval: 30000 
  });
  const { data: models, isLoading: loadingModels } = useQuery({ 
    queryKey: ['models', role, startDate, endDate], 
    queryFn: () => fetcher('/models', role, startDate, endDate), 
    refetchInterval: 30000 
  });
  const { data: agents, isLoading: loadingAgents } = useQuery({ 
    queryKey: ['agents', role, startDate, endDate], 
    queryFn: () => fetcher('/agents', role, startDate, endDate), 
    refetchInterval: 30000 
  });
  const { data: investigators, isLoading: loadingInvestigators } = useQuery({ 
    queryKey: ['investigators', role, startDate, endDate], 
    queryFn: () => fetcher('/investigators', role, startDate, endDate), 
    refetchInterval: 30000 
  });

  if (loadingOverview || loadingFraud || loadingFunnel || loadingModels || loadingAgents || loadingInvestigators) {
    return <div className="p-8 text-center text-gray-500">Loading Enterprise Analytics Dashboard...</div>;
  }

  const funnelData = [
    { stage: 'Submitted', count: funnel?.submitted || 0 },
    { stage: 'Predicted Fraud', count: funnel?.predicted_fraud || 0 },
    { stage: 'Investigated', count: funnel?.investigated || 0 },
    { stage: 'Confirmed Fraud', count: funnel?.confirmed_fraud || 0 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-slate-800">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Enterprise Analytics Platform</h1>
          <p className="text-gray-500 mt-1">Real-time business insights, operational KPIs, and AI monitoring.</p>
        </div>
        
        <div className="flex flex-wrap gap-4 items-center bg-white p-3 rounded-md shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Role:</label>
            <select 
              value={role} 
              onChange={(e) => setRole(e.target.value)}
              className="text-sm border border-gray-300 rounded-md p-1"
            >
              <option value="Admin">Admin</option>
              <option value="Investigator">Investigator</option>
            </select>
          </div>
          
          <div className="h-6 w-px bg-gray-300 hidden md:block"></div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">From:</label>
            <input 
              type="date" 
              value={startDate ? format(startDate, 'yyyy-MM-dd') : ''} 
              onChange={(e) => setStartDate(e.target.value ? new Date(e.target.value) : undefined)}
              className="text-sm border border-gray-300 rounded-md p-1"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">To:</label>
            <input 
              type="date" 
              value={endDate ? format(endDate, 'yyyy-MM-dd') : ''} 
              onChange={(e) => setEndDate(e.target.value ? new Date(e.target.value) : undefined)}
              className="text-sm border border-gray-300 rounded-md p-1"
            />
          </div>

          <button
            onClick={async () => {
              try {
                const res = await apiClient.get(`/api/analytics/export?format=csv&x_user_role=${role}`, { responseType: 'blob' });
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `fraud_analytics_${new Date().toISOString().slice(0,10)}.csv`);
                document.body.appendChild(link);
                link.click();
                link.remove();
              } catch (e) { console.error('Export failed', e); }
            }}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition ml-2"
          >
            <Download size={18} /> Export CSV
          </button>
        </div>
      </div>

      {role === "Investigator" && (
        <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800">
          <h3 className="font-bold">Investigator View Active</h3>
          <p className="text-sm">Global fraud metrics, prediction drift, and geographic analytics are hidden due to Role-Based Access Control (RBAC). You are only viewing investigator performance statistics.</p>
        </div>
      )}

      {/* Executive KPIs */}
      {role === "Admin" && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium">Total Claims</h3>
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{overview?.total_claims}</div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium">Fraud Detected</h3>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">{overview?.fraud_claims}</div>
              <p className="text-xs text-red-500 font-semibold">{overview?.fraud_rate}% fraud rate</p>
            </div>
          </div>
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium">Pending Investigations</h3>
              <Activity className="h-4 w-4 text-yellow-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">{overview?.pending_investigations}</div>
              <p className="text-xs text-gray-500">{overview?.completed_investigations} completed</p>
            </div>
          </div>
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium">Avg Resolution Time</h3>
              <Users className="h-4 w-4 text-green-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">{overview?.avg_investigation_time_days} days</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Investigation Funnel */}
        {role === "Admin" && (
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <div>
              <h3 className="text-lg font-bold mb-4">Investigation Funnel</h3>
            </div>
            <div className="h-[300px]">
              {/* @ts-ignore */}
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={funnelData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="stage" type="category" width={120} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Prediction Drift */}
        {role === "Admin" && (
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <div>
              <h3 className="text-lg font-bold mb-4">Prediction Drift</h3>
            </div>
            <div className="h-[300px]">
              {/* @ts-ignore */}
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[
                  { name: 'Training Baseline', value: models?.drift?.training_fraud_percent },
                  { name: 'Last 30 Days', value: models?.drift?.last_30_days_percent },
                  { name: 'Last 7 Days', value: models?.drift?.last_7_days_percent },
                  { name: 'All Time', value: models?.drift?.all_time_fraud_percent }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8">
                    {
                      [0,1,2,3].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))
                    }
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Geographic Fraud Heatmap Proxy */}
        {role === "Admin" && (
          <div className="bg-white p-6 rounded-xl border shadow-sm col-span-1">
            <div>
              <h3 className="text-lg font-bold mb-4">Fraud by State</h3>
            </div>
            <div className="h-[250px]">
              {/* @ts-ignore */}
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={fraud?.slice(0,5)} dataKey="fraud_count" nameKey="state" cx="50%" cy="50%" outerRadius={80} label>
                    {fraud?.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Model Monitoring */}
        {role === "Admin" && (
          <div className="bg-white p-6 rounded-xl border shadow-sm col-span-1">
            <div>
              <h3 className="text-lg font-bold mb-4">ML Model Monitoring</h3>
            </div>
            <div>
              <ul className="space-y-4">
                <li className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Current Version</span>
                  <span className="font-semibold">{models?.monitoring?.current_version || "production.pkl"}</span>
                </li>
                <li className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Total Predictions</span>
                  <span className="font-semibold">{models?.monitoring?.prediction_count || 0}</span>
                </li>
                <li className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Avg Confidence</span>
                  <span className="font-semibold">{models?.monitoring?.average_confidence || 0}%</span>
                </li>
                <li className="flex justify-between pb-2">
                  <span className="text-gray-500">Status</span>
                  <span className={`font-semibold ${models?.drift?.drift_detected ? 'text-red-500' : 'text-green-500'}`}>
                    {models?.drift?.drift_detected ? 'Drift Detected' : 'Healthy'}
                  </span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* AI Agent Monitoring */}
        {role === "Admin" && (
          <div className="bg-white p-6 rounded-xl border shadow-sm col-span-1">
            <div>
              <h3 className="text-lg font-bold mb-4">AI Agent Analytics</h3>
            </div>
            <div>
              <ul className="space-y-4">
                <li className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Total Executions</span>
                  <span className="font-semibold">{agents?.total_executions || 0}</span>
                </li>
                <li className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Avg Latency</span>
                  <span className="font-semibold">{agents?.average_latency_ms || 0} ms</span>
                </li>
                <li className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Avg Cost</span>
                  <span className="font-semibold">${agents?.average_cost_usd || 0}</span>
                </li>
                <li className="flex justify-between pb-2">
                  <span className="text-gray-500">Success Rate</span>
                  <span className="font-semibold text-green-500">{agents?.success_rate || 0}%</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Investigator Performance */}
      <div className="bg-white p-6 rounded-xl border shadow-sm">
        <div>
          <h3 className="text-lg font-bold mb-4">Investigator Performance Leaderboard</h3>
        </div>
        <div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                <tr>
                  <th className="px-6 py-3">Investigator ID</th>
                  <th className="px-6 py-3">Completed Cases</th>
                  <th className="px-6 py-3">Pending Cases</th>
                  <th className="px-6 py-3">Avg Resolution (Days)</th>
                  <th className="px-6 py-3">Fraud Confirm Rate</th>
                </tr>
              </thead>
              <tbody>
                {investigators?.length > 0 ? investigators.map((inv: any, i: number) => (
                  <tr key={i} className="bg-white border-b hover:bg-gray-50 transition">
                    <td className="px-6 py-4 font-medium">{inv.investigator_id || 'Unassigned'}</td>
                    <td className="px-6 py-4">{inv.completed_cases}</td>
                    <td className="px-6 py-4">{inv.pending_cases}</td>
                    <td className="px-6 py-4">{inv.average_resolution_time_days}</td>
                    <td className="px-6 py-4 text-red-500 font-semibold">{inv.fraud_confirmation_rate}%</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={5} className="text-center py-6 text-gray-500">No investigator data available for this time range.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
