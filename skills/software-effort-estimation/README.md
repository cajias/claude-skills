# Software Effort Estimation & Codebase Valuation Skill

Generate comprehensive software effort estimation reports analyzing codebase complexity, traditional
development effort estimates, and LLM-assisted productivity gains.

## Overview

This skill enables Claude to produce professional documentation analyzing:

- **Codebase Statistics**: Lines of code, files, commits, contributors
- **Effort Estimation**: Five independent models for triangulation (COCOMO II, Industry Benchmarks,
  Infrastructure Multiplier, Blended Hybrid, Team Analysis)
- **Productivity Analysis**: LLM-assisted vs traditional development multipliers
- **Verification**: Three-stage verification process with 90%+ accuracy
- **Strategic Insights**: Project planning guidelines and recommendations

## When to Use

Use this skill when you need to:

- Estimate traditional development effort for an existing codebase
- Demonstrate productivity gains from LLM-assisted development
- Value a software project for business purposes
- Provide defensible effort estimates backed by multiple models
- Analyze codebase complexity for project planning
- Compare actual vs estimated development timelines
- Generate comprehensive documentation for stakeholders

## Prerequisites

**Required Tools:**

- Git (for repository analysis)
- `cloc` (Count Lines of Code) - Install via `brew install cloc` (macOS) or
  `apt-get install cloc` (Linux)

**Optional Tools:**

- GitHub CLI (`gh`) for enhanced git statistics
- Language-specific analysis tools (gocloc, tokei, etc.)

**Repository Requirements:**

- Git repository with commit history
- Readable source files
- Standard project structure

## Key Features

### 1. Automated Data Collection

Uses command-line tools to gather verifiable metrics:

- Git statistics (commits, contributors, timeline)
- Code metrics (LOC by language, file counts)
- Infrastructure inventory (AWS CDK, Kubernetes, Docker)
- Generated code detection (Smithy, OpenAPI, protobuf)

### 2. Five Independent Estimation Models

Provides triangulation through multiple methodologies:

- **COCOMO II**: Industry-standard constructive cost model
- **Industry Benchmarks**: Productivity rates by complexity level
- **Infrastructure Multiplier**: Component-based cloud/infrastructure effort
- **Blended Hybrid**: Weighted approach by code type
- **Team Analysis**: Reverse engineering from actual timelines

### 3. Productivity Multiplier Analysis

Quantifies LLM-assisted development gains:

- Traditional effort estimates (400-600 person-months typical)
- Actual effort from commit history
- Productivity multiplier (often 50-100x)
- Time compression analysis

### 4. Three-Stage Verification

Ensures accuracy and defensibility:

- **Automated Counting**: Primary data from tools
- **Manual Verification**: Spot-checking critical numbers
- **Cross-Model Validation**: Convergence across models

### 5. Comprehensive Report Generation

Produces 15,000+ word markdown reports with:

- Executive summary with key metrics
- Detailed methodology notes
- Comparison tables across all models
- Strategic recommendations
- Reproducibility instructions

## Output Files

The skill generates:

1. **effort_estimation.md** - Main report (15,000-25,000 words)
2. **verification_report.md** - Accuracy assessment with confidence level
3. **raw_metrics.json** - Machine-readable data for further analysis
4. **cloc_report.json** - Detailed lines of code analysis

## Success Metrics

A successful implementation should:

- ✅ Generate 15,000+ word comprehensive report
- ✅ Achieve 90%+ verification accuracy
- ✅ Provide 5 independent effort estimates
- ✅ Include reproducibility commands
- ✅ Document all assumptions and limitations
- ✅ Complete analysis in <5 minutes for typical repo
- ✅ Produce professional, publication-ready output

## Limitations

- Requires accessible git repository with commit history
- Code metrics depend on accurate language detection
- Effort models assume traditional waterfall development
- Monetary valuations require manual hourly rate input
- Cannot assess code quality or technical debt directly
- Infrastructure counting requires standard patterns (CDK, K8s manifests)

## Key Insights

**What Makes This Skill Effective:**

1. **Multiple Models**: Convergence across 5 models (400-600 person-months) provides confidence
2. **Automated Collection**: All git/cloc stats extracted via reproducible scripts
3. **Verification Process**: 92%+ accuracy through three-stage verification
4. **Transparent Methodology**: Every number explained and reproducible
5. **Generated Code Tracking**: Smithy/OpenAPI codegen counted separately
6. **FTE Calculation**: Weighted by commit percentage for realistic effort estimates

## Related Skills

- Project planning and estimation
- Technical documentation generation
- Codebase analysis and metrics
- Software valuation and assessment

## References

Key sources for estimation models:

- COCOMO II Model - USC CSSE (<http://csse.usc.edu/tools/COCOMOII.php>)
- Capers Jones - "Estimating Software Costs" (2007)
- Steve McConnell - "Software Estimation: Demystifying the Black Art" (2006)
- Industry benchmarks from Stack Overflow, Robert Half, Glassdoor data
