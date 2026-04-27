"use client";

import { useState, type FormEvent } from "react";

import styles from "./AuthPanel.module.scss";
import { Input } from "@/src/fsd/shared/ui/Input/Input";
import { Button } from "@/src/fsd/shared/ui/Button/Button";
import { Spinner } from "@/src/fsd/shared/ui/Spinner/Spinner";
import { getErrorMessage } from "@/src/fsd/shared/lib/apiError";
import { useLoginMutation, useRegisterMutation } from "../api/authApi";

const initialLogin = { username: "", password: "" };
const initialRegister = { username: "", email: "", password: "" };

export const AuthPanel = () => {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [notice, setNotice] = useState("");
  const [loginForm, setLoginForm] = useState(initialLogin);
  const [registerForm, setRegisterForm] = useState(initialRegister);

  const [login, loginState] = useLoginMutation();
  const [register, registerState] = useRegisterMutation();

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice("");

    try {
      await login(loginForm).unwrap();
      setLoginForm(initialLogin);
    } catch {
      // handled by UI state
    }
  };

  const handleRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice("");

    try {
      await register(registerForm).unwrap();
      setRegisterForm(initialRegister);
      setMode("login");
      setNotice("Account created. Please log in.");
    } catch {
      // handled by UI state
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${mode === "login" ? styles.active : ""}`}
          onClick={() => setMode("login")}
        >
          Sign in
        </button>
        <button
          type="button"
          className={`${styles.tab} ${mode === "register" ? styles.active : ""}`}
          onClick={() => setMode("register")}
        >
          Create account
        </button>
      </div>

      {notice ? <div className={styles.notice}>{notice}</div> : null}

      {mode === "login" ? (
        <form className={styles.form} onSubmit={handleLogin}>
          <Input
            label="Username"
            value={loginForm.username}
            onChange={(event) =>
              setLoginForm((prev) => ({
                ...prev,
                username: event.target.value,
              }))
            }
            placeholder="john_doe"
            required
          />
          <Input
            label="Password"
            type="password"
            value={loginForm.password}
            onChange={(event) =>
              setLoginForm((prev) => ({
                ...prev,
                password: event.target.value,
              }))
            }
            placeholder="Your secure password"
            required
          />
          {loginState.error ? (
            <p className={styles.error}>{getErrorMessage(loginState.error)}</p>
          ) : null}
          <Button type="submit" disabled={loginState.isLoading}>
            {loginState.isLoading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      ) : (
        <form className={styles.form} onSubmit={handleRegister}>
          <Input
            label="Username"
            value={registerForm.username}
            onChange={(event) =>
              setRegisterForm((prev) => ({
                ...prev,
                username: event.target.value,
              }))
            }
            placeholder="john_doe"
            required
          />
          <Input
            label="Email"
            type="email"
            value={registerForm.email}
            onChange={(event) =>
              setRegisterForm((prev) => ({
                ...prev,
                email: event.target.value,
              }))
            }
            placeholder="name@domain.com"
            required
          />
          <Input
            label="Password"
            type="password"
            value={registerForm.password}
            onChange={(event) =>
              setRegisterForm((prev) => ({
                ...prev,
                password: event.target.value,
              }))
            }
            placeholder="8+ characters"
            required
          />
          {registerState.error ? (
            <p className={styles.error}>
              {getErrorMessage(registerState.error)}
            </p>
          ) : null}
          <Button type="submit" disabled={registerState.isLoading}>
            {registerState.isLoading ? "Creating..." : "Create account"}
          </Button>
        </form>
      )}

      {(loginState.isLoading || registerState.isLoading) && (
        <div className={styles.loading}>
          <Spinner label="Securing session" />
        </div>
      )}
    </div>
  );
};
