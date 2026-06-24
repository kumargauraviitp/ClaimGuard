"use client";

import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment } from "@react-three/drei";
import * as THREE from "three";
import { motion, AnimatePresence } from "motion/react";
import { CheckCircle2, Sparkles, ServerCrash, X } from "lucide-react";
import apiClient from "@/lib/apiClient";
import { Button } from "./button";

/* ------------------------------------------------------------------ */
/*  Holographic fraud-scan visualization                              */
/*                                                                    */
/*  - A faceted crystal core (the AI fraud engine) that pulses.       */
/*  - Two orbital scan rings rotating on perpendicular axes.          */
/*  - A radar sweep beam that orbits and "verifies" a lattice of      */
/*    data nodes distributed on a sphere — each node lights up as     */
/*    the beam passes over it.                                        */
/* ------------------------------------------------------------------ */

const NODE_COUNT = 140;

/** Evenly distribute points on a sphere (Fibonacci lattice). */
function useFibonacciSphere(count: number, radius: number) {
  return useMemo(() => {
    const pts: THREE.Vector3[] = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1)) * 2; // 1 to -1
      const r = Math.sqrt(1 - y * y);
      const theta = golden * i;
      pts.push(
        new THREE.Vector3(
          Math.cos(theta) * r * radius,
          y * radius,
          Math.sin(theta) * r * radius
        )
      );
    }
    return pts;
  }, [count, radius]);
}

/** Faceted crystal core that glows and breathes with progress. */
function CrystalCore({ progress, done }: { progress: number; done: boolean }) {
  const solid = useRef<THREE.Mesh>(null);
  const wire = useRef<THREE.Mesh>(null);
  const p = progress / 100;

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (solid.current) {
      const breathe = 1 + Math.sin(t * 2) * 0.04 + p * 0.15;
      solid.current.scale.setScalar(breathe);
      solid.current.rotation.y = t * 0.3;
      solid.current.rotation.x = t * 0.15;
      const m = solid.current.material as THREE.MeshStandardMaterial;
      m.emissiveIntensity = 0.6 + Math.sin(t * 3) * 0.2 + p * 0.8;
    }
    if (wire.current) {
      wire.current.rotation.y = -t * 0.2;
      wire.current.rotation.z = t * 0.1;
      wire.current.scale.copy(solid.current!.scale).multiplyScalar(1.05);
    }
  });

  const coreColor = done ? "#10b981" : "#7c3aed";
  const wireColor = done ? "#34d399" : "#a78bfa";

  return (
    <group>
      <mesh ref={solid}>
        <icosahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          color={coreColor}
          emissive={coreColor}
          emissiveIntensity={0.8}
          metalness={0.6}
          roughness={0.2}
          transparent
          opacity={0.55}
          toneMapped={false}
        />
      </mesh>
      <mesh ref={wire}>
        <icosahedronGeometry args={[1, 1]} />
        <meshBasicMaterial color={wireColor} wireframe transparent opacity={0.35} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** Two thin orbital rings rotating on perpendicular axes. */
function ScanRings({ done }: { done: boolean }) {
  const ringA = useRef<THREE.Mesh>(null);
  const ringB = useRef<THREE.Mesh>(null);
  const color = done ? "#10b981" : "#8b5cf6";

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (ringA.current) {
      ringA.current.rotation.x = t * 0.4;
      ringA.current.rotation.y = t * 0.2;
    }
    if (ringB.current) {
      ringB.current.rotation.z = t * 0.5;
      ringB.current.rotation.x = Math.PI / 2 + t * 0.25;
    }
  });

  return (
    <group>
      <mesh ref={ringA}>
        <torusGeometry args={[2.1, 0.012, 16, 120]} />
        <meshBasicMaterial color={color} transparent opacity={0.5} toneMapped={false} />
      </mesh>
      <mesh ref={ringB}>
        <torusGeometry args={[2.5, 0.012, 16, 120]} />
        <meshBasicMaterial color={color} transparent opacity={0.35} toneMapped={false} />
      </mesh>
    </group>
  );
}

/**
 * A radar sweep beam that orbits the vertical axis. Data nodes within
 * the beam's arc brighten (get "verified"), then settle. Overall node
 * brightness also scales with progress so the lattice fills in.
 */
