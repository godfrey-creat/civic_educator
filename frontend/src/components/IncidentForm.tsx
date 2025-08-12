import { useState } from "react";
import { createIncident } from "../utils/api";
import type { IncidentFormData } from "../types";

const initialForm: IncidentFormData = {
  title: "",
  description: "",
  category: "",
  location_text: "",
  contact_email: "",
};

export default function IncidentForm() {
  const [formData, setFormData] = useState(initialForm);
  const [isLoading, setIsLoading] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      // send payload shaped for backend IncidentRequest
      const payload = {
        title: formData.title,
        description: formData.description,
        category: formData.category,
        contact_email: formData.contact_email,
        location_text: formData.location_text || undefined,
      };
      const response = await createIncident(payload as IncidentFormData);
      setIncidentId(response.incident_id);
      setFormData(initialForm);
    } catch (err: unknown) {
      // parse helpful server message where possible
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message);
          setErrorMsg(parsed.detail ? JSON.stringify(parsed.detail) : err.message);
        } catch {
          setErrorMsg(err.message);
        }
      } else {
        setErrorMsg("Failed to submit incident.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 mb-6 shadow">
      <h2 className="text-2xl font-semibold mb-4">Report Incident</h2>
      <form aria-label="Report Incident Form" onSubmit={handleSubmit}>
        {errorMsg && <p className="text-error mb-2" role="alert">{errorMsg}</p>}

        <input
          name="title"
          value={formData.title}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Title"
          aria-label="title"
          required
        />

        <input
          name="category"
          value={formData.category}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Category (e.g., road_maintenance, waste_management)"
          aria-label="category"
          required
        />

        <input
          name="location_text"
          value={formData.location_text}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Location (landmark or address)"
          aria-label="location"
        />

        <input
          name="contact_email"
          value={formData.contact_email}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Contact email"
          aria-label="contact_email"
          type="email"
        />

        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Description"
          aria-label="description"
          required
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
        <p className="mt-2 text-sm text-success" role="status">
          ✅ Incident submitted! Your reference ID: <strong>{incidentId}</strong>
        </p>
      )}
    </div>
  );
}
