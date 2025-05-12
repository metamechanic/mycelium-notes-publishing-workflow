#!/usr/bin/env python3
"""
Setup Script for Notes Publishing Workflow

This script initializes the repository structure for a multi-platform notes publishing workflow,
supporting Logseq, Obsidian, and Quarto.
"""

import os
import shutil
import argparse
import subprocess

def create_directory_structure(base_dir):
    """Create the directory structure for the notes publishing workflow."""
    directories = [
        # Core content
        "content/notes",
        "content/assets",
        
        # Platform-specific directories
        "logseq/pages",
        "logseq/assets",
        "obsidian/notes",
        "obsidian/.obsidian",
        "quarto/posts",
        "quarto/_quarto.yml",
        
        # GitHub Actions
        ".github/workflows",
        
        # Scripts
        "scripts"
    ]
    
    for directory in directories:
        os.makedirs(os.path.join(base_dir, directory), exist_ok=True)
        print(f"Created directory: {directory}")

def create_readme(base_dir):
    """Create a README.md file explaining the repository structure."""
    readme_content = """# Notes Publishing Workflow

This repository contains a workflow for publishing notes across multiple platforms:
- Logseq
- Obsidian
- Quarto

## Directory Structure

- `content/`: The core content of your notes
  - `notes/`: Your actual notes in Markdown format
  - `assets/`: Images and other assets used in your notes
- `logseq/`: Logseq-specific files
- `obsidian/`: Obsidian-specific files
- `quarto/`: Quarto project files
- `scripts/`: Utility scripts for syncing notes between platforms
- `.github/workflows/`: GitHub Actions workflows for automation

## Usage

### Manual Sync

Run the sync script to synchronize your notes across platforms:

```bash
python scripts/notes_sync.py --source [logseq|obsidian|quarto|content] --target [logseq|obsidian|quarto|all]
```

### Automated Sync

Changes pushed to the repository will automatically trigger a GitHub Actions workflow that syncs your notes across platforms.

## Setup

To set up the repository:

1. Clone this repository
2. Run `python scripts/setup_repo.py` to initialize the directory structure
3. Configure your Logseq, Obsidian, and Quarto settings as needed
4. Start creating notes!
"""
    
    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Created README.md")

def create_quarto_config(base_dir):
    """Create a basic Quarto configuration file."""
    quarto_config = """project:
  type: website
  output-dir: _site

website:
  title: "Notes"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - about.qmd

format:
  html:
    theme: cosmo
    css: styles.css
    toc: true

execute:
  freeze: auto
"""
    
    with open(os.path.join(base_dir, "quarto", "_quarto.yml"), "w", encoding="utf-8") as f:
        f.write(quarto_config)
    
    # Create basic index and about files
    index_content = """---
title: "Notes"
listing:
  contents: posts
  sort: "date desc"
  type: default
  categories: true
  sort-ui: true
  filter-ui: true
---

Welcome to my notes collection.
"""
    
    about_content = """---
title: "About"
---

About this notes collection.
"""
    
    with open(os.path.join(base_dir, "quarto", "index.qmd"), "w", encoding="utf-8") as f:
        f.write(index_content)
    
    with open(os.path.join(base_dir, "quarto", "about.qmd"), "w", encoding="utf-8") as f:
        f.write(about_content)
    
    # Create styles.css
    styles_content = """/* Custom styles */
"""
    
    with open(os.path.join(base_dir, "quarto", "styles.css"), "w", encoding="utf-8") as f:
        f.write(styles_content)
    
    print("Created Quarto configuration files")

def create_obsidian_config(base_dir):
    """Create a basic Obsidian configuration."""
    app_json = """{
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "notes",
  "attachmentFolderPath": "assets"
}"""
    
    appearance_json = """{
  "baseFontSize": 16
}"""
    
    os.makedirs(os.path.join(base_dir, "obsidian", ".obsidian"), exist_ok=True)
    
    with open(os.path.join(base_dir, "obsidian", ".obsidian", "app.json"), "w", encoding="utf-8") as f:
        f.write(app_json)
    
    with open(os.path.join(base_dir, "obsidian", ".obsidian", "appearance.json"), "w", encoding="utf-8") as f:
        f.write(appearance_json)
    
    print("Created Obsidian configuration files")

def create_logseq_config(base_dir):
    """Create a basic Logseq configuration."""
    config_edn = """{ 
 :preferred-format "markdown"
 :default-templates 
 {:journals ""}
 :shortcuts {}
 :feature/enable-journals? true
 :ui/enable-developer-mode? false
 :preferred-workflow :now
 :git-pull-scheduled? false
 :git-push-scheduled? false
}"""
    
    os.makedirs(os.path.join(base_dir, "logseq"), exist_ok=True)
    
    with open(os.path.join(base_dir, "logseq", "config.edn"), "w", encoding="utf-8") as f:
        f.write(config_edn)
    
    print("Created Logseq configuration files")

