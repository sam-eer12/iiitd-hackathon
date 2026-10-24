"use client";

import { useAuth } from "@/lib/auth-context";
import { useEffect, useState } from "react";
import { Icon } from "./icon";

export function AuthProfile({ compact = false }: { compact?: boolean }) {
  const { user, loading, signInWithGoogle, logOut } = useAuth();
  const [signingIn, setSigningIn] = useState(false);
  const [signInError, setSignInError] = useState("");

  useEffect(() => {
    if (!signInError) return;
    const timer = setTimeout(() => setSignInError(""), 7000);
    return () => clearTimeout(timer);
  }, [signInError]);

  const handleLogin = async () => {
    try {
      setSignInError("");
      setSigningIn(true);
      await signInWithGoogle();
    } catch (err: unknown) {
      console.error("Sign-in failed:", err);
      setSignInError(signInMessage(err));
    } finally {
      setSigningIn(false);
    }
  };

  if (loading) {
    return (
      <div className={`auth-profile-loading ${compact ? "compact" : ""}`}>
        <span className="auth-spinner" />
      </div>
    );
  }

  if (!user) {
    return (
      <span className="auth-signin">
        <button
          onClick={handleLogin}
          disabled={signingIn}
          aria-busy={signingIn}
          className={`button button-small button-google ${compact ? "button-compact" : ""}`}
          title="Sign in with Google"
          aria-label="Sign in with Google"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            className="google-icon"
            aria-hidden="true"
          >
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          {!compact && (
            <span>{signingIn ? "Connecting..." : "Sign in with Google"}</span>
          )}
        </button>
        {signInError && (
          <span className="auth-error" role="alert">
            {signInError}
          </span>
        )}
      </span>
    );
  }

  const initials = (user.displayName || user.email || "U")
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className={`auth-user-badge ${compact ? "compact" : ""}`}>
      {user.photoURL ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={user.photoURL}
          alt={user.displayName || "User avatar"}
          className="user-avatar-img"
          referrerPolicy="no-referrer"
        />
      ) : (
        <span className="user-avatar-initials">{initials}</span>
      )}
      {!compact && (
        <div className="auth-user-info">
          <strong>{user.displayName || "Google User"}</strong>
          <small>{user.email}</small>
        </div>
      )}
      <button
        onClick={logOut}
        className="button-icon-subtle"
        title="Sign out"
        aria-label="Sign out"
      >
        <Icon name="close" size={14} />
      </button>
    </div>
  );
}

/* A short, specific message for failed Google sign-in. Closing the pop-up
   on purpose is not treated as an error. */
function signInMessage(error: unknown) {
  const code =
    typeof error === "object" && error && "code" in error
      ? String((error as { code: unknown }).code)
      : "";
  if (
    code === "auth/popup-closed-by-user" ||
    code === "auth/cancelled-popup-request"
  )
    return "";
  if (code === "auth/popup-blocked")
    return "Your browser blocked the sign-in window. Allow pop-ups for this site and try again.";
  if (code === "auth/network-request-failed")
    return "Sign-in could not reach Google. Check your connection and try again.";
  if (code === "auth/unauthorized-domain")
    return "Sign-in is not enabled for this address. Use the configured domain.";
  return "Sign-in did not complete. Please try again.";
}
