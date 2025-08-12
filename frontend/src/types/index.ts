export interface Citation {
  title: string;
  snippet: string;
  source_link?: string;
}

export interface ChatMessage {
  user: string;
  bot: string;
  citations: Citation[];
  confidence: number;
}

export interface IncidentFormData {
  title: string;
  description: string;
  category: string;
  location_text?: string;
  contact_email: string;
}
