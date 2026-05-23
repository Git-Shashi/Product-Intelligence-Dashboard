import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <CardContent className="pt-5">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
        <p className="text-3xl font-bold text-foreground mt-1">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["quality-summary"], queryFn: api.qualitySummary });

  const refreshMutation = useMutation({
    mutationFn: api.refreshPrices,
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      navigate(`/jobs/${result.job_id}`);
    },
  });

  if (isLoading) return <p className="text-muted-foreground">Loading dashboard…</p>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Quality Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 disabled:opacity-50"
          >
            {refreshMutation.isPending ? "Refreshing…" : "↻ Refresh Prices"}
          </button>
          <Link to="/upload" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90">
            + Upload
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Products" value={data.total_products} />
        <StatCard label="Avg Quality Score" value={`${data.avg_quality_score}%`} />
        <StatCard label="Weak Listings" value={data.weak_listings} sub="score < 60" />
        <StatCard label="Open Issues" value={data.issue_counts.HIGH + data.issue_counts.MEDIUM + data.issue_counts.LOW} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Issues by Severity</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(["HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
              <div key={sev} className="flex items-center justify-between">
                <Badge variant={sev.toLowerCase() as "high" | "medium" | "low"}>{sev}</Badge>
                <div className="flex items-center gap-3 flex-1 ml-4">
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${sev === "HIGH" ? "bg-red-500" : sev === "MEDIUM" ? "bg-yellow-500" : "bg-blue-500"}`}
                      style={{
                        width: `${data.issue_counts.HIGH + data.issue_counts.MEDIUM + data.issue_counts.LOW > 0
                          ? (data.issue_counts[sev] / (data.issue_counts.HIGH + data.issue_counts.MEDIUM + data.issue_counts.LOW)) * 100
                          : 0}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium w-6 text-right">{data.issue_counts[sev]}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Listing Health</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Missing images", value: data.missing_image_count, sev: "high" as const },
              { label: "Invalid prices", value: data.invalid_price_count, sev: "high" as const },
              { label: "Out of stock", value: data.out_of_stock_count, sev: "low" as const },
            ].map(({ label, value, sev }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{label}</span>
                <Badge variant={value > 0 ? sev : "success"}>{value}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <Link to="/products" className="text-sm text-primary hover:underline">View all products →</Link>
      </div>
    </div>
  );
}
