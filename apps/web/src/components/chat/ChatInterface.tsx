'use client';

import { useRef, useEffect } from 'react';
import { Loader2, Copy, Check, Volume2, VolumeX, ChevronDown, ChevronUp, FileText, MapPin, BarChart3, AlertCircle, Info } from 'lucide-react';
import { cn, formatDateTime, getConfidenceColor } from '@/lib/utils';
import type { ChatMessage, ChatResponse, EvidenceRecord } from '@floatchat/shared-types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (content: string) => void;
  inputValue: string;
  setInputValue: (value: string) => void;
  lastResponse: ChatResponse | null;
}

export function ChatInterface({ messages, isLoading, onSendMessage, inputValue, setInputValue, lastResponse }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [audioPlaying, setAudioPlaying] = useState<string | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleAudioToggle = (url: string | null | undefined) => {
    if (!url) return;
    if (audioPlaying === url) {
      setAudioPlaying(null);
    } else {
      setAudioPlaying(url);
    }
  };

  const renderMessageContent = (message: ChatMessage) => {
    if (message.isError) {
      return (
        <div className="rounded-lg bg-rose-50 border border-rose-200 p-4 text-rose-800">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        </div>
      );
    }

    return (
      <div className="whitespace-pre-wrap">{message.content}</div>
    );
  };

  const renderMessageActions = (message: ChatMessage) => {
    if (message.isUser) return null;

    return (
      <div className="flex items-center gap-1 ml-auto">
        <button
          onClick={() => handleCopy(message.content, message.id)}
          className="p-1.5 rounded hover:bg-muted transition-colors"
          aria-label="Copy message"
        >
          {copiedId === message.id ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
        </button>
        {message.audioUrl && (
          <button
            onClick={() => handleAudioToggle(message.audioUrl)}
            className="p-1.5 rounded hover:bg-muted transition-colors"
            aria-label={audioPlaying === message.audioUrl ? 'Stop audio' : 'Play audio'}
          >
            {audioPlaying === message.audioUrl ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </button>
        )}
      </div>
    );
  };

  const renderStructuredQuery = (query: ChatResponse['structured_query']) => {
    return (
      <details className="mt-3 border border-border rounded-lg bg-muted/50">
        <summary className="p-3 cursor-pointer flex items-center gap-2 font-medium text-sm">
          <FileText className="h-4 w-4" />
          Structured Query
        </summary>
        <pre className="p-3 text-xs font-mono overflow-x-auto max-h-64">
          {JSON.stringify(query, null, 2)}
        </pre>
      </details>
    );
  };

  const renderClarification = (question: string, partialQuery: ChatResponse['partial_query']) => {
    return (
      <div className="mt-3 p-4 rounded-lg border border-amber-200 bg-amber-50">
        <div className="flex items-start gap-2">
          <Info className="h-5 w-5 flex-shrink-0 text-amber-600" />
          <div>
            <p className="font-medium text-amber-800">Clarification Needed</p>
            <p className="text-amber-700 mt-1">{question}</p>
            {partialQuery && (
              <details className="mt-2">
                <summary className="text-sm text-amber-600 cursor-pointer">Partial Query</summary>
                <pre className="mt-1 p-2 text-xs font-mono bg-amber-100 rounded overflow-x-auto">
                  {JSON.stringify(partialQuery, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderEvidenceSummary = (evidence: EvidenceRecord) => {
    return (
      <details className="mt-3 border border-border rounded-lg bg-card">
        <summary className="p-3 cursor-pointer flex items-center gap-2 font-medium text-sm">
          <BarChart3 className="h-4 w-4" />
          Evidence Summary
          <span className={cn('ml-auto px-2 py-0.5 rounded text-xs font-medium border', getConfidenceColor(evidence.confidence.label))}>
            {evidence.confidence.label.toUpperCase()}
          </span>
        </summary>
        <div className="px-3 pb-3 space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-muted-foreground">Floats:</span> <span className="font-mono ml-1">{evidence.float_ids.length}</span></div>
            <div><span className="text-muted-foreground">Profiles:</span> <span className="font-mono ml-1">{evidence.profile_count}</span></div>
            <div><span className="text-muted-foreground">Observations:</span> <span className="font-mono ml-1">{evidence.observation_count}</span></div>
            <div><span className="text-muted-foreground">Data Freshness:</span> <span className="font-mono ml-1">{evidence.data_freshness.days_old} days</span></div>
          </div>
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground">{evidence.confidence.explanation}</p>
          </div>
        </div>
      </details>
    );
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <div className="h-16 w-16 rounded-full bg-ocean-100 flex items-center justify-center mb-4">
              <Waves className="h-8 w-8 text-ocean-600" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">Welcome to FloatChat</h3>
            <p className="max-w-sm">Ask questions about ARGO ocean data in any language. Get charts, maps, and full evidence for every answer.</p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
              <span className="px-2 py-1 rounded bg-ocean-100 text-ocean-700">Temperature profiles</span>
              <span className="px-2 py-1 rounded bg-ocean-100 text-ocean-700">Salinity trends</span>
              <span className="px-2 py-1 rounded bg-ocean-100 text-ocean-700">Marine conditions</span>
              <span className="px-2 py-1 rounded bg-ocean-100 text-ocean-700">Anomaly detection</span>
              <span className="px-2 py-1 rounded bg-ocean-100 text-ocean-700">What-if scenarios</span>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={cn('flex gap-3', message.isUser ? 'justify-end' : 'justify-start')}>
            {!message.isUser && (
              <div className="h-8 w-8 rounded-full bg-ocean-100 flex items-center justify-center flex-shrink-0">
                <Waves className="h-4 w-4 text-ocean-600" />
              </div>
            )}
            <div className={cn('flex flex-col gap-1 max-w-[85%]', message.isUser ? 'items-end' : 'items-start')}>
              <div className={cn(
                'rounded-2xl px-4 py-3 shadow-sm',
                message.isUser
                  ? 'bg-primary text-primary-foreground rounded-br-md'
                  : 'bg-card border border-border rounded-bl-md'
              )}>
                {renderMessageContent(message)}
                {renderMessageActions(message)}
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{formatDateTime(message.timestamp)}</span>
                {message.status === 'needs_clarification' && (
                  <span className="px-1.5 py-0.5 rounded text-xs bg-amber-100 text-amber-700">Clarification</span>
                )}
              </div>
              {!message.isUser && message.structuredQuery && renderStructuredQuery(message.structuredQuery)}
              {!message.isUser && message.clarificationQuestion && renderClarification(message.clarificationQuestion, message.partialQuery)}
              {!message.isUser && message.evidence && renderEvidenceSummary(message.evidence)}
            </div>
            {message.isUser && (
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-primary-foreground">
                <span className="text-xs font-medium">You</span>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start gap-3">
            <div className="h-8 w-8 rounded-full bg-ocean-100 flex items-center justify-center flex-shrink-0">
              <Loader2 className="h-4 w-4 text-ocean-600 animate-spin" />
            </div>
            <div className="rounded-2xl px-4 py-3 shadow-sm bg-card border border-border rounded-bl-md flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              <span className="text-muted-foreground">Analyzing your query...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

import { useState } from 'react';
import { Waves } from 'lucide-react';