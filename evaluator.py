"""
evaluator.py

This component is INDEPENDENT of the agent loop.
It acts as an external judge that critiques the agent's output.

It receives:
  1. The original user query
  2. The raw tool outputs
  3. The agent's final answer

And it returns a score with reasoning on three criteria:
  - GROUNDING  : Did the agent avoid hallucinating data not in the tool output?
  - CITATIONS  : Did the agent correctly map findings to source_ids?
  - RELEVANCE  : Did the agent directly answer the user's question?

Usage:
    python evaluator.py "What role does Priya own?"
"""

from __future__ import annotations

import sys
import json
import os

# LLM SDKs — choose one
from dotenv import load_dotenv
from google import genai
import agent
load_dotenv()  # Carga las variables del archivo .env

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError(
        "No se encontró GEMINI_API_KEY ni GOOGLE_API_KEY en el entorno o archivo .env"
    )

client = genai.Client(api_key=api_key)

PREFERRED_MODELS = [
    "gemini-3.0-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]

ACTIVE_MODEL = agent.get_available_model()
# print(f"Modelo seleccionado: {ACTIVE_MODEL}")

# TODO 2: Implement the evaluator
def evaluate(
    query:        str,
    tool_outputs: dict,
    agent_answer: str,
) -> dict:
    """
    Call an LLM to evaluate the agent's response.

    Args:
        query:        The original user question.
        tool_outputs: Raw output from all tool calls made by the agent.
        agent_answer: The agent's final natural-language response.

    Returns:
        A dict with keys: grounding_ok, citation_ok, relevance_ok, score, reasoning.
        Example:
        {
            "grounding_ok": True,
            "citation_ok":  True,
            "relevance_ok": True,
            "score":        "PASS",
            "reasoning":    "All claims trace to tool output. Citations are valid."
        }
    """

    evaluation_prompt = f"""
    You are an independent evaluator for an access-review agent.

    Evaluate the agent answer using ONLY the original query and the raw tool outputs.

    Original query:
    {query}

    Raw tool outputs:
    {json.dumps(tool_outputs, indent=2, ensure_ascii=False, default=str)}

    Agent answer:
    {agent_answer}

    Evaluation criteria:

    1. grounding_ok:
    True only if the factual claims in the answer are supported by the tool outputs.
    False if the answer invents users, roles, history, policies, or other facts.

    2. citation_ok:
    True only if:
    - role_tool information is cited as "Role-DB";
    - document_tool information cites the exact document source_id;
    - citations actually correspond to the claims being made.

    3. relevance_ok:
    True only if the answer directly addresses the original query.
    An appropriate refusal is relevant when the query is out of scope.

    Return ONLY valid JSON with this exact structure:
    {{
    "grounding_ok": true,
    "citation_ok": true,
    "relevance_ok": true,
    "score": "PASS",
    "reasoning": "Brief explanation"
    }}

    The score must be "PASS" only when all three criteria are true.
    """

    response = client.models.generate_content(
        model=ACTIVE_MODEL,
        contents=evaluation_prompt,
    )

    raw_text = (response.text or "").strip()

    # Protección básica frente a respuestas JSON envueltas en Markdown.
    if raw_text.startswith("```"):
        raw_text = raw_text.removeprefix("```json").removeprefix("```")
        raw_text = raw_text.removesuffix("```").strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return {
            "grounding_ok": False,
            "citation_ok": False,
            "relevance_ok": False,
            "score": "FAIL",
            "reasoning": f"Evaluator returned invalid JSON: {exc}",
        }

    required_keys = {
        "grounding_ok",
        "citation_ok",
        "relevance_ok",
        "score",
        "reasoning",
    }

    if not required_keys.issubset(result):
        return {
            "grounding_ok": False,
            "citation_ok": False,
            "relevance_ok": False,
            "score": "FAIL",
            "reasoning": "Evaluator response has an invalid structure.",
        }

    # El score final se calcula localmente para no confiar ciegamente
    # en el score textual producido por el modelo.
    all_checks_passed = all(
        bool(result[key])
        for key in ("grounding_ok", "citation_ok", "relevance_ok")
    )

    result["score"] = "PASS" if all_checks_passed else "FAIL"
    return result
    
def collect_tool_outputs(query: str) -> dict:
    """
    Reproduce la selección determinista de herramientas del agente.
    No ejecuta una llamada LLM.
    """
    from router import route
    from tools import role_tool, document_tool

    decision = route(query)
    entities = decision["entities"]
    outputs = {}

    for tool_name in decision["tools_to_call"]:
        if tool_name == "role_tool":
            if entities["users"]:
                outputs["role_tool"] = role_tool(entities["users"][0])
            else:
                outputs["role_tool"] = {
                    "error": "No known user was detected."
                }

        elif tool_name == "document_tool":
            outputs["document_tool"] = document_tool(query)

    return outputs

# TODO 3: Run the agent and evaluate its output
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python evaluator.py "<query>"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # TODO: 
    #   1. Import and run the agent to get the answer and capture tool outputs
    #   2. Call evaluate() with the results
    #   3. Print the verdict
    
    tool_outputs = collect_tool_outputs(query)


    agent_answer = agent.run_agent(query)
    verdict = evaluate(query, tool_outputs, agent_answer)

    print(json.dumps(verdict, indent=2, ensure_ascii=False))
