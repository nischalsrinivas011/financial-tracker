import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Account } from "@/lib/api";

export function AccountsList({ accounts }: { accounts: Account[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Accounts</CardTitle>
        <CardDescription>{accounts.length} linked</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {accounts.length === 0 && (
          <p className="text-sm text-muted-foreground">No accounts yet. Upload a statement to get started.</p>
        )}
        {accounts.map((account) => (
          <div key={account.id} className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">{account.institution}</p>
              <p className="text-xs text-muted-foreground">
                {account.product ?? account.kind} - {account.account_number_masked}
              </p>
            </div>
            <Badge variant="secondary" className="capitalize">
              {account.kind}
            </Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
