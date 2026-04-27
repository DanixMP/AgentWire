/**
 * Stats bar showing message count, tokens, and cost
 */

import { useMemo } from 'react';
import type { WireMessage } from '../types';

interface StatsBarProps {
  messages: WireMessage[];
}

export function StatsBar({ messages }: StatsBarProps) {
  const stats = useMemo(() => {
    const totalMessages = messages.length;
    const totalTokens = messages.reduce(
      (sum, msg) => sum + msg.tokens_in + msg.tokens_out,
      0
    );
    const totalCost = messages.reduce(
      (sum, msg) => sum + msg.cost_usd,
      0
    );

    return {
      totalMessages,
      totalTokens,
      totalCost: totalCost.toFixed(4),
    };
  }, [messages]);

  return (
    <div className="flex gap-4 p-4 bg-slate-800 border-b border-slate-700">
      <StatCard
        label="Messages"
        value={stats.totalMessages.toLocaleString()}
        icon="💬"
      />
      <StatCard
        label="Tokens"
        value={stats.totalTokens.toLocaleString()}
        icon="🔢"
      />
      <StatCard
        label="Cost"
        value={`$${stats.totalCost}`}
        icon="💰"
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  icon: string;
}

function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-slate-700 rounded-lg">
      <span className="text-2xl">{icon}</span>
      <div>
        <div className="text-xs text-slate-400 uppercase tracking-wide">
          {label}
        </div>
        <div className="text-xl font-semibold text-slate-100">
          {value}
        </div>
      </div>
    </div>
  );
}
