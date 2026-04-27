/**
 * WebSocket hook with auto-reconnect and exponential backoff
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { WireMessage, WebSocketEvent } from '../types';

// Use relative URL for development (proxied by Vite)
const WS_URL = import.meta.env.DEV 
  ? `ws://${window.location.host}/ws`
  : 'ws://localhost:8000/ws';

const MAX_RECONNECT_DELAY = 8000; // 8 seconds
const INITIAL_RECONNECT_DELAY = 500; // 500ms

interface UseWebSocketReturn {
  messages: WireMessage[];
  isConnected: boolean;
  lastError: string | null;
  clearMessages: () => void;
}

export function useWebSocket(sessionId?: string): UseWebSocketReturn {
  const [messages, setMessages] = useState<WireMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const url = sessionId ? `${WS_URL}?session_id=${sessionId}` : WS_URL;
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setLastError(null);
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY; // Reset delay on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const wsEvent: WebSocketEvent = JSON.parse(event.data);
          
          if (wsEvent.event === 'message') {
            const message = wsEvent.data as WireMessage;
            setMessages((prev) => [...prev, message]);
          } else if (wsEvent.event === 'session_start') {
            console.log('Session started:', wsEvent.data);
          } else if (wsEvent.event === 'session_end') {
            console.log('Session ended:', wsEvent.data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setLastError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Auto-reconnect with exponential backoff
        if (shouldReconnectRef.current) {
          const delay = reconnectDelayRef.current;
          console.log(`Reconnecting in ${delay}ms...`);
          
          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectDelayRef.current = Math.min(
              reconnectDelayRef.current * 2,
              MAX_RECONNECT_DELAY
            );
            connect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setLastError('Failed to create WebSocket connection');
    }
  }, [sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    messages,
    isConnected,
    lastError,
    clearMessages,
  };
}
