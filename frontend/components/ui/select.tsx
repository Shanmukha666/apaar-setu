import type { SelectHTMLAttributes } from "react";
export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) { return <select className="rounded border p-2" {...props} />; }
