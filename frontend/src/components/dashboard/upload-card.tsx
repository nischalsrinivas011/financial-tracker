"use client";

import { useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { uploadStatement } from "@/lib/api";

export function UploadCard({ onUploaded }: { onUploaded: () => void }) {
  const { getToken } = useAuth();
  const bankInputRef = useRef<HTMLInputElement>(null);
  const cardInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState<"bank" | "card" | null>(null);

  async function handleUpload(kind: "bank" | "card", file: File) {
    setUploading(kind);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not signed in");
      const result = await uploadStatement(token, kind, file);
      toast.success(
        `Uploaded: ${result.transactions_stored} new transaction${result.transactions_stored === 1 ? "" : "s"}` +
          (result.transactions_uncategorized > 0 ? ` (${result.transactions_uncategorized} uncategorized)` : ""),
      );
      onUploaded();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload a statement</CardTitle>
        <CardDescription>Bank or credit card PDF - parsed and categorized automatically.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-3">
        <input
          ref={bankInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleUpload("bank", e.target.files[0])}
        />
        <input
          ref={cardInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleUpload("card", e.target.files[0])}
        />
        <Button onClick={() => bankInputRef.current?.click()} disabled={uploading !== null}>
          {uploading === "bank" ? "Uploading..." : "Upload bank statement"}
        </Button>
        <Button
          variant="outline"
          onClick={() => cardInputRef.current?.click()}
          disabled={uploading !== null}
        >
          {uploading === "card" ? "Uploading..." : "Upload card statement"}
        </Button>
      </CardContent>
    </Card>
  );
}
