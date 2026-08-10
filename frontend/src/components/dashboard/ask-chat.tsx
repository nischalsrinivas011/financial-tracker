"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { askQuestion } from "@/lib/api";

type ChatEntry = { question: string; answer: string; route: string };

export function AskChat() {
  const { getToken } = useAuth();
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ChatEntry[]>([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || asking) return;
    setAsking(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not signed in");
      const result = await askQuestion(token, q);
      setHistory((prev) => [...prev, { question: q, answer: result.text, route: result.route }]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get an answer");
    } finally {
      setAsking(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask about your finances</CardTitle>
        <CardDescription>e.g. &quot;How much did I spend on food delivery in March?&quot;</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {history.length > 0 && (
          <ScrollArea className="h-64 rounded-md border p-3">
            <div className="space-y-4">
              {history.map((entry, i) => (
                <div key={i} className="space-y-1">
                  <p className="text-sm font-medium">{entry.question}</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{entry.answer}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
        <form onSubmit={handleAsk} className="flex gap-2">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your spending"
            disabled={asking}
          />
          <Button type="submit" disabled={asking || !question.trim()}>
            {asking ? "Asking..." : "Ask"}
          </Button>
        </form>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}
