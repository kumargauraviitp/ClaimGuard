"use client";

import { useState } from "react";
import { useAuthStore } from "@/lib/authStore";
import apiClient from "@/lib/apiClient";
import { Shield, Smartphone, Key, ShieldCheck, Copy, CheckCircle2, User, Mail, Briefcase } from "lucide-react";
import { toast } from "sonner";
import { motion } from "motion/react";

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);
  const [setupData, setSetupData] = useState<{ secret: string; provisioning_uri: string; qrBase64?: string } | null>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [loading, setLoading] = useState(false);
  
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    phone: user?.phone || "",
    age: "",
    dob: ""
  });
  const [updating, setUpdating] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdating(true);
    try {
      await apiClient.put("/auth/me", {
        full_name: formData.full_name,
        phone: formData.phone,
        age: parseInt(formData.age) || 0,
        dob: formData.dob || ""
      });
      updateUser({ full_name: formData.full_name, phone: formData.phone });
      setIsEditing(false);
      toast.success("Profile updated successfully!");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to update profile");
    } finally {
      setUpdating(false);
    }
  };

  const startMfaSetup = async () => {
    try {
      setLoading(true);
      const res = await apiClient.post("/auth/mfa/setup");
      setSetupData(res.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to start MFA setup");
    } finally {
      setLoading(false);
    }
  };

  const verifyMfa = async () => {
    try {
      setLoading(true);
      await apiClient.post("/auth/mfa/verify", { code: verifyCode });
      updateUser({ mfa_enabled: true });
      setSetupData(null);
      toast.success("MFA successfully enabled!");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Invalid code");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">My Profile</h1>
        <p className="text-slate-400">Manage your account settings and security preferences.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Profile Card */}
        <div className="col-span-1 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col items-center text-center">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
              <span className="text-3xl font-bold text-white">{user.full_name.charAt(0)}</span>
            </div>
            <h2 className="text-xl font-bold text-white">{user.full_name}</h2>
            <p className="text-blue-400 text-sm font-medium">{user.roles.join(", ")}</p>
            <div className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {user.status}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
              <h3 className="font-semibold text-white">Contact Info</h3>
              <button 
                onClick={() => setIsEditing(!isEditing)} 
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                {isEditing ? "Cancel" : "Edit"}
              </button>
            </div>
            <div className="p-6">
              {isEditing ? (
                <form onSubmit={handleUpdateProfile} className="space-y-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Full Name</label>
                    <input 
                      type="text" 
                      value={formData.full_name} 
                      onChange={e => setFormData({...formData, full_name: e.target.value})}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white" 
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Phone</label>
                    <input 
                      type="tel" 
                      value={formData.phone} 
                      onChange={e => setFormData({...formData, phone: e.target.value})}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white" 
                    />
                  </div>
                  {user.customer_id && (
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-xs text-slate-400 block mb-1">Age</label>
                          <input 
                            type="number" 
                            value={formData.age} 
                            onChange={e => setFormData({...formData, age: e.target.value})}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white" 
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-400 block mb-1">DOB</label>
                          <input 
                            type="date" 
                            value={formData.dob} 
                            onChange={e => setFormData({...formData, dob: e.target.value})}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white" 
                          />
                        </div>
                      </div>
                  )}
                  <button 
                    type="submit" 
                    disabled={updating}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded py-2 text-sm transition-colors"
                  >
                    {updating ? "Saving..." : "Save Changes"}
                  </button>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center text-slate-300">
                    <User className="w-5 h-5 mr-3 text-slate-500" />
                    <span>{user.username}</span>
                  </div>
                  <div className="flex items-center text-slate-300">
                    <Mail className="w-5 h-5 mr-3 text-slate-500" />
                    <span>{user.email}</span>
                  </div>
                  {user.phone && (
                      <div className="flex items-center text-slate-300">
                        <Smartphone className="w-5 h-5 mr-3 text-slate-500" />
                        <span>{user.phone}</span>
                      </div>
                  )}
                  <div className="flex items-center text-slate-300">
                    <Briefcase className="w-5 h-5 mr-3 text-slate-500" />
                    <span>{user.roles[0] || "Employee"}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Security Section */}
        <div className="col-span-1 md:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-800 flex items-center">
              <Shield className="w-5 h-5 text-blue-400 mr-2" />
              <h3 className="font-semibold text-white">Security & Authentication</h3>
            </div>
            
            <div className="p-6 space-y-8">
              {/* MFA Status */}
              <div className="flex flex-col md:flex-row md:items-center justify-between p-4 bg-slate-950/50 rounded-lg border border-slate-800/50">
                <div className="flex items-start">
                  <div className={`p-2 rounded-lg mr-4 ${user.mfa_enabled ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                    <Smartphone className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-white font-medium">Multi-Factor Authentication (MFA)</h4>
                    <p className="text-sm text-slate-400 mt-1 max-w-md">
                      {user.mfa_enabled 
                        ? "Your account is protected by MFA. You must use an authenticator app when signing in."
                        : "Enhance your account security by enabling two-factor authentication."}
                    </p>
                  </div>
                </div>
                {!user.mfa_enabled && !setupData && (
                  <button 
                    onClick={startMfaSetup}
                    disabled={loading}
                    className="mt-4 md:mt-0 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
                  >
                    Enable MFA
                  </button>
                )}
                {user.mfa_enabled && (
                  <div className="mt-4 md:mt-0 flex items-center text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-md border border-emerald-500/20">
                    <ShieldCheck className="w-4 h-4 mr-2" />
                    <span className="text-sm font-medium">Enabled</span>
                  </div>
                )}
              </div>

              {/* MFA Setup Flow */}
              {setupData && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="bg-slate-950/80 border border-blue-500/30 rounded-xl p-6"
                >
                  <h4 className="text-lg font-semibold text-white mb-4">Set up Authenticator App</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4 text-sm text-slate-300">
                      <p>1. Install an authenticator app like Google Authenticator or Authy on your mobile device.</p>
                      <p>2. Scan the QR code or manually enter the secret key below.</p>
                      <div className="bg-slate-900 p-3 rounded flex items-center justify-between border border-slate-800">
                        <code className="text-blue-400 tracking-widest">{setupData.secret}</code>
                        <button 
                          onClick={() => {
                            navigator.clipboard.writeText(setupData.secret);
                            toast.success("Copied to clipboard");
                          }}
                          className="text-slate-400 hover:text-white"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <p>3. Enter the 6-digit code generated by the app to verify.</p>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="bg-white p-4 rounded-lg inline-block mx-auto">
                        {/* Since we generate a URI, ideally we show a QR code. Here we can use a library or just display the URI text as fallback */}
                        {/* We could use the QR code API from backend if we exposed base64 image, but since we didn't hook it up, we'll just show the manual instructions */}
                        <div className="text-slate-900 text-center font-bold mb-2">QR Code Area</div>
                        <div className="text-xs text-slate-500 max-w-[200px] text-center break-all">
                          {setupData.provisioning_uri}
                        </div>
                      </div>
                      
                      <div className="flex space-x-2">
                        <input
                          type="text"
                          value={verifyCode}
                          onChange={(e) => setVerifyCode(e.target.value)}
                          placeholder="000000"
                          maxLength={6}
                          className="flex-1 bg-slate-900 border border-slate-700 rounded-md px-4 py-2 text-white text-center tracking-widest font-mono text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          onClick={verifyMfa}
                          disabled={loading || verifyCode.length !== 6}
                          className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-md transition-colors"
                        >
                          Verify
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
