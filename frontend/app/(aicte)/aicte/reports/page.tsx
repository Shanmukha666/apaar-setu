"use client";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { PageHeader, Panel } from "@/components/common";

export default function ReportsPage() {
  return (
    <RoleGuard roles={["aicte_officer"]}>
      <AppShell>
        <PageHeader title="Reports" subtitle="CSV export is planned for the full version." />
        <Panel title="Planned reports">
          <ul className="list-disc space-y-1 pl-5 text-sm">
            <li>Enrolment by institution, programme and academic year</li>
            <li>Excess-intake register for approval and accreditation reviews</li>
            <li>Cross-institution duplicate enrolment register</li>
            <li>Institution data-quality and risk scorecards</li>
          </ul>
        </Panel>
      </AppShell>
    </RoleGuard>
  );
}
