import type { HTMLAttributes } from "react";
export function Badge({ className = "", ...props }: HTMLAttributes<HTMLSpanElement>) { return <span className={`rounded bg-slate-100 px-2 py-1 text-xs ${className}`} {...props} />; }
