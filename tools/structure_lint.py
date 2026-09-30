"""Structural rules of the package, checked rather than reviewed.

Every check is registered as data. Output is `path:line: check: message`.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "quranic_phonemizer"
TOOLS = ROOT / "tools"

#: Which package may import which. A node absent from this map is an error,
#: so a new package must declare itself before anything may reach it. `""`
#: is the package root; `dataio` and `model` are leaves by construction.
ALLOWED: dict[str, set[str]] = {
    "": {"analysis", "model", "stop_editions"},
    "dataio": set(),
    "model": set(),
    "corpus": {"model"},
    # Waqf-mark overlays over a packed corpus: one mushaf edition as another.
    "stop_editions": {"corpus"},
    "orthography": {"dataio", "model"},
    "canon": {"dataio", "model", "orthography"},
    "engine": {"model"},
    "rules": {"engine", "model"},
    "render": {"dataio", "model"},
    "riwayat": {
        "canon", "corpus", "dataio", "engine", "model", "orthography", "rules",
        "stop_editions",
    },
    # The composition root. Nothing imports it, so a second riwayah stays
    # additive: it appears here and nowhere else.
    "api": {
        "canon", "corpus", "engine", "model", "orthography", "render",
        "riwayat", "stop_editions",
    },
    # The resolved request: words, boundaries, and the built score. It reads
    # the request layers and nothing of the projection above it.
    "session": {"canon", "corpus", "engine", "model"},
    # The native projection's facts. It reimplements what it needs and reads
    # only the resolved request, the model, the notation, the pen, and the
    # riwayah registry for the per-reading rule catalogue -- no edge to the
    # public assembler above it.
    "analysis": {"api", "model", "orthography", "render", "riwayat", "session"},
    # Above `api`: it imports the assembled bundle rather than re-deriving
    # it. It reaches the request layers through `session` now, so it keeps no
    # direct canon, corpus or engine edge -- a declared edge nothing exercises
    # fails `_unused_permissions`.
    "phonemize": {
        "api", "model", "orthography", "render", "session",
    },
}

#: The output alphabet is data and lives in one place. A phoneme string
#: anywhere else means a projection decision leaked into a decision layer.
PHONEME_MARKERS = ("ˤ", "ː", "m̃", "ñ")

#: Narrower than the package edge: `canon` reaches only one orthography module.
MODULE_ALLOWED: dict[tuple[str, str], set[str]] = {
    ("canon", "orthography"): {"adapter"},
    ("session", "canon"): {"build", "ledger"},
    ("session", "engine"): {"boundary_plan"},
    # The transformed cell view spells the performed letter with the pen; it
    # takes typed canon values and returns them, so no inventory or codepoint.
    ("analysis", "orthography"): {"write"},
}

#: Names a consumer outside this repository may import. Everything else that
#: nothing here calls is dead.
PUBLIC_API = frozenset({
    "Option", "VariantSelection", "KhilafId", "Riwayah", "Script",
    "Phonemizer", "Result", "UnknownExtraPhoneme", "UnknownRiwayah",
    "UnknownRule", "UnknownStopSign", "available_stop_signs",
    "available_variants", "supported_riwayat", "tajweed_rules",
})

#: Imports whose only purpose is the side effect of importing them.
SIDE_EFFECT = frozenset({"annotations"})

#: Roles the inventory loader supplies rather than any file naming them.
LOADER_ROLES = frozenset({
    "seat", "structural", "advice",
    "hamza_above", "hamza_below", "hamza_waw", "hamza_yaa",
})

#: The two callback protocols, by parameter names: `Classifier.look` and
#: `LexemePass`. A protocol is the only thing that hands an implementation a
#: parameter it may not want, so these are where an unread one is legitimate
#: -- and where it has to be `del`ed rather than left silent.
PROTOCOLS = {
    ("near", "plan", "at", "boundaries"),
    ("reading", "drafts", "lexicon", "scribe", "selection"),
}

MAX_FILE_LINES = 410
MAX_FUNCTION_LINES = 66

Problem = tuple[Path, int, str, str]


def _modules() -> Iterator[tuple[Path, ast.Module]]:
    for path in sorted(PACKAGE.rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def _node_of(path: Path) -> str:
    """A subpackage by its directory, a root module by its own name."""
    rel = path.relative_to(PACKAGE)
    if len(rel.parts) > 1:
        return rel.parts[0]
    return "" if rel.stem == "__init__" else rel.stem


def _targets(path: Path, tree: ast.Module) -> Iterator[tuple[int, list[str]]]:
    """Every internal import, as the dotted parts below the package root."""
    anchor = list(path.relative_to(PACKAGE).parts[:-1])
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            base = anchor[: len(anchor) - node.level + 1]
            if node.module:
                yield node.lineno, base + node.module.split(".")
            else:
                for alias in node.names:
                    yield node.lineno, base + [alias.name]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").startswith("quranic_phonemizer"):
                yield node.lineno, (node.module or "").split(".")[1:]
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("quranic_phonemizer"):
                    yield node.lineno, alias.name.split(".")[1:]


def import_graph() -> list[Problem]:
    """Package edges against `ALLOWED`, plus module cycles."""
    out: list[Problem] = []
    seen: set[tuple[str, str]] = set()
    edges: dict[str, set[str]] = {}
    for path, tree in _modules():
        source = _node_of(path)
        if source not in ALLOWED:
            out.append((path, 1, "import-graph", f"package {source!r} undeclared"))
            continue
        for line, parts in _targets(path, tree):
            target = parts[0] if parts else ""
            if target == source or not parts:
                continue
            if target not in ALLOWED:
                out.append((path, line, "import-graph", f"{target!r} undeclared"))
            elif target not in ALLOWED[source]:
                out.append((path, line, "import-graph",
                            f"{source or 'root'} may not import {target}"))
            else:
                narrow = MODULE_ALLOWED.get((source, target))
                if narrow and (len(parts) < 2 or parts[1] not in narrow):
                    out.append((path, line, "import-graph",
                                f"{source} reaches {target} only via {sorted(narrow)}"))
                seen.add((source, target))
        edges.setdefault(_dotted(path), set()).update(
            _dotted_target(path, parts) for _, parts in _targets(path, tree)
        )
    out.extend(_unused_permissions(seen))
    out.extend(_cycles(edges))
    return out


def _dotted(path: Path) -> str:
    rel = path.relative_to(PACKAGE)
    parts = list(rel.parts[:-1]) + ([] if rel.stem == "__init__" else [rel.stem])
    return ".".join(parts)


def _dotted_target(path: Path, parts: list[str]) -> str:
    del path
    return ".".join(parts)


def _unused_permissions(seen: set[tuple[str, str]]) -> list[Problem]:
    out = []
    for source, targets in ALLOWED.items():
        for target in sorted(targets - {t for s, t in seen if s == source}):
            out.append((PACKAGE / "__init__.py", 1, "import-graph",
                        f"{source or 'root'} -> {target} is permitted and unused"))
    return out


def _cycles(edges: dict[str, set[str]]) -> list[Problem]:
    """Any module reachable from itself. Import order is not a design."""
    out = []
    for start in sorted(edges):
        stack, seen = [start], set()
        while stack:
            node = stack.pop()
            for nxt in edges.get(node, ()):
                if nxt == start:
                    out.append((PACKAGE / start.replace(".", "/"), 1,
                                "import-graph", f"{start} imports itself via {node}"))
                    stack = []
                    break
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return out


def unused_imports() -> list[Problem]:
    out: list[Problem] = []
    for path, tree in _modules():
        bound = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bound[alias.asname or alias.name.split(".")[0]] = node.lineno
        used = _names_used(tree)
        for name, line in sorted(bound.items(), key=lambda kv: kv[1]):
            if name not in used and name not in SIDE_EFFECT:
                out.append((path, line, "unused-imports", f"{name} is never used"))
    return out


def _names_used(tree: ast.Module) -> set[str]:
    """Loads, attribute roots, and any identifier inside a string -- which
    covers `__all__` and a docstring naming what it re-exports."""
    import re

    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name):
                used.add(root.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            used.update(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", node.value))
    return used


def module_size() -> list[Problem]:
    out: list[Problem] = []
    for path, tree in _modules():
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > MAX_FILE_LINES:
            out.append((path, 1, "module-size",
                        f"{lines} lines, over {MAX_FILE_LINES}"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            span = (node.end_lineno or node.lineno) - node.lineno
            if span > MAX_FUNCTION_LINES:
                out.append((path, node.lineno, "module-size",
                            f"{node.name} is {span} lines, over {MAX_FUNCTION_LINES}"))
    return out


def dead_exports() -> list[Problem]:
    """A name in `__all__` that nothing imports and no public consumer needs."""
    out: list[Problem] = []
    readers = _identifiers_outside(PACKAGE)
    for path, tree in _modules():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not any(getattr(t, "id", None) == "__all__" for t in node.targets):
                continue
            for element in getattr(node.value, "elts", ()):
                name = getattr(element, "value", None)
                if not isinstance(name, str) or name in PUBLIC_API:
                    continue
                if readers.get(name, 0) <= _self_uses(tree, name):
                    out.append((path, node.lineno, "dead-exports",
                                f"{name} is exported and never imported"))
    return out


def _self_uses(tree: ast.Module, name: str) -> int:
    return sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == name
    )


def _identifiers_outside(package: Path) -> dict[str, int]:
    import re

    counts: dict[str, int] = {}
    for base in (package, ROOT / "tests", TOOLS):
        for path in base.rglob("*.py"):
            for token in re.findall(
                r"[A-Za-z_][A-Za-z_0-9]*", path.read_text(encoding="utf-8")
            ):
                counts[token] = counts.get(token, 0) + 1
    return counts


_SMOKE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("_smoke", sys.argv[1])
module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
except SystemExit:
    pass
"""


