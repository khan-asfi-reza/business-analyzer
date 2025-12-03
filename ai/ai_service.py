import os
from typing import Dict, Any, Optional

from .providers.huggingface import HuggingFaceProvider
from .providers.openai import OpenAIProvider
from .providers.gemini import GeminiProvider
from prompts import PROMPT_SENTIMENT_CLASSIFICATION


class AIService:
    """
    AI Service with pluggable providers.

    Default provider: HuggingFace (when model parameter is omitted)

    Usage:
        ai_service = AIService()  # Uses HuggingFace by default
        ai_service = AIService(model="openai")
        ai_service = AIService(model="gemini")
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize AI Service with specified provider.

        Args:
            model: Provider name ('huggingface', 'openai', 'gemini')
                   Defaults to 'huggingface' if not specified
        """
        # Default to HuggingFace if no model specified
        if model is None:
            model = os.getenv("DEFAULT_AI_PROVIDER", "huggingface")

        self.model = model.lower()

        # Initialize appropriate provider
        if self.model == "openai":
            self.provider = OpenAIProvider()
        elif self.model == "gemini":
            self.provider = GeminiProvider()
        else:  # Default to HuggingFace
            self.provider = HuggingFaceProvider()

        print(f"AIService initialized with provider: {self.provider.__class__.__name__}")

    def classify_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Classify sentiment of given text.

        Args:
            text: Text to analyze

        Returns:
            {
                "sentiment_score": float,  # -1 to 1
                "sentiment_label": "positive" | "negative" | "neutral",
                "confidence": float  # 0 to 1
            }
        """
        # Get prompt from centralized location
        prompt = PROMPT_SENTIMENT_CLASSIFICATION.format(text=text)

        # Call provider-specific implementation
        return self.provider.classify_sentiment(prompt, text)

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate text completion using the AI provider.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        return self.provider.generate_text(prompt, max_tokens)