#!/usr/bin/env python3
"""
Bidirectional Notes Synchronization Script

This script provides intelligent bidirectional synchronization between:
- Logseq (bullets, folding structure)
- Obsidian (folder organization, prose)
- Quarto (interactive elements)

It uses a unified schema to determine which sections to sync and how to format them.
"""

import os
import re
import yaml
import json
import glob
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import frontmatter  # pip install python-frontmatter
import difflib  # For comparing changes
import hashlib  # For creating hashes of content to detect changes

# Load the schema
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), '..', 'unified_note_schema.json')

def load_schema():
    """Load the unified note schema."""
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Schema file not found at {SCHEMA_FILE}. Using default schema.")
        return {
            "schema_version": "1.0",
            "note_types": {
                "note": {
                    "sections": {
                        "overview": {"sync": True},
                        "notes": {"sync": True},
                        "references": {"sync": True}
                    }
                }
            }
        }

# Global schema
SCHEMA = load_schema()

# Configuration
CONFIG = {
    "logseq": {
        "required_yaml": ["title", "type"],
        "source_dir": "content/pages",
        "target_dir": "logseq/pages",
        "publish_url": "logseq.metamechanic.net",
        "syntax": "logseq",
        "templates_dir": "templates/logseq"
    },
    "obsidian": {
        "required_yaml": ["title", "tags", "created"],
        "source_dir": "content/pages",
        "target_dir": "obsidian",
        "publish_url": "obsidian.metamechanic.net",
        "syntax": "markdown",
        "templates_dir": "templates/obsidian",
        "folders": {
            "person": "People",
            "book": "Books",
            "article": "Articles",
            "place": "Places",
            "organization": "Organizations",
            "default": "Notes"
        }
    },
    "quarto": {
        "required_yaml": ["title", "format", "date", "categories"],
        "source_dir": "content/pages",
        "target_dir": "quarto/posts",
        "publish_url": "quarto.metamechanic.net",
        "syntax": "markdown",
        "templates_dir": "templates/quarto",
        "visualization_dir": "quarto/visualizations"
    }
}

