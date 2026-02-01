# Typography Guide for LaTeX Books

## Font Selection

### Body Text (Serif)

Professional options for body text:

| Font             | Package                       | Character                        |
| ---------------- | ----------------------------- | -------------------------------- |
| Palatino         | `\usepackage{palatino}`       | Classic, highly readable         |
| Charter          | `\usepackage{charter}`        | Clean, modern feel               |
| Source Serif Pro | `\usepackage{sourceserifpro}` | Contemporary                     |
| Libertinus       | `\usepackage{libertinus}`     | Open-source Palatino alternative |
| EB Garamond      | `\usepackage{ebgaramond}`     | Traditional, elegant             |

### Headings (Sans-serif)

Pair with contrasting sans-serif:

| Font            | Package                            | Notes                        |
| --------------- | ---------------------------------- | ---------------------------- |
| Helvetica       | `\usepackage[scaled=0.92]{helvet}` | Classic, widely available    |
| Source Sans Pro | `\usepackage{sourcesanspro}`       | Pairs well with Source Serif |
| Fira Sans       | `\usepackage{FiraSans}`            | Modern, Mozilla-developed    |
| Lato            | `\usepackage{lato}`                | Friendly, warm feel          |

### Code (Monospace)

For code listings:

| Font            | Package                      | Features                  |
| --------------- | ---------------------------- | ------------------------- |
| Inconsolata     | `\usepackage{inconsolata}`   | Clean, popular            |
| Fira Code       | Requires XeLaTeX             | Ligatures for programming |
| JetBrains Mono  | Requires XeLaTeX             | Purpose-built for code    |
| Source Code Pro | `\usepackage{sourcecodepro}` | Matches Source family     |

## Page Layout

### Margins for Binding

```latex
% For perfect binding (glued spine)
\setlrmarginsandblock{1in}{1.25in}{*}  % Inner, outer

% For saddle-stitch (stapled)
\setlrmarginsandblock{0.75in}{0.75in}{*}

% For spiral/wire binding
\setlrmarginsandblock{1.25in}{1in}{*}  % Extra inner margin
```

### Vertical Spacing

```latex
% Prevent stretched pages
\raggedbottom

% Or allow mild stretching
\sloppybottom

% Paragraph spacing (pick one approach)
\setlength{\parskip}{0.4\baselineskip}  % Space between paragraphs
\setlength{\parindent}{1.5em}            % First-line indent
```

## Chapter Styles in Memoir

Available built-in styles:

- `default` - Simple, no decoration
- `section` - Minimal
- `madsen` - Rules above/below title
- `veelo` - Modern, clean
- `ell` - Elegant with rules
- `pedersen` - Bold, contemporary
- `bianchi` - Classic with spacing
- `ger` - German-style
- `lyhne` - Scandinavian minimal
- `wilsondob` - Traditional

Custom style example:

```latex
\makechapterstyle{professional}{%
    \chapterstyle{default}
    \renewcommand*{\chapnamefont}{\normalfont\Large\sffamily\scshape}
    \renewcommand*{\chapnumfont}{\normalfont\huge\sffamily\bfseries}
    \renewcommand*{\chaptitlefont}{\normalfont\HUGE\sffamily\bfseries}
    \renewcommand*{\printchaptertitle}[1]{%
        \hrule height 0.5pt \vskip 6pt
        \chaptitlefont ##1
        \vskip 4pt \hrule height 2pt
    }
}
```

## Color Palettes

### Professional Blue Theme

```latex
\definecolor{chaptercolor}{RGB}{60, 100, 160}
\definecolor{linkcolor}{RGB}{50, 90, 140}
\definecolor{accentcolor}{RGB}{180, 130, 50}
```

### Warm Earth Theme

```latex
\definecolor{chaptercolor}{RGB}{120, 80, 50}
\definecolor{linkcolor}{RGB}{100, 70, 40}
\definecolor{accentcolor}{RGB}{60, 100, 80}
```

### High Contrast (Accessibility)

```latex
\definecolor{chaptercolor}{RGB}{0, 0, 0}
\definecolor{linkcolor}{RGB}{0, 0, 150}
\definecolor{accentcolor}{RGB}{150, 0, 0}
```

## Code Listing Styles

### Minimal (No Line Numbers)

```latex
\lstset{
    basicstyle=\ttfamily\footnotesize,
    backgroundcolor=\color{gray!5},
    frame=l,
    framerule=2pt,
    rulecolor=\color{blue!50},
    numbers=none,
    breaklines=true,
}
```

### Full Featured

```latex
\lstset{
    basicstyle=\ttfamily\footnotesize,
    backgroundcolor=\color{gray!5},
    frame=single,
    numbers=left,
    numberstyle=\tiny\color{gray},
    breaklines=true,
    showstringspaces=false,
    commentstyle=\color{green!50!black}\itshape,
    keywordstyle=\color{blue!70}\bfseries,
    stringstyle=\color{red!60!black},
}
```

## Table Styling

### Professional Tables

```latex
\usepackage{booktabs}
\renewcommand{\arraystretch}{1.2}

\begin{table}[htbp]
\centering
\small  % Slightly smaller text in tables
\begin{tabularx}{\textwidth}{lX}
\toprule
\textbf{Header 1} & \textbf{Header 2} \\
\midrule
Content & More content \\
Content & More content \\
\bottomrule
\end{tabularx}
\caption{Table caption}
\end{table}
```

### Alternating Row Colors

```latex
\usepackage[table]{xcolor}
\rowcolors{2}{gray!10}{white}

\begin{tabular}{ll}
\rowcolor{gray!30}
\textbf{Header} & \textbf{Header} \\
Row 1 & Data \\
Row 2 & Data \\
\end{tabular}
```

## Headers and Footers

### Simple with Rule

```latex
\makepagestyle{book}
\makeevenhead{book}{\thepage}{}{\small\scshape\leftmark}
\makeoddhead{book}{\small\scshape\rightmark}{}{\thepage}
\makeheadrule{book}{\textwidth}{0.4pt}
\pagestyle{book}
```

### Centered Page Numbers

```latex
\makepagestyle{centered}
\makeevenfoot{centered}{}{\thepage}{}
\makeoddfoot{centered}{}{\thepage}{}
\pagestyle{centered}
```

## Common Typography Mistakes

1. **Using `[h]` for floats** - Always use `[htbp]`
2. **Forcing justified bottoms** - Use `\raggedbottom`
3. **Default line spacing** - Consider `\linespread{1.05}`
4. **Cramped tables** - Always set `\arraystretch`
5. **Too many font sizes** - Stick to 2-3 sizes per hierarchy level
6. **Colored body text** - Keep body text black
7. **Underlining for emphasis** - Use italics instead
8. **Double spaces after periods** - LaTeX handles this automatically
