"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useSession } from "@/components/session-provider";

export default function HomePage() {
  const router = useRouter();
  const { hydrated, session } = useSession();

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    router.replace(session ? "/meetings" : "/sign-in");
  }, [hydrated, router, session]);

  return <main className="loading-page">Opening workspace...</main>;
}
