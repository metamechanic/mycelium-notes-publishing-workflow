# Enhanced Notes Publishing Workflow Guide

This guide explains how to use the enhanced bidirectional notes publishing workflow between Logseq, Obsidian, and Quarto.

## Workflow Overview

This workflow allows you to:

1. **Write in Logseq** using bullet points and folding structure
2. **Process in Obsidian** with folder organization and long-form content
3. **Publish with Quarto** adding interactive elements and visualizations

The key feature of this workflow is **bidirectional synchronization** - changes made in any platform can flow to the others, with intelligent handling of different formats and content.

## The Unified Schema

The workflow uses a unified schema (`unified_note_schema.json`) that defines:

- **Note types** (person, book, place, etc.)
- **Sections** within each note type
- **Formatting rules** for each section in each platform
- **Synchronization behavior** (which sections sync and in which direction)

This schema gives you control over how content is transformed and synchronized.

## How Bidirectional Sync Works

The sync system works by:

1. **Extracting sections** from notes using headings (## Section Name)
2. **Comparing content** between platforms for each section
3. **Determining sync direction** based on the schema and content differences
4. **Converting formats** (bullets → paragraphs, paragraphs → bullets, etc.)
5. **Merging changes** intelligently

### Example Sync Behaviors

- **Logseq Bio (bullets) → Obsidian Bio (paragraphs)**: Bullet points are merged into paragraphs
- **Obsidian Analysis (new section) → Logseq**: Section is added, formatted as bullets
- **Logseq References (updated) → Obsidian**: New references are added, maintaining format
- **Quarto Visualizations → Obsidian/Logseq**: Code sections can be configured to stay in Quarto only

## Recommended Workflow

### 1. Start in Logseq

```
title:: New Note
type:: person
tags:: people

# Person Name

## Bio
- Point 1
- Point 2

## Key Accomplishments
- Accomplishment 1
- Accomplishment 2
```

### 2. Sync to Other Platforms

```bash
python3 scripts/bidirectional_sync.py --source logseq --target all
```

### 3. Edit in Obsidian

- Open the note in Obsidian (it will be in the appropriate folder)
- Add detailed narrative content to the Bio section
- Add a new "Analysis" section with long-form prose

### 4. Sync Back to Logseq and Forward to Quarto

```bash
python3 scripts/bidirectional_sync.py --source obsidian --target all --bidirectional
```

### 5. Add Interactive Elements in Quarto

- Open the note in Quarto
- Add data visualization code
- Generate interactive elements

### 6. Final Sync and Publish

```bash
python3 scripts/bidirectional_sync.py --source quarto --target all --bidirectional
git add .
git commit -m "Update notes across platforms"
git push
```

## Working with Different Note Types

The schema includes templates for different entity types:

### Person Notes

```
title:: Alan Turing
type:: person
tags:: computer-science, history

# Alan Turing

## Bio
- British mathematician and computer scientist
- Father of theoretical computer science

## Key Accomplishments
- Developed the concept of the Turing machine
- Work on breaking the Enigma code
```

### Book Notes

```
title:: Thinking, Fast and Slow
type:: book
author:: Daniel Kahneman
published:: 2011

# Thinking, Fast and Slow

## Summary
- Explores two modes of thought: System 1 (fast, intuitive) and System 2 (slow, deliberate)

## Key Ideas
- Cognitive biases and heuristics
- Prospect theory
```

### Place Notes

```
title:: Paris
type:: place
country:: France
coordinates:: 48.8566, 2.3522

# Paris

## Description
- Capital of France
- Known for art, fashion, gastronomy

## Notable Features
- Eiffel Tower
- Louvre Museum
```

## Custom Section Behavior

You can control which sections sync and how they transform:

### In the schema:

```json
"bio": {
  "sync": true,
  "logseq_format": "bullets",
  "obsidian_format": "paragraphs",
  "quarto_format": "paragraphs"
}
```

### Platform-Specific Sections:

```json
"analysis": {
  "sync": false,
  "obsidian_only": true,
  "logseq_format": null,
  "obsidian_format": "paragraphs"
}
```

## Troubleshooting

If you encounter sync issues:

1. **Check File Formats**: Ensure proper headings (## Section Name)
2. **Run with Verbose Logging**: Add `--verbose` flag
3. **Sync a Single File**: Use `--file filename.md` flag
4. **Resolve Conflicts Manually**: Edit the conflicting sections

## Extending the Workflow

You can extend this workflow by:

1. **Modifying the Schema**: Add new note types or sections
2. **Creating Templates**: Add templates for new entity types
3. **Enhancing Transforms**: Modify how content transforms between platforms
4. **Adding Visualization Types**: Create new Quarto templates with different visualizations

For advanced users, you can even add custom transformation logic to the sync script.

## Command Reference

```bash
# Initialize the directory structure and schema
python3 scripts/bidirectional_sync.py --init

# Sync from Logseq to all platforms
python3 scripts/bidirectional_sync.py --source logseq --target all

# Sync from Obsidian to all platforms with bidirectional changes
python3 scripts/bidirectional_sync.py --source obsidian --target all --bidirectional

# Sync a specific file
python3 scripts/bidirectional_sync.py --source logseq --target all --file "person/alan-turing.md"
```

## Best Practices

1. **Use Consistent Headings**: Always use level 2 headings (##) for sections
2. **Follow the Schema**: Use the note types and sections defined in the schema
3. **Sync Frequently**: Don't let changes accumulate too much before syncing
4. **Commit After Syncing**: Save your work in git after successful syncs
5. **Back Up Regularly**: Use git to maintain a history of your changes