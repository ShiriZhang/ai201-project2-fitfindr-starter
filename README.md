# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

A multi-tool AI agent that helps users find secondhand clothing pieces
and build outfits around their finds. Users describe what they're looking for in natural language; the agent searches a mock listings dataset, suggests outfit combinations using their existing wardrobe, and generates a shareable caption — all in one step.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:

```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:

```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

## Tool Inventory

### `search_listings(description, size, max_price)`

**Purpose:** Searches the mock listings dataset for secondhand items matching
a natural language description, with optional size and price filters.

| Parameter     | Type            | Description                                                                                                   |
| ------------- | --------------- | ------------------------------------------------------------------------------------------------------------- |
| `description` | `str`           | Keywords describing the item (e.g. "vintage graphic tee"). Scored against title, description, and style_tags. |
| `size`        | `str \| None`   | Size to filter by. Case-insensitive substring match — "M" matches "S/M" and "M/L". Pass `None` to skip.       |
| `max_price`   | `float \| None` | Maximum price in USD, inclusive. Pass `None` to skip.                                                         |

**Returns:** A list of matching listing dicts sorted by relevance score
(highest first). Each dict contains `id`, `title`, `description`,
`category`, `style_tags`, `size`, `condition`, `price`, `colors`,
`brand`, `platform`. Returns `[]` if no listings match — never raises
an exception.

---

### `suggest_outfit(new_item, wardrobe)`

**Purpose:** Calls the Groq LLM to suggest 1–2 complete outfit combinations
using the thrifted item and the user's existing wardrobe.

| Parameter  | Type   | Description                                        |
| ---------- | ------ | -------------------------------------------------- |
| `new_item` | `dict` | A listing dict for the item being considered.      |
| `wardrobe` | `dict` | A wardrobe dict with an `items` key. May be empty. |

**Returns:** A non-empty string with outfit suggestions. If the wardrobe
is empty, returns general styling advice instead of crashing.

---

### `create_fit_card(outfit, new_item)`

**Purpose:** Calls the Groq LLM at high temperature to generate a
short, shareable Instagram/TikTok-style caption for the outfit.

| Parameter  | Type   | Description                                                                                               |
| ---------- | ------ | --------------------------------------------------------------------------------------------------------- |
| `outfit`   | `str`  | The outfit suggestion from `suggest_outfit()`. If empty, returns an error string without calling the LLM. |
| `new_item` | `dict` | The listing dict for the thrifted item.                                                                   |

**Returns:** A 2–4 sentence caption mentioning the item name, price, and
platform once each. Output varies on each call due to elevated temperature
(`1.2`). Never raises an exception.

---

## How the Planning Loop Works

`run_agent()` in `agent.py` follows a conditional 7-step loop:

1. Initialize a `session` dict via `_new_session()`
2. Parse the query with regex to extract `description`, `size`, and
   `max_price`
3. Call `search_listings()` with the parsed parameters

**Branch point — this is where the agent's behavior diverges:**

- If `search_listings()` returns `[]`: set `session["error"]` to a
  helpful message and **return immediately** — `suggest_outfit` and
  `create_fit_card` are never called
- If results exist: set `session["selected_item"] = results[0]` and
  continue

4. Call `suggest_outfit(selected_item, wardrobe)` and store the result
5. Call `create_fit_card(outfit_suggestion, selected_item)` and store
   the result
6. Return the complete session

The agent is not a fixed pipeline — it only calls all three tools when
`search_listings` returns matches. An impossible query like
`"designer ballgown size XXS under $5"` exits after Step 3 and never
reaches the LLM tools.

---

## State Management

All state lives in a single `session` dict created at the start of each
`run_agent()` call. No global variables are used.

Each step writes to a specific key; the next step reads from it:

```
\_new_session() → query, wardrobe, error=None, fit_card=None, ...
parse query → session["parsed"] {description, size, max_price}
search_listings() → session["search_results"]
select top result → session["selected_item"]
suggest_outfit() → session["outfit_suggestion"]
create_fit_card() → session["fit_card"]
```

No tool receives the raw query string directly. For example,
`suggest_outfit()` receives `session["selected_item"]` and
`session["wardrobe"]` — not the original text. This means if
`search_listings` is skipped (empty results), `suggest_outfit` is
never given empty input.

---

## Error Handling

| Tool              | Failure mode                    | Agent response                                                                                                                                                                       |
| ----------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `search_listings` | No listings match the query     | Sets `session["error"]` to `"No listings found for '...'. Try removing the size filter or raising your price limit."` and returns the session early. The LLM tools are never called. |
| `suggest_outfit`  | Wardrobe is empty               | Not treated as an error. Automatically switches to a general styling prompt. Returns a non-empty string as normal.                                                                   |
| `create_fit_card` | `outfit` is empty or whitespace | Returns `"Cannot create fit card: outfit suggestion is missing. Make sure suggest_outfit ran successfully first."` without calling the LLM.                                          |

**Concrete example from testing:**

Running `python test_fitcard.py` with `create_fit_card("", item)`:

```
Cannot create fit card: outfit suggestion is missing.
Make sure suggest_outfit ran successfully first.
Guard triggered correctly: True
```

No exception was raised. The agent continued normally.

---

## Spec Reflection

**One way the spec helped:** Writing the planning.md Architecture diagram
before any code made it immediately clear that `suggest_outfit` should
never be called when `search_results` is empty. Without the diagram, it
would have been easy to wire the tools in a linear sequence and only
discover the bug when testing the no-results path.

**One way implementation diverged from the spec:** The spec described
`size` matching as "case-insensitive", but didn't specify whether it
should be exact or substring-based. During implementation, I chose
substring matching (`size.lower() in listing["size"].lower()`) so that
a query for `"M"` correctly matches listings with size `"S/M"` or
`"M/L"`. This decision was made by inspecting the actual data in
`listings.json`, where size formats are inconsistent.

---

## AI Usage

**Instance 1 — Implementing `search_listings`:**
I provided Claude with the Tool 1 spec block from `planning.md`
(inputs, return value, failure mode) and the note that size matching
must be case-insensitive substring-based. Claude generated the
filtering and keyword-scoring logic. I verified it against three test
cases before using it: normal search, zero-results path, and price
filter. The output matched the spec exactly and needed no changes.

**Instance 2 — Implementing `run_agent`:**
I provided Claude with the Architecture diagram and Planning Loop
section from `planning.md`. The generated code correctly branched on
`search_listings` results and stored values in the session dict.
However, the initial query parser used a single regex that missed the
`"under $30"` pattern (it only caught bare `"$30"`). I added a second
`re.search` for the `"under \$?"` pattern before the bare-dollar
fallback, and verified with the query `"vintage graphic tee under $30"`.
