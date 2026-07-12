"""RAGAS evaluation tooling for Sage.

Kept in its own subpackage (and its own `eval` dependency group) because it pulls
in RAGAS + langchain-openai. The RAG pipeline itself stays framework-free — this
is measurement tooling, not product code.
"""
