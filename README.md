# Mathematical-Engineer-Test-AI-Agents

Welcome to the RevAIsor technical test. Your task is to build a tool-augmented AI agent that helps security teams navigate access policies. The code in this repo is your starting point — read the comments and TODOs in each file carefully before you begin.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python agent.py "What role does Priya own?"
python agent.py "What is the difference between GBR and ZGBR?"
python agent.py "Show me Priya's access review history."
python agent.py "Order a pizza for the office"
```

# RevAIsor Access Review Agent

This implementation presents a tool-augmented agent for answering access-review questions about users, roles, role types, documents, and review history.

## Knowledge Graph Schema

The Knowledge Graph is stored in `knowledge_graph.py` as the `KG` dictionary. It contains:

- `users`: user records keyed by name. Each user may contain owned role IDs, role type information, department data, and review history.
- `role_types`: the supported role categories, such as `GBR` and `ZGBR`.
- `documents`: policy or reference documents. Each document contains a `source_id` and the information used for document-based answers.

The tools in `tools.py` read this shared structure instead of maintaining a separate copy of the data.

## Routing Strategy

Routing is deterministic and runs before the LLM. The router:

1. Extracts known users and role types from the query.
2. Classifies the query intent.
3. Selects the required tools.

User ownership and history questions use `role_tool`. Questions about role definitions or comparisons use `document_tool`. Queries that do not match the supported access-review intents are classified as `out_of_scope` and do not call tools.

This approach keeps tool selection predictable and avoids unnecessary LLM calls for unsupported requests.

## Agent and Citations

`agent.py` loads the API key from the environment or `.env` file and uses the Google GenAI client to generate the final response. The system prompt restricts the agent to access-review questions and requires citations:

- `Role-DB` for information returned by `role_tool`.
- The exact `source_id` for information returned by `document_tool`.

## Response Verification

`verify_response()` performs rule-based checks after the agent responds. For in-scope queries, it verifies that:

- The response contains at least one valid source.
- Role identifiers mentioned in the response use the expected format.
- Mentioned role IDs exist in the Knowledge Graph.
- Known document source IDs are removed before role detection, preventing identifiers such as `GBR-001` inside `Policy-Doc-GBR-001` from being treated as roles.

For out-of-scope queries, verification instead checks that the agent provided an appropriate refusal; citations are not required.

## External Evaluator

`evaluator.py` is reserved for the optional external LLM evaluator. Its purpose is to independently assess grounding, citation accuracy, and relevance using the original query, tool outputs, and final answer.

## API Key Configuration

Each user must provide their own Google Gemini API key. Create a `.env` file in the project root and add one of the following variables:

```env
GEMINI_API_KEY=your_api_key_here
```
or:
```env
GOOGLE_API_KEY=your_api_key_here
```

The application loads the key using `python-dotenv`. Each user is responsible for obtaining and configuring their own key and for any associated API usage or quota.

## Current Trade-offs

The project prioritizes a simple, deterministic and predictable workflow over a fully autonomous agent architecture.

- **Deterministic routing:** Keyword-based routing makes tool selection fast and reproducible, but it may not recognize every possible wording of a valid access-review question.
- **Shared Knowledge Graph:** Keeping the data in a single `KG` structure avoids inconsistencies between tools. 
- **Rule-based verification:** The verifier is transparent and inexpensive to run. Its checks focus on known citations, role identifiers, and out-of-scope refusals, so it does not provide the broader semantic analysis of an additional language model.
- **External evaluation:** An independent LLM evaluator can assess grounding, citation accuracy, and relevance in greater depth, but it introduces an additional API call, latency, and usage cost.
- **Model availability:** The application prefers lightweight Flash models to reduce latency and cost. Actual availability still depends on the configured API key, quota, and provider availability.
- **User-provided credentials:** Each user configures their own Gemini API key, which keeps credentials separate but requires an additional setup step.

These choices keep the implementation lightweight and easy to inspect while leaving room for future improvements such as semantic intent detection, persistent data storage, and more comprehensive response evaluation.