import { useState, useRef, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Mic, MicOff, Send, Loader2, Volume2, Phone, PhoneOff, Globe, Camera, MapPin } from 'lucide-react';
import clsx from 'clsx';
import { processText, processPhoto } from '../api/voice';
import type { ConversationTurn } from '../types';

const LANGUAGES = [
  { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
  { code: 'sw', name: 'Swahili', native: 'Kiswahili' },
  { code: 'en', name: 'English', native: 'English' },
];

const EXAMPLE_QUESTIONS: Record<string, string[]> = {
  hi: [
    'Mere tamatar ke patte peele ho rahe hain, kya karoon?',
    'Gehu ki buvai ka sahi samay kya hai?',
    'PM KISAN yojana ke liye kaise apply karein?',
  ],
  te: [
    'Naa vari pantalo purugulu vasthunnaayi, em cheyali?',
    'Patti pantaku manchhi samayam eppudu?',
  ],
  en: [
    'My cotton plants have white spots on the leaves. What should I do?',
    'When is the best time to plant wheat this season?',
    'What is the current market price for rice?',
  ],
  ta: [
    'En nel payiril puzhu thakkam irukku, enna seyya vendum?',
  ],
  sw: [
    'Mimea yangu ya mahindi yana wadudu, nifanye nini?',
  ],
};

export default function VoiceDemo() {
  const [language, setLanguage] = useState('hi');
  const [country, setCountry] = useState('IN');
  const [isCallActive, setIsCallActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [conversation, setConversation] = useState<ConversationTurn[]>([]);
  const [sessionId] = useState(() => `web_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`);
  const recognitionRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Language codes for Web Speech API
  const SPEECH_LANG_MAP: Record<string, string> = {
    hi: 'hi-IN', te: 'te-IN', ta: 'ta-IN', sw: 'sw-KE', en: 'en-IN',
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Speak text using browser SpeechSynthesis with best available voice
  const speakResponse = (text: string, lang: string) => {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const targetLang = SPEECH_LANG_MAP[lang] || 'en-IN';
    utterance.lang = targetLang;
    utterance.rate = 0.85;
    utterance.pitch = 1.0;

    // Try to find the best voice for this language
    const voices = window.speechSynthesis.getVoices();
    const langPrefix = targetLang.split('-')[0]; // "te" from "te-IN"

    // Prefer: Google > Microsoft > any matching voice
    const googleVoice = voices.find(v => v.lang.startsWith(langPrefix) && v.name.includes('Google'));
    const femaleVoice = voices.find(v => v.lang.startsWith(langPrefix) && (v.name.includes('Female') || v.name.includes('Lakshmi') || v.name.includes('Lekha')));
    const anyVoice = voices.find(v => v.lang.startsWith(langPrefix));

    const bestVoice = googleVoice || femaleVoice || anyVoice;
    if (bestVoice) {
      utterance.voice = bestVoice;
    }

    window.speechSynthesis.speak(utterance);
  };

  const textMutation = useMutation({
    mutationFn: (text: string) => processText(text, language, sessionId, undefined, country),
    onSuccess: (data) => {
      setConversation(prev => [
        ...prev,
        { role: 'farmer', text: data.transcript, language: data.language },
        { role: 'advisor', text: data.response_text, language: data.language, audio_url: data.audio_url },
      ]);
      // Use browser SpeechSynthesis (free, no API key needed)
      speakResponse(data.response_text, data.language);
      setTextInput('');
      setTimeout(scrollToBottom, 100);
    },
  });

  const startRecording = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = SPEECH_LANG_MAP[language] || 'en-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setIsRecording(false);
      // Send transcribed text to backend (no audio upload needed)
      textMutation.mutate(transcript);
    };

    recognition.onerror = () => {
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  }, [language, sessionId]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    textMutation.mutate(textInput.trim());
  };

  const handleExampleClick = (q: string) => {
    textMutation.mutate(q);
  };

  const isProcessing = isRecording || textMutation.isPending;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Phone Simulator */}
        <div className="lg:col-span-2 flex justify-center">
          <div className="w-[320px]">
            {/* Phone frame */}
            <div className="bg-gray-900 rounded-[2.5rem] p-3 shadow-2xl">
              <div className="bg-gray-800 rounded-[2rem] overflow-hidden">
                {/* Status bar */}
                <div className="bg-gray-800 px-6 py-2 flex items-center justify-between">
                  <span className="text-gray-400 text-xs">KisanVaani</span>
                  <div className="w-20 h-5 bg-gray-900 rounded-full" /> {/* notch */}
                  <span className="text-gray-400 text-xs">{language.toUpperCase()}</span>
                </div>

                {/* Screen */}
                <div className="bg-white min-h-[480px] flex flex-col">
                  {/* Conversation */}
                  <div className="flex-1 p-4 space-y-3 overflow-y-auto max-h-[360px]">
                    {conversation.length === 0 && !isCallActive && (
                      <div className="text-center py-12">
                        <Phone className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-400 text-sm">Press the green button to start</p>
                      </div>
                    )}
                    {isCallActive && conversation.length === 0 && (
                      <div className="text-center py-8">
                        <div className="relative inline-block">
                          <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
                            <Volume2 className="h-8 w-8 text-primary-600" />
                          </div>
                          <div className="absolute inset-0 w-16 h-16 rounded-full border-2 border-primary-400 animate-pulse-ring" />
                        </div>
                        <p className="text-primary-600 text-sm mt-4 font-medium">Connected</p>
                        <p className="text-gray-400 text-xs mt-1">Ask your farming question</p>
                      </div>
                    )}
                    {conversation.map((turn, i) => (
                      <div key={i} className={clsx('flex', turn.role === 'farmer' ? 'justify-end' : 'justify-start')}>
                        <div className={clsx(
                          'max-w-[85%] px-3 py-2 rounded-2xl text-sm',
                          turn.role === 'farmer'
                            ? 'bg-primary-500 text-white rounded-br-md'
                            : 'bg-gray-100 text-gray-800 rounded-bl-md'
                        )}>
                          {turn.text}
                        </div>
                      </div>
                    ))}
                    {isProcessing && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 px-4 py-2 rounded-2xl rounded-bl-md">
                          <Loader2 className="h-4 w-4 animate-spin text-primary-600" />
                        </div>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Controls */}
                  <div className="p-4 border-t border-gray-100">
                    {!isCallActive ? (
                      <button
                        onClick={() => setIsCallActive(true)}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-green-500 text-white rounded-full font-medium hover:bg-green-600 transition-colors"
                      >
                        <Phone className="h-5 w-5" />
                        Start Call
                      </button>
                    ) : (
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => { setIsCallActive(false); setConversation([]); }}
                          className="p-3 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                        >
                          <PhoneOff className="h-5 w-5" />
                        </button>
                        <button
                          onMouseDown={startRecording}
                          onMouseUp={stopRecording}
                          onTouchStart={startRecording}
                          onTouchEnd={stopRecording}
                          disabled={isProcessing}
                          className={clsx(
                            'flex-1 flex items-center justify-center gap-2 py-3 rounded-full font-medium transition-all',
                            isRecording
                              ? 'bg-red-500 text-white scale-105'
                              : 'bg-primary-500 text-white hover:bg-primary-600',
                            isProcessing && 'opacity-50'
                          )}
                        >
                          {isRecording ? (
                            <><MicOff className="h-5 w-5" /> Release to send</>
                          ) : isProcessing ? (
                            <><Loader2 className="h-5 w-5 animate-spin" /> Thinking...</>
                          ) : (
                            <><Mic className="h-5 w-5" /> Hold to speak</>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Side panel */}
        <div className="lg:col-span-3 space-y-6">
          {/* Country & Language selector */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="h-5 w-5 text-primary-600" />
              <h3 className="font-semibold text-gray-900">Country</h3>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {[
                { code: 'IN', name: 'India', flag: '🇮🇳' },
                { code: 'KE', name: 'Kenya', flag: '🇰🇪' },
                { code: 'NG', name: 'Nigeria', flag: '🇳🇬' },
                { code: 'ET', name: 'Ethiopia', flag: '🇪🇹' },
              ].map((c) => (
                <button
                  key={c.code}
                  onClick={() => setCountry(c.code)}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                    country === c.code
                      ? 'bg-primary-100 text-primary-800 border-2 border-primary-300'
                      : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                  )}
                >
                  {c.flag} {c.name}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 mb-3">
              <Globe className="h-5 w-5 text-primary-600" />
              <h3 className="font-semibold text-gray-900">Language</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={clsx(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    language === lang.code
                      ? 'bg-primary-100 text-primary-800 border-2 border-primary-300'
                      : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                  )}
                >
                  {lang.name} <span className="text-xs opacity-70">({lang.native})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Photo diagnosis */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Camera className="h-5 w-5 text-green-600" />
              <h3 className="font-semibold text-gray-900">Photo Diagnosis</h3>
            </div>
            <p className="text-sm text-gray-500 mb-3">Upload a photo of your crop problem for AI diagnosis</p>
            <input
              type="file"
              accept="image/*"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const result = await processPhoto(file, textInput || 'Please diagnose this crop problem', language, sessionId, undefined, country);
                setConversation(prev => [
                  ...prev,
                  { role: 'farmer', text: `[Photo uploaded] ${textInput || 'Please diagnose this'}`, language: result.language },
                  { role: 'advisor', text: result.response_text, language: result.language },
                ]);
                speakResponse(result.response_text, result.language);
              }}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
          </div>

          {/* Text input fallback */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Type your question (text mode)</h3>
            <form onSubmit={handleTextSubmit} className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder={language === 'hi' ? 'Apna sawaal likhein...' : 'Type your farming question...'}
                disabled={isProcessing}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
              />
              <button
                type="submit"
                disabled={isProcessing || !textInput.trim()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>

          {/* Example questions */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Try these examples</h3>
            <div className="space-y-2">
              {(EXAMPLE_QUESTIONS[language] || EXAMPLE_QUESTIONS.en).map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleExampleClick(q)}
                  disabled={isProcessing}
                  className="w-full text-left px-4 py-2.5 bg-gray-50 rounded-lg text-sm text-gray-700 hover:bg-primary-50 hover:text-primary-700 transition-colors disabled:opacity-50"
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>

          {/* Latest response detail */}
          {conversation.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3">Latest AI Response</h3>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {conversation[conversation.length - 1]?.text}
                </p>
              </div>
              <button
                onClick={() => {
                  const lastAdvisor = [...conversation].reverse().find(t => t.role === 'advisor');
                  if (lastAdvisor) speakResponse(lastAdvisor.text, lastAdvisor.language);
                }}
                className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-lg text-sm font-medium hover:bg-primary-200 transition-colors"
              >
                <Volume2 className="h-4 w-4" />
                Play Audio Response
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Hidden audio element for fallback */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
