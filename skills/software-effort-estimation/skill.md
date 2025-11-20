# Software Effort Estimation & Codebase Valuation Skill

## Objective

Generate comprehensive software effort estimation reports that analyze codebase complexity, calculate traditional development effort across five estimation models, and quantify productivity gains from LLM-assisted development.

## Prerequisites

1. **Tools installed:**
   - Git (standard on most systems)
   - `cloc` (Count Lines of Code): `brew install cloc` (macOS) or `apt-get install cloc` (Linux)
   - `bc` calculator (usually pre-installed)

2. **Repository access:**
   - Local clone or path to git repository
   - Read access to all files
   - Complete git history available

## Quick Start

Use the provided scripts for automated data collection:

```bash
# Navigate to the repository you want to analyze
cd /path/to/repository

# Run the master collection script
/path/to/skills/software-effort-estimation/scripts/collect_all_metrics.sh .

# This creates effort_estimation_output/ with all collected data
```

See `scripts/README.md` for detailed script documentation.

## Step-by-Step Workflow

### Phase 1: Data Collection

Use the automated scripts to collect all necessary metrics:

**Option A: Collect all metrics at once (recommended)**

```bash
cd /path/to/repository
./scripts/collect_all_metrics.sh .
```

**Option B: Run individual scripts**

```bash
# Git statistics
./scripts/collect_git_stats.sh . output/git_stats.txt

# Code metrics (requires cloc)
./scripts/collect_code_metrics.sh . output/metrics

# Infrastructure inventory
./scripts/collect_infrastructure.sh . output/infrastructure.txt
```

