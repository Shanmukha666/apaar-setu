"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { homeFor, useAuth } from "@/lib/auth";
import { Loading } from "@/components/common";

/** The root path just forwards to the right place for the signed-in role. */
export default function Home() {
  const router = useRouter();
  const { user, ready } = useAuth();
  useEffect(() => {
    if (ready) router.replace(user ? homeFor(user.role) : "/login");
  }, [ready, user, router]);
  return <Loading />;
}
