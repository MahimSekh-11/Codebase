import ast
import re
from typing import List, Dict, Any

class CodeParser:
    """
    Parses code to extract structure (classes, functions).
    Uses 'ast' for Python. Uses Regex/Fallback for other languages.
    Designed so tree-sitter can be easily swapped in later.
    """
    
    def parse_python(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Python code using AST to find functions and classes."""
        chunks = []
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                    
                    symbol_type = "class" if isinstance(node, ast.ClassDef) else "function"
                    
                    # Extract the snippet
                    snippet_lines = lines[start_line-1:end_line]
                    snippet = '\n'.join(snippet_lines)
                    
                    chunks.append({
                        "symbol_name": node.name,
                        "symbol_type": symbol_type,
                        "start_line": start_line,
                        "end_line": end_line,
                        "content": snippet
                    })
        except SyntaxError:
            # Fallback to plain chunking if syntax is invalid
            pass
            
        return chunks

    def parse_generic(self, content: str, language: str) -> List[Dict[str, Any]]:
        """A simple regex-based fallback for non-Python languages."""
        chunks = []
        lines = content.split('\n')
        
        # Extremely basic regex for JS/TS/Java/C++ functions/classes
        # Real world would use tree-sitter.
        pattern = re.compile(r'^(?:export\s+)?(?:default\s+)?(?:class|function)\s+([a-zA-Z0-9_]+)')
        
        current_symbol = None
        current_start = 0
        
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                if current_symbol:
                    # Save previous symbol
                    chunks.append({
                        "symbol_name": current_symbol,
                        "symbol_type": "unknown",
                        "start_line": current_start + 1,
                        "end_line": i,
                        "content": '\n'.join(lines[current_start:i])
                    })
                current_symbol = match.group(1)
                current_start = i
                
        if current_symbol:
            chunks.append({
                "symbol_name": current_symbol,
                "symbol_type": "unknown",
                "start_line": current_start + 1,
                "end_line": len(lines),
                "content": '\n'.join(lines[current_start:])
            })
            
        return chunks
        
    def parse_file(self, content: str, language: str, file_path: str) -> List[Dict[str, Any]]:
        if language == 'python':
            structs = self.parse_python(content, file_path)
            if structs:
                return structs
        
        # Fallback for others or if python ast failed/found nothing
        structs = self.parse_generic(content, language)
        if structs:
            return structs
            
        # Absolute fallback: treat the whole file as one chunk (Chunker will break it down if too big)
        return [{
            "symbol_name": "global",
            "symbol_type": "file",
            "start_line": 1,
            "end_line": len(content.split('\n')),
            "content": content
        }]
