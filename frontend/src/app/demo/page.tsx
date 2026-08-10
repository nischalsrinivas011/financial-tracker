import Link from "next/link";
import { AccountsList } from "@/components/dashboard/accounts-list";
import { SpendingChart } from "@/components/dashboard/spending-chart";
import { TransactionsTable } from "@/components/dashboard/transactions-table";
import { DemoAskChat } from "@/components/dashboard/demo-ask-chat";
import { buttonVariants } from "@/components/ui/button";
import demoData from "@/data/demo-data.json";
import type { Account, Transaction, CategorySummary } from "@/lib/api";

export default function DemoPage() {
  const accounts = demoData.accounts as Account[];
  const transactions = demoData.transactions as Transaction[];
  const summary = demoData.summary as CategorySummary[];

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Sample dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Synthetic data for arjun_salaried, a Bengaluru salaried persona. No account needed.
          </p>
        </div>
        <Link href="/" className={buttonVariants({ variant: "outline" })}>
          Back home
        </Link>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <AccountsList accounts={accounts} />
        <SpendingChart summary={summary} />
      </div>
      <DemoAskChat qa={demoData.qa} />
      <TransactionsTable transactions={transactions} />
    </div>
  );
}
