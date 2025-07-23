"""
Improved installation logic proposal for claude-context-box
"""

def install_claude_context_box(force=False):
    """
    Install or update Claude Context Box
    
    Args:
        force: If True, completely replace existing installation
               If False, merge and preserve user changes
    """
    
    if force:
        # FORCE MODE: Complete replacement
        print("🔥 FORCE MODE: Complete replacement")
        
        # 1. Create backup (optional, but nice to have)
        if exists('.claude') or exists('CLAUDE.md'):
            backup_dir = create_timestamped_backup()
            print(f"📦 Backup created: {backup_dir}")
        
        # 2. Remove everything
        if exists('.claude'):
            shutil.rmtree('.claude')
            print("🗑️  Removed .claude directory")
            
        if exists('CLAUDE.md'):
            os.remove('CLAUDE.md')
            print("🗑️  Removed CLAUDE.md")
            
        if exists('PROJECT.llm'):
            os.remove('PROJECT.llm')
            print("🗑️  Removed PROJECT.llm")
        
        # 3. Fresh installation
        install_fresh()
        print("✅ Fresh installation completed")
        
    else:
        # NORMAL MODE: Smart merge
        print("🔄 NORMAL MODE: Smart update with merge")
        
        # 1. Update .claude scripts (always safe to update)
        if exists('.claude'):
            # Update each script, preserving user scripts
            for script in get_official_scripts():
                install_script(script)
            print("✅ Scripts updated")
        else:
            # First time installation
            install_claude_directory()
            print("✅ .claude directory created")
        
        # 2. Handle CLAUDE.md intelligently
        if exists('CLAUDE.md'):
            merge_claude_md()
            print("✅ CLAUDE.md merged (user customizations preserved)")
        else:
            create_claude_md()
            print("✅ CLAUDE.md created")
        
        # 3. Handle PROJECT.llm
        if not exists('PROJECT.llm'):
            create_project_llm()
            print("✅ PROJECT.llm created")
        # Never touch existing PROJECT.llm in normal mode
        
def merge_claude_md():
    """
    Intelligently merge CLAUDE.md preserving user changes
    """
    existing = read_file('CLAUDE.md')
    template = get_latest_claude_md_template()
    
    # Preserve user customizations:
    # 1. Custom command mappings
    user_commands = extract_command_mappings(existing)
    
    # 2. Additional user sections
    user_sections = extract_user_sections(existing)
    
    # 3. Modified rules
    user_rules = detect_user_modifications(existing, template)
    
    # Build merged version
    merged = template
    
    # Apply user command mappings
    if user_commands:
        merged = replace_command_mappings(merged, user_commands)
    
    # Append user sections
    if user_sections:
        merged += "\n\n# User Customizations\n\n" + user_sections
    
    # Create backup of existing
    write_file('CLAUDE.md.backup', existing)
    
    # Write merged version
    write_file('CLAUDE.md', merged)
    
    # Show what was preserved
    if user_commands or user_sections:
        print("  📝 Preserved:")
        if user_commands:
            print("     - Custom command mappings")
        if user_sections:
            print("     - User-added sections")

# Usage in install.py:
force = os.getenv('CLAUDE_FORCE', '').lower() in ('1', 'true', 'yes')
install_claude_context_box(force=force)