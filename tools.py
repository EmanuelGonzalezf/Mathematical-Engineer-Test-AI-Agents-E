"""
tools.py — Tool stubs for the RevAIsor Access Review Agent.

"""
from knowledge_graph import KG

def role_tool(user_id: str) -> dict:
    """
    Retrieves mock ownership data for a given user.

    Args:
        user_id: The user's display name (e.g. "Priya").

    Returns:
        A dict with the user's role ownership info, for example:
        {
            "Priya": {
                "owns": ["GBR-1234"],
                "role_type": "GBR",
                "department": "Engineering",
                "review_history": [...]
            }
        }
        Returns {"error": "..."} if the user is not found.

    TODO: The mock data below is intentionally minimal.
          You may expand it to support your Knowledge Graph.
    """
    for name, data in KG["users"].items():
        if name.lower() == user_id.strip().lower():
            return {name: data}

    return {"error": f"User '{user_id}' not found in Role DB."}



def document_tool(query: str) -> list:
    """
    Returns relevant policy document fragments for a given query.
    Each result includes a source_id that your agent MUST cite.

    Args:
        query: A natural-language or keyword search string.

    Returns:
        A list of matching document dicts, each containing:
        {
            "source_id": str,   <- cite this in every response
            "title":     str,
            "content":   str,
            "keywords":  list[str]
        }
        Returns an empty list if no documents match.

    TODO: Add more policy documents to support your Knowledge Graph.
    """
    query_lower = query.lower()

    return [
        document
        for document in KG["documents"]
        if any(
            keyword.lower() in query_lower
            for keyword in document.get("keywords", [])
        )
    ]
