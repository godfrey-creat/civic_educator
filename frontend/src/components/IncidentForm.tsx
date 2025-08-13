import { useState } from "react";
import { createIncident } from "../utils/api";
import type { IncidentFormData } from "../types";

<<<<<<< HEAD
=======
interface ValidationError {
  [key: string]: string;
}

// Matches Pydantic error structure
interface PydanticErrorItem {
  loc?: [string, string] | string[];
  msg: string;
}

// Matches API error object with optional array or detail
interface APIErrorResponse {
  status: number;
  data?: PydanticErrorItem[] | { detail?: string };
}

interface APIError {
  response?: APIErrorResponse;
}

>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
const initialForm: IncidentFormData = {
  title: "",
  description: "",
  category: "",
  location_text: "",
  contact_email: "",
};

<<<<<<< HEAD
export default function IncidentForm() {
  const [formData, setFormData] = useState(initialForm);
  const [isLoading, setIsLoading] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
=======
// Valid categories from backend
const CATEGORY_OPTIONS = [
  "road_maintenance",
  "waste_management",
  "water_supply",
  "electricity",
  "street_lighting",
  "drainage",
  "other",
];

export default function IncidentForm() {
  const [formData, setFormData] = useState(initialForm);
  const [errors, setErrors] = useState<ValidationError>({});
  const [isLoading, setIsLoading] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
<<<<<<< HEAD
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
=======
    setErrors({});
    setIncidentId(null);
    setIsLoading(true);

    try {
      const payload = {
        ...formData,
        location_text: formData.location_text || undefined,
      };

      const response = await createIncident(payload);
      setIncidentId(response.incident_id);
      setFormData(initialForm);
    } catch (err: unknown) {
      const errorObj = err as APIError;
      if (errorObj.response?.status === 422) {
        const errResponse = errorObj.response;
        if (Array.isArray(errResponse.data)) {
          const fieldErrors: ValidationError = {};
          (errResponse.data as PydanticErrorItem[]).forEach((e) => {
            const field =
              (Array.isArray(e.loc) && e.loc[1]) || "general";
            fieldErrors[field] = e.msg;
          });
          setErrors(fieldErrors);
        } else if (
          errResponse.data &&
          "detail" in errResponse.data &&
          errResponse.data.detail
        ) {
          setErrors({ general: errResponse.data.detail });
        }
      } else {
        // Keep UI-friendly message for generic errors
        setErrors({
          general: "❌ Failed to submit incident. Please try again.",
        });
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 mb-6 shadow">
      <h2 className="text-2xl font-semibold mb-4">Report Incident</h2>
      <form aria-label="Report Incident Form" onSubmit={handleSubmit}>
<<<<<<< HEAD
        {errorMsg && <p className="text-error mb-2" role="alert">{errorMsg}</p>}
=======
        {errors.general && (
          <p className="text-error mb-2" role="alert">
            {errors.general}
          </p>
        )}
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b

        <input
          name="title"
          value={formData.title}
          onChange={handleChange}
<<<<<<< HEAD
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
=======
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-1 rounded"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
          placeholder="Title"
          aria-label="title"
          required
        />
<<<<<<< HEAD

        <input
          name="category"
          value={formData.category}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Category (e.g., road_maintenance, waste_management)"
          aria-label="category"
          required
        />
=======
        {errors.title && <p className="text-error mb-2">{errors.title}</p>}

        <select
          name="category"
          value={formData.category}
          onChange={handleChange}
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-1 rounded"
          aria-label="category"
          required
        >
          <option value="">Select category</option>
          {CATEGORY_OPTIONS.map((cat) => (
            <option key={cat} value={cat}>
              {cat.replace("_", " ")}
            </option>
          ))}
        </select>
        {errors.category && (
          <p className="text-error mb-2">{errors.category}</p>
        )}
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b

        <input
          name="location_text"
          value={formData.location_text}
          onChange={handleChange}
<<<<<<< HEAD
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
          placeholder="Location (landmark or address)"
          aria-label="location"
        />
=======
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-1 rounded"
          placeholder="Location (landmark or address)"
          aria-label="location"
        />
        {errors.location_text && (
          <p className="text-error mb-2">{errors.location_text}</p>
        )}
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b

        <input
          name="contact_email"
          value={formData.contact_email}
          onChange={handleChange}
<<<<<<< HEAD
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
=======
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-1 rounded"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
          placeholder="Contact email"
          aria-label="contact_email"
          type="email"
        />
<<<<<<< HEAD
=======
        {errors.contact_email && (
          <p className="text-error mb-2">{errors.contact_email}</p>
        )}
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b

        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
<<<<<<< HEAD
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-2 rounded"
=======
          className="w-full bg-midnight border border-divider text-textPrimary p-2 mb-1 rounded"
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
          placeholder="Description"
          aria-label="description"
          required
        />
<<<<<<< HEAD
=======
        {errors.description && (
          <p className="text-error mb-2">{errors.description}</p>
        )}
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b

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
<<<<<<< HEAD
          ✅ Incident submitted! Your reference ID: <strong>{incidentId}</strong>
=======
          ✅ Incident submitted! Your reference ID:{" "}
          <strong>{incidentId}</strong>
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
        </p>
      )}
    </div>
  );
}
