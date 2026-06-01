"""
Blaze-Agent Skills Manager
Manages and runs skills based on message content.
"""

import yaml
import os
import re
from typing import Tuple

SKILLS_CONFIG_PATH = "config/skills.yaml"

def load_skills_config() -> dict:
    if os.path.exists(SKILLS_CONFIG_PATH):
        with open(SKILLS_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_skills_config(config: dict):
    with open(SKILLS_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

def is_skill_enabled(skill_name: str) -> bool:
    config = load_skills_config()
    return config.get(skill_name, False)

async def check_skills(message: str, soul: dict, discord_message) -> Tuple[str, bool]:
    """Check if any skill should handle this message.
    Returns (response, handled)."""
    skills_config = load_skills_config()
    message_lower = message.lower().strip()

    # FAQ skill -- check first, saves AI costs
    if skills_config.get("faq", False):
        response = _check_faq(message_lower, soul)
        if response:
            return response, True

    # Complaint handler -- check before order/booking to catch anger
    if skills_config.get("complaint_handler", False):
        complaint_keywords = [
            "complaint", "complain", "unhappy", "angry", "terrible",
            "awful", "worst", "bad service", "refund", "scam", "rip off",
            "demand", "manager", "owner", "report", "not good", "hate",
            "disappointed", "disgusting", "never again", "cancel my"
        ]
        if any(kw in message_lower for kw in complaint_keywords):
            return _handle_complaint(message_lower, soul,discord_message), True

    # Order taking skill
    if skills_config.get("order_taking", False):
        order_keywords = [
            "i want to order", "can i order", "i would like to order",
            "place an order", "order please", "i want", "i need",
            "can i get", "give me", "i'll take", "let me get"
        ]
        if any(kw in message_lower for kw in order_keywords):
            return await _handle_order(message, soul, discord_message), True

    # Booking skill
    if skills_config.get("booking", False):
        booking_keywords = [
            "book", "appointment", "schedule", "reserve", "booking",
            "make an appointment", "when can i", "available slot",
            "available time"
        ]
        if any(kw in message_lower for kw in booking_keywords):
            return await _handle_booking(message, soul, discord_message), True

    # Lead capture skill
    if skills_config.get("lead_capture", False):
        lead_keywords = [
            "tell me more", "i'm interested", "i am interested",
            "contact me", "call me", "send me info", "more info",
            "more information", "price list", "brochure", "how much",
            "interested in"
        ]
        if any(kw in message_lower for kw in lead_keywords):
            return _handle_lead_capture(message, soul, discord_message), True

    # File creation skill
    if skills_config.get("file_creation", False):
        file_keywords = [
            "invoice", "receipt", "copy of", "send me", "pdf",
            "document", "download", "generate", "create a file",
            "i need a copy", "can i get a"
        ]
        if any(kw in message_lower for kw in file_keywords):
            return await _handle_file_request(message, soul, discord_message), True

    return "", False

def _check_faq(message: str, soul: dict) -> str:
    """Check if message matches any FAQ entry."""
    faq = soul.get("faq", [])
    if not faq:
        return ""

    # Score each FAQ entry
    best_match = None
    best_score = 0
    threshold = 0.4  # minimum similarity

    for entry in faq:
        question = entry.get("question", "").lower()
        answer = entry.get("answer", "")
        if not question or not answer:
            continue

        # Simple keyword overlap scoring
        msg_words = set(re.findall(r'\w+', message))
        q_words = set(re.findall(r'\w+', question))
        if not q_words:
            continue

        overlap = len(msg_words & q_words)
        score = overlap / len(q_words)

        # Boost for key phrase matches
        key_phrases = [w for w in q_words if len(w) > 4]
        matched_key = sum(1 for p in key_phrases if p in message)

        score = score + (matched_key * 0.15)

        if score > best_score:
            best_score = score
            best_match = answer

    if best_match and best_score >= threshold:
        return best_match
    return ""

def _handle_complaint(message: str, soul: dict, discord_message) -> str:
    """Handle a customer complaint."""
    biz = soul.get("business", {})
    biz_name = biz.get("business_name", "our business")
    contact = biz.get("contact", biz.get("phone", ""))

    response = (
        f"I am really sorry to hear about your experience. "
        f"That is not the standard we aim for at {biz_name}. "
    )

    if contact and contact != "N/A":
        response += (
            f"I will make sure this gets to the right people. "
            f"You can also reach us directly at {contact}. "
        )

    response += (
        "Could you tell me more about what happened so I can note it down?"
    )

    return response

async def _handle_order(message: str, soul: dict, discord_message) -> str:
    """Start the order flow. Returns initial response."""
    biz = soul.get("business", {})
    knowledge = soul.get("knowledge", {})

    # If we have menu/knowledge items, show them
    if knowledge:
        items = []
        for key, val in knowledge.items():
            if val and val.lower() != "n/a":
                items.append(f"  • {key.replace('_', ' ').title()}: {val}")

        if items:
            menu_text = "\n".join(items[:10])  # limit to 10
            return (
                f"Great, let me help you order!\n\n"
                f"Here is what we offer:\n{menu_text}\n\n"
                f"What would you like? Just tell me what you need!"
            )

    return (
        "I would love to help you place an order! "
        "What would you like? Tell me the items and quantities."
    )

async def _handle_booking(message: str, soul: dict, discord_message) -> str:
    """Start the booking flow."""
    biz = soul.get("business", {})
    hours = biz.get("hours", "our operating hours")

    return (
        "I can help you book an appointment!\n\n"
        f"We are open {hours}. What day and time works for you? "
        "Also let me know which service you are interested in."
    )

def _handle_lead_capture(message: str, soul: dict, discord_message) -> str:
    """Start lead capture flow."""
    biz = soul.get("business", {})
    biz_name = biz.get("business_name", "our team")

    return (
        f"I would be happy to help! Let me get someone from {biz_name} "
        f"to reach out to you.\n\n"
        f"Can I get your name and a contact number? "
        f"Also let me know what you are interested in specifically."
    )

async def _handle_file_request(message: str, soul: dict, discord_message) -> str:
    """Handle a file/document request."""
    bot_name = soul.get("identity", {}).get("name", "Assistant")

    return (
        f"I can help with that! Let me prepare the document for you.\n"
        f"One moment... I will send it here when it is ready."
    )

def get_skills_status() -> dict:
    """Return all skills and their enabled status."""
    config = load_skills_config()
    return config

def set_skill(skill_name: str, enabled: bool):
    """Enable or disable a skill."""
    config = load_skills_config()
    config[skill_name] = enabled
    save_skills_config(config)
