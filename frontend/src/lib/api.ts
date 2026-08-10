const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Account = {
  id: string;
  kind: string;
  institution: string;
  product: string | null;
  account_number_masked: string;
};

export type Transaction = {
  id: string;
  date: string;
  narration: string;
  merchant: string | null;
  category: string | null;
  direction: string;
  amount_paise: number;
};

export type CategorySummary = {
  category: string | null;
  total_paise: number;
  count: number;
};

export type AskResponse = {
  text: string;
  route: string;
  used_llm: boolean;
  sources: string[];
};

export type UploadResult = {
  account_id: string;
  statement_ids: string[];
  transactions_parsed: number;
  transactions_stored: number;
  transactions_uncategorized: number;
};

async function apiFetch<T>(path: string, token: string | null, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export function listAccounts(token: string) {
  return apiFetch<Account[]>("/accounts", token);
}

export function listTransactions(token: string, params?: { category?: string; account_id?: string }) {
  const qs = params ? new URLSearchParams(params).toString() : "";
  return apiFetch<Transaction[]>(`/transactions${qs ? `?${qs}` : ""}`, token);
}

export function categorySummary(token: string) {
  return apiFetch<CategorySummary[]>("/transactions/summary", token);
}

export function askQuestion(token: string, question: string) {
  return apiFetch<AskResponse>("/ask", token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export async function uploadStatement(token: string, kind: "bank" | "card", file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<UploadResult>(`/statements/${kind}`, token, {
    method: "POST",
    body: formData,
  });
}

export function formatRupees(paise: number): string {
  return `₹${(paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatCategory(category: string | null): string {
  return category ? category.replace(/_/g, " ") : "uncategorized";
}
