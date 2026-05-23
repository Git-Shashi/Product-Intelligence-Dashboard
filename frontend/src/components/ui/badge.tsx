import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "high" | "medium" | "low" | "open" | "acknowledged" | "default" | "success";
  className?: string;
}

const variantClass: Record<string, string> = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-blue-100 text-blue-700 border-blue-200",
  open: "bg-red-100 text-red-700 border-red-200",
  acknowledged: "bg-gray-100 text-gray-600 border-gray-200",
  success: "bg-green-100 text-green-700 border-green-200",
  default: "bg-gray-100 text-gray-700 border-gray-200",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        variantClass[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