def tool_import_smoke() -> list[Problem]:
    """A committed tool that cannot be imported is a broken workflow."""
    out: list[Problem] = []
    for path in sorted(TOOLS.glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        done = subprocess.run(
            [sys.executable, "-c", _SMOKE, str(path)],
            capture_output=True, text=True, cwd=ROOT,
        )
        if done.returncode:
            out.append(
                (path, 1, "tool-import-smoke",
                 done.stderr.strip().splitlines()[-1])
            )
    return out


def phoneme_strings() -> list[Problem]:
    """Output notation outside `render/`."""
    out: list[Problem] = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if path.relative_to(PACKAGE).parts[0] == "render":
            continue
        for line, text in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for marker in PHONEME_MARKERS:
                if marker in text:
                    out.append((path, line, "phoneme-strings",
                                f"{marker!r} outside render/"))
    return out


def _role_sites(tree: ast.Module) -> Iterator[ast.expr]:
    """Every expression this module hands to a role lookup."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("has", "mark")
        ):
            yield from node.args
        elif (
            isinstance(node, ast.Compare)
            and _names_role(node.left)
            # An identity test compares enum members, never a role string.
            and not any(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops)
        ):
            yield from node.comparators


def _role_holders(trees: list[ast.Module]) -> set[str]:
    """Names the package uses where a role is expected.

    A constant holding a role is the third shape, after a bare literal and a
    set splatted into `has`. `DAGGER` and `CROSS_WORD_ROLE` are both this.
    """
    out: set[str] = set()
    for tree in trees:
        for site in _role_sites(tree):
            node = site.value if isinstance(site, ast.Starred) else site
            if isinstance(node, ast.Name):
                out.add(node.id)
            elif isinstance(node, ast.Attribute):
                out.add(node.attr)
    return out


def _role_literals(tree: ast.Module, holders: set[str]) -> Iterator[tuple[int, str]]:
    """Strings this module uses as an inventory role."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in holders for t in node.targets
        ):
            yield from _strings(ast.walk(node.value), node.lineno)
    for site in _role_sites(tree):
        yield from _strings([site], site.lineno)


