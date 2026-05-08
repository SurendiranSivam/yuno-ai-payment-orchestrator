"use client";

import { useEffect, useRef, useCallback, useState } from "react";

/**
 * WebSocket hook for realtime event streaming from the backend.
 * Auto-reconnects on disconnect with exponential backoff.
 *
 * Uses a ref for the event handler to avoid infinite reconnection loops
 * caused by callback reference changes on parent re-renders.
 */
export function useWebSocket(onEvent: (event: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelay = useRef(1000);

  // Store the latest callback in a ref so `connect` doesn't depend on it
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    // Don't connect during SSR
    if (typeof window === "undefined") return;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    let ws: WebSocket;

    try {
      ws = new WebSocket(`${wsUrl}/ws/events`);
    } catch {
      // Schedule retry if WebSocket constructor fails
      reconnectTimeout.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
        connect();
      }, reconnectDelay.current);
      return;
    }

    ws.onopen = () => {
      setIsConnected(true);
      reconnectDelay.current = 1000; // Reset backoff on successful connection
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onEventRef.current(data);
      } catch {
        // Skip malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect with exponential backoff (max 30s)
      reconnectTimeout.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, []); // No dependencies — uses refs for mutable state

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    };
  }, [connect]);

  // Send periodic pings to keep connection alive
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return { isConnected };
}

