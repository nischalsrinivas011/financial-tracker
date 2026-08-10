"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { redirect } from "next/navigation";
import { UploadCard } from "@/components/dashboard/upload-card";
import { AccountsList } from "@/components/dashboard/accounts-list";
import { SpendingChart } from "@/components/dashboard/spending-chart";
import { TransactionsTable } from "@/components/dashboard/transactions-table";
import { AskChat } from "@/components/dashboard/ask-chat";
import {
  listAccounts,
  listTransactions,
  categorySummary,
  type Account,
  type Transaction,
  type CategorySummary,
} from "@/lib/api";

export default function DashboardPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<CategorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        const token = await getToken();
        if (!token) throw new Error("Not signed in");
        const [accountsData, transactionsData, summaryData] = await Promise.all([
          listAccounts(token),
          listTransactions(token),
          categorySummary(token),
        ]);
        if (cancelled) return;
        setAccounts(accountsData);
        setTransactions(transactionsData);
        setSummary(summaryData);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, getToken, refreshKey]);

  if (isLoaded && !isSignedIn) {
    redirect("/");
  }

  if (!isLoaded || loading) {
    return (
      <div className="p-6 text-sm text-muted-foreground">Loading dashboard...</div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <UploadCard onUploaded={() => setRefreshKey((k) => k + 1)} />
      <div className="grid gap-6 md:grid-cols-2">
        <AccountsList accounts={accounts} />
        <SpendingChart summary={summary} />
      </div>
      <AskChat />
      <TransactionsTable transactions={transactions} />
    </div>
  );
}
