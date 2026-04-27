/**
 * Replay controls for stepping through session messages
 */

import { useEffect, useRef } from 'react';

interface ReplayBarProps {
  isReplaying: boolean;
  replayIndex: number;
  totalMessages: number;
  replaySpeed: number;
  isPlaying: boolean;
  onToggleReplay: () => void;
  onSetIndex: (index: number) => void;
  onSetSpeed: (speed: number) => void;
  onTogglePlay: () => void;
  onFirst: () => void;
  onPrev: () => void;
  onNext: () => void;
  onLast: () => void;
}

const SPEED_OPTIONS = [0.5, 1, 2, 5, 10];

export function ReplayBar({
  isReplaying,
  replayIndex,
  totalMessages,
  replaySpeed,
  isPlaying,
  onToggleReplay,
  onSetIndex,
  onSetSpeed,
  onTogglePlay,
  onFirst,
  onPrev,
  onNext,
  onLast,
}: ReplayBarProps) {
  const intervalRef = useRef<number | null>(null);

  // Auto-play logic
  useEffect(() => {
    if (isPlaying && isReplaying) {
      const delay = 1000 / replaySpeed;
      
      intervalRef.current = window.setInterval(() => {
        if (replayIndex < totalMessages - 1) {
          onNext();
        } else {
          // Reached the end, stop playing
          onTogglePlay();
        }
      }, delay);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [isPlaying, isReplaying, replayIndex, totalMessages, replaySpeed, onNext, onTogglePlay]);

  if (!isReplaying) {
    return null;
  }

  const progress = totalMessages > 0 ? (replayIndex / (totalMessages - 1)) * 100 : 0;

  return (
    <div className="fixed bottom-0 left-64 right-0 bg-slate-800 border-t border-slate-700 p-4 shadow-lg">
      <div className="flex items-center gap-4">
        {/* Exit replay button */}
        <button
          onClick={onToggleReplay}
          className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors"
          title="Exit replay mode"
        >
          ✕ Exit
        </button>

        {/* Playback controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={onFirst}
            disabled={replayIndex === 0}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="First message"
          >
            ⏮
          </button>
          
          <button
            onClick={onPrev}
            disabled={replayIndex === 0}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Previous message"
          >
            ◀
          </button>
          
          <button
            onClick={onTogglePlay}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>
          
          <button
            onClick={onNext}
            disabled={replayIndex >= totalMessages - 1}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Next message"
          >
            ▶
          </button>
          
          <button
            onClick={onLast}
            disabled={replayIndex >= totalMessages - 1}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Last message"
          >
            ⏭
          </button>
        </div>

        {/* Timeline scrubber */}
        <div className="flex-1 flex items-center gap-3">
          <span className="text-sm text-slate-400 whitespace-nowrap">
            {replayIndex + 1} / {totalMessages}
          </span>
          
          <div className="flex-1 relative">
            <input
              type="range"
              min="0"
              max={Math.max(0, totalMessages - 1)}
              value={replayIndex}
              onChange={(e) => onSetIndex(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${progress}%, #475569 ${progress}%, #475569 100%)`,
              }}
            />
          </div>
        </div>

        {/* Speed control */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">Speed:</span>
          <select
            value={replaySpeed}
            onChange={(e) => onSetSpeed(parseFloat(e.target.value))}
            className="px-3 py-2 bg-slate-700 text-white rounded text-sm cursor-pointer hover:bg-slate-600 transition-colors"
          >
            {SPEED_OPTIONS.map((speed) => (
              <option key={speed} value={speed}>
                {speed}×
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
