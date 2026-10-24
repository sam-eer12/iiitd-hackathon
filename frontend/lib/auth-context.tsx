"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User, onAuthStateChanged } from "firebase/auth";
import {
  auth,
  signInWithGoogle as fbSignIn,
  logOut as fbSignOut,
} from "@/lib/firebase";
import { upsertUser } from "@/lib/dataconnect";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<User>;
  logOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signInWithGoogle: async () => {
    throw new Error("AuthProvider not mounted");
  },
  logOut: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      setLoading(false);

      if (currentUser && currentUser.email) {
        try {
          // Sync authenticated user to PostgreSQL via Firebase Data Connect
          await upsertUser({
            email: currentUser.email,
            displayName: currentUser.displayName || null,
            photoUrl: currentUser.photoURL || null,
          });
        } catch {
          // If offline/emulator not connected, don't block user session
        }
      }
    });

    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    const loggedUser = await fbSignIn();
    return loggedUser;
  };

  const logOut = async () => {
    await fbSignOut();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, logOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
