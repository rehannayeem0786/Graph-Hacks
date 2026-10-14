"""Configuration management for GraphLens."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# LLM settings — Groq and OpenRouter only
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-70b-instruct")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# FalkorDB settings (supports local Docker AND FalkorDB Cloud)
FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_GRAPH_NAME = os.getenv("FALKORDB_GRAPH_NAME", "graphlens")
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD", "")
FALKORDB_SSL = os.getenv("FALKORDB_SSL", "false").lower() in ("true", "1", "yes")

# Supported file extensions for parsing
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
}

# Directories to skip during scanning
SKIP_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".tox",
    "dist", "build", ".eggs", "*.egg-info", ".mypy_cache",
    ".pytest_cache", ".idea", ".vs",
}
