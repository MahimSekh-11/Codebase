import uuid
from typing import List, Dict, Any

class Chunker:
    """
    Takes parsed logical blocks and ensures they fit within model context limits.
    If a function/class is too large, it breaks it down further.
    """
    def __init__(self, max_chars: int = 2000, overlap: int = 200):
        self.max_chars = max_chars
        self.overlap = overlap

    def chunk_parsed_data(self, parsed_blocks: List[Dict[str, Any]], repo_id: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        final_chunks = []
        
        for block in parsed_blocks:
            content = block["content"]
            
            # If the block is small enough, keep it intact
            if len(content) <= self.max_chars:
                block["chunk_id"] = f"{repo_id}_{uuid.uuid4().hex[:8]}"
                block["repository_id"] = repo_id
                block["file_path"] = file_path
                block["language"] = language
                final_chunks.append(block)
            else:
                # Naive character splitting with overlap for oversized blocks
                start = 0
                lines = content.split('\n')
                total_lines = len(lines)
                
                # We'll chunk by lines to avoid cutting lines in half
                current_chunk_lines = []
                current_length = 0
                current_start_line_offset = 0
                
                for i, line in enumerate(lines):
                    line_len = len(line) + 1 # +1 for newline
                    if current_length + line_len > self.max_chars and current_chunk_lines:
                        # Save current chunk
                        chunk_str = '\n'.join(current_chunk_lines)
                        final_chunks.append({
                            "chunk_id": f"{repo_id}_{uuid.uuid4().hex[:8]}",
                            "repository_id": repo_id,
                            "file_path": file_path,
                            "language": language,
                            "symbol_name": block["symbol_name"],
                            "symbol_type": block["symbol_type"],
                            "start_line": block["start_line"] + current_start_line_offset,
                            "end_line": block["start_line"] + i - 1,
                            "content": chunk_str
                        })
                        # Start new chunk with overlap
                        overlap_lines_count = max(1, len(current_chunk_lines) // 4) # rough overlap
                        current_chunk_lines = current_chunk_lines[-overlap_lines_count:] + [line]
                        current_length = sum(len(l) + 1 for l in current_chunk_lines)
                        current_start_line_offset = i - overlap_lines_count
                    else:
                        current_chunk_lines.append(line)
                        current_length += line_len
                
                if current_chunk_lines:
                    chunk_str = '\n'.join(current_chunk_lines)
                    final_chunks.append({
                        "chunk_id": f"{repo_id}_{uuid.uuid4().hex[:8]}",
                        "repository_id": repo_id,
                        "file_path": file_path,
                        "language": language,
                        "symbol_name": block["symbol_name"],
                        "symbol_type": block["symbol_type"],
                        "start_line": block["start_line"] + current_start_line_offset,
                        "end_line": block["end_line"],
                        "content": chunk_str
                    })
                    
        return final_chunks
