"use client";
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Point { name: string; intake: number; enrolled: number }

/** Intake vs enrolment. Enrolled bars are red where an institution/state is over its approved intake. */
export default function IntakeChart({ data }: { data: Point[] }) {
  const rows = data.map((d) => ({ name: d.name, "Approved intake": d.intake, Enrolled: d.enrolled, over: d.enrolled > d.intake }));
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Approved intake" fill="#94a3b8" isAnimationActive={false} />
          <Bar dataKey="Enrolled" fill="#1e3a8a" isAnimationActive={false}>{rows.map((r) => <Cell key={r.name} fill={r.over ? "#dc2626" : "#1e3a8a"} />)}</Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
