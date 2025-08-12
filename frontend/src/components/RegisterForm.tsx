import { useState } from "react";
import { registerUser } from "../utils/api";

export default function RegisterForm({
  onRegister,
}: {
  onRegister?: () => void;
}) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [isStaff, setIsStaff] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      await registerUser(email, password, fullName, isStaff);
      setSuccessMsg("User registered successfully!");
      setEmail("");
      setFullName("");
      setPassword("");
      setIsStaff(false);
      onRegister?.();
    } catch (error: unknown) {
      setErr(
        error instanceof Error ? error.message : "Unknown error occurred."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 border rounded bg-panel text-textPrimary"
    >
      <h3 className="font-semibold mb-2">Register</h3>
      {err && <p className="text-error mb-2">{err}</p>}
      {successMsg && <p className="text-green-500 mb-2">{successMsg}</p>}

      <input
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email address"
        type="email"
        required
        className="w-full mb-2 p-2 bg-panel border border-divider rounded text-white placeholder-gray-400 focus:outline-none focus:border-accentCyan"
      />

      <input
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        placeholder="Full name (optional)"
        className="w-full mb-2 p-2 bg-panel border border-divider rounded text-white placeholder-gray-400 focus:outline-none focus:border-accentCyan"
      />

      <input
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        type="password"
        required
        className="w-full mb-2 p-2 bg-panel border border-divider rounded text-white placeholder-gray-400 focus:outline-none focus:border-accentCyan"
      />

      <label className="flex items-center gap-2 mb-3">
        <input
          type="checkbox"
          checked={isStaff}
          onChange={(e) => setIsStaff(e.target.checked)}
        />
        <span>Register as staff</span>
      </label>

      <button
        type="submit"
        className="bg-accentPink hover:bg-pink-500 text-white px-4 py-2 rounded w-full"
        disabled={loading}
      >
        {loading ? "Registering..." : "Register"}
      </button>
    </form>
  );
}
