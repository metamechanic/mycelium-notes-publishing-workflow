#!/usr/bin/env python3
"""
Notes Synchronization Script

This script synchronizes Markdown notes between Logseq, Obsidian, and Quarto,
handling the different YAML frontmatter requirements for each platform.
"""

import os
import re
import yaml
import glob
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import frontmatter  # pip install python-frontmatter
import git  # pip install GitPython
import uuid

# Configuration
CONFIG = {
    "logseq": {
        "required_yaml": ["title", "type"],
        "content_dir": "content/notes",
        "publish_dir": "logseq/pages",
        "publish_url": "notes-logseq.yourdomain.com",  # Update with your actual subdomain
        "syntax": "logseq"
    },
    "obsidian": {
        "required_yaml": ["title", "tags", "created"],
        "content_dir": "content/notes",
        "publish_dir": "obsidian/notes",
        "publish_url": "notes-obsidian.yourdomain.com",  # Update with your actual subdomain
        "syntax": "markdown"
    },
    "quarto": {
        "required_yaml": ["title", "format", "date", "categories"],
        "content_dir": "content/notes",
        "publish_dir": "quarto/posts",
        "publish_url": "notes-quarto.yourdomain.com",  # Update with your actual subdomain
        "syntax": "markdown"
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
            property_pattern = re.compile(r'^([a-zA-Z0-9_-]+):: (.*)

def merge_frontmatter(source_meta, target_meta, platform, file_path=None):
    """Merge frontmatter, prioritizing source while preserving platform-specific fields."""
    merged = {**target_meta}  # Start with the target metadata
    
    # Update with source metadata, but don't overwrite platform-specific fields
    for key, value in source_meta.items():
        # Skip platform-specific keys if they already exist in target
        if key in CONFIG[platform]["required_yaml"] and key in target_meta:
            continue
        merged[key] = value
    
    # Ensure required YAML fields for the platform
    for key in CONFIG[platform]["required_yaml"]:
        if key not in merged:
            if key == "title" and file_path and Path(file_path).stem:
                merged[key] = Path(file_path).stem.replace("-", " ").title()
            elif key == "date" or key == "created":
                merged[key] = datetime.now().strftime("%Y-%m-%d")
            elif key == "format":
                merged[key] = "html"
            elif key == "type":
                merged[key] = "note"
            elif key == "tags" or key == "categories":
                merged[key] = []
            else:
                merged[key] = ""
    
    return merged

def convert_logseq_syntax(content, target_platform):
    """Convert Logseq-specific syntax to target platform format."""
    # Handle block references (e.g., ((block-id)) in Logseq)
    if target_platform == 'obsidian':
        # Obsidian uses [[^block-id]] for block references
        content = re.sub(r'\(\(([a-zA-Z0-9-]+)\)\)', r'[[^\1]]', content)
        
        # Convert page embeds
        content = re.sub(r'\{\{embed \[\[([^\]]+)\]\]\}\}', r'![[&1]]', content)
    elif target_platform == 'quarto':
        # For Quarto, we simply remove block references as they don't have a direct equivalent
        content = re.sub(r'\(\(([a-zA-Z0-9-]+)\)\)', r'[*Block Reference*]', content)
        
        # Convert page embeds to markdown includes if possible or to links
        content = re.sub(r'\{\{embed \[\[([^\]]+)\]\]\}\}', r'See: [\1](\1)', content)
    
    # Handle Logseq bullet format (- item) for non-Logseq platforms
    # This is more complex and may need custom handling depending on the document structure
    
    return content

def sync_files(source_dir, target_dir, platform):
    """Sync files from source to target with proper frontmatter, handling both YAML and Logseq formats."""
    os.makedirs(target_dir, exist_ok=True)
    
    # Process all markdown files in source directory
    for file_path in glob.glob(os.path.join(source_dir, "**/*.md"), recursive=True):
        relative_path = os.path.relpath(file_path, source_dir)
        target_path = os.path.join(target_dir, relative_path)
        
        # Create target directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Parse source frontmatter and content
        source_meta, source_content = parse_frontmatter(file_path)
        
        # Process Logseq-specific syntax if needed
        if platform != 'logseq':
            # Convert Logseq block references to other formats if needed
            source_content = convert_logseq_syntax(source_content, platform)
        
        # Check if target file exists
        if os.path.exists(target_path):
            # Parse target frontmatter
            target_meta, target_content = parse_frontmatter(target_path)
            
            # Determine which content is newer
            # For simplicity, we'll just check file modification times
            # A more sophisticated approach would diff the actual content
            if os.path.getmtime(file_path) > os.path.getmtime(target_path):
                content_to_use = source_content
            else:
                content_to_use = target_content
                
            # Merge frontmatter
            merged_meta = merge_frontmatter(source_meta, target_meta, platform)
        else:
            # Target doesn't exist, use source content and adapt frontmatter
            content_to_use = source_content
            merged_meta = merge_frontmatter(source_meta, {}, platform)
        
        # Write the file with the appropriate format based on platform
        if platform == 'logseq':
            # Write with Logseq property format
            with open(target_path, 'w', encoding='utf-8') as f:
                # Write properties at the top
                for key, value in merged_meta.items():
                    f.write(f"{key}:: {value}\n")
                
                # Add a blank line if we have properties
                if merged_meta:
                    f.write("\n")
                    
                f.write(content_to_use)
        else:
            # Write with standard YAML frontmatter
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                f.write(yaml.dump(merged_meta, default_flow_style=False))
                f.write("---\n\n")
                f.write(content_to_use)
        
        print(f"Synced: {relative_path} -> {target_path}")

def sync_assets(content_dir, platform_dirs):
    """Sync assets to all platform directories."""
    assets_source = os.path.join(content_dir, "assets")
    if not os.path.exists(assets_source):
        return
        
    for platform_dir in platform_dirs:
        assets_target = os.path.join(platform_dir, "assets")
        os.makedirs(assets_target, exist_ok=True)
        
        # Copy all assets
        for asset in glob.glob(os.path.join(assets_source, "**"), recursive=True):
            if os.path.isfile(asset):
                relative_path = os.path.relpath(asset, assets_source)
                target_path = os.path.join(assets_target, relative_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(asset, target_path)
                print(f"Synced asset: {relative_path}")

def get_modified_files(repo_path, since_commit=None):
    """Get files modified since the given commit."""
    repo = git.Repo(repo_path)
    
    if since_commit:
        # Get modified files since the specified commit
        diff = repo.git.diff('--name-only', since_commit)
    else:
        # Get modified files in working directory
        diff = repo.git.diff('--name-only')
    
    return [f for f in diff.split('\n') if f.endswith('.md')]

def main():
    parser = argparse.ArgumentParser(description='Sync notes between Logseq, Obsidian, and Quarto')
    parser.add_argument('--source', choices=['logseq', 'obsidian', 'quarto', 'content'], 
                        help='Source platform to sync from')
    parser.add_argument('--target', choices=['logseq', 'obsidian', 'quarto', 'all'],
                        help='Target platform to sync to')
    parser.add_argument('--modified-only', action='store_true',
                        help='Only sync files modified since last sync')
    parser.add_argument('--since-commit', 
                        help='Only sync files modified since specified commit')
    args = parser.parse_args()
    
    # Default sync behavior: from content to all platforms
    source = args.source or 'content'
    target = args.target or 'all'
    
    # Set up source and target directories
    if source == 'content':
        source_dir = CONFIG['logseq']['content_dir']  # Use the content directory
    else:
        source_dir = CONFIG[source]['publish_dir']
    
    if target == 'all':
        # Sync to all platforms
        for platform in ['logseq', 'obsidian', 'quarto']:
            print(f"Syncing to {platform}...")
            sync_files(source_dir, CONFIG[platform]['publish_dir'], platform)
    else:
        # Sync to specific platform
        sync_files(source_dir, CONFIG[target]['publish_dir'], target)
    
    # Sync assets to all platforms or specified target
    platform_dirs = [CONFIG[p]['publish_dir'] for p in ['logseq', 'obsidian', 'quarto']] \
                   if target == 'all' else [CONFIG[target]['publish_dir']]
    sync_assets(CONFIG['logseq']['content_dir'], platform_dirs)
    
    print("Sync completed!")

if __name__ == "__main__":
    main()
, re.MULTILINE)
            matches = property_pattern.findall(content)
            
            for key, value in matches:
                logseq_properties[key] = value
                
            # Remove properties from content
            content = property_pattern.sub('', content)
            return logseq_properties, content.strip()
        else:
            # Standard YAML frontmatter
            post = frontmatter.load(content)
            return post.metadata, post.content
    except Exception as e:
        print(f"Error parsing frontmatter in {file_path}: {e}")
        return {}, ""

def merge_frontmatter(source_meta, target_meta, platform):
    """Merge frontmatter, prioritizing source while preserving platform-specific fields."""
    merged = {**target_meta}  # Start with the target metadata
    
    # Update with source metadata, but don't overwrite platform-specific fields
    for key, value in source_meta.items():
        # Skip platform-specific keys if they already exist in target
        if key in CONFIG[platform]["required_yaml"] and key in target_meta:
            continue
        merged[key] = value
    
    # Ensure required YAML fields for the platform
    for key in CONFIG[platform]["required_yaml"]:
        if key not in merged:
            if key == "title" and Path(file_path).stem:
                merged[key] = Path(file_path).stem.replace("-", " ").title()
            elif key == "date" or key == "created":
                merged[key] = datetime.now().strftime("%Y-%m-%d")
            elif key == "format":
                merged[key] = "html"
            elif key == "type":
                merged[key] = "note"
            else:
                merged[key] = ""
    
    return merged

def sync_files(source_dir, target_dir, platform):
    """Sync files from source to target with proper frontmatter."""
    os.makedirs(target_dir, exist_ok=True)
    
    # Process all markdown files in source directory
    for file_path in glob.glob(os.path.join(source_dir, "**/*.md"), recursive=True):
        relative_path = os.path.relpath(file_path, source_dir)
        target_path = os.path.join(target_dir, relative_path)
        
        # Create target directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Parse source frontmatter and content
        source_meta, source_content = parse_frontmatter(file_path)
        
        # Check if target file exists
        if os.path.exists(target_path):
            # Parse target frontmatter
            target_meta, target_content = parse_frontmatter(target_path)
            
            # Determine which content is newer
            # For simplicity, we'll just check file modification times
            # A more sophisticated approach would diff the actual content
            if os.path.getmtime(file_path) > os.path.getmtime(target_path):
                content_to_use = source_content
            else:
                content_to_use = target_content
                
            # Merge frontmatter
            merged_meta = merge_frontmatter(source_meta, target_meta, platform)
        else:
            # Target doesn't exist, use source content and adapt frontmatter
            content_to_use = source_content
            merged_meta = merge_frontmatter(source_meta, {}, platform)
        
        # Write the file with merged frontmatter
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write("---\n")
            f.write(yaml.dump(merged_meta, default_flow_style=False))
            f.write("---\n\n")
            f.write(content_to_use)
        
        print(f"Synced: {relative_path} -> {target_path}")

def sync_assets(content_dir, platform_dirs):
    """Sync assets to all platform directories."""
    assets_source = os.path.join(content_dir, "assets")
    if not os.path.exists(assets_source):
        return
        
    for platform_dir in platform_dirs:
        assets_target = os.path.join(platform_dir, "assets")
        os.makedirs(assets_target, exist_ok=True)
        
        # Copy all assets
        for asset in glob.glob(os.path.join(assets_source, "**"), recursive=True):
            if os.path.isfile(asset):
                relative_path = os.path.relpath(asset, assets_source)
                target_path = os.path.join(assets_target, relative_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(asset, target_path)
                print(f"Synced asset: {relative_path}")

def get_modified_files(repo_path, since_commit=None):
    """Get files modified since the given commit."""
    repo = git.Repo(repo_path)
    
    if since_commit:
        # Get modified files since the specified commit
        diff = repo.git.diff('--name-only', since_commit)
    else:
        # Get modified files in working directory
        diff = repo.git.diff('--name-only')
    
    return [f for f in diff.split('\n') if f.endswith('.md')]

def main():
    parser = argparse.ArgumentParser(description='Sync notes between Logseq, Obsidian, and Quarto')
    parser.add_argument('--source', choices=['logseq', 'obsidian', 'quarto', 'content'], 
                        help='Source platform to sync from')
    parser.add_argument('--target', choices=['logseq', 'obsidian', 'quarto', 'all'],
                        help='Target platform to sync to')
    parser.add_argument('--modified-only', action='store_true',
                        help='Only sync files modified since last sync')
    parser.add_argument('--since-commit', 
                        help='Only sync files modified since specified commit')
    args = parser.parse_args()
    
    # Default sync behavior: from content to all platforms
    source = args.source or 'content'
    target = args.target or 'all'
    
    # Set up source and target directories
    if source == 'content':
        source_dir = CONFIG['logseq']['content_dir']  # Use the content directory
    else:
        source_dir = CONFIG[source]['publish_dir']
    
    if target == 'all':
        # Sync to all platforms
        for platform in ['logseq', 'obsidian', 'quarto']:
            print(f"Syncing to {platform}...")
            sync_files(source_dir, CONFIG[platform]['publish_dir'], platform)
    else:
        # Sync to specific platform
        sync_files(source_dir, CONFIG[target]['publish_dir'], target)
    
    # Sync assets to all platforms or specified target
    platform_dirs = [CONFIG[p]['publish_dir'] for p in ['logseq', 'obsidian', 'quarto']] \
                   if target == 'all' else [CONFIG[target]['publish_dir']]
    sync_assets(CONFIG['logseq']['content_dir'], platform_dirs)
    
    print("Sync completed!")

if __name__ == "__main__":
    main()