def parse_frontmatter(file_path):
    """Parse frontmatter from a markdown file, handling both YAML and Logseq property formats."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if this is a Logseq file (properties with :: syntax)
        logseq_properties = {}
        if not content.startswith('---'):
            # Look for Logseq properties pattern: property:: value
            property_pattern = re.compile(r'^([a-zA-Z0-9_-]+):: (.*)$', re.MULTILINE)
            matches = property_pattern.findall(content)
            
            for key, value in matches:
                logseq_properties[key] = value
                
            # Remove properties from content
            content = property_pattern.sub('', content)
            return logseq_properties, content.strip()
        else:
            # Standard YAML frontmatter
            post = frontmatter.loads(content)
            return post.metadata, post.content
    except Exception as e:
        print(f"Error parsing frontmatter in {file_path}: {e}")
        return {}, ""

def extract_sections(content):
    """Extract sections from the content based on markdown headings."""
    sections = {}
    current_section = "content"
    section_content = []
    
    lines = content.split('\n')
    for line in lines:
        if re.match(r'^##\s+', line):  # Level 2 heading
            if section_content:
                sections[current_section] = '\n'.join(section_content).strip()
                section_content = []
            current_section = re.sub(r'^##\s+', '', line).lower().replace(' ', '_')
        else:
            section_content.append(line)
    
    # Add the last section
    if section_content:
        sections[current_section] = '\n'.join(section_content).strip()
    
    return sections

def get_section_hash(section_content):
    """Generate a hash of section content to detect changes."""
    return hashlib.md5(section_content.encode('utf-8')).hexdigest()

def determine_sync_direction(source_sections, target_sections, note_type):
    """Determine which sections should be synced and in which direction."""
    sync_directions = {}
    
    # Get schema for this note type
    type_schema = SCHEMA["note_types"].get(note_type, SCHEMA["note_types"]["note"])
    sections_schema = type_schema.get("sections", {})
    
    for section_name in set(list(source_sections.keys()) + list(target_sections.keys())):
        section_schema = sections_schema.get(section_name, {"sync": True})
        
        # Skip sections that shouldn't be synced
        if not section_schema.get("sync", True):
            if section_schema.get("obsidian_only", False):
                sync_directions[section_name] = "target_only"
            elif section_schema.get("logseq_only", False):
                sync_directions[section_name] = "source_only"
            elif section_schema.get("quarto_only", False):
                sync_directions[section_name] = "ignore"
            else:
                sync_directions[section_name] = "ignore"
            continue
        
        # Both exist - determine which is newer based on content
        if section_name in source_sections and section_name in target_sections:
            source_hash = get_section_hash(source_sections[section_name])
            target_hash = get_section_hash(target_sections[section_name])
            
            if source_hash == target_hash:
                sync_directions[section_name] = "none"  # No change needed
            else:
                # Check for substantive changes using diff ratio
                similarity = difflib.SequenceMatcher(None, 
                                                    source_sections[section_name], 
                                                    target_sections[section_name]).ratio()
                
                if similarity > 0.9:  # Very similar content
                    sync_directions[section_name] = "none"
                else:
                    # Here we could implement a more sophisticated strategy
                    # For now, prefer source content for simplicity
                    sync_directions[section_name] = "source_to_target"
        
        # Only in source - copy to target
        elif section_name in source_sections:
            sync_directions[section_name] = "source_to_target"
            
        # Only in target - copy to source
        else:
            sync_directions[section_name] = "target_to_source"
    
    return sync_directions

def convert_bullet_to_paragraph(content, platform="obsidian"):
    """Convert bullet points to paragraphs for a specific platform."""
    if platform not in ["obsidian", "quarto"]:
        return content  # No conversion needed
        
    # Split into lines
    lines = content.split('\n')
    paragraphs = []
    current_paragraph = ""
    in_code_block = False
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            if current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = ""
            continue
            
        # Preserve code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            paragraphs.append(line)
            continue
            
        if in_code_block:
            paragraphs.append(line)
            continue
        
        # If it's a heading, add it directly
        if line.strip().startswith('#'):
            if current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = ""
            paragraphs.append(line)
            continue
            
        # Remove bullet points and indentation
        clean_line = re.sub(r'^[\s]*-\s*', '', line)
        
        # If it's a sub-bullet, make it part of the current paragraph
        if line.startswith('  ') or line.startswith('\t'):
            if current_paragraph:
                current_paragraph += " " + clean_line
            else:
                current_paragraph = clean_line
        else:
            # New top-level bullet becomes a new paragraph
            if current_paragraph:
                paragraphs.append(current_paragraph)
            current_paragraph = clean_line
    
    # Add the last paragraph
    if current_paragraph:
        paragraphs.append(current_paragraph)
        
    return '\n\n'.join(paragraphs)

def convert_paragraph_to_bullet(content):
    """Convert paragraphs to bullet points for Logseq."""
    # Split content into paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    result = []
    
    for para in paragraphs:
        lines = para.strip().split('\n')
        
        # Check if it's a heading
        if lines and re.match(r'^#+\s+', lines[0]):
            result.append(lines[0])
            lines = lines[1:]
            if lines:
                # Convert remaining lines to bullets
                for line in lines:
                    result.append(f"- {line}")
            else:
                # Empty heading, add placeholder bullet
                result.append("- ")
        else:
            # Regular paragraph - convert to bullets
            for i, line in enumerate(lines):
                if i == 0:
                    result.append(f"- {line}")
                else:
                    # Subsequent lines are indented
                    result.append(f"  {line}")
    
    return '\n'.join(result)

def convert_section_format(section_content, note_type, section_name, source_format, target_format):
    """Convert section content between formats based on schema."""
    # Get schema for this note type and section
    type_schema = SCHEMA["note_types"].get(note_type, SCHEMA["note_types"]["note"])
    section_schema = type_schema.get("sections", {}).get(section_name, {})
    
    source_format_type = section_schema.get(f"{source_format}_format", "bullets")
    target_format_type = section_schema.get(f"{target_format}_format", "paragraphs")
    
    # No conversion needed if formats are the same
    if source_format_type == target_format_type:
        return section_content
    
    # Convert between formats
    if source_format_type == "bullets" and target_format_type == "paragraphs":
        return convert_bullet_to_paragraph(section_content)
    elif source_format_type == "paragraphs" and target_format_type == "bullets":
        return convert_paragraph_to_bullet(section_content)
    elif source_format_type == "bullets" and target_format_type == "blockquotes":
        # Convert bullets to blockquotes
        lines = section_content.split('\n')
        return '\n'.join([f"> {re.sub(r'^[\s]*-\s*', '', line)}" for line in lines])
    elif source_format_type == "blockquotes" and target_format_type == "bullets":
        # Convert blockquotes to bullets
        lines = section_content.split('\n')
        return '\n'.join([f"- {re.sub(r'^>\s*', '', line)}" for line in lines])
    
    # Default: return original content
    return section_content

def merge_sections(source_sections, target_sections, note_type, sync_directions, source_platform, target_platform):
    """Merge sections based on sync directions."""
    merged_sections = {}
    
    for section_name, direction in sync_directions.items():
        if direction == "none":
            # No change needed, keep target content
            merged_sections[section_name] = target_sections.get(section_name, "")
        elif direction == "source_to_target":
            # Convert source format to target format
            source_content = source_sections.get(section_name, "")
            merged_sections[section_name] = convert_section_format(
                source_content, note_type, section_name, source_platform, target_platform)
        elif direction == "target_to_source":
            # Keep target content as is
            merged_sections[section_name] = target_sections.get(section_name, "")
        elif direction == "target_only":
            # Section should only exist in target
            if section_name in target_sections:
                merged_sections[section_name] = target_sections[section_name]
        elif direction == "source_only":
            # Section should only exist in source when syncing to source
            # For target, we skip it
            pass
    
    return merged_sections

def get_target_folder(metadata, platform):
    """Determine the target folder for Obsidian based on metadata."""
    if platform != 'obsidian':
        return ""
        
    note_type = metadata.get('type', 'default').lower()
    folders = CONFIG[platform]['folders']
    
    # If the note type matches a folder, use it
    if note_type in folders:
        return folders[note_type]
    
    # Check if any tags match folder names
    tags = metadata.get('tags', [])
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(',')]
        
    for tag in tags:
        tag = tag.lower()
        if tag in folders:
            return folders[tag]
    
    # Default folder
    return folders['default']

def create_target_path(file_path, source_dir, platform, metadata, verbose=False):
    """Create the appropriate target path based on platform and metadata."""
    if verbose:
        print(f"  Creating target path for: {file_path}")
        print(f"  Source dir: {source_dir}")
        print(f"  Target platform: {platform}")
    
    # Special handling for Quarto as source
    if source_dir.endswith('quarto/posts') or '/quarto/posts/' in source_dir or \
       source_dir.endswith('quarto/visualizations') or '/quarto/visualizations/' in source_dir:
        filename = os.path.basename(file_path)
        # Strip .qmd extension if present and replace with .md
        if filename.endswith('.qmd'):
            filename = filename[:-4] + '.md'
        
        if verbose:
            print(f"  Quarto source detected, using filename: {filename}")
        
        if platform == 'logseq':
            return os.path.join(CONFIG[platform]['target_dir'], filename)
        elif platform == 'content':
            return os.path.join(CONFIG['logseq']['source_dir'], filename)
        elif platform == 'obsidian':
            folder = get_target_folder(metadata, platform)
            return os.path.join(CONFIG[platform]['target_dir'], folder, filename)
    
    # Special handling for Obsidian as source because of its folder structure
    elif source_dir.endswith('obsidian') or '/obsidian/' in source_dir:
        # Just get the filename without the path for Obsidian sources
        filename = os.path.basename(file_path)
        
        if verbose:
            print(f"  Obsidian source detected, using filename: {filename}")
        
        if platform == 'logseq':
            return os.path.join(CONFIG[platform]['target_dir'], filename)
        elif platform == 'content':
            # When syncing from Obsidian to content
            return os.path.join(CONFIG['logseq']['source_dir'], filename)
        elif platform == 'quarto':
            # Check if it should go to visualizations or regular posts
            if metadata.get('interactive', False) or 'visualization' in metadata.get('tags', []):
                # Change extension to .qmd for Quarto markdown with code execution
                if filename.endswith('.md'):
                    filename = filename[:-3] + '.qmd'
                return os.path.join(CONFIG[platform]['visualization_dir'], filename)
            else:
                return os.path.join(CONFIG[platform]['target_dir'], filename)
    else:
        # Normal case - handle relative path from source_dir
        relative_path = os.path.relpath(file_path, source_dir)
        
        if verbose:
            print(f"  Standard source, relative path: {relative_path}")
        
        if platform == 'logseq':
            # Logseq preserves the original file structure
            return os.path.join(CONFIG[platform]['target_dir'], relative_path)
        
        elif platform == 'obsidian':
            # Obsidian organizes by folder based on note type/tags
            folder = get_target_folder(metadata, platform)
            filename = os.path.basename(relative_path)
            return os.path.join(CONFIG[platform]['target_dir'], folder, filename)
        
        elif platform == 'quarto':
            # Quarto can have special handling for interactive content
            if metadata.get('interactive', False) or 'visualization' in metadata.get('tags', []):
                filename = os.path.basename(relative_path)
                # Change extension to .qmd for Quarto markdown with code execution
                if filename.endswith('.md'):
                    filename = filename[:-3] + '.qmd'
                return os.path.join(CONFIG[platform]['visualization_dir'], filename)
            else:
                filename = os.path.basename(relative_path)
                return os.path.join(CONFIG[platform]['target_dir'], filename)
        
    # Default fallback
    return os.path.join(CONFIG[platform]['target_dir'], os.path.basename(file_path))

def merge_frontmatter(source_meta, target_meta, platform, file_path=None):
    """Merge frontmatter from source and target, using schema guidance."""
    # Start with target and update with source, but preserve platform-specific fields
    merged = {**target_meta}
    
    # Get the note type for schema reference
    note_type = source_meta.get("type", "note").lower()
    
    # Update with source metadata except for platform-specific fields
    for key, value in source_meta.items():
        # Skip platform-specific keys if they already exist in target
        if key in CONFIG[platform]["required_yaml"] and key in target_meta:
            continue
        merged[key] = value
    
    # Ensure required fields for the platform exist
    for key in CONFIG[platform]["required_yaml"]:
        if key not in merged:
            if key == "title" and file_path and Path(file_path).stem:
                merged[key] = Path(file_path).stem.replace("-", " ").title()
            elif key == "date" or key == "created":
                merged[key] = datetime.now().strftime("%Y-%m-%d")
            elif key == "format":
                merged[key] = "html"
            elif key == "type":
                merged[key] = note_type
            elif key == "tags" or key == "categories":
                # Convert between tags and categories if needed
                if key == "tags" and "categories" in source_meta:
                    merged[key] = source_meta["categories"]
                elif key == "categories" and "tags" in source_meta:
                    merged[key] = source_meta["tags"]
                else:
                    merged[key] = []
            else:
                merged[key] = ""
    
    # For Quarto, handle special case of categories/tags conversion
    if platform == "quarto" and "tags" in source_meta and "categories" not in merged:
        merged["categories"] = source_meta["tags"]
    
    return merged

def reconstruct_content(sections):
    """Reconstruct full content from sections."""
    content = []
    
    # Add main content if it exists outside sections
    if "content" in sections:
        content.append(sections["content"])
    
    # Add each section with its heading
    for section_name, section_content in sections.items():
        if section_name != "content" and section_content.strip():
            heading_name = " ".join(word.capitalize() for word in section_name.split('_'))
            content.append(f"## {heading_name}\n\n{section_content}")
    
    return "\n\n".join(content)

def sync_file(source_file, source_platform, target_platform, verbose=False):
    """Sync a single file between platforms with bidirectional support."""
    if verbose:
        print(f"\nSyncing file: {source_file}")
        print(f"  From: {source_platform} to {target_platform}")
    
    # Parse source frontmatter and content
    source_meta, source_content = parse_frontmatter(source_file)
    
    if verbose:
        print(f"  Source metadata: {source_meta}")
    
    # Get note type for schema reference
    note_type = source_meta.get("type", "note").lower()
    
    # Extract sections from source content
    source_sections = extract_sections(source_content)
    
    if verbose:
        print(f"  Source sections: {list(source_sections.keys())}")
    
    # Initialize sync_directions
    sync_directions = {}
    
    # Determine source directory for relative path calculation
    if source_platform == 'content':
        source_dir = CONFIG['logseq']['source_dir']
    elif source_platform == 'obsidian':
        source_dir = CONFIG[source_platform]['target_dir']
    elif source_platform == 'quarto':
        # For Quarto, handle both posts and visualizations
        if source_file.startswith(CONFIG[source_platform]['visualization_dir']):
            source_dir = CONFIG[source_platform]['visualization_dir']
        else:
            source_dir = CONFIG[source_platform]['target_dir']
    else:
        source_dir = CONFIG[source_platform]['source_dir']
    
    if verbose:
        print(f"  Source directory: {source_dir}")
    
    # Determine target path
    target_file = create_target_path(
        source_file, 
        source_dir,
        target_platform, 
        source_meta
    )
    
    if verbose:
        print(f"  Target file: {target_file}")
    
    # Create target directory if it doesn't exist
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    
    # Get target content if it exists
    if os.path.exists(target_file):
        if verbose:
            print(f"  Target file exists, merging content")
        
        target_meta, target_content = parse_frontmatter(target_file)
        target_sections = extract_sections(target_content)
        
        if verbose:
            print(f"  Target metadata: {target_meta}")
            print(f"  Target sections: {list(target_sections.keys())}")
        
        # Determine which sections to sync in which direction
        sync_directions = determine_sync_direction(source_sections, target_sections, note_type)
        
        if verbose:
            print(f"  Sync directions: {sync_directions}")
        
        # Merge sections
        merged_sections = merge_sections(
            source_sections, target_sections, note_type, 
            sync_directions, source_platform, target_platform
        )
        
        # Merge frontmatter
        merged_meta = merge_frontmatter(source_meta, target_meta, target_platform, target_file)
    else:
        if verbose:
            print(f"  Target file does not exist, creating new file")
        
        # Target doesn't exist, convert all sections
        merged_sections = {}
        for section_name, section_content in source_sections.items():
            merged_sections[section_name] = convert_section_format(
                section_content, note_type, section_name, 
                source_platform, target_platform
            )
        
        # Convert frontmatter
        merged_meta = merge_frontmatter(source_meta, {}, target_platform, target_file)
    
    # Reconstruct the full content
    merged_content = reconstruct_content(merged_sections)
    
    # Write the file with the appropriate format based on platform
    if target_platform == 'logseq':
        # Write with Logseq property format
        with open(target_file, 'w', encoding='utf-8') as f:
            # Write properties at the top
            for key, value in merged_meta.items():
                f.write(f"{key}:: {value}\n")
            
            # Add a blank line if we have properties
            if merged_meta:
                f.write("\n")
                
            f.write(merged_content)
    else:
        # Write with standard YAML frontmatter
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write("---\n")
            f.write(yaml.dump(merged_meta, default_flow_style=False))
            f.write("---\n\n")
            f.write(merged_content)
    
    print(f"Synced: {source_file} -> {target_file}")
    
    # If we're syncing bidirectionally, sync back to source where needed
    if sync_directions.get("bidirectional", False):
        # Only do this if target existed and had content to merge back
        if os.path.exists(target_file) and any(d == "target_to_source" for d in sync_directions.values()):
            print(f"Syncing back: {target_file} -> {source_file}")
            sync_file(target_file, target_platform, source_platform, verbose)

def sync_all_files(source_platform, target_platform, bidirectional=False, verbose=False):
    """Sync all files from source to target platform, handling platform-specific folder structures."""
    # Handle different source platforms
    if source_platform == 'content':
        source_dir = CONFIG['logseq']['source_dir']
        search_pattern = os.path.join(source_dir, "**/*.md")
    elif source_platform == 'obsidian':
        # For Obsidian, we need to handle its folder structure
        source_dir = CONFIG[source_platform]['target_dir']
        # Search in all subfolders of Obsidian
        search_pattern = os.path.join(source_dir, "**/*.md")
    elif source_platform == 'quarto':
        # For Quarto, we need to handle both posts and visualizations
        source_dir = os.path.dirname(CONFIG[source_platform]['target_dir'])  # Get the quarto base directory
        # Create a list to collect files from multiple directories
        quarto_files = []
        # Look in both posts and visualizations directories
        quarto_files.extend(glob.glob(os.path.join(CONFIG[source_platform]['target_dir'], "**/*.md"), recursive=True))
        quarto_files.extend(glob.glob(os.path.join(CONFIG[source_platform]['target_dir'], "**/*.qmd"), recursive=True))
        quarto_files.extend(glob.glob(os.path.join(CONFIG[source_platform]['visualization_dir'], "**/*.md"), recursive=True))
        quarto_files.extend(glob.glob(os.path.join(CONFIG[source_platform]['visualization_dir'], "**/*.qmd"), recursive=True))
        
        if verbose:
            print(f"Found {len(quarto_files)} files in Quarto directories")
            for file in quarto_files:
                print(f"  - {file}")
        
        # Process each Quarto file
        for file_path in quarto_files:
            # Skip files in specific directories that should be ignored
            if '/_site/' in file_path or '/.quarto/' in file_path:
                if verbose:
                    print(f"Skipping generated file: {file_path}")
                continue
                
            # Apply the sync process
            if verbose:
                print(f"Processing Quarto file: {file_path}")
            sync_file(file_path, source_platform, target_platform, verbose)
        
        print(f"Synchronized Quarto files to {target_platform}")
        return
    else:
        source_dir = CONFIG[source_platform]['source_dir']
        search_pattern = os.path.join(source_dir, "**/*.md")
    
    # For platforms other than Quarto, use the normal approach
    # Find all markdown files in source directory and its subdirectories
    for file_path in glob.glob(search_pattern, recursive=True):
        # Skip files in specific directories that should be ignored
        if '.obsidian/' in file_path or '/_site/' in file_path or '/.quarto/' in file_path:
            if verbose:
                print(f"Skipping config/generated file: {file_path}")
            continue
            
        # Apply the sync process
        if verbose:
            print(f"Processing file: {file_path}")
        sync_file(file_path, source_platform, target_platform, verbose)
    
    print(f"Synchronized all files from {source_platform} to {target_platform}")

def sync_assets(source_dir, platforms):
    """Sync assets to all platform directories."""
    assets_source = os.path.join(os.path.dirname(source_dir), "assets")
    if not os.path.exists(assets_source):
        return
        
    for platform in platforms:
        if platform == 'logseq':
            assets_target = os.path.join(os.path.dirname(CONFIG[platform]['target_dir']), "assets")
        elif platform == 'obsidian':
            assets_target = os.path.join(CONFIG[platform]['target_dir'], "assets")
        elif platform == 'quarto':
            assets_target = os.path.join(os.path.dirname(CONFIG[platform]['target_dir']), "assets")
        
        os.makedirs(assets_target, exist_ok=True)
        
        # Copy all assets
        for asset in glob.glob(os.path.join(assets_source, "**"), recursive=True):
            if os.path.isfile(asset):
                relative_path = os.path.relpath(asset, assets_source)
                target_path = os.path.join(assets_target, relative_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(asset, target_path)
                print(f"Synced asset: {relative_path}")

def create_folder_structure():
    """Create the necessary folder structure for all platforms."""
    # Create main directories
    for platform, config in CONFIG.items():
        os.makedirs(config['target_dir'], exist_ok=True)
        
        # Create platform-specific folder structure
        if platform == 'obsidian':
            for folder in config['folders'].values():
                os.makedirs(os.path.join(config['target_dir'], folder), exist_ok=True)
        elif platform == 'quarto':
            os.makedirs(config['visualization_dir'], exist_ok=True)
    
    # Create template directories
    for platform, config in CONFIG.items():
        templates_dir = config.get('templates_dir')
        if templates_dir:
            os.makedirs(templates_dir, exist_ok=True)
    
    # Create content directory if it doesn't exist
    os.makedirs(CONFIG['logseq']['source_dir'], exist_ok=True)
    
    # Create assets directory
    os.makedirs(os.path.join(os.path.dirname(CONFIG['logseq']['source_dir']), "assets"), exist_ok=True)
    
    # Ensure schema directory exists - create full path if needed
    schema_dir = os.path.dirname(SCHEMA_FILE)
    if schema_dir and schema_dir != "":
        os.makedirs(schema_dir, exist_ok=True)
    
    # Create schema file if it doesn't exist
    if not os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'w', encoding='utf-8') as f:
            json.dump(SCHEMA, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Bidirectional sync between Logseq, Obsidian, and Quarto')
    parser.add_argument('--source', choices=['logseq', 'obsidian', 'quarto', 'content'], 
                        help='Source platform to sync from')
    parser.add_argument('--target', choices=['logseq', 'obsidian', 'quarto', 'all'],
                        help='Target platform to sync to')
    parser.add_argument('--bidirectional', action='store_true',
                        help='Enable bidirectional sync (sync changes back to source)')
    parser.add_argument('--init', action='store_true',
                        help='Initialize folder structure and schema')
    parser.add_argument('--file', 
                        help='Sync a specific file (relative to source directory)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    args = parser.parse_args()
    
    verbose = args.verbose
    
    if verbose:
        print("Running in verbose mode")
    
    # Initialize if requested
    if args.init:
        create_folder_structure()
        print("Initialized folder structure and schema.")
        return
    
    # Default source is content
    source = args.source or 'content'
    
    if verbose:
        print(f"Source platform: {source}")
    
    # Sync a specific file if requested
    if args.file:
        if verbose:
            print(f"Syncing specific file: {args.file}")
        
        # Handle 'content' as a special case
        if source == 'content':
            file_path = os.path.join(CONFIG['logseq']['source_dir'], args.file)
        elif source == 'obsidian':
            # For Obsidian, look in all subfolders
            obsidian_dir = CONFIG['obsidian']['target_dir']
            found = False
            for folder in CONFIG['obsidian']['folders'].values():
                test_path = os.path.join(obsidian_dir, folder, args.file)
                if os.path.exists(test_path):
                    file_path = test_path
                    found = True
                    break
            if not found:
                # Try just the base directory
                test_path = os.path.join(obsidian_dir, args.file)
                if os.path.exists(test_path):
                    file_path = test_path
                    found = True
            if not found:
                print(f"Error: File not found in any Obsidian folder: {args.file}")
                return
        elif source == 'quarto':
            # For Quarto, check both posts and visualizations
            posts_path = os.path.join(CONFIG['quarto']['target_dir'], args.file)
            if os.path.exists(posts_path):
                file_path = posts_path
            else:
                # Try with .qmd extension
                posts_qmd_path = os.path.join(CONFIG['quarto']['target_dir'], f"{os.path.splitext(args.file)[0]}.qmd")
                if os.path.exists(posts_qmd_path):
                    file_path = posts_qmd_path
                else:
                    # Try visualizations folder
                    viz_path = os.path.join(CONFIG['quarto']['visualization_dir'], args.file)
                    if os.path.exists(viz_path):
                        file_path = viz_path
                    else:
                        # Try with .qmd extension
                        viz_qmd_path = os.path.join(CONFIG['quarto']['visualization_dir'], f"{os.path.splitext(args.file)[0]}.qmd")
                        if os.path.exists(viz_qmd_path):
                            file_path = viz_qmd_path
                        else:
                            print(f"Error: File not found in any Quarto location: {args.file}")
                            return
        else:
            file_path = os.path.join(CONFIG[source]['source_dir'], args.file)
        
        if verbose:
            print(f"Full file path: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
        
        if args.target == 'all':
            for platform in ['logseq', 'obsidian', 'quarto']:
                if platform != source:
                    sync_file(file_path, source, platform, verbose)
        else:
            sync_file(file_path, source, args.target, verbose)
        
        return
    
    # Sync all files
    if args.target == 'all':
        for platform in ['logseq', 'obsidian', 'quarto']:
            if platform != source:
                sync_all_files(source, platform, args.bidirectional, verbose)
        
        # Sync assets to all platforms
        # Handle special cases for source directory
        if source == 'content':
            source_dir = CONFIG['logseq']['source_dir']
        elif source == 'obsidian':
            source_dir = CONFIG['obsidian']['target_dir']
        elif source == 'quarto':
            source_dir = os.path.dirname(CONFIG['quarto']['target_dir'])  # Use quarto root
        else:
            source_dir = CONFIG[source]['source_dir']
            
        sync_assets(source_dir, 
                   [p for p in ['logseq', 'obsidian', 'quarto'] if p != source])
    else:
        sync_all_files(source, args.target, args.bidirectional, verbose)
        
        # Handle special cases for source directory
        if source == 'content':
            source_dir = CONFIG['logseq']['source_dir']
        elif source == 'obsidian':
            source_dir = CONFIG['obsidian']['target_dir']
        elif source == 'quarto':
            source_dir = os.path.dirname(CONFIG['quarto']['target_dir'])  # Use quarto root
        else:
            source_dir = CONFIG[source]['source_dir']
            
        sync_assets(source_dir, [args.target])
    
    print("Sync completed!")

if __name__ == "__main__":
    main()