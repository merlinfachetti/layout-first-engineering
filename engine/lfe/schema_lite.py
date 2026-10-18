"""Minimal JSON Schema (draft 2020-12 subset) validator, standard library only.

Only the keywords in SUPPORTED are understood. Any other keyword raises
UnsupportedKeyword instead of being silently ignored, so a schema can never
look stricter than what is actually enforced.
"""
from __future__ import annotations

import re

ANNOTATIONS = {"$schema", "$id", "title", "description", "$comment", "examples", "default"}
SUPPORTED = ANNOTATIONS | {
    "$ref", "$defs", "type", "enum", "const", "properties", "required",
    "additionalProperties", "propertyNames", "items", "minItems", "maxItems",
    "uniqueItems", "pattern", "minLength", "maxLength", "minimum", "maximum",
    "anyOf",
}


class UnsupportedKeyword(Exception):
    pass


def _type_ok(value, expected):
    # bool is a subclass of int in Python; JSON keeps them distinct.
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "null":
        return value is None
    raise UnsupportedKeyword(f"type {expected!r}")


def validate(instance, schema, root=None, path="$"):
    """Return a list of (path, message) violations."""
    root = schema if root is None else root
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise UnsupportedKeyword(", ".join(sorted(unknown)))
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise UnsupportedKeyword(f"$ref {ref!r}")
        return validate(instance, root["$defs"][ref[len("#/$defs/"):]], root, path)

    errors = []
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(instance, t) for t in types):
            return [(path, f"expected {'/'.join(types)}")]
    if "const" in schema and instance != schema["const"]:
        errors.append((path, f"must equal {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        errors.append((path, f"must be one of {schema['enum']}"))
    if "anyOf" in schema:
        if all(validate(instance, s, root, path) for s in schema["anyOf"]):
            errors.append((path, "matches none of the allowed shapes"))

    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append((path, f"does not match {schema['pattern']}"))
        if len(instance) < schema.get("minLength", 0):
            errors.append((path, "too short"))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append((path, "too long"))
    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append((path, f"must be >= {schema['minimum']}"))
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append((path, f"must be <= {schema['maximum']}"))
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append((path, f"needs at least {schema['minItems']} item(s)"))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append((path, f"allows at most {schema['maxItems']} item(s)"))
        if schema.get("uniqueItems"):
            seen = []
            for item in instance:
                if item in seen:
                    errors.append((path, "items must be unique"))
                    break
                seen.append(item)
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append((f"{path}.{key}", "is required"))
        props = schema.get("properties", {})
        for key, value in instance.items():
            if "propertyNames" in schema:
                errors += [(f"{path}.{key}", f"key {m}") for _, m in
                           validate(key, schema["propertyNames"], root, path)]
            if key in props:
                errors += validate(value, props[key], root, f"{path}.{key}")
            elif "additionalProperties" in schema:
                extra = schema["additionalProperties"]
                if extra is False:
                    errors.append((f"{path}.{key}", "is not allowed"))
                elif isinstance(extra, dict):
                    errors += validate(value, extra, root, f"{path}.{key}")
    return errors
