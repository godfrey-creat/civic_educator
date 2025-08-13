import { useEffect, useState } from "react";
<<<<<<< HEAD
import { getKbDocs, getAllIncidents } from "../utils/api";
import { getToken, isStaff } from "../utils/auth";
=======
import {
  getKbDocs,
  getAllIncidents,
  updateIncidentStatus,
} from "../utils/api";
import { isStaff } from "../utils/auth";
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
import LoginForm from "./LoginForm";

interface KbDoc {
  doc_id: string;
  title: string;
  snippet: string;
  score: number;
}

interface Incident {
  incident_id: string;
<<<<<<< HEAD
  description: string;
  status: string;
  last_update: string;
}

export default function StaffTools() {
  const [docs, setDocs] = useState<KbDoc[]>([]);
  const [kbError, setKbError] = useState<string | null>(null);
  const [kbQuery, setKbQuery] = useState("");
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);

  const staffToken = getToken();

  const handleSearch = async () => {
    try {
      if (!kbQuery.trim()) {
        setKbError("Please enter a search term");
        setDocs([]);
        return;
      }
      const results = await getKbDocs(kbQuery);
      setDocs(results.results);
      setKbError(results.results.length ? null : "No knowledge base entries found");
    } catch {
      setKbError("Failed to fetch KB");
      setDocs([]);
=======
  title: string;
  category: string;
  status: string;
  created_at: string;
  updated_at: string;
  priority: string;
  description?: string;
}

const STATUS_OPTIONS = ["NEW", "IN_PROGRESS", "RESOLVED", "CLOSED"] as const;

export default function StaffTools() {
  const [docs, setDocs] = useState<KbDoc[]>([]);
  const [kbError, setKbError] = useState<string | null>(null);
  const [kbLoading, setKbLoading] = useState(false);
  const [kbQuery, setKbQuery] = useState("");
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  /** KB search */
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!kbQuery.trim()) {
      setKbError("Please enter a search term");
      setDocs([]);
      return;
    }
    setKbLoading(true);
    try {
      const results = await getKbDocs(kbQuery);
      const items = results.results || [];
      setDocs(items);
      setKbError(items.length ? null : "No knowledge base entries found");
    } catch {
      setKbError("Failed to fetch KB");
      setDocs([]);
    } finally {
      setKbLoading(false);
    }
  };

  /** Incidents fetch */
  const fetchIncidents = async () => {
    try {
      const data = await getAllIncidents();
      setIncidents(data as unknown as Incident[]);
      setIncidentsError(null);
    } catch {
      setIncidentsError("Failed to load incidents");
      setIncidents([]);
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
    }
  };

  useEffect(() => {
<<<<<<< HEAD
    const fetchIncidents = async () => {
      try {
        const data = await getAllIncidents();
        setIncidents(data);
      } catch {
        setIncidentsError("Failed to load incidents");
      }
    };
    if (staffToken) fetchIncidents();
  }, [staffToken]);

  if (!isStaff()) {
    return (
      <div className="bg-panel p-4 rounded-xl">
        <p className="mb-4">You must be logged in as a staff member to view this section.</p>
=======
    fetchIncidents();
  }, []);

  /** Update status inline */
 const handleStatusChange = async (incidentId: string, newStatus: string) => {
  try {
    setUpdatingId(incidentId);
    const updated = await updateIncidentStatus(incidentId, newStatus);
    setIncidents((prev) =>
      prev.map((inc) =>
        inc.incident_id === incidentId
          ? {
              ...inc,
              status: updated.status ?? newStatus,
              updated_at: updated.last_update || inc.updated_at,
            }
          : inc
      )
    );
  } catch {
    alert("Failed to update status");
  } finally {
    setUpdatingId(null);
  }
};


  /** Staff gate */
  if (!isStaff()) {
    return (
      <div className="bg-panel p-4 rounded-xl">
        <p className="mb-4">
          You must be logged in as a staff member to view this section.
        </p>
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
        <LoginForm onLogin={() => window.location.reload()} />
      </div>
    );
  }

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 shadow">
      <h2 className="text-2xl font-semibold mb-4">Staff Tools</h2>