def _names_role(node: ast.expr) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "role"


def _strings(nodes, line: int) -> Iterator[tuple[int, str]]:
    for node in nodes:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield line, node.value


def _declared_roles() -> set[str]:
    """Every role a derivation says it reads or an inventory says it writes."""
    import yaml

    out: set[str] = set()
    for _, tree in _modules():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "MarkEntry"
            ):
                out |= {
                    str(keyword.value.value)
                    for keyword in node.keywords
                    if keyword.arg == "role"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                }
            if not (isinstance(node, ast.Call) and _is_register(node.func)):
                continue
            for keyword in node.keywords:
                if keyword.arg == "requires":
                    out |= {
                        role for _, role in _strings(ast.walk(keyword.value), 0)
                    }
    for path in sorted((PACKAGE / "data").rglob("scripts/*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for section in ("evidences", "decorates", "advice", "structural"):
            entries = data.get(section) or {}
            # An entry that names no role is keyed by the scalar it is
            # written with, and the loader uses that as the role.
            out |= set(entries)
            if isinstance(entries, dict):
                out |= {
                    str(spec["role"])
                    for spec in entries.values()
                    if isinstance(spec, dict) and "role" in spec
                }
    return out


def _is_register(func: ast.expr) -> bool:
    return (isinstance(func, ast.Name) and func.id == "register") or (
        isinstance(func, ast.Attribute) and func.attr == "register"
    )


def role_vocabulary() -> list[Problem]:
    """A role name in code that no derivation and no inventory declares.

    `Cluster.has` answers `False` for an unknown role rather than raising, so
    without this a one-character slip is a silent output change.
    """
    declared = _declared_roles() | LOADER_ROLES
    modules = list(_modules())
    holders = _role_holders([tree for _, tree in modules])
    out: list[Problem] = []
    for path, tree in modules:
        for line, role in sorted(set(_role_literals(tree, holders))):
            if role not in declared:
                out.append((path, line, "role-vocabulary",
                            f"{role!r} is a role nothing declares"))
    return out


#: Attributes that name a rule's identity. Reading either to decide a
#: transformed status is what the transform lint forbids. The source columns
#: read occurrences for the silence law and the highlights read a rule family,
#: both legitimately, so the ban is scoped to the one transform module.
_RULE_IDENTITY = frozenset({"rule", "rule_id"})


def transform_rule_id() -> list[Problem]:
    """`transform.py` must decide status from the attribution kind and the
    letter, never from a rule identity ported out of the legacy respelling."""
    out: list[Problem] = []
    path = PACKAGE / "analysis" / "cells" / "transform.py"
    if not path.exists():
        return out
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _RULE_IDENTITY:
            out.append((path, node.lineno, "transform-rule-id",
                        f"reads .{node.attr} to decide a transformed status"))
    return out


def _parameters(node) -> tuple[str, ...]:
    """Positional and keyword-only names, less `self`. Keyed on names rather
    than on the function's own name, so an implementation is recognised by
    the protocol it satisfies."""
    args = node.args
    return tuple(
        arg.arg
        for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)
        if arg.arg != "self"
    )


def _is_stub(node) -> bool:
    """A Protocol's own body is a docstring and `...`: it declares the
    parameters and by construction reads none of them."""
    return not [
        statement
        for statement in node.body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
        )
    ]


