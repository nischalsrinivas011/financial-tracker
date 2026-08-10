"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

type DemoQA = { question: string; answer: string; route: string };

export function DemoAskChat({ qa }: { qa: DemoQA[] }) {
  const [selected, setSelected] = useState<DemoQA | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask about your finances</CardTitle>
        <CardDescription>Sample questions - answered from arjun_salaried&apos;s data, no live typing in demo mode.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {qa.map((entry) => (
            <Button
              key={entry.question}
              variant={selected?.question === entry.question ? "default" : "outline"}
              size="sm"
              onClick={() => setSelected(entry)}
            >
              {entry.question}
            </Button>
          ))}
        </div>
        {selected && (
          <ScrollArea className="max-h-64 rounded-md border p-3">
            <p className="text-sm font-medium">{selected.question}</p>
            <p className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">{selected.answer}</p>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
