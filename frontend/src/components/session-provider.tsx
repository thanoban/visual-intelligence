"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { ApiError, fetchSession } from "@/lib/api";
import type { AuthSessionResponse } from "@/lib/types";

const SESSION_STORAGE_KEY = "visualsprint.session";

interface SessionContextValue {
  hydrated: boolean;
  session: AuthSessionResponse | null;
  saveSession: (session: AuthSessionResponse) => void;
  clearSession: () => void;
  refreshSession: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [hydrated, setHydrated] = useState(false);
  const [session, setSession] = useState<AuthSessionResponse | null>(null);

  const clearSession = useCallback(() => {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    setSession(null);
  }, []);

  const saveSession = useCallback((nextSession: AuthSessionResponse) => {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
  }, []);

  const refreshSession = useCallback(async () => {
    const currentToken = session?.access_token;
    if (!currentToken) {
      clearSession();
      return;
    }

    try {
      const refreshedSession = await fetchSession(currentToken);
      saveSession({ ...refreshedSession, access_token: currentToken });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearSession();
        return;
      }
      throw error;
    }
  }, [clearSession, saveSession, session?.access_token]);

  useEffect(() => {
    const rawSession = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!rawSession) {
      setHydrated(true);
      return;
    }

    try {
      const parsedSession = JSON.parse(rawSession) as AuthSessionResponse;
      setSession(parsedSession);
      void fetchSession(parsedSession.access_token)
        .then((refreshedSession) => {
          saveSession({ ...refreshedSession, access_token: parsedSession.access_token });
        })
        .catch((error) => {
          if (error instanceof ApiError && error.status === 401) {
            clearSession();
            return;
          }
          throw error;
        })
        .finally(() => {
          setHydrated(true);
        });
      return;
    } catch {
      clearSession();
    }

    setHydrated(true);
  }, [clearSession, saveSession]);

  const value = useMemo<SessionContextValue>(
    () => ({
      hydrated,
      session,
      saveSession,
      clearSession,
      refreshSession,
    }),
    [clearSession, hydrated, refreshSession, saveSession, session],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
}
