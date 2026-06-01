"""
Blaze-Agent Soul.md Parser
Parses the Soul.md configuration file into structured data.
"""

import os
import re
import yaml
from typing import Optional

SOUL_PATH = "config/soul.md"

def load_soul(path: str = SOUL_PATH) -> dict:
    """Parse Soul.md into a structured dictionary."""
    if not os.path.exists(path):
        # Return a default empty soul
        return {
            "identity": {},
            "business": {},
            "knowledge": {},
            "faq": [],
            "policies": [],
            "rules": {},
            "capabilities": [],
            "raw": ""
        }

    with open(path, "r") as f:
        content = f.read()

    return parse_soul_md(content)

def parse_soul_md(content: str) -> dict:
    """Parse Soul.md content into structured sections."""
    result = {
        "identity": {},
        "business": {},
        "knowledge": {},
        "faq": [],
        "policies": [],
        "rules": {},
        "capabilities": [],
        "raw": content
    }

    lines = content.split("\n")
    current_section = None
    current_subsection = None
    section_lines = []

    def _save_section():
        if current_section and section_lines:
            text = "\n".join(section_lines).strip()
            section_key = current_section.lower().replace(" ", "_")

            if "identity" in section_key:
                result["identity"] = _parse_key_values(text)
            elif "business" in section_key or "info" in section_key:
                result["business"] = _parse_key_values(text)
            elif "knowledge" in section_key or "services" in section_key or "products" in section_key or "menu" in section_key:
                result["knowledge"] = _parse_key_values(text)
            elif "faq" in section_key:
                result["faq"] = _parse_faq(text)
            elif "policies" in section_key:
                result["policies"] = _parse_list(text)
            elif "behavior" in section_key or "rules" in section_key:
                result["rules"] = _parse_key_values(text)
            elif "capabilities" in section_key:
                result["capabilities"] = _parse_list(text)

    for line in lines:
        stripped = line.strip()

        # Detect section headers
        if stripped.startswith("#"):
            # Save previous section
            _save_section()
            section_lines = []

            # Get section name
            section_name = stripped.lstrip("#").strip()
            current_section = section_name
            continue

        if stripped:
            section_lines.append(stripped)

    # Save last section
    _save_section()

    return result

def _parse_key_values(text: str) -> dict:
    """Parse 'Key: Value' lines into a dict."""
    result = {}
    for line in text.split("\n"):
        line = line.strip().lstrip("- ").lstrip("* ")
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            if key and value:
                result[key] = value
    return result

def _parse_faq(text: str) -> list:
    """Parse FAQ entries. Supports formats:
    - Question? -> Answer
    - Q: Question / A: Answer
    - Question: Answer
    """
    faq = []
    for line in text.split("\n"):
        line = line.strip().lstrip("- ").lstrip("* ")
        if not line:
            continue

        # Format: Question? -> Answer
        if "->" in line:
            parts = line.split("->", 1)
            q = parts[0].strip().rstrip("?")
            a = parts[1].strip()
            faq.append({"question": q, "answer": a})
        # Format: Q: ... A: ...
        elif line.lower().startswith("q:") and "a:" in line.lower():
            q_match = re.split(r'(?i)a:', line[2:], maxsplit=1)
            if len(q_match) == 2:
                faq.append({"question": q_match[0].strip(), "answer": q_match[1].strip()})
        # Format: Key: Value
        elif ":" in line:
            key, _, value = line.partition(":")
            faq.append({"question": key.strip(), "answer": value.strip()})

    return faq

def _parse_list(text: str) -> list:
    """Parse bullet list items."""
    items = []
    for line in text.split("\n"):
        line = line.strip().lstrip("- ").lstrip("* ").lstrip("[] ").lstrip("x ")
        if line and len(line) > 2:
            items.append(line)
    return items

def get_soul_text_for_ai(soul: dict) -> str:
    """Convert parsed Soul.md into a text block for AI system prompt."""
    parts = []

    # Identity
    identity = soul.get("identity", {})
    if identity:
        name = identity.get("name", "Assistant")
        role = identity.get("role", "Assistant")
        personality = identity.get("personality", "friendly")
        parts.append(f"You are {name}, a {role}.")
        parts.append(f"Your personality is: {personality}")

    # Business info
    biz = soul.get("business", {})
    if biz:
        parts.append("")
        parts.append("## About the business:")
        for key, val in biz.items():
            parts.append(f"  {key.replace('_', ' ').title()}: {val}")

    # Knowledge (services, products, menu)
    knowledge = soul.get("knowledge", {})
    if knowledge:
        parts.append("")
        parts.append("## Our services/products:")
        for key, val in knowledge.items():
            if val:
                parts.append(f"  {key.replace('_', ' ').title()}: {val}")

    # FAQ
    faq = soul.get("faq", [])
    if faq:
        parts.append("")
        parts.append("## Frequently Asked Questions:")
        for item in faq:
            q = item.get("question", "")
            a = item.get("answer", "")
            if q and a:
                parts.append(f"  {q} -> {a}")

    # Rules
    rules = soul.get("rules", {})
    if rules:
        parts.append("")
        parts.append("## Your rules:")
        for key, val in rules.items():
            parts.append(f"  {key.replace('_', ' ').title()}: {val}")

    # Fallback
    fallback = (rules.get("fallback") or rules.get("dont") or
                "I am not sure about that. Let me connect you with a human who can help.")
    parts.append("")
    parts.append(f"If you dont know the answer, say: \"{fallback}\"")

    return "\n".join(parts)

def reload_soul() -> dict:
    """Force reload Soul.md from disk."""
    return load_soul()