def _accounted_for(node) -> set[str]:
    """Every name the body reads or deletes. A nested closure counts as the
    enclosing function reading it, which is what a pass built by a factory
    needs."""
    out = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
            out.add(inner.id)
        elif isinstance(inner, ast.Delete):
            out |= {t.id for t in inner.targets if isinstance(t, ast.Name)}
    return out


def signature_honesty() -> list[Problem]:
    """A protocol parameter an implementation neither reads nor `del`s.

    Nothing else here looks at signatures, so without this an absent `del`
    cannot be told from a parameter the author forgot.
    """
    out: list[Problem] = []
    for path, tree in _modules():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            parameters = _parameters(node)
            if parameters not in PROTOCOLS or _is_stub(node):
                continue
            accounted = _accounted_for(node)
            out.extend(
                (path, node.lineno, "signature-honesty",
                 f"{node.name} ignores {name!r} without a `del`")
                for name in parameters
                if name not in accounted
            )
    return out


CHECKS = {
    "import-graph": import_graph,
    "role-vocabulary": role_vocabulary,
    "transform-rule-id": transform_rule_id,
    "phoneme-strings": phoneme_strings,
}


def main() -> int:
    problems: list[Problem] = []
    for check in CHECKS.values():
        problems.extend(check())
    for path, line, check, message in sorted(
        problems, key=lambda p: (str(p[0]), p[1])
    ):
        print(f"{path.relative_to(ROOT)}:{line}: {check}: {message}")
    print(f"\n{len(problems)} problems in {len(list(PACKAGE.rglob('*.py')))} files")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
