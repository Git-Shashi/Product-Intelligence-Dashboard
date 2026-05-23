import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const sevVariant = { HIGH: "high", MEDIUM: "medium", LOW: "low" } as const;

export function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const qc = useQueryClient();

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["alerts", severityFilter, statusFilter],
    queryFn: () => api.listAlerts({
      ...(severityFilter ? { severity: severityFilter } : {}),
      ...(statusFilter ? { status: statusFilter } : {}),
    }),
  });

  const ackMutation = useMutation({
    mutationFn: (id: number) => api.acknowledgeAlert(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Alerts</h1>

      <div className="flex gap-3">
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
          className="border border-border rounded-lg px-3 py-2 text-sm focus:outline-none">
          <option value="">All severities</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-border rounded-lg px-3 py-2 text-sm focus:outline-none">
          <option value="">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="ACKNOWLEDGED">Acknowledged</option>
        </select>
      </div>

      <Card>
        <CardHeader><CardTitle>{alerts.length} alert{alerts.length !== 1 ? "s" : ""}</CardTitle></CardHeader>
        <CardContent className="p-0 px-6 pb-2">
          {isLoading && <p className="py-4 text-sm text-muted-foreground">Loading…</p>}
          {!isLoading && alerts.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">No alerts found.</p>
          )}
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-start gap-3 py-3 border-b border-border last:border-0">
              <Badge variant={sevVariant[alert.severity]} className="mt-0.5 shrink-0">{alert.severity}</Badge>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{alert.message}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-muted-foreground">{new Date(alert.created_at).toLocaleString()}</span>
                  {alert.product_id && (
                    <Link to={`/products`} className="text-xs text-primary hover:underline">View product</Link>
                  )}
                </div>
              </div>
              {alert.status === "OPEN" ? (
                <button
                  onClick={() => ackMutation.mutate(alert.id)}
                  disabled={ackMutation.isPending}
                  className="shrink-0 text-xs px-2.5 py-1 border border-border rounded-md hover:bg-gray-50 disabled:opacity-50"
                >
                  Acknowledge
                </button>
              ) : (
                <Badge variant="acknowledged">Acknowledged</Badge>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
