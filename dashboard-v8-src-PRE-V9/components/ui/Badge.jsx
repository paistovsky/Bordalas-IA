import { cn } from "../../lib/utils";

export function Badge({ children, tone = "default", className }) {
  return <span className={cn("badge", `badge-${tone}`, className)}>{children}</span>;
}
