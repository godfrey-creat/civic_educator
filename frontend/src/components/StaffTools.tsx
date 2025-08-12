import { useEffect, useState } from "react";
import { getKbDocs, getAllIncidents } from "../utils/api";
import { getToken, isStaff } from "../utils/auth";
import LoginForm from "./LoginForm";

interface KbDoc {
  doc_id: string;
  title: string;
  snippet: string;
  score: number;
}

interface Incident {
  incident_id: string;
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
    }
  };

  useEffect(() => {
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
        <LoginForm onLogin={() => window.location.reload()} />
      </div>
    );
  }

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 shadow">
      <h2 className="text-2xl font-semibold mb-4">Staff Tools</h2>
      {/* KB Search */}
      <div className="mb-4">
        <input
          type="text"
          value={kbQuery}
          onChange={(e) => setKbQuery(e.target.value)}
          placeholder="Search Knowledge Base..."
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
              <p className="font-bold">{doc.title}</p>
              <p className="text-sm text-textMuted">{doc.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
