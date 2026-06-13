# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**

<!-- Describe what this tool does in 1–2 sentences -->

Searches the mock listings dataset for secondhand items matching a natural language description, with optional size and price filters. Returns a relevance-ranked list of matching listing dicts, or an empty list if nothing matches — never raises an exception.

**Input parameters:**

<!-- List each parameter, its type, and what it represents -->

- `description` (str): Natural language keywords describing the item the user wants (e.g., "vintage graphic tee"). Used for keyword scoring against each listing's title description, and style_tags.
- `size` (str): Size string to filter by (e.g., "M"). Matching is case-insensitive and substring-based — "M" matches "S/M" and "M/L". Pass None to skip size filtering.
- `max_price` (float): Maximum price in USD, inclusive. Only listings at or below this price are returned. Pass None to skip price filtering.

**What it returns:**

<!-- Describe the return value — what fields does a result contain? -->

A list of listing dicts sorted by relevance score, highest first. Each dict contains: id, title, description, category, style_tags (list[str]), size, condition, price (float), colors (list[str]), brand (str or None), platform. Returns [] if no listings match.

**What happens if it fails or returns nothing:**

<!-- What should the agent do if no listings match? -->

If the list is empty, the agent sets session["error"] to a helpful message - e.g., "No listings found for 'designer ballgown'. Try removing the size filter or raising your price limit." - then returns the session immediately without calling suggest_outfit or create_fit_card.

---

### Tool 2: suggest_outfit

**What it does:**

<!-- Describe what this tool does in 1–2 sentences -->

Calls the LLM to suggest 1-2 complete outfit combinations using the thrifted item. Handles two cases: if the wardrobe is empty, it returns general styling advice (what vibes the items suits, what types of pieces pair well); if the wardrobe has items, it references specific pieces the user already owns to build concrete outfit combinations.

**Input parameters:**

<!-- List each parameter, its type, and what it represents -->

- `new_item` (dict): A listing dict for the item the user is considering buying. Contains fields like title, style_tags, colors, category, and price.
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts (name, category, colors, style_tags). May be empty - this case must be handled gracefully without crashing.

**What it returns:**

<!-- Describe the return value -->

A non-empty string containing outfit suggestions from the LLM. If the wardrobe is empty, the string contains general styling advice. If the wardrobe has items, the string references specific named pieces (e.g., "pair with your dark-wash baggy jeans and black combat boots"). Never returns an empty string.

**What happens if it fails or returns nothing:**

<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

If wardrobe['items'] is empty, the tool does NOT crash or return "" — it switches to the general styling prompt automatically. If the LLM call fails, the tool returns a fallback string: "Could not generate outfit suggestion. Try again shortly."

---

### Tool 3: create_fit_card

**What it does:**

<!-- Describe what this tool does in 1–2 sentences -->

Calls the LLM at high temperature to generate a short, shareable outfit caption - 2-4 sentencese written like a real OOTD post, not a product listing. Output varies each time even for the same input, due to elevated temperature.

**Input parameters:**

<!-- List each parameter, its type, and what it represents -->

- `outfit` (str): The outfit suggestion string returned by suggest_outfit(). If empty or whitespace-only, the tool returns an error string immediately without calling the LLM.
- `new_item` (dict): The listing dict for the thrifted item. Used to pull title, price, and platform into the caption naturally (each mentioned once).

**What it returns:**

<!-- Describe the return value -->

A 2–4 sentence string styled as an Instagram/TikTok caption: casual, authentic, mentioning the item name, price, and platform once each, and capturing the outfit vibe in specific terms. Each call produces a different result for the same input.

**What happens if it fails or returns nothing:**

<!-- What should the agent do if the outfit data is incomplete? -->

If `outfit` is empty or whitespace-only, returns the error string: "Cannot create fit card: outfit suggestion is missing. Make sure suggest_outfit ran successfully first." Does not raise an exception under any circumstances.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

After initializing the session, the agent parses the user query using regex to extract description, size (optional), and max_price (optional). It then calls search_listings() with these parameters.

**Branch point:** If search_listings() returns an empty list, the agent sets session["error"] to a helpful message and returns the session immediately — suggest_outfit and create_fit_card are NOT called.

If results is non-empty, the agent sets session["selected_item"] = results[0] (the top-ranked match) and calls suggest_outfit() with selected_item and wardrobe. The result is stored in session["outfit_suggestion"].

Finally, the agent calls create_fit_card() with session["outfit_suggestion"] and session["selected_item"], storing the result in session["fit_card"].

The loop terminates after create_fit_card() completes and returns the full session dict.

---

## State Management

**How does information from one tool get passed to the next?**

<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

All state for a single interaction is stored in a session dict created by \_new_session() at the start of run_agent(). No global variables are used —
data flows exclusively through this dict.

Each step writes its output to a specific key and the next step reads from it:

\_new_session() → writes: query, wardrobe, parsed={}, error=None
parse query → writes: session["parsed"]
search_listings() → writes: session["search_results"]
select top result → writes: session["selected_item"]
suggest_outfit() → writes: session["outfit_suggestion"]
create_fit_card() → writes: session["fit_card"]

