import { useState } from "react";
import { getKbDocs } from "../utils/api";

interface KbDoc {
  doc_id: string;
  title: string;
  snippet: string;
  score: number;
}

export default function StaffTools() {
  const [docs, setDocs] = useState<KbDoc[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  const handleSearch = async () => {
    try {
      const results = await getKbDocs();
      setDocs(results);
      setIsLoaded(true);
    } catch {
      alert("⚠️ Failed to fetch KB.");
    }
  };

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 shadow">
      <h2 className="text-2xl font-semibold mb-4">Staff Tools</h2>
      <button
        onClick={handleSearch}
        className="bg-accentPink hover:bg-pink-500 text-white px-4 py-2 rounded mb-4"
      >
        Load Knowledge Base
      </button>

      {isLoaded && (
        <div className="space-y-4">
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
