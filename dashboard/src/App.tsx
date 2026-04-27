/**
 * Main App component
 */

import { useState, useEffect, useMemo } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Sidebar } from './components/Sidebar';
import { StatsBar } from './components/StatsBar';
import { MessageFeed } from './components/MessageFeed';
import { GraphView } from './components/GraphView';
import { ReplayBar } from './components/ReplayBar';
import type { GraphData } from './types';

type ViewMode = 'feed' | 'graph';

function App() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('feed');
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  
  // Replay state
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const [replaySpeed, setReplaySpeed] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const { messages, isConnected, lastError, clearMessages } = useWebSocket();

  // Get current session ID (use the most recent session)
  const currentSessionId = useMemo(() => {
    if (messages.length === 0) return null;
    return messages[messages.length - 1].session_id;
  }, [messages]);

  // Fetch graph data when switching to graph view or when messages change
  useEffect(() => {
    if (viewMode === 'graph' && currentSessionId) {
      fetch(`/api/sessions/${currentSessionId}/graph`)
        .then(res => res.json())
        .then(data => setGraphData(data))
        .catch(err => console.error('Failed to fetch graph data:', err));
    }
  }, [viewMode, currentSessionId, messages.length]);

  const handleClearAll = () => {
    if (confirm('Are you sure you want to clear all messages?')) {
      clearMessages();
      setGraphData({ nodes: [], edges: [] });
      setIsReplaying(false);
      setReplayIndex(0);
    }
  };

  const handleFilterPair = (source: string, _target: string) => {
    // For now, just filter by source agent
    // In the future, could implement pair filtering
    setSelectedAgent(source);
    setViewMode('feed');
  };

  const handleStartReplay = () => {
    setIsReplaying(true);
    setReplayIndex(0);
    setIsPlaying(false);
    setViewMode('feed'); // Start in feed view
  };

  const handleToggleReplay = () => {
    setIsReplaying(!isReplaying);
    if (isReplaying) {
      // Exiting replay mode
      setIsPlaying(false);
      setReplayIndex(messages.length - 1);
    }
  };

  const handleTogglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSetIndex = (index: number) => {
    setReplayIndex(index);
    setIsPlaying(false); // Pause when manually scrubbing
  };

  const handleFirst = () => {
    setReplayIndex(0);
    setIsPlaying(false);
  };

  const handlePrev = () => {
    setReplayIndex(Math.max(0, replayIndex - 1));
    setIsPlaying(false);
  };

  const handleNext = () => {
    setReplayIndex(Math.min(messages.length - 1, replayIndex + 1));
  };

  const handleLast = () => {
    setReplayIndex(messages.length - 1);
    setIsPlaying(false);
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <Sidebar
        messages={messages}
        selectedAgent={selectedAgent}
        onSelectAgent={setSelectedAgent}
        onClearAll={handleClearAll}
        onStartReplay={handleStartReplay}
        hasMessages={messages.length > 0}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Connection status */}
        <div className={`px-4 py-2 text-sm ${isConnected ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`}>
          {isConnected ? (
            <span>🟢 Connected to AgentWire</span>
          ) : (
            <span>🔴 Disconnected - Reconnecting...</span>
          )}
          {lastError && (
            <span className="ml-4 text-red-300">Error: {lastError}</span>
          )}
          {isReplaying && (
            <span className="ml-4 text-yellow-300">⏮ Replay Mode</span>
          )}
        </div>

        {/* Stats bar */}
        <StatsBar messages={messages} />

        {/* View mode tabs */}
        <div className="flex gap-2 px-4 py-2 bg-slate-800 border-b border-slate-700">
          <button
            onClick={() => setViewMode('feed')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              viewMode === 'feed'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            📝 Feed
          </button>
          <button
            onClick={() => setViewMode('graph')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              viewMode === 'graph'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            🕸️ Graph
          </button>
        </div>

        {/* Content area */}
        {viewMode === 'feed' ? (
          <MessageFeed
            messages={messages}
            selectedAgent={selectedAgent}
            isReplaying={isReplaying}
            replayIndex={replayIndex}
          />
        ) : (
          <GraphView
            graphData={graphData}
            onFilterAgent={(agent) => {
              setSelectedAgent(agent);
              setViewMode('feed');
            }}
            onFilterPair={handleFilterPair}
            isReplaying={isReplaying}
            replayIndex={replayIndex}
            messages={messages}
          />
        )}

        {/* Replay bar */}
        <ReplayBar
          isReplaying={isReplaying}
          replayIndex={replayIndex}
          totalMessages={messages.length}
          replaySpeed={replaySpeed}
          isPlaying={isPlaying}
          onToggleReplay={handleToggleReplay}
          onSetIndex={handleSetIndex}
          onSetSpeed={setReplaySpeed}
          onTogglePlay={handleTogglePlay}
          onFirst={handleFirst}
          onPrev={handlePrev}
          onNext={handleNext}
          onLast={handleLast}
        />
      </div>
    </div>
  );
}

export default App;
