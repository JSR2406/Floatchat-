"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Send, MicOff, Volume2, VolumeX, Globe, FileText, AlertTriangle } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  language?: string;
  evidence?: any[];
  visualizations?: any;
  riskAssessment?: any;
}

interface ChatInterfaceProps {
  onVoiceStart?: () => void;
  onVoiceStop?: () => void;
}

export function ChatInterface({ onVoiceStart, onVoiceStop }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Welcome to ORCA! I'm your marine intelligence assistant. Ask me about ocean conditions, route safety, hazards, or scenario projections. I support 10 Indian coastal languages.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("en-IN");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const languages = [
    { code: "en-IN", name: "English", flag: "🇮🇳" },
    { code: "hi-IN", name: "हिंदी", flag: "🇮🇳" },
    { code: "ml-IN", name: "മലയാളം", flag: "🇮🇳" },
    { code: "ta-IN", name: "தமிழ்", flag: "🇮🇳" },
    { code: "te-IN", name: "తెలుగు", flag: "🇮🇳" },
    { code: "bn-IN", name: "বাংলা", flag: "🇮🇳" },
    { code: "gu-IN", name: "ગુજરાતી", flag: "🇮🇳" },
    { code: "mr-IN", name: "मराठी", flag: "🇮🇳" },
    { code: "or-IN", name: "ଓଡ଼ିଆ", flag: "🇮🇳" },
    { code: "kn-IN", name: "ಕನ್ನಡ", flag: "🇮🇳" },
  ];
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
      language: selectedLanguage,
    };
    
    setMessages(prev => [...prev, userMessage]);
    const userInput = input.trim();
    setInput("");
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const responses: Record<string, string> = {
        "en-IN": `Based on the latest ARGO data, here are the current conditions in the ${userInput.includes("arabian") ? "Arabian Sea" : userInput.includes("bay of bengal") ? "Bay of Bengal" : "Indian Ocean"}:\n\n**Temperature:** 28.5°C (avg)\n**Salinity:** 35.2 PSU (avg)\n**Wave Height:** 1.2m\n**Wind:** 8 m/s from SW\n\n**Risk Assessment:** LOW - Conditions are favorable for marine activities.\n\n*Data from 16 ARGO floats, updated 6 hours ago.*`,
        "hi-IN": `नवीनतम ARGO डेटा के आधार पर, ${userInput.includes("अरब") ? "अरब सागर" : "हिंद महासागर"} में वर्तमान स्थिति:\n\n**तापमान:** 28.5°C (औसत)\n**लवणता:** 35.2 PSU (औसत)\n**लहर ऊंचाई:** 1.2m\n**हवा:** 8 m/s दक्षिण-पश्चिम से\n\n**जोखिम मूल्यांकन:** कम - समुद्री गतिविधियों के लिए स्थितियाँ अनुकूल हैं।\n\n*16 ARGO फ्लोट्स से डेटा, 6 घंटे पहले अपडेट किया गया।`,
        "ml-IN": `ഏറ്റവും ഒടുവിലത്തെ ARGO ഡാറ്റയുടെ അടിസ്ഥാനത്തിൽ, ${userInput.includes("അറബിക്കടൽ") ? "അറബിക്കടൽ" : "ഇന്ത്യൻ മഹാസമുദ്രം"} linh मुद्दों:\n\n**താപനില:** 28.5°C (ശരാശരി)\n**ലവണത:** 35.2 PSU (ശരാശരി)\n**അലപ്പേരു:** 1.2m\n**കാറ്റ്:** 8 m/s തെക്കുപടിഞ്ഞാറൻ ദിശയിൽ നിന്ന്\n\n**കmonton പ്രശ്നപരിഹാരം:** കം - സമുദ്ര പ്രവർത്തനങ്ങൾക്കായി സാഹചര്യങ്ങൾ അനുകൂലമാണ്।\n\n*16 ARGO ഫ്ലോട്ടുകളിൽ നിന്നുള്ള ഡാറ്റ, 6 മണിക്കൂർ മുമ്പ് അപ്ഡേറ്റ് ചെയ്തത്।`,
      };
      
      const langResponse = responses[selectedLanguage] || responses["en-IN"];
      
      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: "assistant",
        content: langResponse,
        timestamp: new Date(),
        language: selectedLanguage,
        evidence: [
          { source: "ARGO", profiles: 16, observations: 35520, freshness: "6 hours" },
        ],
        visualizations: { type: "map", data: "argo_profiles" },
        riskAssessment: { level: "low", score: 0.15, reasoning: "Favorable conditions" },
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };
  
  const handleVoiceToggle = () => {
    if (isRecording) {
      setIsRecording(false);
      onVoiceStop?.();
    } else {
      setIsRecording(true);
      onVoiceStart?.();
    }
  };
  
  const handleLanguageChange = (lang: string) => {
    setSelectedLanguage(lang);
  };
  
  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center text-white font-bold">
              ORCA
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Marine Intelligence Chat</h1>
              <p className="text-xs text-gray-500">Powered by ARGO • 10 Indian Languages • Voice Enabled</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <select
              value={selectedLanguage}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </option>
              ))}
            </select>
            
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`p-2 rounded-lg transition-colors ${isMuted ? "bg-red-100 text-red-600" : "hover:bg-gray-100"}`}
              title={isMuted ? "Unmute TTS" : "Mute TTS"}
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
            
            <button
              onClick={handleVoiceToggle}
              disabled={isLoading}
              className={`p-2 rounded-lg transition-colors ${isRecording ? "bg-red-600 text-white animate-pulse" : "bg-blue-600 text-white hover:bg-blue-700"}`}
              title={isRecording ? "Stop Recording" : "Start Voice Input"}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>
      
      {/* Messages */}
      <main className="flex-1 overflow-y-auto p-4 max-w-4xl mx-auto w-full">
        <div className="space-y-4" ref={messagesEndRef}>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-[80%] bg-gray-100 rounded-2xl p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </main>
      
      {/* Input */}
      <footer className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about ocean conditions, route safety, hazards, scenarios..."
              rows={1}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
              placeholder="Ask about ocean conditions, route safety, hazards, scenarios... (Press Enter to send, Shift+Enter for new line)"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`px-6 py-3 rounded-xl font-medium transition-colors ${!input.trim() || isLoading ? "bg-gray-300 text-gray-500 cursor-not-allowed" : "bg-blue-600 text-white hover:bg-blue-700"}`}
            >
              Send
            </button>
          </div>
          <p className="text-xs text-gray-500 text-center mt-2">
            Supports: English, Hindi, Malayalam, Tamil, Telugu, Bengali, Gujarati, Marathi, Odia, Kannada
          </p>
        </footer>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const langLabel = message.language ? message.language.replace("-IN", "").toUpperCase() : "";
  
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] ${isUser ? "bg-blue-600 text-white" : "bg-white text-gray-900 border border-gray-200"}`}>
        {!isUser && (
          <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 bg-gray-50">
            <span className="w-6 h-6 bg-gradient-to-br from-blue-600 to-blue-800 rounded-full flex items-center justify-center text-white text-xs font-bold">
              ORCA
            </span>
            {message.language && (
              <span className="ml-2 text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                {message.language.replace("-IN", "").toUpperCase()}
              </span>
            )}
          </div>
        )}
        <div className={`p-4 ${isUser ? "" : "text-gray-900"}`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        {!isUser && message.evidence && message.evidence.length > 0 && (
          <div className="px-4 pb-4 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="px-2 py-0.5 bg-gray-100 rounded">📊 Evidence</span>
              {message.evidence.map((e: any, i: number) => (
                <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
                  {e.source}: {e.profiles} profiles
                </span>
              ))}
            </div>
          </div>
        )}
        {!isUser && message.riskAssessment && (
          <div className="px-4 pb-4 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2 py-0.5 rounded ${
                message.riskAssessment.level === "low" ? "bg-green-100 text-green-700" :
                message.riskAssessment.level === "moderate" ? "bg-yellow-100 text-yellow-700" :
                "bg-red-100 text-red-700"
              }`}>
                ⚠️ Risk: {message.riskAssessment.level.toUpperCase()}
              </span>
              <span className="text-gray-500">Score: {(message.riskAssessment.score * 100).toFixed(0)}%</span>
            </div>
          </div>
        )}
        <div className="px-4 pb-3 text-right">
          <span className={`text-xs ${isUser ? "text-blue-200" : "text-gray-400"}`}>
            {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;