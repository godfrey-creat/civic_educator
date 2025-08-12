import { useState } from "react";
import { createIncident } from "../utils/api";
import type { IncidentFormData } from "../types";

const initialForm: IncidentFormData = {
  title: "",
  description: "",
  category: "",
  location: "",
  contact: "",
};

export default function IncidentForm() {
  const [formData, setFormData] = useState(initialForm);
  const [isLoading, setIsLoading] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await createIncident(formData);
      setIncidentId(response.incident_id);
      setFormData(initialForm);
    } catch {
      alert("⚠️ Failed to submit incident.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 mb-6 shadow">
      <h2 className="text-2xl font-semibold mb-4">Report Incident</h2>
      <form aria-label="Report Incident Form" onSubmit={handleSubmit}>
        {["title", "category", "location", "contact"].map((field) => (
          <input
            key={field}
            name={field}
            value={formData[field as keyof IncidentFormData]}
            onChange={handleChange}
            className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
            placeholder={field[0].toUpperCase() + field.slice(1)}
            aria-label={field}
          />
        ))}

        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Description"
          aria-label="description"
        />

        <button
          type="submit"
          disabled={isLoading}
          className="bg-accentPink hover:bg-pink-500 text-white px-4 py-2 rounded"
        >
          {isLoading ? "Submitting..." : "Submit Incident"}
        </button>
      </form>

      {incidentId && (
        <p className="mt-2 text-sm text-success">
          ✅ Incident submitted! Your reference ID: <strong>{incidentId}</strong>
        </p>
      )}
    </div>
  );
}
