"use client";
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ProgrammeRow } from "@/lib/types";

/** Approved intake vs regular enrolment per programme and year. Over-intake bars turn red. */
export default function ProgrammeChart({ programmes }: { programmes: ProgrammeRow[] }) {
  const data = programmes.map((p) => ({
    name: `${p.code.split("-")[1]} ${p.academic_year}`,
    "Approved intake": p.approved_intake,
    "Enrolled (regular)": p.enrolled_regular,
    over: p.enrolled_regular > p.approved_intake,
  }));
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Approved intake" fill="#94a3b8" isAnimationActive={false} />
          <Bar dataKey="Enrolled (regular)" fill="#1e3a8a" isAnimationActive={false}>
            {data.map((d) => <Cell key={d.name} fill={d.over ? "#dc2626" : "#1e3a8a"} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
