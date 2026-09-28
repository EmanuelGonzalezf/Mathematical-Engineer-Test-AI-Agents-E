"""
router.py — Router for the RevAIsor Access Review Agent.

Your task: implement the router that analyzes the user query and decides
which tools to call before passing control to the agent loop.

The router runs before any LLM or tool call — it should be fast and
deterministic, based on the Knowledge Graph and simple keyword matching.
"""

from knowledge_graph import KG


# TODO 1: Entity extraction
def extract_entities(query: str) -> dict:
    """
    Parse the query and identify known entities.

    Returns:
        {
            "users":      list[str],  — names found in query that exist in KG
            "role_types": list[str],  — role type names found (e.g. ["GBR", "ZGBR"])
        }

    TODO: scan KG["users"] and KG["role_types"] for matches in the query.
          Use case-insensitive matching.

    Example:
        >>> extract_entities("What role does Priya own?")
        {"users": ["Priya"], "role_types": []}

        >>> extract_entities("Compare GBR and ZGBR")
        {"users": [], "role_types": ["GBR", "ZGBR"]}
    """
    entities = {"users": [], "role_types": []}

    # Extract users
    for user in KG["users"]:
        if user.lower() in query.lower():
            entities["users"].append(user)

    # Extract role types
    for role_type in KG["role_types"]:
        if role_type.lower() in query.lower():
            entities["role_types"].append(role_type)

    return entities

# TODO 2: Intent classification
def classify_intent(query: str, entities: dict) -> str:
    """
    Determine the intent of the query.

    Returns one of:
        "role_ownership"  — user wants to know what role someone owns
        "role_comparison" — user wants to compare two role types
        "access_history"  — user wants to see a user's review history
        "out_of_scope"    — query has nothing to do with access review

    TODO: use keyword matching on the query and the extracted entities.

    Example:
        >>> classify_intent("What role does Priya own?", {"users": ["Priya"], ...})
        "role_ownership"

        >>> classify_intent("Order a pizza", {})
        "out_of_scope"
    """
    text = query.lower()

    if (
        any(word in text for word in ("compare", "comparison", "contrast", "difference"))
        and len(entities["role_types"]) >= 1
    ):
        return "role_comparison"

    if (
        any(word in text for word in ("history", "review history", "historial"))
        and entities["users"]
    ):
        return "access_history"

    if (
        entities["users"]
        and any(word in text for word in ("role", "own", "owns", "access", "permission"))
    ):
        return "role_ownership"

    return "out_of_scope"

# TODO 3: Tool selection
def select_tools(intent: str) -> list[str]:
    """
    Given the intent, return the list of tool names to call.

    Returns a list of tool names: "role_tool", "document_tool", or both.
    Returns an empty list for out_of_scope.

    Suggested mapping:
        role_ownership  → ["role_tool"]
        access_history  → ["role_tool"]
        role_comparison → ["document_tool"]
        out_of_scope    → []
    """
    R = []
    if intent in {"role_ownership", "access_history"}:
        return ["role_tool"]

    if intent == "role_comparison":
        return ["document_tool"]

    return []

# TODO 4: Main router entry point
def route(query: str) -> dict:
    """
    Main entry point. Given a raw query, return a routing decision.

    Returns:
        {
            "intent":        str,
            "entities":      dict,
            "tools_to_call": list[str],
        }

    TODO: orchestrate extract_entities → classify_intent → select_tools.
    """
    entities = extract_entities(query)
    intent = classify_intent(query, entities)
    tools_to_call = select_tools(intent)

    return {
        "intent": intent,
        "entities": entities,
        "tools_to_call": tools_to_call,
    }