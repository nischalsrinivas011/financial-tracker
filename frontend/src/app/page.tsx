import Link from "next/link";
import { Show } from "@clerk/nextjs";
import { buttonVariants } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 px-6 text-center">
      <h1 className="text-3xl font-bold">Financial Tracker</h1>
      <p className="text-gray-500 max-w-md">
        Upload your statements, see your spending categorized automatically, and ask questions
        about your finances in plain English.
      </p>
      <Show when="signed-out">
        <p className="text-sm text-gray-400">Sign in above to get started.</p>
      </Show>
      <Show when="signed-in">
        <Link href="/dashboard" className={buttonVariants({ variant: "default" })}>
          Go to dashboard
        </Link>
      </Show>
      <Link href="/demo" className={buttonVariants({ variant: "outline" })}>
        Try with sample data
      </Link>
    </div>
  );
}
