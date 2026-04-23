"""resume-mcp — custom FastMCP server exposing the user's resume + voice corpus.

Tools:
- get_resume_markdown() -> str
- get_profile_field(key: str) -> str | None
- list_voice_samples() -> list[dict]
- find_voice_samples(kind: str | None, top_k: int) -> list[dict]

The corpus is injected at construction time so tests can point at fixtures.
For production use, `build_server()` is called with `ResumeCorpus()` (defaults
to repo `backend/seed/`).
"""
from __future__ import annotations

from fastmcp import FastMCP

from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus


def build_server(corpus: ResumeCorpus | None = None) -> FastMCP:
    """Construct a configured resume-mcp server.

    Injecting corpus (rather than importing a module-level instance) makes the
    server testable against tmp_path fixtures.
    """
    corpus = corpus or ResumeCorpus()
    server: FastMCP = FastMCP(name="resume-mcp")

    @server.tool()
    def get_resume_markdown() -> str:
        """Return the user's resume as Markdown."""
        return corpus.resume_markdown()

    @server.tool()
    def get_profile_field(key: str) -> str | None:
        """Return a single profile field (name, email, linkedin_url, etc.) or null."""
        return corpus.profile_field(key)

    @server.tool()
    def list_voice_samples() -> list[dict]:
        """Return all voice samples as dicts (id, kind, text)."""
        return [
            {"id": s.id, "kind": s.kind, "text": s.text}
            for s in corpus.list_voice_samples()
        ]

    @server.tool()
    def find_voice_samples(kind: str | None = None, top_k: int = 3) -> list[dict]:
        """Return voice samples optionally filtered by kind (cover_letter, essay, email)."""
        return [
            {"id": s.id, "kind": s.kind, "text": s.text}
            for s in corpus.find_voice_samples(query=None, kind=kind, top_k=top_k)
        ]

    return server


def main() -> None:
    """Entry point for running resume-mcp as a standalone MCP stdio server."""
    build_server().run()


if __name__ == "__main__":
    main()