No tool receives raw query text directly — each tool only receives the
already-processed output from the previous step via function arguments drawn
from the session dict. For example, suggest_outfit() receives
session["selected_item"] and session["wardrobe"], not the original query.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool            | Failure mode                          | Agent response                                                                                                                                                                                                   |
| --------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| search_listings | No results match the query            | set session["error"] to "No listings found for '[description]'. Try removing the size filter or raising your price limit." Return the session immediately — suggest_outfit and create_fit_card are never called. |
| suggest_outfit  | Wardrobe is empty                     | Do NOT treat as an error. Automatically switch to a general styling prompt asking the LLM what vibes and item types pair well with the new piece. Return the LLM response as a normal string.                    |
| create_fit_card | Outfit input is missing or incomplete | Return the string "Cannot create fit card: outfit suggestion is missing. Make sure suggest_outfit ran successfully first." Do not call the LLM. Do not raise an exception.                                       |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
User query (natural language)
 │
 ▼
┌─────────────────────────────────────────────────────────┐
│                      Planning Loop                       │
│                                                          │
│  Step 1: _new_session(query, wardrobe)                   │
│  Step 2: parse query → description, size, max_price      │
│                                                          │
│  Step 3: search_listings(description, size, max_price)   │
│           │                                              │
│           ├── results = []                               │
│           │    └──► session["error"] = "No listings..."  │
│           │         return session ◄────────────────┐    │
│           │                                         │    │
│           └── results = [item, ...]                 │    │
│                │                                    │    │
│                ▼                                    │    │
│  Step 4: session["selected_item"] = results[0]      │    │
│                │                                    │    │
│                ▼                                    │    │
│  Step 5: suggest_outfit(selected_item, wardrobe)    │    │
│           │                                         │    │
│           └── session["outfit_suggestion"] = "..."  │    │
│                │                                    │    │
│                ▼                                    │    │
│  Step 6: create_fit_card(outfit_suggestion,         │    │
│                          selected_item)             │    │
│           │                                         │    │
│           └── session["fit_card"] = "..."           │    │
│                │                                    │    │
│  Step 7: return session ────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
   session["fit_card"]   session["error"]
   (happy path)          (no-results path)

Session State (shared across all steps):
  query, parsed{}, search_results[], selected_item,
  wardrobe, outfit_suggestion, fit_card, error
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will give Claude the Tool 1 spec block (inputs, return value, failure mode)
and ask it to implement search_listings() using load_listings() from
data_loader. I will verify the generated code: (1) filters by all three
parameters, (2) uses case-insensitive substring matching for size, (3) returns
[] on no match without raising an exception. I will test with 3 queries before
moving on.

For Tools 2 and 3, I will give Claude each tool's spec block plus the
wardrobe schema and ask it to implement the function using the Groq client.
I will verify the two-branch logic in suggest_outfit and confirm create_fit_card
returns a string (not an exception) when outfit is empty.

**Milestone 4 — Planning loop and state management:**
I will give Claude the Architecture diagram and Planning Loop + State
Management sections from this planning.md and ask it to implement run_agent()
in agent.py. I will verify the generated code branches on search_listings
results, stores values in the session dict (not local variables), and does
not call suggest_outfit when results is empty.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "looking for a vintage graphic tee under $30"

**Step 1:**
The agent calls \_new_session() to initialize the session dict. Sets
session["query"] = "looking for a vintage graphic tee under $30",
session["wardrobe"] = get_example_wardrobe() (10 items), and all other
fields to their defaults (error=None, fit_card=None, etc.).

**Step 2:**
The agent parses the query. Extracts:
description = "vintage graphic tee"
size = None (no size mentioned)
max_price = 30.0
Stores result in session["parsed"].

**Step 3:**
The agent calls search_listings("vintage graphic tee", size=None,
max_price=30.0). The function filters listings to price ≤ $30, then scores
each by keyword overlap with "vintage graphic tee". Returns 3 matches
sorted by score:

1. lst_006 — "Graphic Tee — 2003 Tour Bootleg Style" ($24, depop)
2. lst_033 — "Vintage Band Tee — Faded Grey" ($19, depop)
3. lst_002 — "Y2K Baby Tee — Butterfly Print" ($18, depop)
   Results are non-empty → agent continues (no early return).
   Stores list in session["search_results"].

**Step 4:**
The agent sets session["selected_item"] = session["search_results"][0],
which is the lst_006 listing dict (the top-ranked match).

**Step 5:**
The agent calls suggest_outfit(session["selected_item"],
session["wardrobe"]). The wardrobe is non-empty (10 items), so the LLM
receives a prompt listing the user's existing pieces alongside the new
graphic tee. The LLM returns something like:
"Pair this boxy bootleg tee with your dark-wash baggy jeans and chunky
white sneakers for a classic 90s streetwear look. Alternatively, tuck
it loosely into your wide-leg khakis and add the black crossbody bag
for a more put-together daytime outfit."
Stored in session["outfit_suggestion"].

**Step 6:**
The agent calls create_fit_card(session["outfit_suggestion"],
session["selected_item"]). The LLM generates a caption at high temperature:
"found this faded bootleg tee on depop for $24 and it was made for my
baggy jeans era 🖤 full fit incoming"
Stored in session["fit_card"].

**Step 7:**
run_agent() returns the complete session dict.
session["error"] is None — interaction completed successfully.

**Final output to user (Gradio UI):**
Panel 1 — Top listing: "Graphic Tee — 2003 Tour Bootleg Style |
$24 | depop | Condition: good"
Panel 2 — Outfit idea: The suggest_outfit string from Step 5
Panel 3 — Fit card: The create_fit_card caption from Step 6

**Error path (no-results case):**
If the query were "designer ballgown size XXS under $5",
search_listings() returns []. The agent sets:
session["error"] = "No listings found for 'designer ballgown'.
Try removing the size filter or raising your price limit."
Returns session immediately. suggest_outfit and create_fit_card
are never called. Panels 2 and 3 remain empty in the UI.
