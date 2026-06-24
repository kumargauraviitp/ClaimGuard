"use client";

import React, { useEffect, useState } from "react";
import { PermissionGuard } from "../../../../components/auth/ProtectedRoute";
import apiClient from "../../../../lib/apiClient";

export default function SystemDashboard() {
  const [health, setHealth] = useState<any>({});
  const [metrics, setMetrics] = useState<any>({});
  const [version, setVersion] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [hRes, mRes, vRes] = await Promise.all([
          apiClient.get("/api/system/health/startup"),
          apiClient.get("/api/system/metrics"),
          apiClient.get("/api/system/version"),
        ]);
        setHealth(hRes.data);
        setMetrics(mRes.data);
        setVersion(vRes.data);
      } catch (err) {
        console.error("Failed to load system data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <div className="p-8 text-white">Loading System Metrics...</div>;

  return (
    <PermissionGuard permission="security.read">
      <div className="p-8 max-w-7xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">Enterprise System Health</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#1A1A1A] border border-[#333] p-6 rounded-xl shadow-2xl">
            <h2 className="text-xl font-semibold text-gray-200 mb-4">Core Components</h2>
            <ul className="space-y-3">
              <li className="flex justify-between"><span className="text-gray-400">Database</span><span className="text-green-400">Connected</span></li>
              <li className="flex justify-between"><span className="text-gray-400">Redis Cache</span><span className="text-green-400">Connected</span></li>
              <li className="flex justify-between"><span className="text-gray-400">ML Model</span><span className={health.model_loaded ? "text-green-400" : "text-red-400"}>{health.model_loaded ? "Loaded" : "Offline"}</span></li>
              <li className="flex justify-between"><span className="text-gray-400">Knowledge Base</span><span className={health.knowledge_base_loaded ? "text-green-400" : "text-red-400"}>{health.knowledge_base_loaded ? "Loaded" : "Offline"}</span></li>
            </ul>
          </div>

          <div className="bg-[#1A1A1A] border border-[#333] p-6 rounded-xl shadow-2xl">
            <h2 className="text-xl font-semibold text-gray-200 mb-4">Performance Metrics</h2>
            <ul className="space-y-3">
              {Object.entries(metrics).map(([key, val]) => (
                <li key={key} className="flex justify-between">
                  <span className="text-gray-400">{key}</span>
                  <span className="text-blue-400 font-mono">{String(val)}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-[#1A1A1A] border border-[#333] p-6 rounded-xl shadow-2xl">
            <h2 className="text-xl font-semibold text-gray-200 mb-4">Version Control</h2>
            <ul className="space-y-3">
              {Object.entries(version).map(([key, val]) => (
                <li key={key} className="flex justify-between">
                  <span className="text-gray-400">{key}</span>
                  <span className="text-purple-400 font-mono text-sm">{String(val)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </PermissionGuard>
  );
}