<<<<<<< HEAD
      {/* KB Search */}
      <div className="mb-4">
=======

      {/* KB Search */}
      <form
        onSubmit={handleSearch}
        className="mb-4 flex flex-wrap items-center gap-2"
      >
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
        <input
          type="text"
          value={kbQuery}
          onChange={(e) => setKbQuery(e.target.value)}
          placeholder="Search Knowledge Base..."
<<<<<<< HEAD
          className="border border-divider rounded p-2 mr-2 w-64"
        />
        <button
          onClick={handleSearch}
          className="bg-accentPink hover:bg-pink-500 text-white px-4 py-2 rounded"
        >
          Search KB
        </button>
      </div>
      {/* Incident List */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Incidents</h3>
        {incidentsError && <p className="text-error text-sm">{incidentsError}</p>}
        {!incidentsError && incidents.length === 0 && <p>No incidents found.</p>}
        <ul className="divide-y divide-divider">
          {incidents.map((incident) => (
            <li key={incident.incident_id} className="py-2">
              <p className="font-medium">{incident.incident_id}</p>
              <p className="text-sm">{incident.description}</p>
              <p className="text-xs text-textMuted">
                {incident.status} — Last updated {incident.last_update}
              </p>
            </li>
          ))}
        </ul>
      </div>
      {/* KB Results */}
      {docs.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Knowledge Base</h3>
          {kbError && <p className="text-error">{kbError}</p>}
          {docs.map((doc) => (
            <div key={doc.doc_id}>
=======
          className="border border-divider rounded p-2 w-64 text-black"
          aria-label="Knowledge base search"
        />
        <button
          type="submit"
          className="bg-accentPink hover:bg-pink-500 text-white px-4 py-2 rounded"
        >
          {kbLoading ? "Searching…" : "Search KB"}
        </button>
      </form>
      {kbError && <p className="text-error mb-4">{kbError}</p>}
      {docs.length > 0 && (
        <div className="space-y-4 mb-6">
          <h3 className="text-lg font-medium">Knowledge Base Results</h3>
          {docs.map((doc) => (
            <div key={doc.doc_id} className="p-3 border rounded">
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
              <p className="font-bold">{doc.title}</p>
              <p className="text-sm text-textMuted">{doc.snippet}</p>
            </div>
          ))}
        </div>
      )}
<<<<<<< HEAD
=======

      {/* Incident List */}
      <div>
        <h3 className="text-lg font-medium mb-2">Incidents</h3>
        {incidentsError && (
          <p className="text-error text-sm">{incidentsError}</p>
        )}
        {!incidentsError && incidents.length === 0 && (
          <p>No incidents found.</p>
        )}
        <ul className="divide-y divide-divider">
          {incidents.map((incident) => (
            <li key={incident.incident_id} className="py-3">
              <div className="flex items-start justify-between gap-4">
                {/* Left: details */}
                <div className="min-w-0">
                  <p className="font-medium break-all">
                    {incident.incident_id}
                  </p>
                  <p className="text-sm">{incident.title}</p>
                  <p className="text-sm">Category: {incident.category}</p>
                  {incident.description && (
                    <p className="text-sm">{incident.description}</p>
                  )}
                  <p className="text-xs text-textMuted">
                    Created{" "}
                    {new Date(incident.created_at).toLocaleString()} — Last
                    updated {new Date(incident.updated_at).toLocaleString()}
                  </p>
                </div>

                {/* Right: priority + status */}
                <div className="flex flex-col items-end gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-midnight border border-divider">
                    Priority: {incident.priority}
                  </span>

                  <label className="text-xs text-textMuted">
                    Status
                    <select
                      value={incident.status}
                      onChange={(e) =>
                        handleStatusChange(
                          incident.incident_id,
                          e.target.value
                        )
                      }
                      disabled={updatingId === incident.incident_id}
                      className="ml-2 border border-divider rounded p-1 text-black"
                      aria-label={`Update status for ${incident.incident_id}`}
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </label>

                  {updatingId === incident.incident_id && (
                    <span className="text-accentCyan text-xs">Updating…</span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
    </div>
  );
}
