# utils/openai_schema.py
from copy import deepcopy

def process_openai_json_schema(schema: dict) -> dict:
    """
    Make a Pydantic v2 JSON Schema acceptable to OpenAI Structured Outputs.
    - additionalProperties: false for every object
    - required: list of ALL property keys for every object
    - Recurses through properties, items, anyOf/allOf/oneOf, and $defs
    """
    s = deepcopy(schema)

    def walk(node: dict):
        if not isinstance(node, dict):
            return

        # Process $defs / definitions first (where Pydantic keeps models)
        for defs_key in ("$defs", "definitions"):
            if defs_key in node and isinstance(node[defs_key], dict):
                for _, sub in node[defs_key].items():
                    walk(sub)

        # If this node is an object, lock it down
        if node.get("type") == "object":
            props = node.get("properties") or {}
            node["properties"] = props
            # Forbid extras
            node["additionalProperties"] = False
            # Require all keys
            node["required"] = list(props.keys())
            # Recurse into each property
            for child in props.values():
                walk(child)

        # Arrays
        if node.get("type") == "array" and "items" in node:
            walk(node["items"])

        # Composition keywords
        for key in ("oneOf", "anyOf", "allOf"):
            if key in node and isinstance(node[key], list):
                for child in node[key]:
                    walk(child)

        # If there's a $ref, do nothing here—tightening the target inside $defs handles it.

    walk(s)
    return s