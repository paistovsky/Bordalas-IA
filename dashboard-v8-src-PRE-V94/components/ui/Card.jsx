import { cn } from "../../lib/utils";

export function Card({ className, children }) {
  return <section className={cn("card", className)}>{children}</section>;
}

export function CardHeader({ className, children }) {
  return <header className={cn("card-header", className)}>{children}</header>;
}

export function CardTitle({ className, children }) {
  return <h2 className={cn("card-title", className)}>{children}</h2>;
}
