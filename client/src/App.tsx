import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import "./App.css";
import { type ApiError } from "./api/http";
import { login, logout } from "./api/auth";
import { accountsQueryOptions } from "./query/accountsQueries";
import { currentUserQueryOptions } from "./query/authQueries";
import { categoriesQueryOptions } from "./query/categoriesQueries";
import { queryClient } from "./query/client";

type LoginFormState = {
  email: string;
  password: string;
};

const defaultLoginForm: LoginFormState = {
  email: "",
  password: "",
};

function formatCurrency(cents: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

function getErrorMessage(error: unknown) {
  const apiError = error as ApiError | undefined;
  const detail = apiError?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return "Please double-check the submitted values.";
  }

  return apiError?.message ?? "Something went wrong.";
}

function SignedOutView() {
  const [form, setForm] = useState<LoginFormState>(defaultLoginForm);

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      await queryClient.invalidateQueries({ queryKey: ["accounts"] });
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
      setForm(defaultLoginForm);
    },
  });

  return (
    <section className="shell shell--auth">
      <div className="auth-hero">
        <p className="eyebrow">Argentourse</p>
        <h1>Keep the ledger honest.</h1>
        <p className="lede">
          Your backend is now ready for sessions, accounts, categories, and
          transactions. This frontend starts with the practical part: sign in,
          confirm the session, and show the finance data that already exists.
        </p>

        <div className="hero-points">
          <div className="hero-point">
            <span className="hero-kicker">Session auth</span>
            <strong>Cookie-based login with CSRF-protected writes</strong>
          </div>
          <div className="hero-point">
            <span className="hero-kicker">Live backend</span>
            <strong>Accounts and categories load from your FastAPI API</strong>
          </div>
          <div className="hero-point">
            <span className="hero-kicker">Ready next</span>
            <strong>Transactions, imports, and reclassification screens</strong>
          </div>
        </div>
      </div>

      <form
        className="auth-card"
        onSubmit={(event) => {
          event.preventDefault();
          loginMutation.mutate(form);
        }}
      >
        <div className="card-topline">Sign in</div>
        <h2>Connect this browser to the session-backed API.</h2>

        <label className="field">
          <span>Email</span>
          <input
            autoComplete="email"
            name="email"
            type="email"
            value={form.email}
            onChange={(event) =>
              setForm((current) => ({ ...current, email: event.target.value }))
            }
            placeholder="you@example.com"
            required
          />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            autoComplete="current-password"
            name="password"
            type="password"
            value={form.password}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                password: event.target.value,
              }))
            }
            placeholder="••••••••"
            required
          />
        </label>

        {loginMutation.isError ? (
          <p className="form-error">{getErrorMessage(loginMutation.error)}</p>
        ) : null}

        <button
          className="button button--primary"
          type="submit"
          disabled={loginMutation.isPending}
        >
          {loginMutation.isPending ? "Signing in..." : "Sign in"}
        </button>

        <p className="form-note">
          This uses the backend session cookie flow, not local token storage.
        </p>
      </form>
    </section>
  );
}