function RadarSweep({
  positions,
  progress,
  done,
}: {
  positions: THREE.Vector3[];
  progress: number;
  done: boolean;
}) {
  const beamRef = useRef<THREE.Mesh>(null);
  const beamGlowRef = useRef<THREE.Mesh>(null);
  const matRef = useRef<THREE.PointsMaterial>(null);
  const pointsRef = useRef<THREE.Points>(null);

  // Per-node color buffer so we can light up nodes as the beam sweeps.
  const { geometry, colors } = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(positions.length * 3);
    positions.forEach((p, i) => {
      pos[i * 3] = p.x;
      pos[i * 3 + 1] = p.y;
      pos[i * 3 + 2] = p.z;
    });
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const col = new Float32Array(positions.length * 3).fill(0.3);
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    return { geometry: geo, colors: col };
  }, [positions]);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    const sweepAngle = (t * 1.6) % (Math.PI * 2); // current beam heading

    // Drive the beam rotation.
    if (beamRef.current) beamRef.current.rotation.y = sweepAngle;
    if (beamGlowRef.current) beamGlowRef.current.rotation.y = sweepAngle;

    // Light up nodes near the beam heading. We compare each node's
    // azimuthal angle to the sweep heading.
    const colorAttr = geometry.getAttribute("color") as THREE.BufferAttribute;
    const baseDim = 0.18 + (progress / 100) * 0.35;
    for (let i = 0; i < positions.length; i++) {
      const p = positions[i];
      const nodeAngle = Math.atan2(p.z, p.x); // -PI..PI
      let delta = Math.abs(((nodeAngle - sweepAngle + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
      // delta is now angular distance from beam, 0..PI
      const beamGlow = Math.max(0, 1 - delta / 0.5); // glow within ~0.5 rad
      const intensity = baseDim + beamGlow * 1.1;
      const r = done ? 0.2 : 0.55;
      const g = done ? 1.0 : 0.45;
      const b = done ? 0.55 : 1.0;
      colors[i * 3] = r * intensity;
      colors[i * 3 + 1] = g * intensity;
      colors[i * 3 + 2] = b * intensity;
    }
    colorAttr.needsUpdate = true;

    if (matRef.current) {
      matRef.current.size = 0.09 + (progress / 100) * 0.04;
    }
  });

  return (
    <group>
      {/* Rotating scan beam — a thin translucent wedge */}
      <group ref={beamGlowRef}>
        <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0, 2.7, 32, 1, 0, 0.32]} />
          <meshBasicMaterial
            color={done ? "#10b981" : "#a78bfa"}
            transparent
            opacity={0.16}
            side={THREE.DoubleSide}
            toneMapped={false}
          />
        </mesh>
      </group>
      <group ref={beamRef}>
        <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[2.55, 2.65, 32, 1, 0, 0.32]} />
          <meshBasicMaterial
            color={done ? "#6ee7b7" : "#c4b5fd"}
            transparent
            opacity={0.9}
            side={THREE.DoubleSide}
            toneMapped={false}
          />
        </mesh>
      </group>

      {/* Data-node lattice */}
      <points ref={pointsRef} geometry={geometry}>
        <pointsMaterial
          ref={matRef}
          size={0.09}
          vertexColors
          transparent
          opacity={0.95}
          sizeAttenuation
          toneMapped={false}
        />
      </points>
    </group>
  );
}

