/**
 * Scrolling message feed with auto-scroll
 */

import { useEffect, useRef, useState } from 'react';
import type { WireMessage } from '../types';
import { MESSAGE_TYPE_COLORS } from '../types';

interface MessageFeedProps {
  messages: WireMessage[];
  selectedAgent: string | null;
  isReplaying?: boolean;
  replayIndex?: number;
}

export function MessageFeed({ messages, selectedAgent, isReplaying = false, replayIndex = 0 }: MessageFeedProps) {
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const [userScrolled, setUserScrolled] = useState(false);
  const [newMessageCount, setNewMessageCount] = useState(0);
  const feedRef = useRef<HTMLDivElement>(null);
  const lastMessageCountRef = useRef(messages.length);

  // Filter messages by selected agent
  const filteredMessages = selectedAgent
    ? messages.filter(
        (msg) => msg.sender === selectedAgent || msg.receiver === selectedAgent
      )
    : messages;

  // In replay mode, only show messages up to replayIndex
  const displayMessages = isReplaying
    ? filteredMessages.slice(0, replayIndex + 1)
    : filteredMessages;

  // Auto-scroll to bottom unless user has scrolled up (disabled in replay mode)
  useEffect(() => {
    if (isReplaying) {
      // In replay mode, always scroll to bottom to show current message
      if (feedRef.current) {
        feedRef.current.scrollTop = feedRef.current.scrollHeight;
      }
      return;
    }

    if (!feedRef.current) return;

    const isAtBottom =
      feedRef.current.scrollHeight - feedRef.current.scrollTop <=
      feedRef.current.clientHeight + 100;

    if (isAtBottom && !userScrolled) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
      setNewMessageCount(0);
    } else if (messages.length > lastMessageCountRef.current) {
      // New messages arrived while user scrolled up
      setNewMessageCount((prev) => prev + (messages.length - lastMessageCountRef.current));
    }

    lastMessageCountRef.current = messages.length;
  }, [messages, userScrolled, isReplaying, replayIndex]);

  const handleScroll = () => {
    if (isReplaying) return; // Disable scroll detection in replay mode

    if (!feedRef.current) return;

    const isAtBottom =
      feedRef.current.scrollHeight - feedRef.current.scrollTop <=
      feedRef.current.clientHeight + 100;

    setUserScrolled(!isAtBottom);
    
    if (isAtBottom) {
      setNewMessageCount(0);
    }
  };

  const scrollToBottom = () => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
      setUserScrolled(false);
      setNewMessageCount(0);
    }
  };

  const toggleExpand = (messageId: string) => {
    setExpandedMessages((prev) => {
      const next = new Set(prev);
      if (next.has(messageId)) {
        next.delete(messageId);
      } else {
        next.add(messageId);
      }
      return next;
    });
  };

  return (
    <div className="flex-1 flex flex-col relative">
      {/* Feed */}
      <div
        ref={feedRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-2"
      >
        {displayMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="text-center">
              <div className="text-4xl mb-2">📭</div>
              <p>No messages yet</p>
              <p className="text-sm mt-1">
                Messages will appear here in real-time
              </p>
            </div>
          </div>
        ) : (
          displayMessages.map((msg, index) => (
            <MessageCard
              key={msg.id}
              message={msg}
              isExpanded={expandedMessages.has(msg.id)}
              onToggleExpand={() => toggleExpand(msg.id)}
              isCurrent={isReplaying && index === replayIndex}
            />
          ))
        )}
      </div>

      {/* New messages pill (hidden in replay mode) */}
      {!isReplaying && newMessageCount > 0 && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 left-1/2 transform -translate-x-1/2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-colors flex items-center gap-2"
        >
          <span>↓</span>
          <span>{newMessageCount} new message{newMessageCount > 1 ? 's' : ''}</span>
        </button>
      )}
    </div>
  );
}

interface MessageCardProps {
  message: WireMessage;
  isExpanded: boolean;
  onToggleExpand: () => void;
  isCurrent?: boolean;
}

function MessageCard({ message, isExpanded, onToggleExpand, isCurrent = false }: MessageCardProps) {
  const timestamp = new Date(message.timestamp).toLocaleTimeString();
  const contentPreview = message.content.slice(0, 200);
  const hasMore = message.content.length > 200;

  return (
    <div
      className={`rounded-lg p-3 hover:bg-slate-650 transition-colors cursor-pointer ${
        isCurrent ? 'bg-blue-900 border-2 border-blue-500 animate-pulse' : 'bg-slate-700'
      }`}
      onClick={onToggleExpand}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-300">
            {message.sender}
          </span>
          <span className="text-slate-500">→</span>
          <span className="text-sm font-medium text-slate-300">
            {message.receiver}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${MESSAGE_TYPE_COLORS[message.type]}`}>
            {message.type}
          </span>
          <span className="text-xs text-slate-500">{timestamp}</span>
        </div>
      </div>

      {/* Content */}
      <div className="text-sm text-slate-200 mb-2">
        {isExpanded ? message.content : contentPreview}
        {hasMore && !isExpanded && (
          <span className="text-slate-500">...</span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-4 text-xs text-slate-400">
        {message.tokens_in + message.tokens_out > 0 && (
          <span>
            🔢 {(message.tokens_in + message.tokens_out).toLocaleString()} tokens
          </span>
        )}
        {message.latency_ms > 0 && (
          <span>⏱️ {message.latency_ms}ms</span>
        )}
        {message.cost_usd > 0 && (
          <span>💰 ${message.cost_usd.toFixed(4)}</span>
        )}
        {message.model && (
          <span>🤖 {message.model}</span>
        )}
      </div>
    </div>
  );
}