function SignedInView() {
  const { data: user } = useQuery(currentUserQueryOptions);
  const { data: accounts = [] } = useQuery(accountsQueryOptions);
  const { data: categories = [] } = useQuery(categoriesQueryOptions);

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: async () => {
      queryClient.setQueryData(["currentUser"], null);
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      queryClient.removeQueries({ queryKey: ["accounts"] });
      queryClient.removeQueries({ queryKey: ["categories"] });
    },
  });

  const totalBalance = accounts.reduce(
    (sum, account) => sum + account.current_balance_cents,
    0,
  );

  const expenseCategories = categories.filter(
    (category) => category.category_type.toLowerCase() === "expense",
  ).length;

  const incomeCategories = categories.filter(
    (category) => category.category_type.toLowerCase() === "income",
  ).length;

  return (
    <section className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Argentourse</p>
          <h1>Finance workspace</h1>
        </div>

        <div className="topbar-actions">
          <div className="user-chip">
            <span className="user-chip__label">Signed in as</span>
            <strong>
              {user?.first_name} {user?.last_name}
            </strong>
          </div>
          <button
            className="button button--ghost"
            type="button"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
          >
            {logoutMutation.isPending ? "Signing out..." : "Logout"}
          </button>
        </div>
      </header>

      <section className="overview-grid">
        <article className="metric-card metric-card--balance">
          <span className="metric-label">Tracked balance</span>
          <strong>{formatCurrency(totalBalance)}</strong>
          <p>{accounts.length} linked accounts across your ledger.</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">Categories</span>
          <strong>{categories.length}</strong>
          <p>
            {incomeCategories} income and {expenseCategories} expense buckets.
          </p>
        </article>

        <article className="metric-card">
          <span className="metric-label">Backend status</span>
          <strong>Ready</strong>
          <p>Transactions, CSV import preview/commit, and reclassify routes exist.</p>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="card-topline">Accounts</p>
              <h2>Your current ledger containers</h2>
            </div>
            <span className="badge">{accounts.length}</span>
          </div>

          <div className="stack">
            {accounts.length === 0 ? (
              <p className="empty-state">
                No accounts yet. Create one in the API or your next frontend form.
              </p>
            ) : (
              accounts.map((account) => (
                <div className="list-card" key={account.id}>
                  <div>
                    <strong>{account.name}</strong>
                    <p>
                      {account.institution} · {account.account_type}
                    </p>
                  </div>
                  <span className="money-pill">
                    {formatCurrency(account.current_balance_cents)}
                  </span>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="card-topline">Categories</p>
              <h2>Spending and income buckets</h2>
            </div>
            <span className="badge">{categories.length}</span>
          </div>

          <div className="stack">
            {categories.length === 0 ? (
              <p className="empty-state">
                No categories yet. The backend is ready whenever you add the UI.
              </p>
            ) : (
              categories.map((category) => (
                <div className="list-card" key={category.id}>
                  <div>
                    <strong>{category.name}</strong>
                    <p>{category.category_type}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel panel--wide">
          <div className="panel-heading">
            <div>
              <p className="card-topline">Next frontend slice</p>
              <h2>What we can build next without backend churn</h2>
            </div>
          </div>

          <div className="roadmap">
            <div className="roadmap-item">
              <strong>Transaction list + filters</strong>
              <p>Hook up `GET /transactions` with account and category selectors.</p>
            </div>
            <div className="roadmap-item">
              <strong>Manual transaction form</strong>
              <p>Create a write flow for `POST /transactions` with CSRF-aware mutations.</p>
            </div>
            <div className="roadmap-item">
              <strong>CSV import review</strong>
              <p>Upload a CSV, preview dedupe warnings, then commit approved rows.</p>
            </div>
            <div className="roadmap-item">
              <strong>Reclassify interactions</strong>
              <p>Use the new single and bulk reclassify routes from the transactions table.</p>
            </div>
          </div>
        </article>
      </section>
    </section>
  );
}

function App() {
  const currentUserQuery = useQuery({
    ...currentUserQueryOptions,
    retry: false,
  });

  if (currentUserQuery.isLoading) {
    return (
      <main className="loading-shell">
        <div className="loading-card">
          <p className="eyebrow">Argentourse</p>
          <h1>Checking your session...</h1>
          <p>Rehydrating the dashboard from the cookie-backed API.</p>
        </div>
      </main>
    );
  }

  if (currentUserQuery.error) {
    const error = currentUserQuery.error as ApiError;
    if (error.status !== 401) {
      return (
        <main className="loading-shell">
          <div className="loading-card loading-card--error">
            <p className="eyebrow">Frontend sync issue</p>
            <h1>Could not reach the API cleanly.</h1>
            <p>{getErrorMessage(error)}</p>
          </div>
        </main>
      );
    }
  }

  return (
    <main className="app-shell">
      {currentUserQuery.data ? <SignedInView /> : <SignedOutView />}
    </main>
  );
}

export default App;