function ScanScene({ progress, status }: { progress: number; status: string }) {
  const done = status === "success";
  const positions = useFibonacciSphere(NODE_COUNT, 2.6);
  return (
    <>
      <ambientLight intensity={0.6} />
      <pointLight position={[6, 6, 6]} intensity={1.2} color={done ? "#10b981" : "#8b5cf6"} />
      <pointLight position={[-6, -4, -6]} intensity={0.6} color={done ? "#34d399" : "#6366f1"} />
      <CrystalCore progress={progress} done={done} />
      <ScanRings done={done} />
      <RadarSweep positions={positions} progress={progress} done={done} />
      <Environment preset="city" />
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Modal shell (logic unchanged: progress phases + real API call)    */
/* ------------------------------------------------------------------ */

const PHASES = [
  "Initializing Secure Connection...",
  "Extracting Claim Features...",
  "Evaluating Decision Trees...",
  "Aggregating SHAP Values...",
  "Finalizing Risk Score..."
];

export function ScanModal({
  isOpen,
  onClose,
  claimId,
  onComplete
}: {
  isOpen: boolean;
  onClose: () => void;
  claimId: string;
  onComplete: () => void;
}) {
  const [progress, setProgress] = React.useState(0);
  const [phaseIndex, setPhaseIndex] = React.useState(0);
  const [status, setStatus] = React.useState<"idle" | "scanning" | "success" | "error">("idle");
  const [errorMsg, setErrMsg] = React.useState("");

  React.useEffect(() => {
    if (isOpen) {
      startScan();
    } else {
      setProgress(0);
      setPhaseIndex(0);
      setStatus("idle");
      setErrMsg("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const startScan = async () => {
    setStatus("scanning");
    setProgress(0);
    setPhaseIndex(0);

    const interval = setInterval(() => {
      setProgress(p => (p >= 90 ? p : p + Math.random() * 5));
    }, 200);

    const phaseInterval = setInterval(() => {
      setPhaseIndex(prev => Math.min(prev + 1, PHASES.length - 1));
    }, 1000);

    try {
      const startTime = Date.now();
      await apiClient.post(`/api/claims/${claimId}/scan`);

      const elapsed = Date.now() - startTime;
      if (elapsed < 4500) {
        await new Promise(r => setTimeout(r, 4500 - elapsed));
      }

      clearInterval(interval);
      clearInterval(phaseInterval);
      setProgress(100);
      setPhaseIndex(PHASES.length - 1);
      setStatus("success");

      setTimeout(() => {
        onComplete();
        onClose();
      }, 2000);
    } catch (err: any) {
      clearInterval(interval);
      clearInterval(phaseInterval);
      setStatus("error");
      setErrMsg(err.response?.data?.detail || err.message || "An error occurred");
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
      >
        {/* 3D scan scene fills the backdrop */}
        <div className="absolute inset-0 pointer-events-none">
          <Canvas camera={{ position: [0, 1.5, 7], fov: 45 }} dpr={[1, 2]}>
            <ScanScene progress={progress} status={status} />
          </Canvas>
        </div>

        <motion.div
          initial={{ scale: 0.92, y: 24, opacity: 0 }}
          animate={{ scale: 1, y: 0, opacity: 1 }}
          transition={{ delay: 0.15, type: "spring", stiffness: 220, damping: 24 }}
          className="relative z-10 w-full max-w-md p-8 overflow-hidden border border-white/10 rounded-3xl shadow-2xl bg-zinc-950/55 backdrop-blur-xl text-center"
        >
          {status === "error" && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-white/50 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          <div className="flex justify-center mb-6">
            {status === "scanning" && (
              <div className="relative">
                <div className="absolute inset-0 blur-xl bg-violet-500/40 rounded-full animate-pulse" />
                <Sparkles className="w-12 h-12 text-violet-300 animate-pulse relative z-10" />
              </div>
            )}
            {status === "success" && <CheckCircle2 className="w-12 h-12 text-emerald-400" />}
            {status === "error" && <ServerCrash className="w-12 h-12 text-rose-500" />}
          </div>

          <h2 className="text-2xl font-light text-white tracking-wide mb-2">
            {status === "scanning"
              ? "ClaimGuard AI Scanning"
              : status === "success"
              ? "Analysis Complete"
              : "Scan Failed"}
          </h2>

          <p className="text-sm text-zinc-400 mb-8 h-5 font-mono">
            {status === "scanning" && PHASES[phaseIndex]}
            {status === "success" && "Risk score generated successfully."}
            {status === "error" && errorMsg}
          </p>

          <div className="space-y-2">
            <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${
                  status === "error"
                    ? "bg-rose-500"
                    : status === "success"
                    ? "bg-emerald-500"
                    : "bg-gradient-to-r from-violet-500 to-indigo-400"
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                transition={{ ease: "easeOut", duration: 0.4 }}
              />
            </div>
            <div className="flex justify-between text-xs text-zinc-500 font-mono">
              <span>{Math.round(progress)}%</span>
              <span>
                {status === "scanning" ? "Processing" : status === "success" ? "Done" : "Halted"}
              </span>
            </div>
          </div>

          {status === "error" && (
            <div className="mt-8">
              <Button
                onClick={onClose}
                variant="outline"
                className="w-full border-white/10 text-white hover:bg-white/10"
              >
                Close
              </Button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
