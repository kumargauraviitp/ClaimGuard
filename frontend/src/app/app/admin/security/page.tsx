"use client";

import { useEffect, useState } from "react";
import { PermissionGuard } from "@/components/auth/ProtectedRoute";
import apiClient from "@/lib/apiClient";
import { ShieldAlert, UserX, Lock, Shield, RefreshCw, ShieldCheck } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";

interface SecurityEvent {
  id: string;
  event_type: string;
  description: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
}

interface UserData {
  id: string;
  username: string;
  email: string;
  status: string;
  roles: string[];
}

export default function SecurityDashboardPage() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [eventsRes, usersRes] = await Promise.all([
        apiClient.get("/auth/events"),
        apiClient.get("/auth/users")
      ]);
      setEvents(eventsRes.data);
      setUsers(usersRes.data);
    } catch (err: any) {
      toast.error("Failed to load security data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const changeUserStatus = async (userId: string, newStatus: string) => {
    try {
      await apiClient.post(`/auth/users/${userId}/status?status=${newStatus}`);
      toast.success("User status updated");
      fetchData();
    } catch (err) {
      toast.error("Failed to update status");
    }
  };

  return (
    <PermissionGuard permission="*" fallback={<div className="p-8 text-red-500">Access Denied</div>}>
      <div className="p-8 max-w-7xl mx-auto space-y-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Security Dashboard</h1>
            <p className="text-slate-400">Enterprise Authentication & Authorization Monitoring</p>
          </div>
          <button 
            onClick={fetchData}
            className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-md transition-colors"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* User Management */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center">
                <Shield className="w-5 h-5 text-emerald-400 mr-2" />
                <h3 className="font-semibold text-white">Identity Management</h3>
              </div>
            </div>
            <div className="flex-1 p-0 overflow-auto max-h-[500px]">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/50 text-xs uppercase text-slate-400 sticky top-0">
                  <tr>
                    <th className="px-6 py-3">User</th>
                    <th className="px-6 py-3">Roles</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {users.map(u => (
                    <tr key={u.id} className="hover:bg-slate-800/50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-white">{u.username}</div>
                        <div className="text-xs text-slate-500">{u.email}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="bg-slate-800 text-slate-300 px-2 py-1 rounded text-xs">{u.roles.join(', ')}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${
                          u.status === 'Active' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                          u.status === 'Suspended' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 
                          'bg-red-500/10 text-red-400 border-red-500/20'
                        }`}>
                          {u.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        {u.status === 'Active' ? (
                          <button onClick={() => changeUserStatus(u.id, 'Suspended')} className="text-amber-400 hover:text-amber-300" title="Suspend User">
                            <UserX className="w-4 h-4 inline" />
                          </button>
                        ) : (
                          <button onClick={() => changeUserStatus(u.id, 'Active')} className="text-emerald-400 hover:text-emerald-300" title="Activate User">
                            <ShieldCheck className="w-4 h-4 inline" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Immutable Audit Log */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center">
                <ShieldAlert className="w-5 h-5 text-red-400 mr-2" />
                <h3 className="font-semibold text-white">Immutable Audit Log</h3>
              </div>
              <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">Append-Only</span>
            </div>
            <div className="flex-1 p-0 overflow-auto max-h-[500px]">
              <div className="divide-y divide-slate-800/50">
                {events.map(event => (
                  <div key={event.id} className="p-4 hover:bg-slate-800/30 transition-colors">
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex items-center">
                        <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                          event.event_type.includes('fail') || event.event_type.includes('lock') ? 'bg-red-500' :
                          event.event_type.includes('mfa') || event.event_type.includes('success') ? 'bg-emerald-500' :
                          'bg-blue-500'
                        }`} />
                        <span className="font-medium text-slate-200">{event.event_type}</span>
                      </div>
                      <span className="text-xs text-slate-500 font-mono">
                        {format(new Date(event.timestamp), "MMM d, HH:mm:ss")}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 ml-4">{event.description}</p>
                    <div className="mt-2 ml-4 flex items-center text-xs text-slate-500 space-x-4">
                      {event.ip_address && <span>IP: {event.ip_address}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </PermissionGuard>
  );
}
