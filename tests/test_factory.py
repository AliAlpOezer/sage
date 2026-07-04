import pytest

from sage import factory
from sage.config import Settings
from sage.models import Chunk


def test_unknown_backend_raises_with_available_list():
    settings = Settings(embedder="nope")
    with pytest.raises(ValueError, match="Unknown embedder 'nope'"):
        factory.make_embedder(settings)


def test_registered_adapter_is_built_with_settings():
    @factory.register_embedder("dummy")
    class DummyEmbedder:
        def __init__(self, settings: Settings):
            self.settings = settings

        @property
        def dimension(self) -> int:
            return 3

        async def embed(self, texts):
            return [[0.0, 0.0, 0.0] for _ in texts]

    embedder = factory.make_embedder(Settings(embedder="dummy", collection="test"))
    assert embedder.settings.collection == "test"
    assert embedder.dimension == 3


def test_chunk_id_is_deterministic_and_content_sensitive():
    a = Chunk.make_id("https://x/page.md", "some text")
    b = Chunk.make_id("https://x/page.md", "some text")
    c = Chunk.make_id("https://x/page.md", "other text")
    assert a == b
    assert a != c
