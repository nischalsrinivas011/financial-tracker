import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCategory, formatRupees, type Transaction } from "@/lib/api";

export function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent transactions</CardTitle>
        <CardDescription>{transactions.length} shown</CardDescription>
      </CardHeader>
      <CardContent>
        {transactions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No transactions yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="whitespace-nowrap text-muted-foreground">{t.date}</TableCell>
                  <TableCell>{t.merchant ?? t.narration}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {formatCategory(t.category)}
                    </Badge>
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono ${t.direction === "credit" ? "text-green-600" : ""}`}
                  >
                    {t.direction === "credit" ? "+" : "-"}
                    {formatRupees(t.amount_paise)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
