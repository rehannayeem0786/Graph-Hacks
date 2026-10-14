"""
AST-based code parser — inspired by Graphify's deterministic extraction.

Parses Python files using the built-in `ast` module and extracts:
- Modules, Classes, Functions, Methods
- Imports and dependencies
- Call relationships
- Inheritance

Every edge is explained: we store the relationship type and line number.
No vector store needed — pure structural extraction.
"""

import ast
from pathlib import Path
from typing import Generator

from src.config import SUPPORTED_EXTENSIONS, SKIP_DIRS


class CodeNode:
    """Represents a node in the code graph."""

    def __init__(self, node_id: str, node_type: str, name: str,
                 file_path: str, line_start: int, line_end: int,
                 docstring: str = "", metadata: dict = None):
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.file_path = file_path
        self.line_start = line_start
        self.line_end = line_end
        self.docstring = docstring
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "name": self.name,
            "file": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
            **self.metadata,
        }


class CodeEdge:
    """Represents a relationship between two code nodes."""

    def __init__(self, source_id: str, target_id: str,
                 edge_type: str, line: int = 0, metadata: dict = None):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.line = line
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type,
            "line": self.line,
            **self.metadata,
        }


class ParseResult:
    """Result of parsing a codebase."""

    def __init__(self):
        self.nodes: list[CodeNode] = []
        self.edges: list[CodeEdge] = []

    def add_node(self, node: CodeNode):
        self.nodes.append(node)

    def add_edge(self, edge: CodeEdge):
        self.edges.append(edge)


def scan_directory(root_path: str) -> Generator[Path, None, None]:
    """Recursively scan directory for supported source files."""
    root = Path(root_path)
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts[:-1]):
            continue
        if path.suffix in SUPPORTED_EXTENSIONS:
            yield path


def _get_name(node: ast.expr) -> str | None:
    """Extract a name from an AST expression node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        value = _get_name(node.value)
        return f"{value}.{node.attr}" if value else node.attr
    elif isinstance(node, ast.Call):
        return _get_name(node.func)
    return None


def _parse_function(node, parent_id: str, file_path: str,
                    result: ParseResult, is_method: bool):
    """Parse a function or method definition."""
    prefix = "method" if is_method else "function"
    func_id = f"{prefix}:{file_path}:{node.name}"
    decorators = [_get_name(d) for d in node.decorator_list]
    result.add_node(CodeNode(
        node_id=func_id,
        node_type="Method" if is_method else "Function",
        name=node.name, file_path=file_path,
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
        docstring=ast.get_docstring(node) or "",
        metadata={
            "decorators": [d for d in decorators if d],
            "args": [a.arg for a in node.args.args],
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        },
    ))
    result.add_edge(CodeEdge(
        source_id=parent_id, target_id=func_id,
        edge_type="CONTAINS", line=node.lineno,
    ))
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            callee_name = _get_name(child.func)
            if callee_name:
                callee_id = f"call:{callee_name}"
                result.add_node(CodeNode(
                    node_id=callee_id, node_type="Call",
                    name=callee_name, file_path="",
                    line_start=child.lineno,
                    line_end=child.end_lineno or child.lineno,
                ))
                result.add_edge(CodeEdge(
                    source_id=func_id, target_id=callee_id,
                    edge_type="CALLS", line=child.lineno,
                ))

def _parse_class(node: ast.ClassDef, parent_id: str, file_path: str,
                 result: ParseResult):
    """Parse a class definition."""
    class_id = f"class:{file_path}:{node.name}"
    result.add_node(CodeNode(
        node_id=class_id, node_type="Class", name=node.name,
        file_path=file_path, line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
        docstring=ast.get_docstring(node) or "",
    ))
    result.add_edge(CodeEdge(
        source_id=parent_id, target_id=class_id,
        edge_type="CONTAINS", line=node.lineno,
    ))
    for base in node.bases:
        base_name = _get_name(base)
        if base_name:
            base_id = f"class:{base_name}"
            result.add_node(CodeNode(
                node_id=base_id, node_type="Class",
                name=base_name, file_path="",
                line_start=0, line_end=0,
            ))
            result.add_edge(CodeEdge(
                source_id=class_id, target_id=base_id,
                edge_type="INHERITS", line=node.lineno,
            ))
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _parse_function(item, class_id, file_path, result, is_method=True)


def parse_python_file(file_path: str, relative_path: str) -> ParseResult:
    """Parse a single Python file and extract the code graph."""
    result = ParseResult()
    try:
        source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=file_path)
    except (SyntaxError, UnicodeDecodeError):
        return result

    module_id = f"module:{relative_path}"
    result.add_node(CodeNode(
        node_id=module_id, node_type="Module", name=relative_path,
        file_path=relative_path, line_start=1,
        line_end=len(source.splitlines()),
        docstring=ast.get_docstring(tree) or "",
    ))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target_id = f"module:{alias.name}"
                result.add_node(CodeNode(
                    node_id=target_id, node_type="ExternalModule",
                    name=alias.name, file_path="",
                    line_start=node.lineno, line_end=node.lineno,
                ))
                result.add_edge(CodeEdge(
                    source_id=module_id, target_id=target_id,
                    edge_type="IMPORTS", line=node.lineno,
                ))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                target_id = f"module:{node.module}"
                result.add_node(CodeNode(
                    node_id=target_id, node_type="ExternalModule",
                    name=node.module, file_path="",
                    line_start=node.lineno, line_end=node.lineno,
                ))
                result.add_edge(CodeEdge(
                    source_id=module_id, target_id=target_id,
                    edge_type="IMPORTS", line=node.lineno,
                ))

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            _parse_class(node, module_id, relative_path, result)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _parse_function(node, module_id, relative_path, result, is_method=False)

    return result


def parse_codebase(root_path: str) -> ParseResult:
    """Parse an entire codebase directory into a code graph."""
    combined = ParseResult()
    root = Path(root_path)
    for file_path in scan_directory(root_path):
        relative = str(file_path.relative_to(root))
        lang = SUPPORTED_EXTENSIONS.get(file_path.suffix)
        if lang == "python":
            file_result = parse_python_file(str(file_path), relative)
            combined.nodes.extend(file_result.nodes)
            combined.edges.extend(file_result.edges)
    return combined
