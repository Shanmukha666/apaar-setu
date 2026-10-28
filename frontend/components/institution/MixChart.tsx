"use client";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { InstitutionSummary } from "@/lib/types";

const COLORS = ["#1e3a8a", "#f59e0b", "#0d9488", "#7c3aed", "#db2777"];

export default function MixChart({ mix }: { mix: InstitutionSummary["category_mix"] }) {
  const data = [
    { name: "Regular", value: mix.regular }, { name: "Supernumerary", value: mix.supernumerary },
    { name: "NRI", value: mix.nri }, { name: "OCI", value: mix.oci }, { name: "Foreign national", value: mix.fn },
  ];
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 24, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={110} />
          <Tooltip />
          <Bar dataKey="value" name="Students" isAnimationActive={false}>
            {data.map((d, i) => <Cell key={d.name} fill={COLORS[i]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
