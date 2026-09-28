"""
agent.py — RevAIsor Access Review Agent

Run from the command line:
    python agent.py "What role does Priya own?"
    python agent.py "What is the difference between GBR and ZGBR?"
    python agent.py "Show me Priya's access review history."
    python agent.py "Order a pizza for the office"

Your tasks:
  1. Set your API key in the environment.
  2. Implement build_system_prompt()
  3. Implement run_agent()
  4. Implement verify_response()
"""

from __future__ import annotations

import sys
import json
import os
import re

from tools import role_tool, document_tool
from router import route
from knowledge_graph import KG
# TODO 1: LLM setup
# TODO: initialize your client

from dotenv import load_dotenv
from google import genai

load_dotenv()  # Carga las variables del archivo .env

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError(
        "No se encontró GEMINI_API_KEY ni GOOGLE_API_KEY en el entorno o archivo .env"
    )

client = genai.Client(api_key=api_key)

# Tool registry — maps tool names to functions
TOOLS = {
    "role_tool":     role_tool,
    "document_tool": document_tool,
}

PREFERRED_MODELS = [
    "gemini-3.0-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]


def get_available_model() -> str:
    """Devuelve el primer modelo disponible para generación de contenido."""
    available_models = {}

    for model in client.models.list():
        name = model.name.removeprefix("models/")
        supported_actions = getattr(model, "supported_actions", [])

        if not supported_actions or "generateContent" in supported_actions:
            available_models[name] = True

    for model_name in PREFERRED_MODELS:
        if model_name in available_models:
            return model_name

    raise RuntimeError(
        "No hay modelos Gemini disponibles para generateContent con esta API key."
    )


ACTIVE_MODEL = get_available_model()
# print(f"Modelo seleccionado: {ACTIVE_MODEL}")

# TODO 2: Build the system prompt
def build_system_prompt() -> str:
    """
    Build the system prompt that defines the agent's behavior.

    Must include:
      - The agent's role and scope (access review only)
      - Citation rules: cite 'Role-DB' for role_tool, cite source_id for document_tool
      - Out-of-scope instructions: refuse politely without calling any tools
    """
    prompt = (
        "You are the RevAIsor Access Review Agent. Your only role is to assist users with access review queries and information that may con"
        "related to role ownership, role comparisons, and access review history." \
        "The agent must always cite sources for any information provided. "
        "You must provide accurate information based on the Knowledge Graph and the tools available. "
        "You have access to the following tools:\n"
        "1. role_tool: Retrieves ownership data for a given user. Cite as 'Role-DB'.\n"
        "2. document_tool: Retrieves documents by source_id. Cite as the provided source_id.\n"
        "3. Knowledge Graph: Contains known users and role types.\n"
        "You must not hallucinate information. If a query is out of scope, politely refuse without calling any tools."
    )
    return prompt



# TODO 3: Agent loop
def run_agent(query: str) -> str:
    """
    Main agent loop.

    Flow:
      1. Call route(query) to get intent, entities, and tools_to_call
      2. If out_of_scope, return a polite refusal without calling the LLM
      3. Execute the tools specified in tools_to_call
      4. Send system prompt + query + tool results to the LLM
      5. Return the final cited response

    Args:
        query: The raw user query string.

    Returns:
        str — the agent's final cited response.
    """
    decision = route(query)

    intent = decision["intent"]
    entities = decision["entities"]
    tools_to_call = decision["tools_to_call"]
    print(f"Router decision: Intent: {intent}, Entities: {entities}, Tools: {tools_to_call}")

    if intent == "out_of_scope":
        return "I'm sorry, but I can only help with access review queries. Please ask a question related to that."
    tool_results = []
    # Execute the tools
    for tool_name in tools_to_call:
        if tool_name == "role_tool":
            if not entities["users"]:
                return "Please specify a known user."
            result = role_tool(user_id=entities["users"][0])

        elif tool_name == "document_tool":
            result = document_tool(query=query)

        else:
            continue

        tool_results.append(result)
    

    # Send system prompt + query + tool results to the LLM
    final_prompt = build_system_prompt() + f"\n\nQuery: {query}\n\nTool Results: {tool_results}"
    response = client.models.generate_content(
        model=ACTIVE_MODEL,
        contents=final_prompt
    )

    return response.text

# TODO 4: Verifier
def verify_response(query: str, response: str) -> dict:
    """
    Rule-based check on the agent's final response. No LLM call.

    Checks:
      1. citation_present  : does the response mention at least one valid source_id?
      2. no_invented_roles : does the response mention role IDs not in the KG?

    Returns:
        {
            "status": "SUCCESS" | "FAIL",
            "checks": [
                { "name": str, "passed": bool, "detail": str },
                ...
            ]
        }
    """
    decision = route(query)
    intent = decision["intent"]

    if intent == "out_of_scope":
        refusal_markers = (
            "only help with access review",
            "out of scope",
            "access review queries",
            "cannot assist with that",
            "not related to access review",
            "I can only provide information related to access review",
        )

        refusal_present = any(
            marker in response.lower()
            for marker in refusal_markers
        )

        return {
            "status": "SUCCESS" if refusal_present else "FAIL",
            "checks": [
                {
                    "name": "Out-of-Scope Refusal",
                    "passed": refusal_present,
                    "detail": (
                        "The agent correctly refused the out-of-scope query."
                        if refusal_present
                        else "The agent did not provide an appropriate refusal."
                    ),
                }
            ],
        }
    valid_sources = {
        "Role-DB",
        *(
            document["source_id"]
            for document in KG.get("documents", [])
            if document.get("source_id")
        ),
    }

    cited_sources = {
        source
        for source in valid_sources
        if source.lower() in response.lower()
    }

    valid_role_ids = {
        role_id
        for user in KG.get("users", {}).values()
        for role_id in user.get("owns", [])
    }

    response_without_sources = response
    for source_id in valid_sources:
        response_without_sources = re.sub(
            re.escape(source_id),
            "",
            response_without_sources,
            flags=re.IGNORECASE,
        )

    mentioned_role_ids = {
        role_id.upper()
        for role_id in re.findall(
            r"(?<![A-Za-z0-9_-])(?:GBR|ZGBR)-\d+(?![A-Za-z0-9_-])",
            response_without_sources,
            flags=re.IGNORECASE,
        )
    }

    invented_roles = mentioned_role_ids - valid_role_ids

    citation_present = bool(cited_sources)
    no_invented_roles = not invented_roles

    return {
        "status": "SUCCESS" if citation_present and no_invented_roles else "FAIL",
        "checks": [
            {
                "name": "Citation Present",
                "passed": citation_present,
                "detail": (
                    f"Valid citations: {sorted(cited_sources)}"
                    if cited_sources
                    else "No valid citation found."
                ),
            },
            {
                "name": "No Invented Roles",
                "passed": no_invented_roles,
                "detail": (
                    "No invented role IDs found."
                    if no_invented_roles
                    else f"Unknown roles: {sorted(invented_roles)}"
                ),
            },
        ],
    }

# Entry point
def _print_section(title: str, content: str) -> None:
    width = 60
    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}")
    print(content)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python agent.py "<your query>"')
        sys.exit(1)

    user_query = sys.argv[1]

    print(f"\n{'═' * 60}")
    print(f"  REVAISOR ACCESS REVIEW AGENT")
    print(f"{'═' * 60}")
    print(f"  Query: {user_query!r}")

    response = run_agent(user_query)
    _print_section("AGENT ANSWER", response)

    verification = verify_response(user_query, response)
    status = verification["status"]
    checks = "\n".join(
        f"  {'✓' if c['passed'] else '✗'} {c['name']}: {c['detail']}"
        for c in verification["checks"]
    )
    _print_section("VERIFICATION", f"Status: {status}\n{checks}")

    print(f"\n{'═' * 60}\n")