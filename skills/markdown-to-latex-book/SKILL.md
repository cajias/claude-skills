---
name: markdown-to-latex-book
description: >-
  This skill should be used when the user asks to "convert markdown to
  LaTeX", "create a PDF book from markdown", "turn markdown files into a
  professional book", "generate LaTeX from markdown", or mentions creating
  professional PDF documentation from markdown sources.
---

# Markdown to LaTeX Book Conversion

Convert collections of markdown files into professionally typeset LaTeX books with proper
typography, consistent styling, and publication-ready output.

## Overview

This skill transforms markdown documentation (such as Obsidian vaults, documentation folders,
or playbooks) into professional LaTeX books. The process involves:

1. Analyzing markdown content structure
2. Designing a logical book hierarchy
3. Creating modular LaTeX files
4. Applying professional typography
5. Compiling to PDF

## When to Use

- Converting documentation collections to PDF books
- Creating professional technical manuals from markdown
- Transforming wiki/vault content into publishable format
- Generating training materials or playbooks as books

## Workflow

### Phase 1: Content Analysis

Before writing any LaTeX, explore the markdown source:

```text
Use the Explore agent to analyze:
- All markdown files and their purposes
- Logical structure/hierarchy of content
- Links between files (wiki-links, references)
- Main topics and how they relate
- Content elements: tables, code blocks, diagrams
```

Key questions to answer:

- How many files? What are their sizes?
- What's the natural grouping (parts/chapters)?
- Are there Mermaid diagrams that need conversion?
- What code languages are used?

### Phase 2: Structure Design

Map markdown files to book structure:

```text
Front Matter
├── Half-title page
├── Title page
├── Copyright page
├── Table of Contents
└── Introduction/Preface

Main Matter (Parts → Chapters)
├── Part I: [Logical Grouping]
│   ├── Chapter 1: [file1.md]
│   └── Chapter 2: [file2.md]
└── Part II: [Another Grouping]
    └── Chapter 3: [file3.md]

Back Matter
├── Appendix A: Reference Material
├── Appendix B: Checklists/Quick Refs
└── Index (optional)
```

### Phase 3: LaTeX Setup

Create modular file structure:

```text
project/
├── main.tex          # Master document
└── chapters/
    ├── ch01-name.tex
    ├── ch02-name.tex
    └── appendix-a.tex
```

#### Essential Packages

```latex
\documentclass[11pt,letterpaper,openany]{memoir}

% Typography
\usepackage[T1]{fontenc}
\usepackage{microtype}
\usepackage{palatino}           % Professional serif
\usepackage[scaled=0.92]{helvet} % Sans for headings
\usepackage{inconsolata}        % Code font

% Layout
\raggedbottom                   % Prevent underfull vbox
\renewcommand{\arraystretch}{1.2} % Better table spacing

% Code listings
\usepackage{listings}

% Colored boxes
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}

% Diagrams
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}

% Links with metadata
\usepackage[
    colorlinks=true,
    linkcolor=RoyalBlue!80!black,
    pdftitle={Book Title},
    pdfauthor={Author Name}
]{hyperref}
```

### Phase 4: Typography Rules

Apply these professional typography standards:

| Element         | Recommendation                            |
| --------------- | ----------------------------------------- |
| Body font       | Palatino, Charter, or Source Serif Pro    |
| Heading font    | Helvetica, Source Sans, or matching sans  |
| Code font       | Inconsolata, Fira Code, or JetBrains Mono |
| Float placement | `[htbp]` not `[h]` alone                  |
| Page bottoms    | `\raggedbottom` to prevent stretching     |
| Table rows      | `\arraystretch{1.2}` minimum              |
| Margins         | Account for binding gutter                |

### Phase 5: Content Conversion

#### Markdown Elements to LaTeX

| Markdown        | LaTeX                                 |
| --------------- | ------------------------------------- |
| `# Heading`     | `\chapter{}` or `\section{}`          |
| `**bold**`      | `\textbf{}`                           |
| `*italic*`      | `\textit{}`                           |
| `` `code` ``    | `\texttt{}`                           |
| `[link](url)`   | `\href{url}{text}`                    |
| `[[wiki-link]]` | `Chapter~\ref{ch:label}`              |
| `> quote`       | `\begin{quote}...\end{quote}`         |
| `- list`        | `\begin{itemize}...\end{itemize}`     |
| `1. list`       | `\begin{enumerate}...\end{enumerate}` |
| Tables          | `tabularx` with `booktabs`            |
| Code blocks     | `lstlisting` environment              |

#### Mermaid Diagrams

Convert Mermaid to TikZ or note for external compilation:

```latex
% Simple flowchart replacement
\begin{tikzpicture}[node distance=2cm]
    \node[draw, rounded corners, fill=blue!10] (a) {Step A};
    \node[draw, rounded corners, fill=green!10, right=of a] (b) {Step B};
    \draw[->, thick] (a) -- (b);
\end{tikzpicture}
```

#### Custom Boxes for Patterns

```latex
\newtcolorbox{problembox}{
    enhanced,
    colback=Goldenrod!8!white,
    colframe=Goldenrod!80!black,
    title={\sffamily\bfseries Problem},
    leftrule=3pt,
    arc=2pt,
    breakable
}

\newtcolorbox{solutionbox}{
    enhanced,
    colback=RoyalBlue!6!white,
    colframe=RoyalBlue!70!black,
    title={\sffamily\bfseries Pattern},
    leftrule=3pt,
    arc=2pt,
    breakable
}
```

### Phase 6: Compilation

Use tectonic for reliable compilation:

```bash
# Install if needed
brew install tectonic

# Compile (handles multiple passes automatically)
tectonic main.tex
```

Common issues and fixes:

- `Underfull vbox`: Add `\raggedbottom`
- `Not in outer par mode`: Don't put floats inside tcolorbox
- `Undefined language`: Remove unsupported `language=yaml` from listings
- `Overfull hbox`: Adjust content or allow `\sloppy` locally

### Phase 7: Polish

Final improvements checklist:

- [ ] Draft watermark if needed (`draftwatermark` package)
- [ ] PDF metadata (title, author, keywords)
- [ ] Consistent heading styles
- [ ] Working cross-references
- [ ] No compilation warnings (or understood)

## Critical Pitfalls

### Avoid These Common Mistakes

1. **Floats inside boxes**: Tables/figures can't be inside tcolorbox
   - Fix: Move table outside the box environment

2. **`[h]` float placement**: Causes poor page breaks
   - Fix: Always use `[htbp]`

3. **Missing `\raggedbottom`**: Causes stretched pages
   - Fix: Add after `\checkandfixthelayout`

4. **Unsupported listing languages**: `yaml`, `json` not built-in
   - Fix: Remove language option or define custom language

5. **Arrow syntax in TikZ**: `{Stealth[]}` can cause issues
   - Fix: Use simpler `<->` or `->`

## Additional Resources

### Reference Files

- **`references/main-template.tex`** - Complete main.tex template
- **`references/typography-guide.md`** - Detailed typography decisions

### Examples

- **`examples/chapter-template.tex`** - Standard chapter structure
