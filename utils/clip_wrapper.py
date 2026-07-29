"""Dedicated wrapper around Hugging Face Transformers CLIP.

Encapsulates model loading, device placement, embedding generation, and
caching. This module is the single place in the codebase that talks to the
CLIP model, matching the architecture requirement in AGENTS.md.
"""

import threading
from typing import List, Union

import numpy as np
from PIL import Image


class CLIPWrapper:
    """Lazy-loading, singleton-style CLIP wrapper.

    The wrapper is intentionally implemented as a plain class plus a module-level
    factory function. Callers can use :func:`get_clip_wrapper` for the shared
    application instance, or instantiate ``CLIPWrapper`` directly for tests.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = None):
        self.model_name = model_name
        self.device = device or self._get_device()
        self._model = None
        self._processor = None
        self._lock = threading.Lock()

    @staticmethod
    def _get_device() -> str:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> "CLIPWrapper":
        """Load the model and processor if they are not already loaded."""
        if self.is_loaded():
            return self

        with self._lock:
            if self.is_loaded():
                return self
            from transformers import CLIPModel, CLIPProcessor

            self._model = CLIPModel.from_pretrained(self.model_name)
            self._processor = CLIPProcessor.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
        return self

    def _ensure_loaded(self):
        if not self.is_loaded():
            self.load()

    @property
    def model(self):
        self._ensure_loaded()
        return self._model

    @property
    def processor(self):
        self._ensure_loaded()
        return self._processor

    def embed_text(self, texts: Union[str, List[str]], batch_size: int = 8) -> np.ndarray:
        """Return L2-normalized text embeddings as a NumPy array."""
        import torch

        self._ensure_loaded()
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = self._processor(
                text=batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                emb = self._model.get_text_features(**inputs)
                if hasattr(emb, "pooler_output"):
                    emb = emb.pooler_output
                if hasattr(emb, "last_hidden_state"):
                    emb = emb.last_hidden_state
                emb = emb / emb.norm(dim=-1, keepdim=True)
            embeddings.append(emb.cpu().numpy())

        return np.concatenate(embeddings, axis=0)

    def embed_image(self, image: Union[Image.Image, str, np.ndarray]) -> np.ndarray:
        """Return the L2-normalized embedding for a single image."""
        import torch

        self._ensure_loaded()
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            emb = self._model.get_image_features(**inputs)
            if hasattr(emb, "pooler_output"):
                emb = emb.pooler_output
            if hasattr(emb, "last_hidden_state"):
                emb = emb.last_hidden_state
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb.cpu().numpy()


# Global application instance. Lazy-loaded on first use so importing this
# module does not trigger a model download.
_clip_wrapper: CLIPWrapper = None


def get_clip_wrapper(model_name: str = "openai/clip-vit-base-patch32", device: str = None) -> CLIPWrapper:
    """Return the shared :class:`CLIPWrapper` instance."""
    global _clip_wrapper
    if _clip_wrapper is None:
        _clip_wrapper = CLIPWrapper(model_name=model_name, device=device)
    return _clip_wrapper


def reset_clip_wrapper():
    """Reset the shared wrapper instance. Useful in tests."""
    global _clip_wrapper
    _clip_wrapper = None
