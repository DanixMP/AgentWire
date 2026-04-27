/**
 * Sidebar with sessions and agents list
 */

import { useMemo } from 'react';
import type { WireMessage } from '../types';

interface SidebarProps {
  messages: WireMessage[];
  selectedAgent: string | null;
  onSelectAgent: (agent: string | null) => void;
  onClearAll: () => void;
  onStartReplay?: () => void;
  hasMessages?: boolean;
}

export function Sidebar({
  messages,
  selectedAgent,
  onSelectAgent,
  onClearAll,
  onStartReplay,
  hasMessages = false,
}: SidebarProps) {
  const { sessions, agents } = useMemo(() => {
    const sessionMap = new Map<string, number>();
    const agentSet = new Set<string>();

    messages.forEach((msg) => {
      // Count messages per session
      sessionMap.set(msg.session_id, (sessionMap.get(msg.session_id) || 0) + 1);
      
      // Collect unique agents (exclude system)
      if (msg.sender !== 'system') {
        agentSet.add(msg.sender);
      }
      if (msg.receiver !== 'system' && msg.receiver !== 'broadcast' && msg.receiver !== 'unknown') {
        agentSet.add(msg.receiver);
      }
    });

    return {
      sessions: Array.from(sessionMap.entries()).map(([id, count]) => ({
        id,
        count,
      })),
      agents: Array.from(agentSet).sort(),
    };
  }, [messages]);

  return (
    <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h1 className="text-xl font-bold text-slate-100">AgentWire</h1>
        <p className="text-xs text-slate-400 mt-1">Real-time agent inspector</p>
      </div>

      {/* Sessions */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">
            Sessions
          </h2>
          {sessions.length === 0 ? (
            <p className="text-sm text-slate-500 italic">No sessions yet</p>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="px-3 py-2 bg-slate-700 rounded text-sm hover:bg-slate-600 cursor-pointer transition-colors"
                >
                  <div className="font-medium text-slate-200 truncate">
                    {session.id}
                  </div>
                  <div className="text-xs text-slate-400">
                    {session.count} messages
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Agents */}
        <div className="p-4 border-t border-slate-700">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">
            Agents
          </h2>
          {agents.length === 0 ? (
            <p className="text-sm text-slate-500 italic">No agents yet</p>
          ) : (
            <div className="space-y-1">
              <button
                onClick={() => onSelectAgent(null)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selectedAgent === null
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                }`}
              >
                All Agents
              </button>
              {agents.map((agent) => (
                <button
                  key={agent}
                  onClick={() => onSelectAgent(agent)}
                  className={`w-full text-left px-3 py-2 rounded text-sm transition-colors truncate ${
                    selectedAgent === agent
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                  }`}
                >
                  {agent}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700 space-y-2">
        {onStartReplay && hasMessages && (
          <button
            onClick={onStartReplay}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors mb-2"
          >
            ⏮ Replay Session
          </button>
        )}
        <button
          onClick={onClearAll}
          className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors"
        >
          Clear All
        </button>
      </div>
    </div>
  );
}
