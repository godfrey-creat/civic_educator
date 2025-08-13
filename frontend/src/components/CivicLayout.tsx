import { useState, useEffect } from "react";
import StaffTools from "./StaffTools";
import RoleToggle from "./RoleToggle";
import ChatInterface from "./ChatInterface";
import IncidentForm from "./IncidentForm";
import StatusLookup from "./StatusLookup";
import LoginForm from "./LoginForm";
import RegisterForm from "./RegisterForm";
import { getToken, logout } from "../utils/auth";

export default function CivicLayout() {
  const [role, setRole] = useState<"resident" | "staff">("resident");
  const [tab, setTab] = useState("chat");
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(!!getToken());

  useEffect(() => {
    setIsLoggedIn(!!getToken());
  }, []);

  const isResident = role === "resident";
<<<<<<< HEAD
=======

  // Keep Staff Tools in the tab list anytime role = "staff"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
  const tabs = isResident
    ? [
        { key: "chat", label: "Ask Services" },
        { key: "report", label: "Report Incident" },
        { key: "status", label: "Check Status" },
      ]
    : [
        { key: "chat", label: "Ask Services" },
        { key: "staff-tools", label: "Staff Tools" },
      ];

  const handleLogout = () => {
    logout();
    setIsLoggedIn(false);
<<<<<<< HEAD
    // ensure staff-only UI is hidden
=======
    // ensure staff-only UI is hidden and we land on a safe tab
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
    setTab("chat");
  };

  return (
    <div className="min-h-screen bg-midnight text-textPrimary px-4 py-6 sm:px-6 md:px-8">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4 sm:gap-0 border-b border-divider pb-4">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-wide text-center sm:text-left">
          CivicNavigator
        </h1>

        <div className="flex items-center gap-4">
<<<<<<< HEAD
          <RoleToggle role={role} onChange={(r) => { setRole(r); setTab("chat"); }} />
          {isLoggedIn && (
=======
          <RoleToggle
            role={role}
            onChange={(r) => {
              setRole(r);
              setTab("chat");
            }}
          />
          {/* Show Logout only when staff and logged in */}
          {!isResident && isLoggedIn && (
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
            <button
              onClick={handleLogout}
              className="px-3 py-2 text-sm bg-red-600 text-white rounded"
            >
              Logout
            </button>
          )}
        </div>
      </header>

      {/* Tabs navigation */}
      <nav className="flex flex-wrap justify-center gap-3 mb-6">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm sm:text-base rounded border border-divider min-w-[120px] text-center transition-colors duration-200 ${
<<<<<<< HEAD
              tab === key ? "bg-accentCyan text-midnight font-semibold" : "bg-panel hover:bg-accentCyan/10"
=======
              tab === key
                ? "bg-accentCyan text-midnight font-semibold"
                : "bg-panel hover:bg-accentCyan/10"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
            }`}
          >
            {label}
          </button>
        ))}

        {/* Show Login/Register tabs when staff role chosen and not logged in */}
        {!isResident && !isLoggedIn && (
          <>
            <button
              onClick={() => setTab("login")}
              className={`px-4 py-2 text-sm sm:text-base rounded border border-divider min-w-[120px] text-center transition-colors duration-200 ${
<<<<<<< HEAD
                tab === "login" ? "bg-accentCyan text-midnight font-semibold" : "bg-panel hover:bg-accentCyan/10"
=======
                tab === "login"
                  ? "bg-accentCyan text-midnight font-semibold"
                  : "bg-panel hover:bg-accentCyan/10"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
              }`}
            >
              Login
            </button>

            <button
              onClick={() => setTab("register")}
              className={`px-4 py-2 text-sm sm:text-base rounded border border-divider min-w-[120px] text-center transition-colors duration-200 ${
<<<<<<< HEAD
                tab === "register" ? "bg-accentCyan text-midnight font-semibold" : "bg-panel hover:bg-accentCyan/10"
=======
                tab === "register"
                  ? "bg-accentCyan text-midnight font-semibold"
                  : "bg-panel hover:bg-accentCyan/10"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
              }`}
            >
              Register
            </button>
          </>
        )}
      </nav>

      {/* Main content */}
      <main className="max-w-3xl mx-auto space-y-6 sm:space-y-8">
        {tab === "chat" && <ChatInterface role={role} />}
        {tab === "report" && isResident && <IncidentForm />}
        {tab === "status" && isResident && <StatusLookup />}

        {/* Staff Tools */}
        {tab === "staff-tools" && !isResident && (
          <>
            {isLoggedIn ? (
              <StaffTools />
            ) : (
<<<<<<< HEAD
              <p className="text-center text-textMuted">You must be logged in as staff to view this section.</p>
=======
              <p className="text-center text-textMuted">
                You must be logged in as staff to view this section.
              </p>
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
            )}
          </>
        )}

        {/* Login */}
        {tab === "login" && !isLoggedIn && (
          <LoginForm
            onLogin={() => {
              setIsLoggedIn(true);
              setTab("staff-tools");
            }}
          />
        )}

        {/* Register */}
        {tab === "register" && !isLoggedIn && (
          <RegisterForm
            onRegister={() => {
              // after successful registration we go to login tab
              setTab("login");
            }}
          />
        )}
      </main>
    </div>
  );
}
