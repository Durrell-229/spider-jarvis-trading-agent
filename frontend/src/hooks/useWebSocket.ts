import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../stores/useStore';
import type { EventLog, JEVDecision, PaperStats, SystemStatus, TokenNode } from '../types';

const WS_URL = `ws://${window.location.hostname}:8000/ws`;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const {
    setStatus,
    setNodes,
    addEvent,
    setJev,
    setPaperStats,
    setSpider,
    setConnected,
  } = useStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('[WS] connected');
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('[WS] disconnected — retry in 3s');
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      setConnected(false);
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        switch (msg.type) {
          case 'status':
            setStatus(msg.payload as SystemStatus);
            break;
          case 'graph':
            setNodes((msg.payload.nodes || []) as TokenNode[]);
            break;
          case 'event':
            addEvent(msg.payload as EventLog);
            break;
          case 'jev':
            setJev(msg.payload as JEVDecision);
            break;
          case 'paper_stats':
            setPaperStats(msg.payload as PaperStats);
            break;
          case 'spider_state':
            setSpider(
              msg.payload.state,
              msg.payload.message,
              msg.payload.color || '#3b82f6'
            );
            break;
          case 'ping':
            ws.send(JSON.stringify({ type: 'ping' }));
            break;
          default:
            break;
        }
      } catch (e) {
        console.warn('[WS] parse error', e);
      }
    };
  }, [setStatus, setNodes, addEvent, setJev, setPaperStats, setSpider, setConnected]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const sendControl = useCallback((action: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'control', action }));
    } else {
      fetch(`http://${window.location.hostname}:8000/api/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      }).catch(console.error);
    }
  }, []);

  return { sendControl };
}
