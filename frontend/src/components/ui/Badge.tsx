import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "danger" | "warning";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  const variants: Record<string, string> = {
    default: "bg-surface-light text-text",
    success: "bg-green-900/50 text-success border-green-700",
    danger: "bg-red-900/50 text-danger border-red-700",
    warning: "bg-yellow-900/50 text-warning border-yellow-700",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
