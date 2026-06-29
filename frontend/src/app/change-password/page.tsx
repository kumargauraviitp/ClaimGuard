"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/apiClient";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/lib/authStore";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { CanvasRevealEffect, MiniNavbar } from "@/components/ui/sign-in-flow-1";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  
  const updateUser = useAuthStore((state) => state.updateUser);

  const [step, setStep] = useState<"form" | "success">("form");
  const [initialCanvasVisible, setInitialCanvasVisible] = useState(true);
  const [reverseCanvasVisible, setReverseCanvasVisible] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await apiClient.post("/auth/change-password", {
        old_password: oldPassword,
        new_password: newPassword
      });
      
      toast.success("Password updated successfully.");
      updateUser({ force_password_change: false });
      
      setReverseCanvasVisible(true);
      setTimeout(() => setInitialCanvasVisible(false), 50);
      setStep("success");
      
      setTimeout(() => {
        router.push("/app");
      }, 2000);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to update password");
      setLoading(false);
    }
  };

  return (
    <div className="flex w-[100%] flex-col min-h-screen bg-black relative">
      <div className="absolute inset-0 z-0">
        {initialCanvasVisible && (
          <div className="absolute inset-0">
            <CanvasRevealEffect
              animationSpeed={3}
              containerClassName="bg-black"
              colors={[
                [139, 92, 246], // Violet 500
                [168, 85, 247], // Purple 500
              ]}
              opacities={[0.5, 0.5, 0.5, 0.8, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0]}
              dotSize={4}
              reverse={false}
            />
          </div>
        )}
        
        {reverseCanvasVisible && (
          <div className="absolute inset-0">
            <CanvasRevealEffect
              animationSpeed={4}
              containerClassName="bg-black"
              colors={[
                [168, 85, 247], // Purple 500
                [192, 38, 211], // Fuchsia 600
              ]}
              opacities={[0.5, 0.5, 0.5, 0.8, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0]}
              dotSize={4}
              reverse={true}
            />
          </div>
        )}
        
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(0,0,0,0.15)_0%,_rgba(0,0,0,0.85)_100%)]" />
        <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-black to-transparent" />
      </div>
      
      <div className="relative z-10 flex flex-col flex-1">
        <MiniNavbar />

        <div className="flex flex-1 flex-col lg:flex-row">
          <div className="flex-1 flex flex-col justify-center items-center">
            <div className="w-full mt-[100px] max-w-sm">
              <AnimatePresence mode="wait">
                {step === "form" ? (
                  <motion.div 
                    key="form-step"
                    initial={{ opacity: 0, x: -100 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className="space-y-6 text-center"
                  >
                    <div className="space-y-1">
                      <h1 className="text-[2.5rem] font-bold leading-[1.1] tracking-tight bg-gradient-to-br from-violet-200 via-purple-300 to-fuchsia-400 bg-clip-text text-transparent pb-1">
                        Change Password
                      </h1>
                      <p className="text-[1.2rem] text-violet-200/70 font-light">
                        Your account requires a password change
                      </p>
                    </div>
                    
                    <div className="space-y-4">
                      <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                          <input 
                            type="password" 
                            placeholder="Current Password"
                            value={oldPassword}
                            onChange={(e) => setOldPassword(e.target.value)}
                            className="w-full backdrop-blur-[1px] text-white border-1 border-white/10 rounded-full py-3 px-4 focus:outline-none focus:border focus:border-white/30 text-center bg-white/5"
                            required
                          />
                        </div>
                        <div>
                          <input 
                            type="password" 
                            placeholder="New Password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="w-full backdrop-blur-[1px] text-white border-1 border-white/10 rounded-full py-3 px-4 focus:outline-none focus:border focus:border-white/30 text-center bg-white/5"
                            required
                          />
                        </div>
                        <div>
                          <input 
                            type="password" 
                            placeholder="Confirm New Password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full backdrop-blur-[1px] text-white border-1 border-white/10 rounded-full py-3 px-4 focus:outline-none focus:border focus:border-white/30 text-center bg-white/5"
                            required
                          />
                        </div>
                        <button 
                          type="submit"
                          disabled={loading}
                          className="w-full flex justify-center items-center backdrop-blur-[2px] bg-white text-black hover:bg-white/90 rounded-full py-3 px-4 transition-colors font-medium mt-2"
                        >
                          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Update Password"}
                        </button>
                      </form>
                    </div>
                    
                    <p className="text-xs text-white/40 pt-4">
                      Min 12 chars, upper, lower, num, special
                    </p>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="success-step"
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, ease: "easeOut", delay: 0.3 }}
                    className="space-y-6 text-center"
                  >
                    <div className="space-y-1">
                      <h1 className="text-[2.5rem] font-bold leading-[1.1] tracking-tight bg-gradient-to-br from-violet-200 via-purple-300 to-fuchsia-400 bg-clip-text text-transparent pb-1">
                        Password Updated
                      </h1>
                      <p className="text-[1.25rem] text-violet-200/50 font-light">
                        Your password has been changed successfully
                      </p>
                    </div>
                    
                    <motion.div 
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: 0.5, delay: 0.5 }}
                      className="py-10"
                    >
                      <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </motion.div>
                    
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1 }}
                      className="w-full flex justify-center items-center rounded-full bg-white text-black font-medium py-3 opacity-50"
                    >
                      <Loader2 className="w-5 h-5 animate-spin mr-2" />
                      Redirecting to dashboard...
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