def copy_scripts(base_dir):
    """Copy the sync and transform scripts to the scripts directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Copy sync script
    shutil.copy2(
        os.path.join(script_dir, "notes_sync.py"),
        os.path.join(base_dir, "scripts", "notes_sync.py")
    )
    
    # Copy YAML transformer script
    shutil.copy2(
        os.path.join(script_dir, "yaml_transformer.py"),
        os.path.join(base_dir, "scripts", "yaml_transformer.py")
    )
    
    # Make scripts executable
    os.chmod(os.path.join(base_dir, "scripts", "notes_sync.py"), 0o755)
    os.chmod(os.path.join(base_dir, "scripts", "yaml_transformer.py"), 0o755)
    
    print("Copied scripts to scripts/ directory")

def copy_github_workflow(base_dir):
    """Copy the GitHub Actions workflow files."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create workflows directory
    workflows_dir = os.path.join(base_dir, ".github", "workflows")
    os.makedirs(workflows_dir, exist_ok=True)
    
    # Copy workflow files
    workflow_files = [
        "sync-notes.yml",
        "logseq_publish.yml",
        "obsidian_publish.yml", 
        "quarto_publish.yml"
    ]
    
    for workflow_file in workflow_files:
        shutil.copy2(
            os.path.join(script_dir, workflow_file),
            os.path.join(workflows_dir, workflow_file)
        )
    
    # Copy publishing config
    shutil.copy2(
        os.path.join(script_dir, "publishing_config.yml"),
        os.path.join(base_dir, "publishing_config.yml")
    )
    
    print("Copied GitHub Actions workflow files and publishing configuration")

def create_sample_note(base_dir):
    """Create a sample note to demonstrate the workflow."""
    sample_note = """---
title: Sample Note
type: note
---

# Sample Note

This is a sample note to demonstrate the notes publishing workflow.

## Features

- Write notes in Logseq
- Process in Obsidian
- Publish with Quarto
- Sync changes across platforms

## Next Steps

1. Create more notes
2. Organize them with tags
3. Publish to the web

"""
    
    with open(os.path.join(base_dir, "content", "notes", "sample-note.md"), "w", encoding="utf-8") as f:
        f.write(sample_note)
    
    print("Created sample note")

def init_git_repo(base_dir):
    """Initialize a Git repository if one doesn't already exist."""
    if not os.path.exists(os.path.join(base_dir, ".git")):
        subprocess.run(["git", "init"], cwd=base_dir, check=True)
        print("Initialized Git repository")
    else:
        print("Git repository already exists")

def create_gitignore(base_dir):
    """Create a .gitignore file."""
    gitignore_content = """# Quarto
_site/
.quarto/
/.quarto/
_freeze/

# Obsidian
.obsidian/workspace
.obsidian/workspace.json
.obsidian/cache

# Logseq
logseq/.recycle
logseq/bak
logseq/version-files
logseq/graphs-cache.edn
logseq/broken-config.edn

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/

# macOS
.DS_Store

# VS Code
.vscode/

# GitHub Pages
_site/

# Temporary files
*.tmp
*.temp
*.log
"""
    
    with open(os.path.join(base_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("Created .gitignore file")

def setup_custom_domains(base_dir):
    """Set up configuration for custom domains."""
    # Create CNAME files for each platform
    domains = {
        "logseq": "notes-logseq.yourdomain.com",
        "obsidian": "notes-obsidian.yourdomain.com",
        "quarto": "notes-quarto.yourdomain.com"
    }
    
    for platform, domain in domains.items():
        with open(os.path.join(base_dir, f"{platform}/CNAME"), "w", encoding="utf-8") as f:
            f.write(domain)
    
    print("Created CNAME files for custom domains")

def main():
    parser = argparse.ArgumentParser(description="Setup a notes publishing workflow repository")
    parser.add_argument("--dir", default=".", help="Base directory for repository setup")
    parser.add_argument("--logseq-domain", default="notes-logseq.yourdomain.com", help="Custom domain for Logseq publishing")
    parser.add_argument("--obsidian-domain", default="notes-obsidian.yourdomain.com", help="Custom domain for Obsidian publishing")
    parser.add_argument("--quarto-domain", default="notes-quarto.yourdomain.com", help="Custom domain for Quarto publishing")
    args = parser.parse_args()
    
    base_dir = os.path.abspath(args.dir)
    
    # Update domains in configuration
    global CONFIG
    CONFIG["logseq"]["publish_url"] = args.logseq_domain
    CONFIG["obsidian"]["publish_url"] = args.obsidian_domain
    CONFIG["quarto"]["publish_url"] = args.quarto_domain
    
    # Create directory structure
    create_directory_structure(base_dir)
    
    # Create configuration files
    create_readme(base_dir)
    create_quarto_config(base_dir)
    create_obsidian_config(base_dir)
    create_logseq_config(base_dir)
    
    # Copy scripts
    copy_scripts(base_dir)
    
    # Copy GitHub workflow
    copy_github_workflow(base_dir)
    
    # Set up custom domains
    setup_custom_domains(base_dir)
    
    # Create sample note
    create_sample_note(base_dir)
    
    # Initialize Git repository
    init_git_repo(base_dir)
    
    # Create .gitignore
    create_gitignore(base_dir)
    
    print(f"\nRepository setup complete at {base_dir}")
    print("\nNext steps:")
    print(f"1. Update domains in publishing_config.yml with your actual custom domains")
    print(f"2. Add remote repository with: git remote add origin <repository-url>")