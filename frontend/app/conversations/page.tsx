"use client";

import { useEffect, useState } from "react";
import { conversationAPI, type Conversation } from "@/lib/api";
import { formatTime, formatRelativeTime } from "@/lib/utils";
import { MessageSquare, ArrowUpRight, ArrowDownLeft, Phone } from "lucide-react";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    conversationAPI.list(100).then(setConversations).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Group by phone number
  const grouped = conversations.reduce<Record<string, Conversation[]>>((acc, conv) => {
    const key = conv.user_phone;
    if (!acc[key]) acc[key] = [];
    acc[key].push(conv);
    return acc;
  }, {});

  const [selectedPhone, setSelectedPhone] = useState<string | null>(null);
  const selectedThread = selectedPhone ? grouped[selectedPhone] || [] : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Conversations</h1>
        <p className="text-sm text-muted-foreground mt-1">WhatsApp message history and workflow results</p>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading conversations...</p>
      ) : conversations.length === 0 ? (
        <div className="rounded-lg border border-border bg-card py-16 text-center">
          <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">No conversations yet</p>
          <p className="text-xs text-muted-foreground mt-1">Send a simulated WhatsApp message from the dashboard</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contact List */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-2">
            <h3 className="text-sm font-medium mb-3">Contacts</h3>
            {Object.entries(grouped).map(([phone, msgs]) => (
              <button key={phone} onClick={() => setSelectedPhone(phone)}
                className={`w-full text-left p-3 rounded-md border transition-colors ${
                  selectedPhone === phone ? "border-primary bg-primary/5" : "border-border hover:border-primary/30"
                }`}>
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-sm font-medium">{phone}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 truncate">{msgs[msgs.length - 1]?.message || ""}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{msgs.length} messages</p>
              </button>
            ))}
          </div>

          {/* Thread */}
          <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
            {selectedPhone ? (
              <>
                <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-emerald-400" />
                  {selectedPhone}
                </h3>
                <div className="space-y-3 max-h-[500px] overflow-y-auto">
                  {selectedThread.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map((msg) => (
                    <div key={msg.id} className={`flex ${msg.direction === "outbound" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] rounded-lg px-4 py-3 ${
                        msg.direction === "outbound"
                          ? "bg-primary/15 border border-primary/20"
                          : "bg-accent border border-border"
                      }`}>
                        <div className="flex items-center gap-2 mb-1">
                          {msg.direction === "inbound" ? (
                            <ArrowDownLeft className="w-3 h-3 text-blue-400" />
                          ) : (
                            <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                          )}
                          <span className="text-[10px] text-muted-foreground">
                            {msg.direction === "inbound" ? "Customer" : "AI Response"}
                          </span>
                          <span className="text-[10px] text-muted-foreground">
                            {msg.created_at ? formatTime(msg.created_at) : ""}
                          </span>
                        </div>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{msg.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-16 text-center">
                <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">Select a contact to view conversation</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
