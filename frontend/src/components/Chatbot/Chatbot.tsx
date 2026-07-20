"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useThemeStore } from "@/store/theme-store";
import { useTranslation } from "@/i18n";
import { chatbotApi, type ChatMessage } from "@/lib/api";
import { Mic, Send, X, Bot, User, Sparkles, Loader2, Volume2, VolumeX } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Utility para mergear classes de Tailwind
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { language } = useThemeStore();
  const t = useTranslation();
  const recognitionRef = useRef<any>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Mensaje de bienvenida
  const welcomeMessage: ChatMessage = {
    role: "assistant",
    content: language === "es" 
      ? "¡Hola! Soy VineGuard AI, tu asistente virtual especializado en el diagnóstico de enfermedades de las uvas. ¿En qué puedo ayudarte hoy?"
      : language === "en"
      ? "Hello! I'm VineGuard AI, your virtual assistant specialized in grape disease diagnosis. How can I help you today?"
      : "Olá! Sou o VineGuard AI, seu assistente virtual especializado no diagnóstico de doenças da videira. Em que posso ajudar você hoje?"
  };

  // Scroll automático al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Limpieza: detener la voz al desmontar el componente
  useEffect(() => {
    return () => {
      stopSpeaking();
    };
  }, []);

  // Cuando se abre el chatbot por primera vez, agregar el mensaje de bienvenida
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([welcomeMessage]);
    }
  }, [isOpen, language]); // Volver a establecer el mensaje de bienvenida si cambia el idioma

  // Inicializar reconocimiento de voz
  useEffect(() => {
    if (typeof window !== "undefined" && ("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = language === "es" ? "es-ES" : language === "en" ? "en-US" : "pt-BR";

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, [language]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: inputValue.trim() };
    const currentMessages = [...messages, userMessage];
    setMessages(currentMessages);
    setInputValue("");
    setIsLoading(true);

    try {
      // Simular una pequeña demora para que se sienta natural, pero no excesivo
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const response = await chatbotApi.sendMessage({
        messages: currentMessages,
        language,
      });

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      // Hablar automáticamente la respuesta
      speak(assistantMessage.content);
    } catch (error) {
      console.error("Error en el chatbot:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: t("chatbot.error"),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const speak = (text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      return;
    }

    // Cancelar cualquier habla anterior
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === "es" ? "es-ES" : language === "en" ? "en-US" : "pt-BR";
    utterance.rate = 1;
    utterance.pitch = 1;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert(t("chatbot.voice.notSupported"));
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Botón de apertura - FANCY */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="w-16 h-16 rounded-full shadow-2xl bg-gradient-to-br from-green-600 to-green-800 hover:from-green-700 hover:to-green-900 text-white transition-all duration-300 hover:scale-110 active:scale-95 group"
        >
          <Bot size={32} className="group-hover:rotate-12 transition-transform duration-300" />
          <div className="absolute -top-1 -right-1 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center animate-bounce">
            <Sparkles size={14} className="text-white" />
          </div>
        </Button>
      )}

      {/* Ventana del chatbot - FANCY */}
      {isOpen && (
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl w-[400px] max-w-[90vw] h-[600px] flex flex-col overflow-hidden border border-gray-100 dark:border-gray-700">
          {/* Header - FANCY */}
          <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-700 bg-gradient-to-r from-green-600 to-green-800 text-white">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                <Bot size={28} className="text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold">{t("chatbot.title")}</h3>
                <p className="text-xs opacity-80 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-300 rounded-full animate-pulse" />
                  {language === "es" ? "En línea" : language === "en" ? "Online" : "Online"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isSpeaking && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={stopSpeaking}
                  className="text-white hover:bg-white/20 rounded-full transition-all"
                  title={language === "es" ? "Detener habla" : language === "en" ? "Stop speaking" : "Parar de falar"}
                >
                  <VolumeX size={20} />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  stopSpeaking();
                  setIsOpen(false);
                }}
                className="text-white hover:bg-white/20 rounded-full transition-all"
              >
                <X size={24} />
              </Button>
            </div>
          </div>

          {/* Messages - FANCY */}
          <div className="flex-1 overflow-y-auto p-4 space-y-5 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 items-end ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                {/* Avatar */}
                <div className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm",
                  msg.role === "user" 
                    ? "bg-gradient-to-br from-blue-500 to-blue-700"
                    : "bg-gradient-to-br from-green-500 to-green-700"
                )}>
                  {msg.role === "user" ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
                </div>
                
                {/* Mensaje */}
                <div
                  className={cn(
                    "max-w-[75%] px-5 py-3 rounded-2xl shadow-sm whitespace-pre-line",
                    msg.role === "user"
                      ? "bg-gradient-to-br from-blue-600 to-blue-800 text-white rounded-br-sm"
                      : "bg-white dark:bg-gray-700 text-gray-800 dark:text-white rounded-bl-sm border border-gray-200 dark:border-gray-600"
                  )}
                >
                  <div className="flex items-start gap-2">
                    <p className="text-sm leading-relaxed flex-1">{msg.content}</p>
                    {msg.role === "assistant" && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => speak(msg.content)}
                        className="text-gray-500 hover:text-green-600 dark:text-gray-400 h-6 w-6 p-0"
                      >
                        <Volume2 size={16} />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Estado de carga - FANCY */}
            {isLoading && (
              <div className="flex gap-3 items-end">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-green-700 flex items-center justify-center flex-shrink-0 shadow-sm">
                  <Bot size={20} className="text-white" />
                </div>
                <div className="bg-white dark:bg-gray-700 text-gray-800 dark:text-white px-5 py-3 rounded-2xl rounded-bl-sm border border-gray-200 dark:border-gray-600 shadow-sm flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin text-green-600" />
                  <p className="text-sm">{t("common.loading")}</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input - FANCY */}
          <div className="p-5 border-t border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleListening}
                className={cn(
                  "rounded-full transition-all duration-200",
                  isListening 
                    ? "bg-red-100 text-red-600 animate-pulse" 
                    : "text-gray-500 hover:text-green-600 hover:bg-green-50 dark:text-gray-400"
                )}
                title={isListening ? t("chatbot.voice.stop") : t("chatbot.voice.start")}
              >
                <Mic size={22} />
              </Button>
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t("chatbot.placeholder")}
                className="flex-1 rounded-full border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:ring-green-500 focus:border-green-500"
                disabled={isLoading}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="w-12 h-12 rounded-full bg-gradient-to-br from-green-600 to-green-800 hover:from-green-700 hover:to-green-900 text-white shadow-lg transition-all duration-300 hover:scale-105 active:scale-95"
              >
                <Send size={20} />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
