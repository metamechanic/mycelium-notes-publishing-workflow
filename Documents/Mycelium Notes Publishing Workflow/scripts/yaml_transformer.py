#!/usr/bin/env python3
"""
YAML Frontmatter Transformer

This utility handles the transformation of YAML frontmatter between different platforms:
- Logseq: Minimal frontmatter (title, type)
- Obsidian: Enhanced metadata for personal knowledge management (title, tags, created)
- Quarto: Publication-ready frontmatter (title, format, date, categories)
"""

import re
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# Platform-specific transformations
TRANSFORMATIONS = {
    'logseq_to_obsidian': {
        'title': lambda x: x,  # Keep as is
        'type': lambda x: None,  # Remove type
        'tags': lambda x: x.split(',') if isinstance(x, str) else x,  # Convert to list if string
        'created': lambda x: x if x else datetime.now().strftime('%Y-%m-%d')  # Set current date if missing
    },
    'logseq_to_quarto': {
        'title': lambda x: x,  # Keep as is
        'type': lambda x: None,  # Remove type
        'format': lambda x: 'html',  # Default format
        'date': lambda x: datetime.now().strftime('%Y-%m-%d'),  # Current date
        'categories': lambda x: []  # Empty categories
    },
    'obsidian_to_logseq': {
        'title': lambda x: x,  # Keep as is
        'tags': lambda x: None,  # Remove tags
        'created': lambda x: None,  # Remove created
        'type': lambda x: 'note'  # Add type
    },
    'obsidian_to_quarto': {
        'title': lambda x: x,  # Keep as is
        'tags': lambda x: None,  # Remove tags
        'created': lambda x: None,  # Remove created
        'format': lambda x: 'html',  # Default format
        'date': lambda x, meta: meta.get('created', datetime.now().strftime('%Y-%m-%d')),  # Use created date or current
        'categories': lambda x, meta: meta.get('tags', [])  # Use tags as categories
    },
    'quarto_to_logseq': {
        'title': lambda x: x,  # Keep as is
        'format': lambda x: None,  # Remove format
        'date': lambda x: None,  # Remove date
        'categories': lambda x: None,  # Remove categories
        'type': lambda x: 'note'  # Add type
    },
    'quarto_to_obsidian': {
        'title': lambda x: x,  # Keep as is
        'format': lambda x: None,  # Remove format
        'date': lambda x: None,  # Remove date
        'categories': lambda x: None,  # Remove categories
        'tags': lambda x, meta: meta.get('categories', []),  # Use categories as tags
        'created': lambda x, meta: meta.get('date', datetime.now().strftime('%Y-%m-%d'))  # Use date as created
    }
}

def read_file(file_path):
    """Read a markdown file and extract the YAML frontmatter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for YAML frontmatter
    yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        try:
            frontmatter = yaml.safe_load(yaml_text)
            remaining_content = content[yaml_match.end():]
            return frontmatter, remaining_content
        except yaml.YAMLError:
            pass
    
    # No valid frontmatter
    return {}, content

def transform_frontmatter(frontmatter, source_platform, target_platform):
    """Transform frontmatter from source platform to target platform."""
    transform_key = f"{source_platform}_to_{target_platform}"
    if transform_key not in TRANSFORMATIONS:
        raise ValueError(f"Transformation from {source_platform} to {target_platform} not supported")
    
    transformed = {}
    transformations = TRANSFORMATIONS[transform_key]
    
    # Apply transformations
    for key, transform_func in transformations.items():
        if key in frontmatter:
            try:
                # Some transformation functions might need the whole metadata
                result = transform_func(frontmatter[key], frontmatter)
            except TypeError:
                # If the function doesn't accept the metadata, call it with just the value
                result = transform_func(frontmatter[key])
                
            if result is not None:  # None means remove the key
                transformed[key] = result
        elif transform_func.__code__.co_argcount == 1:
            # Function with single argument is a default value generator
            result = transform_func(None)
            if result is not None:
                transformed[key] = result
    
    # Copy any other keys not specifically transformed
    for key, value in frontmatter.items():
        if key not in transformations and key not in transformed:
            transformed[key] = value
    
    return transformed

def write_file(file_path, frontmatter, content):
    """Write frontmatter and content to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False)
        f.write('---\n\n')
        f.write(content)

def transform_file(file_path, source_platform, target_platform, output_path=None):
    """Transform a file from one platform to another."""
    if output_path is None:
        output_path = file_path
    
    frontmatter, content = read_file(file_path)
    transformed = transform_frontmatter(frontmatter, source_platform, target_platform)
    write_file(output_path, transformed, content)
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Transform YAML frontmatter between platforms')
    parser.add_argument('file', help='Input file path')
    parser.add_argument('--source', choices=['logseq', 'obsidian', 'quarto'], required=True,
                        help='Source platform')
    parser.add_argument('--target', choices=['logseq', 'obsidian', 'quarto'], required=True,
                        help='Target platform')
    parser.add_argument('--output', help='Output file path (default: overwrite input)')
    args = parser.parse_args()
    
    output_path = transform_file(args.file, args.source, args.target, args.output)
    print(f"Transformed {args.file} from {args.source} to {args.target} format. Output: {output_path}")

if __name__ == "__main__":
    main()