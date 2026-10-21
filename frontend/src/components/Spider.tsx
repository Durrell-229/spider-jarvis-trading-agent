import { useEffect, useRef } from 'react';
import { useStore } from '../stores/useStore';
import { STATE_COLORS, type SpiderState } from '../types';

/**
 * Animated spider driven by real backend state.
 * Canvas-based for 60fps smooth motion.
 */
export function Spider() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { spiderState, spiderColor, spiderMessage, nodes } = useStore();
  const animRef = useRef({
    x: 400,
    y: 300,
    targetX: 400,
    targetY: 300,
    angle: 0,
    legPhase: 0,
    speed: 0.5,
    trails: [] as { x: number; y: number; life: number }[],
  });

  useEffect(() => {
    if (nodes.length > 0 && ['SCANNING', 'TARGET_SELECTED', 'TRAVELLING', 'ANALYSING'].includes(spiderState)) {
      const target = nodes[Math.floor(Math.random() * Math.min(nodes.length, 5))];
      if (target) {
        animRef.current.targetX = target.x || 400;
        animRef.current.targetY = target.y || 300;
      }
    }
    if (spiderState === 'IDLE' || spiderState === 'EMERGENCY_STOP') {
      animRef.current.targetX = 400;
      animRef.current.targetY = 300;
    }
    const speedMap: Partial<Record<SpiderState, number>> = {
      IDLE: 0.3,
      SCANNING: 1.8,
      TRAVELLING: 3.5,
      ANALYSING: 0.8,
      WAITING_FOR_JEV: 0.4,
      PAPER_ORDER: 1.2,
      REJECTED: 0.2,
      EMERGENCY_STOP: 0,
      ERROR: 0,
    };
    animRef.current.speed = speedMap[spiderState] ?? 0.5;
  }, [spiderState, nodes]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    const color = STATE_COLORS[spiderState] || spiderColor || '#22d3ee';

    const draw = () => {
      const a = animRef.current;
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const dx = a.targetX - a.x;
      const dy = a.targetY - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > 2) {
        a.x += (dx / dist) * a.speed;
        a.y += (dy / dist) * a.speed;
        a.angle = Math.atan2(dy, dx);
        a.legPhase += 0.25 * a.speed;
        if (a.speed > 0.5) {
          a.trails.push({ x: a.x, y: a.y, life: 1 });
          if (a.trails.length > 40) a.trails.shift();
        }
      } else {
        a.legPhase += 0.05;
      }

      for (let i = 0; i < a.trails.length; i++) {
        const t = a.trails[i];
        t.life -= 0.02;
        if (t.life <= 0) continue;
        ctx.beginPath();
        ctx.strokeStyle = `rgba(34, 211, 238, ${t.life * 0.4})`;
        ctx.lineWidth = 1.5;
        if (i > 0) {
          ctx.moveTo(a.trails[i - 1].x, a.trails[i - 1].y);
          ctx.lineTo(t.x, t.y);
          ctx.stroke();
        }
      }
      a.trails = a.trails.filter((t) => t.life > 0);

      const bx = a.x;
      const by = a.y;

      const gradient = ctx.createRadialGradient(bx, by, 0, bx, by, 40);
      gradient.addColorStop(0, color + 'aa');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(bx, by, 40, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.ellipse(bx - 6, by, 14, 11, a.angle, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.ellipse(bx + 10, by, 9, 7, a.angle, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(bx + 10, by, 3, 0, Math.PI * 2);
      ctx.fill();

      for (let i = 0; i < 8; i++) {
        const side = i < 4 ? -1 : 1;
        const idx = i % 4;
        const baseAngle = a.angle + side * (0.4 + idx * 0.35);
        const legLen = 28 + idx * 4;
        const phase = a.legPhase + i * 0.8;
        const lift = Math.sin(phase) * 6 * (a.speed > 0.2 ? 1 : 0.3);

        const jointX = bx + Math.cos(baseAngle) * 12;
        const jointY = by + Math.sin(baseAngle) * 10 - lift * 0.3;
        const endX = jointX + Math.cos(baseAngle + side * 0.3) * legLen;
        const endY = jointY + Math.sin(baseAngle + side * 0.3) * legLen + lift;

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.moveTo(bx, by);
        ctx.quadraticCurveTo(jointX, jointY - 8, endX, endY);
        ctx.stroke();

        ctx.fillStyle = color + '88';
        ctx.beginPath();
        ctx.arc(endX, endY, 2, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.font = '11px monospace';
      ctx.fillStyle = color;
      ctx.textAlign = 'center';
      ctx.fillText(spiderState, bx, by - 28);
      if (spiderMessage) {
        ctx.fillStyle = 'rgba(200,220,255,0.7)';
        ctx.font = '10px monospace';
        const msg = spiderMessage.length > 36 ? spiderMessage.slice(0, 34) + '…' : spiderMessage;
        ctx.fillText(msg, bx, by + 36);
      }

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [spiderState, spiderColor, spiderMessage]);

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={600}
      style={{
        width: '100%',
        height: '100%',
        background: 'transparent',
        display: 'block',
      }}
    />
  );
}
