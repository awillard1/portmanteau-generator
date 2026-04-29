"""
rerank.py – AI-powered re-ranking of top name candidates via a local Ollama LLM.

No extra Python packages are required: communication uses stdlib ``urllib``.
Ollama must be running locally (default: http://localhost:11434) or at a URL
supplied by the caller.

The re-ranker sends the top-N candidates to the model with a structured prompt
and asks it to return a ranked JSON list with one-line reasons.  If the model
or Ollama is unavailable, the original order is returned unchanged.

Usage::

    from portmanteau_power.rerank import ai_rerank

    reranked = ai_rerank(
        candidates,        # List[Candidate]
        context="AI-powered productivity app",
        top_n=20,          # names to send to the model
        model="llama3",
        ollama_url="http://localhost:11434",
    )
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from portmanteau_power.explain import Candidate

_DEFAULT_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3"
_TIMEOUT = 60  # seconds; LLM generation can be slow


_PROMPT_TEMPLATE = """\
You are a branding expert. Below is a list of candidate brand names generated \
for: {context}.

Evaluate each name and return ONLY a JSON array (no markdown fences, no \
preamble) of objects with keys "name" and "reason", ordered from best to worst. \
Include all {n} names.

Names to rank:
{names_block}

Return only valid JSON like:
[{{"name":"example","reason":"Short, punchy, memorable"}}, ...]"""


def _ollama_generate(
    prompt: str,
    model: str,
    base_url: str,
) -> str:
    """Call Ollama /api/generate and return the full response text."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        raw = resp.read().decode()

    data = json.loads(raw)
    return data.get("response", "")


def _parse_ranked_names(response_text: str) -> List[str]:
    """Extract ordered name list from LLM response JSON."""
    # Strip optional markdown code fences
    text = response_text.strip()
    for fence in ("```json", "```"):
        if text.startswith(fence):
            text = text[len(fence):]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        records = json.loads(text)
        if isinstance(records, list):
            names = []
            for item in records:
                if isinstance(item, dict) and "name" in item:
                    names.append(str(item["name"]).lower().strip())
                elif isinstance(item, str):
                    names.append(item.lower().strip())
            return names
    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    return []


def ai_rerank(
    candidates: "List[Candidate]",
    context: str = "a modern brand",
    top_n: int = 20,
    model: str = _DEFAULT_MODEL,
    ollama_url: str = _DEFAULT_URL,
) -> "List[Candidate]":
    """
    Re-rank the first *top_n* candidates using a local Ollama LLM.

    Candidates beyond *top_n* are appended unchanged after the re-ranked top.
    If Ollama is unreachable or returns unusable output, the original list is
    returned unchanged.

    Parameters
    ----------
    candidates:  Scored candidates, already sorted by descending score.
    context:     One-sentence description of the project / brand domain.
    top_n:       How many top candidates to send to the model.
    model:       Ollama model name (e.g. "llama3", "mistral").
    ollama_url:  Base URL of the Ollama server.

    Returns
    -------
    Re-ordered list; same Candidate objects, new sequence.
    """
    if not candidates:
        return candidates

    pool = candidates[:top_n]
    rest = candidates[top_n:]

    names_block = "\n".join(f"- {c.text}" for c in pool)
    prompt = _PROMPT_TEMPLATE.format(
        context=context,
        n=len(pool),
        names_block=names_block,
    )

    try:
        response = _ollama_generate(prompt, model, ollama_url)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        # Ollama not available – return unchanged
        return candidates

    ranked_names = _parse_ranked_names(response)
    if not ranked_names:
        return candidates

    # Reorder pool according to model's ranking; append any model missed
    name_to_cand = {c.text: c for c in pool}
    reranked: List["Candidate"] = []
    seen = set()

    for n in ranked_names:
        if n in name_to_cand and n not in seen:
            reranked.append(name_to_cand[n])
            seen.add(n)

    # Append any candidates the model didn't mention
    for c in pool:
        if c.text not in seen:
            reranked.append(c)

    return reranked + rest
