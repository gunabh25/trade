'use client';

import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import { useMemo } from 'react';

/** Faceted icosahedron-style faces — SVG paths in isometric projection. */
const POLYHEDRON_FACES = [
  { d: 'M100 28 L128 68 L72 68 Z', fill: 'url(#face-lime)' },
  { d: 'M100 28 L128 68 L148 48 Z', fill: 'url(#face-cyan)' },
  { d: 'M100 28 L72 68 L52 48 Z', fill: 'url(#face-emerald)' },
  { d: 'M128 68 L148 48 L168 72 Z', fill: 'url(#face-teal)' },
  { d: 'M72 68 L52 48 L32 72 Z', fill: 'url(#face-green)' },
  { d: 'M128 68 L168 72 L152 108 Z', fill: 'url(#face-lime-bright)' },
  { d: 'M72 68 L32 72 L48 108 Z', fill: 'url(#face-cyan-deep)' },
  { d: 'M128 68 L152 108 L100 118 Z', fill: 'url(#face-emerald)' },
  { d: 'M72 68 L48 108 L100 118 Z', fill: 'url(#face-teal)' },
  { d: 'M152 108 L168 72 L180 112 Z', fill: 'url(#face-green-dark)' },
  { d: 'M48 108 L32 72 L20 112 Z', fill: 'url(#face-lime)' },
  { d: 'M100 118 L152 108 L140 148 Z', fill: 'url(#face-cyan)' },
  { d: 'M100 118 L48 108 L60 148 Z', fill: 'url(#face-emerald)' },
  { d: 'M152 108 L140 148 L168 132 Z', fill: 'url(#face-teal)' },
  { d: 'M48 108 L60 148 L32 132 Z', fill: 'url(#face-green)' },
  { d: 'M100 118 L140 148 L100 172 Z', fill: 'url(#face-lime-bright)' },
  { d: 'M100 118 L60 148 L100 172 Z', fill: 'url(#face-cyan-deep)' },
  { d: 'M140 148 L168 132 L172 168 Z', fill: 'url(#face-emerald)' },
  { d: 'M60 148 L32 132 L28 168 Z', fill: 'url(#face-teal)' },
  { d: 'M100 172 L140 148 L172 168 Z', fill: 'url(#face-green-dark)' },
  { d: 'M100 172 L60 148 L28 168 Z', fill: 'url(#face-lime)' },
] as const;

const PARTICLE_SEEDS = [
  { x: 12, y: 18, size: 2, opacity: 0.9 },
  { x: 88, y: 8, size: 1.5, opacity: 0.6 },
  { x: 72, y: 32, size: 1, opacity: 0.45 },
  { x: 22, y: 55, size: 1.5, opacity: 0.55 },
  { x: 92, y: 62, size: 2, opacity: 0.75 },
  { x: 8, y: 78, size: 1, opacity: 0.35 },
  { x: 55, y: 5, size: 1, opacity: 0.5 },
  { x: 38, y: 88, size: 1.5, opacity: 0.65 },
  { x: 78, y: 85, size: 1, opacity: 0.4 },
  { x: 48, y: 42, size: 0.8, opacity: 0.3 },
  { x: 65, y: 70, size: 1.2, opacity: 0.5 },
  { x: 18, y: 35, size: 1, opacity: 0.55 },
  { x: 95, y: 42, size: 0.8, opacity: 0.35 },
  { x: 30, y: 12, size: 1.5, opacity: 0.7 },
  { x: 58, y: 92, size: 1, opacity: 0.45 },
] as const;

function WireframeSphere() {
  const latitudes = useMemo(() => [20, 35, 50, 65, 80], []);
  const longitudes = useMemo(() => Array.from({ length: 8 }, (_, i) => i * 22.5), []);

  return (
    <svg viewBox="0 0 200 200" className="absolute inset-0 h-full w-full" aria-hidden>
      <circle
        cx="100"
        cy="100"
        r="78"
        fill="none"
        stroke="rgba(56, 89, 140, 0.5)"
        strokeWidth="0.6"
      />
      {latitudes.map((y) => {
        const ry = Math.sin((y / 100) * Math.PI) * 78;
        return (
          <ellipse
            key={`lat-${String(y)}`}
            cx="100"
            cy="100"
            rx="78"
            ry={ry}
            fill="none"
            stroke="rgba(45, 75, 130, 0.42)"
            strokeWidth="0.5"
          />
        );
      })}
      {longitudes.map((deg) => (
        <ellipse
          key={`lon-${String(deg)}`}
          cx="100"
          cy="100"
          rx="12"
          ry="78"
          fill="none"
          stroke="rgba(45, 75, 130, 0.38)"
          strokeWidth="0.5"
          transform={`rotate(${String(deg)} 100 100)`}
        />
      ))}
    </svg>
  );
}

