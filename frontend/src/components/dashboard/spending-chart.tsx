"use client";

import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { formatCategory, formatRupees, type CategorySummary } from "@/lib/api";

const chartConfig = {
  total: { label: "Spent", color: "var(--chart-1)" },
} satisfies ChartConfig;

export function SpendingChart({ summary }: { summary: CategorySummary[] }) {
  const data = [...summary]
    .sort((a, b) => b.total_paise - a.total_paise)
    .slice(0, 8)
    .map((row) => ({
      category: formatCategory(row.category),
      total: row.total_paise / 100,
    }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending by category</CardTitle>
        <CardDescription>Top {data.length} categories, debits only.</CardDescription>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No spending data yet.</p>
        ) : (
          <ChartContainer config={chartConfig} className="h-64 w-full">
            <BarChart data={data} margin={{ left: 8, right: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="category"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                interval={0}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value) => formatRupees(Number(value) * 100)}
                  />
                }
              />
              <Bar dataKey="total" fill="var(--color-total)" radius={4} />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
