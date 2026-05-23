import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

const queryClient = new QueryClient();

function HealthBadge() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.get("/health").then((r) => r.data),
    retry: 1,
  });

  if (isLoading) return <span className="text-muted-foreground text-sm">Checking backend…</span>;
  if (isError) return <span className="inline-flex items-center gap-1.5 text-sm text-destructive">● Backend unreachable</span>;

  return (
    <div className="flex items-center gap-4 text-sm">
      <span className="inline-flex items-center gap-1.5 text-green-600 font-medium">
        <span className="h-2 w-2 rounded-full bg-green-500 inline-block" />
        Backend online
      </span>
      <span className={data.ocr ? "text-green-600" : "text-yellow-600"}>
        OCR: {data.ocr ? "✓ ready" : "⚠ mock fallback"}
      </span>
      <span className={data.ffmpeg ? "text-green-600" : "text-yellow-600"}>
        ffmpeg: {data.ffmpeg ? "✓ ready" : "⚠ unavailable"}
      </span>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-border px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-foreground tracking-tight">
              Product Intelligence Dashboard
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">Flipkart Seller Tools</p>
          </div>
          <HealthBadge />
        </header>

        <main className="max-w-4xl mx-auto px-6 py-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-6">
            <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>

          <h2 className="text-3xl font-bold text-foreground mb-3">
            Upload a product to get started
          </h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Upload a product video or CSV feed. The system will extract product data,
            validate your listing quality, compare competitor prices, and raise alerts.
          </p>

          <div className="mt-10 flex justify-center gap-4">
            <button
              disabled
              className="px-6 py-3 rounded-lg bg-primary text-primary-foreground text-sm font-medium opacity-60 cursor-not-allowed"
            >
              Upload Video
            </button>
            <button
              disabled
              className="px-6 py-3 rounded-lg bg-secondary text-secondary-foreground text-sm font-medium opacity-60 cursor-not-allowed"
            >
              Upload CSV
            </button>
          </div>
          <p className="text-xs text-muted-foreground mt-4">Full UI coming in the next build</p>
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