The scripts will generate:
- **git_stats.txt**: Total commits, contributors with percentages, active days, timeline
- **metrics/**: Detailed LOC analysis (production, test, generated code)
- **infrastructure.txt**: AWS CDK, Kubernetes, Docker inventory

### Phase 2: Apply Estimation Models

Using the collected data, calculate effort using five independent models:

#### Model 1: COCOMO II

**Formula:** `Effort = 3.0 × (KLOC^1.12) × ComplexityMultiplier`

**Complexity Multipliers:**
- Product Complexity: 1.74 (distributed/event-driven) or 1.30 (standard)
- Required Reliability: 1.26 (high) or 1.00 (normal)
- Database Size: 1.14 (large) or 1.00 (small)
- Platform Difficulty: 1.30 (Kubernetes/serverless) or 1.00 (standard)
- Programmer Capability: 0.86 (very high, reduces effort)
- Software Tools: 0.83 (very high automation, reduces effort)

**Duration:** `Duration = 2.5 × (Effort^0.38)` months

**Example Calculation:**
```python
# From collected data
production_kloc = 53.2  # From metrics/production_code.txt

# Complexity for distributed system
M = 1.74 * 1.26 * 1.14 * 1.30 * 0.86 * 0.83  # = 2.15

# Calculate effort
effort_pm = 3.0 * (53.2 ** 1.12) * 2.15  # = 450 person-months
duration = 2.5 * (450 ** 0.38)  # = 21.3 months
team_size = 450 / 21.3  # = 21 people
```

#### Model 2: Industry Benchmarks

**Productivity Rates:**
- Very High Complexity: 12 LOC/day (distributed, multi-language, event-driven)
- High Complexity: 17.5 LOC/day (microservices, cloud-native)
- Medium Complexity: 37.5 LOC/day (standard web/mobile apps)
- Simple: 75 LOC/day (basic CRUD applications)

**Classification:** Select "Very High" if project has 3+ of:
- Distributed systems architecture
- Real-time processing
- Multi-language codebase (3+ languages)
- Container orchestration (Kubernetes)
- Infrastructure-as-code
- Event-driven patterns
- WASM or specialized compilation

**Calculation:**
```python
production_loc = 74530  # From metrics
productivity_rate = 12  # Very high complexity
developer_days = 74530 / 12  # = 6211 days
person_months = 6211 / 22  # = 282 person-months
```

#### Model 3: Infrastructure Multiplier

**Component Effort Estimates:**
- Lambda Function: 2.5 days each
- CDK Stack: 4 days each
- DynamoDB Table: 2.5 days each
- API Gateway: 2.5 days each
- EventBridge Integration: 4 days each
- Kubernetes Deployment: 3 days each
- Docker Container: 2 days each
- CI/CD Pipeline: 10 days

**Calculation:**
```python
# From infrastructure.txt
components = {
    "Lambda": 23 * 2.5,      # = 57.5 days
    "CDK Stack": 8 * 4,      # = 32 days
    "DynamoDB": 12 * 2.5,    # = 30 days
    # ... add all components
}

infrastructure_days = sum(components.values())
infrastructure_pm = infrastructure_days / 22

# Apply 30-40% premium to code-only estimate
code_estimate = 450  # From Model 1
total_with_infra = code_estimate * 1.35  # = 608 person-months
```

#### Model 4: Blended Hybrid

**Apply different rates by code type:**
```python
code_breakdown = {
    "Production (TS/Go)": (74530, 12),    # LOC, rate
    "Test code": (39960, 25),             # Tests faster to write
    "Generated code": (39960, 100),       # Automated
    "Documentation": (3450, 100),         # Fast
}

total_days = sum(lines / rate for lines, rate in code_breakdown.values())
blended_pm = total_days / 22
blended_with_overhead = blended_pm * 1.30  # Add 30% for integration
```

#### Model 5: Team Analysis

**Calculate equivalent teams for different timelines:**
```python
average_estimate = (450 + 282 + 608 + 400) / 4  # = 435 person-months

timelines = {
    "12-month aggressive": 435 / 12,   # = 36 people
    "18-month standard": 435 / 18,     # = 24 people
    "24-month conservative": 435 / 24, # = 18 people
    "COCOMO optimal": 435 / 21.3,      # = 20 people
}
```

### Phase 3: Productivity Multiplier Analysis

Calculate actual effort and compare to traditional estimates:

**Calculate Effective FTE:**
```python
# From git_stats.txt contributor percentages
contributors = {
    "Lead (52.1%)": 1.0,      # >50% = 1.0 FTE
    "Backend (28.1%)": 0.75,  # >25% = 0.75 FTE
    "Infra (15.0%)": 0.5,     # >10% = 0.5 FTE
    "Others (4.8%)": 0.25,    # <10% = 0.25 FTE
}
effective_fte = 2.5  # Total
```

**Calculate Actual Effort:**
```python
# From git_stats.txt timeline
calendar_months = 7.6
active_ratio = 187 / 227  # Active days / total days = 0.82

actual_effort = calendar_months * effective_fte * active_ratio
# = 7.6 * 2.5 * 0.82 = 15.6 person-months
# Or conservatively: ~9 person-months
```

**Calculate Multiplier:**
```python
traditional_range = (434, 582)  # From models 1-4
actual_effort = 9

multiplier_low = 434 / 9  # = 48x
multiplier_high = 582 / 9  # = 65x
average_multiplier = 53x
```

### Phase 4: Verification Process

**Three-stage verification:**

1. **Automated Re-counting:**
   - Re-run scripts and compare results
   - Use alternative tools (e.g., `tokei` instead of `cloc`)
   - Verify git commit count: `git rev-list --all --count`

2. **Manual Spot-Check (10% sample):**
   - Randomly select files from each category
   - Verify language detection is correct
   - Confirm production vs test categorization
   - Check infrastructure component counts manually

3. **Cross-Model Validation:**
   ```python
   estimates = [450, 282, 608, 400]  # From 4 models
   mean = 435
   std_dev = 135
   coeff_variation = (135 / 435) * 100  # = 31%
   
   # Flag outliers >20% from mean
   # Document variance explanations
   ```

**Calculate Confidence:**
```python
automated_accuracy = 0.98  # % of automated counts that match
manual_pass_rate = 0.92     # % of spot-checks that pass
convergence = 0.85 if coeff_variation < 25 else 0.70

confidence = (automated_accuracy * 0.5 + 
              manual_pass_rate * 0.3 + 
              convergence * 0.2)

# "High" if >0.85, "Medium" if >0.70, else "Low"
```

### Phase 5: Report Generation

Generate comprehensive markdown report with these sections:

**1. Executive Summary (2-3 pages)**
- Key metrics table
- Project overview
- Estimation models summary
- Productivity breakthrough metrics
- Strategic implications

**2. Raw Codebase Metrics (2-3 pages)**
- LOC breakdown by language
- File counts by type
- Git history analysis
- Infrastructure inventory

**3. Five Estimation Models (10-12 pages)**
For each model:
- Methodology explanation
- Calculation steps with actual numbers
- Results and team size implications

**4. Comprehensive Comparison (2-3 pages)**
- Side-by-side model comparison
- Convergence analysis
- Variance explanations

**5. Strategic Recommendations (2-3 pages)**
- Project planning guidelines
- Team sizing formulas
- Timeline estimation best practices

**6. Methodology & Verification (4-5 pages)**
- Data collection commands
- Verification results
- Confidence assessment
- Limitations and caveats
- Reproducibility instructions

**7. Appendices (2-3 pages)**
- Complete git statistics
- Infrastructure component list
- Monetary conversion tables (optional)
- References

**Target:** 15,000-25,000 words total

## Output Files

Generate these files:

1. **effort_estimation.md** - Main report (~20,000 words)
2. **verification_report.md** - Verification details and confidence
3. **raw_metrics.json** - Machine-readable data
4. **effort_estimation_output/** - All collected data (from scripts)

## Best Practices

1. **Use the automated scripts** - Don't manually run individual commands
2. **Triangulate with multiple models** - Never rely on single estimate
3. **Verify, verify, verify** - Three-stage process is critical
4. **Be conservative** - Use mid-range values, document assumptions
5. **Focus on person-months** - Monetary values are secondary reference
6. **Make it reproducible** - Include all commands used
7. **Document limitations** - Be explicit about what's not measured

## Common Pitfalls to Avoid

- ❌ Not excluding build artifacts (node_modules, dist, etc.)
- ❌ Mixing production and test code in estimates
- ❌ Ignoring infrastructure complexity
- ❌ Single-point estimates without ranges
- ❌ Not accounting for generated code
- ❌ Forgetting to verify critical numbers
- ❌ Claiming precision beyond data quality

## Success Criteria

- ✅ Report exceeds 15,000 words
- ✅ Verification confidence is High (>85%)
- ✅ All 5 models converge within ±30%
- ✅ All numbers have reproducible sources
- ✅ Assumptions clearly documented
- ✅ Professional formatting
- ✅ Ready for executive presentation

## Examples

See `examples/example-workflow.md` for a complete real-world example with actual numbers and calculations.
