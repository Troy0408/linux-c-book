"""Conservative language hints for literal source blocks; never alter text.

The result is a presentation hint only. In particular, terminal transcripts
remain Terminal even if they contain C, shell commands or disassembly.
"""
import re


def language(text: str, kind: str, page: str) -> str:
    """Classify text without modifying it; ``page`` is reserved for overrides."""
    del page
    if not text.strip():
        return 'Plain'
    # Screen blocks are output/transcripts, often mixing several languages.
    if kind == 'screen':
        return 'Terminal'
    if kind != 'programlisting':
        return 'Plain'
    s = text.lstrip()
    if re.match(r'#![^\n]*(?:ba|da|k|z)?sh\b', s):
        return 'Shell'
    if re.search(r'(?m)^\s*#\s*include\s*[<"]', text):
        return 'C'
    if re.search(r'(?m)^\s*(?:\.PHONY\s*:|[A-Za-z_][\w./-]*\s*:(?!=)|(?:CFLAGS|LDFLAGS|CC|LD|OBJS|TARGET)\s*[:+?]?=)', text) and re.search(r'(?m)^\t\S|\$\([^)]+\)', text):
        return 'Make'
    if re.search(r'(?m)^\s*(?:\.(?:globl|global|section|text|data|type|size)\b|(?:mov|push|pop|call|ret|jmp|cmp|add|sub|lea|xor)[bwlq]?\s+[^\n]*(?:%[a-z]|\$))', text):
        return 'Assembler'
    if re.search(r'(?m)^\s*#\s*(?:include|define|ifdef|ifndef|endif|if|else|elif|pragma)\b|\b(?:int|char|void|float|double|unsigned|struct|union|typedef|const|static|extern|return|sizeof)\b\s*[\w*({;]|(?:\+\+|--|->|\bprintf\s*\()', text):
        return 'C'
    if re.search(r'(?m)^\s*(?:\$ |\(gdb\)|(?:[\w.-]+@[^\s:]+[^\n]*[$#] ))', text):
        return 'Terminal'
    if re.search(r'(?m)^\s*(?:export\s+\w+=|(?:for|while|if)\b.*;\s*(?:do|then)\b|(?:echo|cd|mkdir|chmod)\s+)', text):
        return 'Shell'
    return 'Plain'
