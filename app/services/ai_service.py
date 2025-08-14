# Simple AI service for demonstration

class AIService:
    def __init__(self):
        pass  # Add any initialization logic here if needed

    async def initialize(self):
        # Dummy async method for compatibility
        pass

    async def cleanup(self):
        # Dummy cleanup method for compatibility
        # Close connections or free resources here if needed
        pass

    @staticmethod
    def chat(messages, model="gpt-3.5-turbo", max_tokens=500, temperature=0.7):
        # Dummy implementation: echo the last user message
        last_user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            ""
        )
        return {
            "response": f"Echo: {last_user_message}",
            "model": model,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

    async def generate_embeddings(self, texts):
        # Dummy implementation: returns a list of zero-vectors
        return [[0.0] * 384 for _ in texts]
