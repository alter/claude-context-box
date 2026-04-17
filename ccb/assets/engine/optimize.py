#!/usr/bin/env python3
"""
Optimize CLAUDE.md for token efficiency
"""

import re
from pathlib import Path

def optimize_claude_md():
    """Create optimized version of CLAUDE.md"""
    
    claude_md = Path('CLAUDE.md')
    if not claude_md.exists():
        print("❌ CLAUDE.md not found!")
        return
    
    content = claude_md.read_text(encoding='utf-8')
    
    # Create optimized version
    optimized = []
    
    # Extract only essential sections
    sections = {
        '## 🚨 КРИТИЧЕСКИЕ ПРАВИЛА': 'critical',
        '## ⛔ СТРОГО ЗАПРЕЩЕНО': 'forbidden',
        '## 📋 ОБЯЗАТЕЛЬНАЯ 7-ШАГОВАЯ ПРОЦЕДУРА': 'procedure',
        '## ⚡ БЫСТРЫЕ КОМАНДЫ': 'commands',
        '### Git Rules': 'git'
    }
    
    for section_header, section_name in sections.items():
        if section_header in content:
            start = content.find(section_header)
            # Find next section
            next_section = float('inf')
            for other_header in sections:
                if other_header != section_header:
                    pos = content.find(other_header, start + 1)
                    if pos > 0 and pos < next_section:
                        next_section = pos
            
            # Also check for ## headers
            next_h2 = content.find('\n## ', start + 1)
            if next_h2 > 0 and next_h2 < next_section:
                next_section = next_h2
            
            if next_section == float('inf'):
                section_content = content[start:]
            else:
                section_content = content[start:next_section]
            
            # Optimize section
            lines = section_content.strip().split('\n')
            optimized_lines = []
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                # Compress multiple spaces
                line = re.sub(r'\s+', ' ', line)
                # Remove markdown formatting where possible
                if line.startswith('- **') and line.endswith('**'):
                    line = line.replace('**', '')
                optimized_lines.append(line)
            
            optimized.append('\n'.join(optimized_lines))
    
    # Add essential reminders
    optimized.append("\n## 💡 QUICK REMINDERS")
    optimized.append("- Type 'refresh' after /compact")
    optimized.append("- Verify changes: scripts→run, libs→import")
    optimized.append("- Stop if verification fails")
    
    # Save optimized version
    optimized_path = Path('.claude/CLAUDE_OPTIMIZED.md')
    optimized_path.write_text('\n\n'.join(optimized), encoding='utf-8')
    
    # Calculate savings
    original_size = len(content)
    optimized_size = len('\n\n'.join(optimized))
    savings = (1 - optimized_size / original_size) * 100
    
    print(f"✅ Created optimized CLAUDE.md")
    print(f"   Original: {original_size} chars")
    print(f"   Optimized: {optimized_size} chars")
    print(f"   Saved: {savings:.1f}%")
    
    # Also create a super-compact version
    super_compact = [
        "# 7-STEP PROCEDURE",
        "1. Read PROJECT.llm",
        "2. Find module",
        "3. Read CONTEXT.llm", 
        "4. Analyze code",
        "5. Minimal changes",
        "6. Verify: run/import/test",
        "7. Update contexts",
        "",
        "NEVER: venv/ .git/ __pycache__/",
        "COMMANDS: u=update c=check refresh=reload",
        "After /compact: type 'refresh'"
    ]
    
    compact_path = Path('.claude/RULES_COMPACT.txt')
    compact_path.write_text('\n'.join(super_compact), encoding='utf-8')
    print(f"\n✅ Created super-compact version: {len('\n'.join(super_compact))} chars")

def main():
    optimize_claude_md()

if __name__ == "__main__":
    main()