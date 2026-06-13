"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    
    # step 1: load all listings
    listings = load_listings()
    
    # step 2: filter by max_price and size
    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.lower() not in listing["size"].lower():
            continue
        filtered.append(listing)
    
    # step 3: score by keyword overlap with description
    scored = []
    keywords = description.lower().split()
    for listing in filtered:
        searchable = " ".join([listing["title"].lower(), listing["description"].lower(), " ".join(listing["style_tags"]).lower()])
        score = sum(1 for kw in keywords if kw in searchable)
        scored.append((score, listing))
    
    # step 4: drop listings with score 0
    scored = [(s, l) for s, l in scored if s > 0]

    # step 5: sort by score, highest first
    scored.sort(key=lambda x: x[0], reverse=True)

    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    client = _get_groq_client()

    item_summary = (
        f"Item: {new_item['title']}\n"
        f"Category: {new_item['category']}\n"
        f"Style tags: {', '.join(new_item['style_tags'])}\n"
        f"Colors: {', '.join(new_item['colors'])}\n"
        f"Price: ${new_item['price']}"
    )

    # Branch 1: empty wardrobe → general styling advice
    if not wardrobe.get("items"):
        prompt = (
            f"A user just found this secondhand item:\n{item_summary}\n\n"
            f"They don't have a wardrobe entered yet. Give them 1-2 short, "
            f"specific styling ideas: what vibe does this piece suit, and what "
            f"types of items would pair well with it? Be casual and direct."
        )
    # Branch 2: wardrobe has items → specific outfit combinations
    else:
        wardrobe_lines = "\n".join(
            f"- {item['name']} ({item['category']}, "
            f"colors: {', '.join(item['colors'])})"
            for item in wardrobe["items"]
        )
        prompt = (
            f"A user just found this secondhand item:\n{item_summary}\n\n"
            f"Their existing wardrobe:\n{wardrobe_lines}\n\n"
            f"Suggest 1-2 complete outfit combinations using the new item and "
            f"specific named pieces from their wardrobe. Be casual and specific."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Could not generate outfit suggestion. Try again shortly."
    except Exception:
        return "Could not generate outfit suggestion. Try again shortly."

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation

    # guard: empty outfit string
    if not outfit or not outfit.strip():
        return ("Cannot create fit card: outfit suggestion is missing."
                "Make sure suggest_outfit ran successfully first.")
    
    client = _get_groq_client()

    prompt = (
        f"Write a 2-4 sentence Instagram/TikTok caption for this thrifted outfit.\n\n"
        f"Thrifted item: {new_item['title']}\n"
        f"Price: ${new_item['price']}\n"
        f"Platform: {new_item['platform']}\n"
        f"Outfit: {outfit}\n\n"
        f"Rules:\n"
        f"- Sound like a real person posting an OOTD, not a product description\n"
        f"- Mention the item name, price, and platform naturally (each once)\n"
        f"- Capture the specific vibe of the outfit\n"
        f"- Casual, lowercase is fine, one emoji max"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=1.2,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Could not generate fit card. Try again shortly."
