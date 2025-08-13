import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import ChatInterface from "./ChatInterface";

// Mock the API call
vi.mock("../utils/api", () => ({
  sendChatMessage: vi.fn(),
}));

import { sendChatMessage } from "../utils/api";
const mockSendChatMessage = sendChatMessage as unknown as jest.Mock;

describe("ChatInterface", () => {
  beforeEach(() => {
    mockSendChatMessage.mockReset();
  });

  it("renders input and send button", () => {
    render(<ChatInterface role="resident" />);
    expect(screen.getByLabelText(/chat input/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
    expect(screen.getByText(/chat/i)).toBeInTheDocument(); // Header
  });

  it("sends a message and displays response with citations", async () => {
    mockSendChatMessage.mockResolvedValue({
      reply: "Garbage is collected every Monday.",
      citations: [
        {
          title: "City Waste Policy",
          snippet: "Garbage is collected weekly in South C...",
          source_link: "https://example.com/policy",
        },
      ],
      confidence: 0.95,
    });

    render(<ChatInterface role="resident" />);
    const input = screen.getByLabelText(/chat input/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "When is garbage collected?");
    fireEvent.click(sendButton);

    await waitFor(() => {
      // Check user message
      expect(screen.getByText("When is garbage collected?")).toBeInTheDocument();
      // Check bot reply
      expect(screen.getByTestId("chat-reply")).toHaveTextContent("Garbage is collected every Monday.");
      // Check citation
      expect(screen.getByText("City Waste Policy")).toBeInTheDocument();
      expect(screen.getByText("Garbage is collected weekly in South C...")).toBeInTheDocument();
      const sourceLink = screen.getByText("[Source]");
      expect(sourceLink).toHaveAttribute("href", "https://example.com/policy");
      expect(sourceLink).toHaveAttribute("target", "_blank");
      expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
    });
  });

  it("shows loading state when submitting", async () => {
    mockSendChatMessage.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({
      reply: "Test response",
      citations: [],
      confidence: 0.9,
    }), 100)));

    render(<ChatInterface role="resident" />);
    const input = screen.getByLabelText(/chat input/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "Hi bot");
    fireEvent.click(sendButton);

    expect(sendButton).toHaveTextContent("Sending...");
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();

    await waitFor(() => {
      expect(sendButton).toHaveTextContent("Send");
      expect(input).not.toBeDisabled();
      expect(sendButton).not.toBeDisabled();
    });
  });

  it("handles empty input gracefully", async () => {
    render(<ChatInterface role="resident" />);
    const sendButton = screen.getByRole("button", { name: /send/i });

    fireEvent.click(sendButton);

    expect(mockSendChatMessage).not.toHaveBeenCalled();
    expect(screen.queryByText(/when is garbage collected/i)).not.toBeInTheDocument();
    expect(screen.queryByTestId("chat-reply")).not.toBeInTheDocument();
  });

  it("displays error message on API failure", async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {}); // Suppress error log
    mockSendChatMessage.mockRejectedValue(new Error("API error"));

    render(<ChatInterface role="resident" />);
    const input = screen.getByLabelText(/chat input/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "Test error");
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/⚠️ Unable to process request./i)).toBeInTheDocument();
    }, { timeout: 2000 });

    vi.spyOn(console, 'error').mockRestore(); // Restore console.error
  });

  it("clears input after sending", async () => {
    mockSendChatMessage.mockResolvedValue({
      reply: "Test response",
      citations: [],
      confidence: 0.9,
    });

    render(<ChatInterface role="resident" />);
    const input = screen.getByLabelText(/chat input/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "Test message");
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(input).toHaveValue("");
    });
  });

  it("handles staff role correctly", async () => {
    mockSendChatMessage.mockResolvedValue({
      reply: "Staff response",
      citations: [],
      confidence: 0.9,
    });

    render(<ChatInterface role="staff" />);
    const input = screen.getByLabelText(/chat input/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "Staff question");
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockSendChatMessage).toHaveBeenCalledWith("Staff question", "staff");
      expect(screen.getByTestId("chat-reply")).toHaveTextContent("Staff response");
    });
  });

  it("ensures accessibility of message history", () => {
    render(<ChatInterface role="resident" />);
    const messageContainer = screen.getByLabelText(/message history/i);
    expect(messageContainer).toHaveAttribute("aria-live", "polite");
  });

  it("handles missing citations gracefully", async () => {
    mockSendChatMessage.mockResolvedValue({
      reply: "No citations response",
      citations: [],
      confidence: 0.9,
    });

    render(<ChatInterface role="resident" />);
    const input = screen.getByLabelText(/chat input/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "No citations");
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByTestId("chat-reply")).toHaveTextContent("No citations response");
      expect(screen.queryByText(/\[source\]/i)).not.toBeInTheDocument();
    });
  });
});