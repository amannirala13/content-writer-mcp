# transport.py
from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Iterable, Set


class TransportEncoder:
    """
    Transport-safe serializer for Pydantic (v2 and v1), dataclasses, dicts, lists, and primitives.

    - Excludes callables automatically.
    - Excludes common runtime fields by default (e.g., 'runtime', 'handler', 'client', 'session').
    - Supports extra excludes and glob-like patterns.
    - Emits plain Python types that json.dumps(...) can serialize without custom encoders.
    """

    def __init__(
        self,
        *,
        by_alias: bool = True,
        mode: str = "json",
        exclude_fields: Set[str] | None = None,
        exclude_patterns: Set[str] | None = None,
        drop_callables: bool = True,  # True => remove; False => str(callable)
        max_depth: int | None = None,  # limit recursion depth; None = unlimited
    ) -> None:
        self.by_alias = by_alias
        self.mode = mode
        self.drop_callables = drop_callables
        self.max_depth = max_depth
        self.exclude_fields = {
            # sensible defaults for “runtime” stuff that shouldn’t be shipped
            "runtime",
            "handler",
            "client",
            "session",
            "_internal",
            "callable",
            "fn",
            "func",
        }
        if exclude_fields:
            self.exclude_fields |= set(exclude_fields)

        # compile simple glob-like patterns into regex
        patterns = exclude_patterns or set()
        self.exclude_regexes = [
            re.compile("^" + re.escape(pat).replace(r"\*", ".*") + "$") for pat in patterns
        ]

    # -------------------- public API --------------------

    def to_dict(self, obj: Any) -> Any:
        return self._visit(obj, depth=0)

    # -------------------- internal helpers --------------------

    def _excluded(self, key: str) -> bool:
        if key in self.exclude_fields:
            return True
        return any(rx.match(key) for rx in self.exclude_regexes)

    def _is_primitive(self, obj: Any) -> bool:
        return obj is None or isinstance(obj, (str, int, float, bool))

    def _is_callable(self, obj: Any) -> bool:
        # treat methods/functions/coroutines/generators as non-serializable
        return callable(obj)

    def _visit(self, obj: Any, *, depth: int) -> Any:
        if self.max_depth is not None and depth > self.max_depth:
            return None  # or "...truncated..."

        # primitives
        if self._is_primitive(obj):
            return obj

        # avoid callables anywhere
        if self._is_callable(obj):
            return None if self.drop_callables else str(obj)

        # Pydantic v2
        if hasattr(obj, "model_dump"):
            try:
                raw = obj.model_dump(mode=self.mode, by_alias=self.by_alias)
                return self._visit_mapping(raw, depth=depth + 1)
            except Exception:
                # last resort: stringify
                return str(obj)

        # Pydantic v1
        if hasattr(obj, "dict"):
            try:
                raw = obj.dict(by_alias=self.by_alias)
                return self._visit_mapping(raw, depth=depth + 1)
            except Exception:
                return str(obj)

        # dataclass
        if is_dataclass(obj):
            return self._visit_mapping(asdict(obj), depth=depth + 1)

        # mapping
        if isinstance(obj, Mapping):
            return self._visit_mapping(obj, depth=depth + 1)

        # iterable (but not str which is handled as primitive)
        if isinstance(obj, Iterable):
            return [self._visit(x, depth=depth + 1) for x in obj]

        # unknown objects -> try best effort: JSON via default=str then back
        try:
            return json.loads(json.dumps(obj, default=str))
        except Exception:
            return str(obj)

    def _visit_mapping(self, mapping: Mapping[str, Any], *, depth: int) -> dict:
        out: dict[str, Any] = {}
        for k, v in mapping.items():
            # skip excluded keys
            if isinstance(k, str) and self._excluded(k):
                continue
            out[k] = self._visit(v, depth=depth)
        return out


# friendly one-liner helper
def transportify(obj: Any, **kwargs) -> Any:
    """
    Serialize any object into a transport-safe structure (dict/list/primitives).
    kwargs are passed to TransportEncoder(...).
    """
    return TransportEncoder(**kwargs).to_dict(obj)