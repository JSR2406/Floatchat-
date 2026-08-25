'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, Loader2, X, Volume2, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceRecorderProps {
  onTranscript: (transcript: string) => void;
  disabled?: boolean;
  inline?: boolean;
  language?: string;
}

export function VoiceRecorder({ onTranscript, disabled = false, inline = false, language = 'ml-IN' }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);
    
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = language;
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setTranscript(finalTranscript);
          onTranscript(finalTranscript);
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
          setError(`Recognition error: ${event.error}`);
        }
        setIsRecording(false);
      };
      
      recognitionRef.current.onend = () => {
        if (isRecording) {
          // Restart if still supposed to be recording
          try {
            recognitionRef.current?.start();
          } catch {
            setIsRecording(false);
          }
        }
      };
    }
  }, [language, onTranscript, isRecording]);

  const startRecording = useCallback(async () => {
    if (!isSupported) {
      setError('Speech recognition not supported in this browser');
      return;
    }

    try {
      setError(null);
      setTranscript('');
      
      // Try SpeechRecognition first (better for continuous)
      if (recognitionRef.current) {
        recognitionRef.current.lang = language;
        recognitionRef.current.start();
        setIsRecording(true);
        return;
      }
      
      // Fallback to MediaRecorder
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // In a real app, you'd upload this to the backend for transcription
        // For now, we'll just note that recording stopped
        console.log('Audio recorded, size:', audioBlob.size);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start(100);
      setIsRecording(true);
    } catch (err) {
      console.error('Recording error:', err);
      setError(err instanceof Error ? err.message : 'Failed to start recording');
    }
  }, [isSupported, language]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  const clearTranscript = useCallback(() => {
    setTranscript('');
  }, []);

  if (!isSupported) {
    return (
      <div className={cn('p-3 rounded-lg bg-rose-50 border border-rose-200', inline && 'w-full')}>
        <div className="flex items-center gap-2 text-rose-700 text-sm">
          <AlertCircle className="h-4 w-4" />
          <span>Voice input not supported in this browser. Use Chrome/Edge for best experience.</span>
        </div>
      </div>
    );
  }

  if (inline) {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={disabled}
          className={cn(
            'p-2 rounded-xl transition-colors',
            isRecording
              ? 'bg-rose-100 text-rose-600 animate-pulse'
              : 'bg-muted text-muted-foreground hover:bg-muted/80',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
          title={isRecording ? 'Stop recording' : 'Start voice input'}
        >
          {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </button>
        {transcript && (
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground truncate">{transcript}</p>
            <button
              onClick={clearTranscript}
              className="text-xs text-primary hover:underline mt-1"
            >
              Clear
            </button>
          </div>
        )}
        {error && (
          <span className="text-xs text-rose-600">{error}</span>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-foreground">Voice Input</h4>
        <span className={cn('px-2 py-0.5 rounded text-xs font-medium', language === 'ml-IN' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700')}>
          {language === 'ml-IN' ? 'മലയാളം' : language === 'hi-IN' ? 'हिन्दी' : 'English'}
        </span>
      </div>

      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-center gap-3 px-4 py-4 rounded-xl border-2 transition-all',
          isRecording
            ? 'border-rose-300 bg-rose-50 text-rose-600 animate-pulse'
            : 'border-border bg-background text-foreground hover:border-primary/50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
      >
        {isRecording ? (
          <>
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="font-medium">Recording... Click to stop</span>
            <span className="text-sm text-muted-foreground">Speak now</span>
          </>
        ) : (
          <>
            <Mic className="h-6 w-6" />
            <span className="font-medium">Start Voice Input</span>
            <span className="text-sm text-muted-foreground">Click and speak</span>
          </>
        )}
      </button>

      {transcript && (
        <div className="mt-3 p-3 rounded-lg bg-muted/50 border border-border">
          <div className="flex items-start justify-between gap-2 mb-2">
            <p className="text-sm font-medium text-foreground">Transcript:</p>
            <button
              onClick={clearTranscript}
              className="p-1 rounded hover:bg-muted transition-colors"
              aria-label="Clear transcript"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="text-sm text-foreground whitespace-pre-wrap">{transcript}</p>
          <button
            onClick={() => onTranscript(transcript)}
            className="mt-2 text-sm text-primary hover:underline flex items-center gap-1"
          >
            <CheckCircle className="h-4 w-4" />
            Use this transcript
          </button>
        </div>
      )}

      {error && (
        <div className="mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm">
          {error}
        </div>
      )}

      <p className="mt-3 text-xs text-muted-foreground text-center">
        Supports: Malayalam, Hindi, English • Click microphone to start • Auto-stops on silence
      </p>
    </div>
  );
}

import { AlertCircle } from 'lucide-react';