function PolyhedronCore() {
  return (
    <motion.div
      className="relative z-[2] h-40 w-40 sm:h-52 sm:w-52 md:h-60 md:w-60"
      style={{ perspective: 900 }}
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
    >
      <motion.div
        className="relative h-full w-full"
        style={{ transformStyle: 'preserve-3d' }}
        animate={{ rotateX: [18, 24, 18], rotateY: [0, 360] }}
        transition={{
          rotateX: { duration: 6, repeat: Infinity, ease: 'easeInOut' },
          rotateY: { duration: 22, repeat: Infinity, ease: 'linear' },
        }}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="absolute h-28 w-28 rounded-full bg-lime-400/20 blur-3xl sm:h-36 sm:w-36 md:h-44 md:w-44" />
          <div className="absolute h-20 w-20 rounded-full bg-cyan-400/25 blur-2xl sm:h-28 sm:w-28 md:h-32 md:w-32" />

          <svg
            viewBox="0 0 200 200"
            className="relative h-[88%] w-[88%] drop-shadow-[0_0_28px_rgba(34,211,238,0.35)]"
            aria-hidden
          >
            <defs>
              <linearGradient id="face-lime" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#a3e635" />
                <stop offset="100%" stopColor="#84cc16" />
              </linearGradient>
              <linearGradient id="face-lime-bright" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#bef264" />
                <stop offset="100%" stopColor="#65a30d" />
              </linearGradient>
              <linearGradient id="face-cyan" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
              <linearGradient id="face-cyan-deep" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#0891b2" />
                <stop offset="100%" stopColor="#22d3ee" />
              </linearGradient>
              <linearGradient id="face-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#34d399" />
                <stop offset="100%" stopColor="#10b981" />
              </linearGradient>
              <linearGradient id="face-teal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#2dd4bf" />
                <stop offset="100%" stopColor="#14b8a6" />
              </linearGradient>
              <linearGradient id="face-green" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4ade80" />
                <stop offset="100%" stopColor="#22c55e" />
              </linearGradient>
              <linearGradient id="face-green-dark" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#16a34a" />
                <stop offset="100%" stopColor="#15803d" />
              </linearGradient>
              <filter id="face-glow">
                <feGaussianBlur stdDeviation="1.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <g filter="url(#face-glow)">
              {POLYHEDRON_FACES.map((face, i) => (
                <path
                  key={i}
                  d={face.d}
                  fill={face.fill}
                  stroke="rgba(255,255,255,0.12)"
                  strokeWidth="0.5"
                  strokeLinejoin="round"
                />
              ))}
            </g>
          </svg>
        </div>
      </motion.div>
    </motion.div>
  );
}

function Particles() {
  return (
    <div className="pointer-events-none absolute inset-0 z-[1]" aria-hidden>
      {PARTICLE_SEEDS.map((p, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-indigo-400/80 dark:bg-white"
          style={{
            left: `${String(p.x)}%`,
            top: `${String(p.y)}%`,
            width: p.size,
            height: p.size,
            opacity: p.opacity,
            boxShadow: '0 0 6px rgba(99,102,241,0.35)',
          }}
          animate={{ opacity: [p.opacity, p.opacity * 0.4, p.opacity] }}
          transition={{
            duration: 2.5 + (i % 3),
            repeat: Infinity,
            ease: 'easeInOut',
            delay: i * 0.15,
          }}
        />
      ))}
    </div>
  );
}

export function Hero3DGraphic() {
  return (
    <div className="relative flex h-[300px] w-full items-center justify-center sm:h-[360px] md:h-[380px] lg:h-[440px]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.14)_0%,transparent_68%)] dark:bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.1)_0%,transparent_68%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_65%_35%,rgba(6,182,212,0.12)_0%,transparent_55%)] dark:bg-[radial-gradient(ellipse_at_65%_35%,rgba(6,182,212,0.08)_0%,transparent_55%)]" />

      <div
        className="pointer-events-none absolute inset-0 opacity-50 dark:opacity-[0.35]"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(148,163,184,0.18) 1px, transparent 1px)',
          backgroundSize: '22px 22px',
        }}
      />

      <motion.div
        initial={{ scale: 0.88, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.9, ease: 'easeOut' }}
        className="relative flex h-52 w-52 items-center justify-center sm:h-60 sm:w-60 md:h-64 md:w-64 lg:h-72 lg:w-72"
      >
        <WireframeSphere />
        <Particles />
        <PolyhedronCore />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.45 }}
        className="border-border bg-card/95 absolute bottom-2 left-1/2 z-10 w-[calc(100%-2rem)] max-w-[220px] -translate-x-1/2 rounded-xl border px-3 py-2.5 shadow-2xl backdrop-blur-md sm:bottom-auto sm:left-auto sm:right-2 sm:top-10 sm:w-auto sm:max-w-none sm:translate-x-0 sm:px-4 sm:py-3 md:right-4 lg:right-6"
      >
        <div className="flex items-center justify-center gap-3 sm:justify-start">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-emerald-500/20 ring-1 ring-emerald-500/30 sm:h-9 sm:w-9">
            <Zap className="h-4 w-4 text-emerald-600 dark:text-emerald-400" fill="currentColor" />
          </div>
          <div className="text-left">
            <p className="text-muted-foreground text-[10px] sm:text-[11px]">Avg. Latency</p>
            <p className="text-sm font-semibold tabular-nums text-emerald-600 sm:text-base dark:text-emerald-400">
              12ms
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
