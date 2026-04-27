"use client";

import { useDispatch } from "react-redux";

import styles from "./HomePage.module.scss";
import { AuthPanel } from "@/src/fsd/features/auth/ui/AuthPanel";
import { FileBrowser } from "@/src/fsd/widgets/file-browser/ui/FileBrowser";
import { Button } from "@/src/fsd/shared/ui/Button/Button";
import { Spinner } from "@/src/fsd/shared/ui/Spinner/Spinner";
import { useSessionBootstrap } from "@/src/fsd/processes/session/model/useSessionBootstrap";
import { useLogoutMutation } from "@/src/fsd/features/auth/api/authApi";
import { clearAccessToken } from "@/src/fsd/shared/lib/authToken";
import { api } from "@/src/fsd/shared/api/api";

export const HomePage = () => {
  const dispatch = useDispatch();
  const { isLoading, isAuthenticated, user } = useSessionBootstrap();
  const [logout, logoutState] = useLogoutMutation();

  const handleLogout = async () => {
    try {
      await logout().unwrap();
    } catch {
      // ignore logout errors
    } finally {
      clearAccessToken();
      dispatch(api.util.resetApiState());
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logo}>DFS</div>
          <div>
            <p className={styles.tagline}>Distributed storage console</p>
            <p className={styles.subtitle}>Secure, replicated, fast.</p>
          </div>
        </div>
        <div className={styles.headerActions}>
          {isAuthenticated ? (
            <Button
              type="button"
              variant="outline"
              onClick={handleLogout}
              disabled={logoutState.isLoading}
            >
              {logoutState.isLoading ? "Signing out..." : "Sign out"}
            </Button>
          ) : null}
        </div>
      </header>

      <main className={styles.grid}>
        <section className={styles.hero}>
          <div className={styles.heroCard}>
            <p className={styles.heroLabel}>Cluster overview</p>
            <h1>Resilient files, steady control.</h1>
            <p>
              Manage your personal namespace, upload new assets, and download
              verified chunks from the DFS nodes. The console keeps your session
              alive with rotating tokens and secure cookies.
            </p>
            <div className={styles.metrics}>
              <div>
                <span>JWT</span>
                <strong>Access + refresh</strong>
              </div>
              <div>
                <span>Download</span>
                <strong>Signed chunk URLs</strong>
              </div>
              <div>
                <span>Replication</span>
                <strong>Quorum aware</strong>
              </div>
            </div>
          </div>
          <div className={styles.heroGlow} />
        </section>

        <section className={styles.panel}>
          {isLoading ? (
            <div className={styles.state}>
              <Spinner label="Checking session" />
            </div>
          ) : isAuthenticated ? (
            <div className={styles.session}>
              <div className={styles.userCard}>
                <div>
                  <p className={styles.userLabel}>Signed in as</p>
                  <h2>{user?.username}</h2>
                  <span className={styles.userMeta}>{user?.email}</span>
                </div>
                <div className={styles.roleBadge}>
                  {user?.role || "member"}
                </div>
              </div>
              <FileBrowser />
            </div>
          ) : (
            <AuthPanel />
          )}
        </section>
      </main>
    </div>
  );
};
