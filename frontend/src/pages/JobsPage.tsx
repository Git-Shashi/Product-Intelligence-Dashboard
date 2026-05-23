import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Job } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/ui/progress";

const statusVariant: Record<string, "high" | "success" | "medium" | "low" | "default" | "acknowledged"> = {
  PENDING: "default",
  RUNNING: "medium",
  COMPLETED: "success",
  FAILED: "high",
  PARTIALLY_COMPLETED: "low",
};

function JobRow({ job }: { job: Job }) {
  const isActive = job.status === "PENDING" || job.status === "RUNNING";
  const qc = useQueryClient();

  useEffect(() => {
    if (!isActive) return;
    const id = setInterval(() => qc.invalidateQueries({ queryKey: ["jobs"] }), 1500);
    return () => clearInterval(id);
  }, [isActive, qc]);

  return (
    <div className="flex items-center gap-4 py-3 border-b border-border last:border-0">
      <div className="w-10 text-sm font-mono text-muted-foreground">#{job.id}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium">{job.type.replace(/_/g, " ")}</span>
          <Badge variant={statusVariant[job.status] ?? "default"}>{job.status}</Badge>
        </div>
        {isActive && <ProgressBar value={job.progress} className="max-w-xs" />}
        {job.error && <p className="text-xs text-destructive mt-1">{job.error}</p>}
        {job.result_summary && (
          <p className="text-xs text-muted-foreground mt-1">
            {(job.result_summary as { inserted?: number; skipped?: number }).inserted !== undefined &&
              `Inserted: ${(job.result_summary as { inserted: number }).inserted}, Skipped: ${(job.result_summary as { skipped: number }).skipped}`}
          </p>
        )}
      </div>
      <div className="text-xs text-muted-foreground text-right whitespace-nowrap">
        {job.started_at ? new Date(job.started_at).toLocaleTimeString() : "—"}
      </div>
    </div>
  );
}

export function JobsPage() {
  const { jobId } = useParams<{ jobId?: string }>();
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: api.listJobs,
    refetchInterval: (query) => {
      const list = query.state.data as Job[] | undefined;
      return list?.some((j) => j.status === "PENDING" || j.status === "RUNNING") ? 1500 : false;
    },
  });

  const highlighted = jobId ? Number(jobId) : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Jobs</h1>
        <Link to="/upload" className="text-sm text-primary hover:underline">+ New upload</Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Jobs</CardTitle>
        </CardHeader>
        <CardContent className="p-0 px-6">
          {isLoading && <p className="py-6 text-sm text-muted-foreground">Loading…</p>}
          {!isLoading && jobs.length === 0 && (
            <p className="py-6 text-sm text-muted-foreground">No jobs yet. <Link to="/upload" className="text-primary hover:underline">Upload a file</Link> to create one.</p>
          )}
          {jobs.map((job) => (
            <div key={job.id} className={highlighted === job.id ? "bg-primary/5 -mx-6 px-6 rounded" : ""}>
              <JobRow job={job} />
            </div>
          ))}
        </CardContent>
      </Card>

      {highlighted && jobs.find((j) => j.id === highlighted && j.status === "COMPLETED") && (
        <div className="flex justify-end">
          <Link to="/products" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90">
            View Products →
          </Link>
        </div>
      )}
    </div>
  );
}
