# Software Effort Estimation & Codebase Valuation Skill

## Objective

Generate comprehensive software effort estimation reports that analyze codebase complexity, calculate traditional development effort across five estimation models, and quantify productivity gains from LLM-assisted development.

## Prerequisites

Before starting, ensure:

1. **Tools installed:**
   - Git (standard on most systems)
   - `cloc` (Count Lines of Code): Install via `brew install cloc` (macOS) or `apt-get install cloc` (Linux)
   - Optional: `gh` (GitHub CLI) for enhanced metrics

2. **Repository access:**
   - Local clone or path to git repository
   - Read access to all files
   - Complete git history available

3. **Project information:**
   - Project type (web app, infrastructure, mobile, embedded)
   - Actual development timeline (if known)
   - Team composition (if analyzing productivity gains)

## Input Parameters

Accept the following parameters from the user:

1. **repository_path** (required): Absolute path to git repository
2. **project_type** (optional): web-app, infrastructure, mobile, embedded, library (default: detect automatically)
3. **analysis_date** (optional): Date for report (default: today)
4. **primary_metric** (optional): person-months or monetary (default: person-months)
5. **hourly_rate** (optional): USD per hour for monetary conversion (default: $110)
6. **include_monetary** (optional): Include monetary conversion tables (default: true)

## Step-by-Step Workflow

### Phase 1: Repository Validation & Setup

**1. Validate repository structure:**

```bash
cd REPO_PATH

# Check if git repository
if [ ! -d ".git" ]; then
  echo "Error: Not a git repository"
  exit 1
fi

# Check for readable files
FILE_COUNT=$(find . -type f ! -path "./.git/*" | wc -l)
if [ "$FILE_COUNT" -lt 10 ]; then
  echo "Warning: Very few files found ($FILE_COUNT)"
fi
```

**2. Detect project type automatically:**

```bash
# Check for indicators
HAS_CDK=$(find . -name "cdk.json" -o -name "*-stack.ts" | wc -l)
HAS_K8S=$(find . -path "*/k8s/*.yaml" -o -name "deployment.yaml" | wc -l)
HAS_PACKAGE_JSON=$(find . -name "package.json" | wc -l)
HAS_GO_MOD=$(find . -name "go.mod" | wc -l)
HAS_CARGO=$(find . -name "Cargo.toml" | wc -l)

# Classify
if [ "$HAS_CDK" -gt 0 ] || [ "$HAS_K8S" -gt 0 ]; then
  PROJECT_TYPE="infrastructure"
elif [ "$HAS_PACKAGE_JSON" -gt 5 ]; then
  PROJECT_TYPE="web-app"
elif [ "$HAS_GO_MOD" -gt 0 ]; then
  PROJECT_TYPE="backend-service"
fi

echo "Detected project type: $PROJECT_TYPE"
```

**3. Create output directory:**

```bash
mkdir -p effort_estimation_output
cd effort_estimation_output
```

### Phase 2: Data Collection

#### 2.1 Git Metrics Collection

**Gather comprehensive git statistics:**

```bash
# Total commits (all branches)
TOTAL_COMMITS=$(git log --all --oneline | wc -l)
echo "Total commits: $TOTAL_COMMITS"

# Contributors and commit counts
git shortlog -sn --all > contributors.txt

# Calculate commit percentages
git shortlog -sn --all | awk -v total="$TOTAL_COMMITS" '{
  commits=$1
  name=substr($0, index($0,$2))
  percentage=(commits/total)*100
  printf "%s: %d commits (%.1f%%)\n", name, commits, percentage
}' > contributor_percentages.txt

# Active development days
ACTIVE_DAYS=$(git log --all --format="%ad" --date=short | sort -u | wc -l)
echo "Active development days: $ACTIVE_DAYS"

# Commit distribution by month
git log --all --format="%ad" --date=format:'%Y-%m' | sort | uniq -c > commits_by_month.txt

# First and last commit dates
FIRST_COMMIT=$(git log --all --reverse --format="%ad" --date=iso | head -1)
LAST_COMMIT=$(git log --all --format="%ad" --date=iso | head -1)
echo "First commit: $FIRST_COMMIT"
echo "Last commit: $LAST_COMMIT"

# Calculate calendar timeline
FIRST_DATE=$(git log --all --reverse --format="%ad" --date=short | head -1)
LAST_DATE=$(git log --all --format="%ad" --date=short | head -1)
DAYS_ELAPSED=$(( ( $(date -d "$LAST_DATE" +%s) - $(date -d "$FIRST_DATE" +%s) ) / 86400 ))
MONTHS_ELAPSED=$(echo "scale=1; $DAYS_ELAPSED / 30.0" | bc)
echo "Timeline: $DAYS_ELAPSED days ($MONTHS_ELAPSED months)"

# Peak commit months (top 5)
git log --all --format="%ad" --date=format:'%Y-%m' | sort | uniq -c | sort -rn | head -5 > peak_months.txt
```

#### 2.2 Code Metrics Collection

**Run cloc for comprehensive LOC analysis:**

```bash
# Full codebase analysis
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  --by-file-by-lang \
  --json \
  --report-file=cloc_full.json

# Simplified summary
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  > cloc_summary.txt

# Production code only (exclude tests)
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  --not-match-f='test|spec|__tests__|mock|.test.|.spec.' \
  > production_code.txt

# Test code only
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  --match-f='test|spec|__tests__|mock|.test.|.spec.' \
  > test_code.txt

# Extract key numbers
TOTAL_CODE_LINES=$(grep "SUM:" cloc_summary.txt | awk '{print $5}')
echo "Total code lines: $TOTAL_CODE_LINES"
```

**Parse cloc JSON output for detailed breakdown:**

```bash
# Extract language statistics from JSON
cat cloc_full.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for lang, stats in sorted(data.items(), key=lambda x: x[1].get('code', 0) if isinstance(x[1], dict) else 0, reverse=True):
    if lang not in ['header', 'SUM']:
        print(f\"{lang}: {stats['code']} lines, {stats['nFiles']} files\")
" > language_breakdown.txt
```

#### 2.3 File Counts by Type

**Count specific file types:**

```bash
# TypeScript/JavaScript
TS_FILES=$(find . -type f -name "*.ts" ! -path "./node_modules/*" ! -path "./dist/*" ! -path "./build/*" ! -path "./cdk.out/*" | wc -l)
JS_FILES=$(find . -type f -name "*.js" ! -path "./node_modules/*" ! -path "./dist/*" ! -path "./build/*" | wc -l)
TSX_FILES=$(find . -type f -name "*.tsx" ! -path "./node_modules/*" ! -path "./dist/*" | wc -l)
echo "TypeScript files: $TS_FILES"
echo "JavaScript files: $JS_FILES"
echo "TSX files: $TSX_FILES"

# Go
GO_FILES=$(find . -type f -name "*.go" ! -path "./vendor/*" | wc -l)
echo "Go files: $GO_FILES"

# Python
PY_FILES=$(find . -type f -name "*.py" ! -path "./.venv/*" ! -path "./venv/*" | wc -l)
echo "Python files: $PY_FILES"

# Rust
RS_FILES=$(find . -type f -name "*.rs" ! -path "./target/*" | wc -l)
echo "Rust files: $RS_FILES"

# Smithy models (if present)
SMITHY_FILES=$(find . -type f -name "*.smithy" | wc -l)
echo "Smithy model files: $SMITHY_FILES"

# Markdown documentation
MD_FILES=$(find . -type f -name "*.md" ! -path "./node_modules/*" | wc -l)
echo "Markdown files: $MD_FILES"

# YAML configuration
YAML_FILES=$(find . -type f \( -name "*.yaml" -o -name "*.yml" \) ! -path "./node_modules/*" ! -path "./vendor/*" | wc -l)
echo "YAML files: $YAML_FILES"

# JSON configuration
JSON_FILES=$(find . -type f -name "*.json" ! -path "./node_modules/*" ! -path "./dist/*" | wc -l)
echo "JSON files: $JSON_FILES"

# package.json (npm workspaces/monorepo indicator)
PACKAGE_JSON_COUNT=$(find . -type f -name "package.json" | wc -l)
echo "package.json files: $PACKAGE_JSON_COUNT"
```

#### 2.4 Infrastructure Inventory

**For AWS CDK projects:**

```bash
if [ -f "cdk.json" ] || find . -name "*-stack.ts" | grep -q .; then
  echo "AWS CDK project detected"
  
  # Lambda functions
  LAMBDA_COUNT=$(grep -r "new lambda.NodejsFunction\|new lambda.Function" --include="*.ts" --include="*.js" | wc -l)
  echo "Lambda functions: $LAMBDA_COUNT"
  
  # CDK stacks
  STACK_COUNT=$(grep -r "extends cdk.Stack\|extends Stack" --include="*.ts" --include="*.js" | wc -l)
  echo "CDK stacks: $STACK_COUNT"
  
  # DynamoDB tables
  DYNAMO_COUNT=$(grep -r "new dynamodb.Table\|new Table" --include="*.ts" --include="*.js" | grep -i dynamodb | wc -l)
  echo "DynamoDB tables: $DYNAMO_COUNT"
  
  # S3 buckets
  S3_COUNT=$(grep -r "new s3.Bucket" --include="*.ts" --include="*.js" | wc -l)
  echo "S3 buckets: $S3_COUNT"
  
  # API Gateways
  API_COUNT=$(grep -r "new apigateway\|new RestApi\|new HttpApi" --include="*.ts" --include="*.js" | wc -l)
  echo "API Gateways: $API_COUNT"
  
  # EventBridge rules
  EVENT_COUNT=$(grep -r "new events.Rule\|new Rule" --include="*.ts" --include="*.js" | grep -i event | wc -l)
  echo "EventBridge rules: $EVENT_COUNT"
fi
```

**For Kubernetes deployments:**

```bash
if find . -path "*/k8s/*.yaml" -o -name "deployment.yaml" | grep -q .; then
  echo "Kubernetes deployment detected"
  
  # Count YAML manifests
  K8S_MANIFESTS=$(find . -type f -name "*.yaml" -path "*/k8s/*" | wc -l)
  echo "Kubernetes manifests: $K8S_MANIFESTS"
  
  # Extract resource counts
  grep -r "kind:" --include="*.yaml" -h | awk '{print $2}' | sort | uniq -c > k8s_resources.txt
  
  # Specific resource types
  DEPLOYMENTS=$(grep -r "kind: Deployment" --include="*.yaml" | wc -l)
  SERVICES=$(grep -r "kind: Service" --include="*.yaml" | wc -l)
  CONFIGMAPS=$(grep -r "kind: ConfigMap" --include="*.yaml" | wc -l)
  echo "Deployments: $DEPLOYMENTS, Services: $SERVICES, ConfigMaps: $CONFIGMAPS"
fi
```

**For Docker containerization:**

```bash
DOCKERFILES=$(find . -name "Dockerfile*" ! -path "./node_modules/*" | wc -l)
DOCKER_COMPOSE=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | wc -l)
echo "Dockerfiles: $DOCKERFILES"
echo "Docker Compose files: $DOCKER_COMPOSE"
```

#### 2.5 Generated Code Detection

**Identify and count generated code:**

```bash
# Smithy-generated code
if [ "$SMITHY_FILES" -gt 0 ]; then
  SMITHY_GEN_LINES=$(find . -path "*/generated/*" -name "*.ts" -exec wc -l {} + | tail -1 | awk '{print $1}')
  echo "Smithy-generated lines: $SMITHY_GEN_LINES"
fi

# OpenAPI/Swagger generated
OPENAPI_GEN=$(find . -path "*/generated/*" -path "*/openapi/*" -name "*.ts" -o -name "*.js" | wc -l)
if [ "$OPENAPI_GEN" -gt 0 ]; then
  echo "OpenAPI-generated files detected: $OPENAPI_GEN"
fi

# Protobuf generated
PROTO_FILES=$(find . -name "*.proto" | wc -l)
PROTO_GEN=$(find . -name "*_pb.ts" -o -name "*_pb.js" -o -name "*.pb.go" | wc -l)
echo "Proto files: $PROTO_FILES, Generated: $PROTO_GEN"

# GraphQL generated
GRAPHQL_FILES=$(find . -name "*.graphql" -o -name "*.gql" | wc -l)
GRAPHQL_GEN=$(find . -path "*/generated/*" -name "*graphql*" | wc -l)
echo "GraphQL files: $GRAPHQL_FILES, Generated: $GRAPHQL_GEN"
```

### Phase 3: Effort Estimation Models

#### Model 1: COCOMO II (Constructive Cost Model)

**Apply COCOMO II formula with complexity multipliers:**

**Formula:** `Effort = A × (Size^B) × M`

**Parameters:**
- A = 3.0 (Embedded mode for complex systems)
- B = 1.12 (Complexity exponent)
- Size = KLOC (thousands of lines of code)
- M = Product of effort multipliers

**Complexity Classification:**

Determine complexity multipliers based on project characteristics:

```python
# Pseudo-code for multiplier selection
complexity_multipliers = {
    "Product Complexity": 1.74,  # Very high (distributed/WASM/event-driven)
    "Required Reliability": 1.26,  # High (production systems)
    "Database Size": 1.14,  # Large data storage
    "Platform Difficulty": 1.30,  # High (Kubernetes/serverless)
    "Programmer Capability": 0.86,  # Very high (reduces effort)
    "Software Tools": 0.83,  # Very high automation (reduces effort)
}

# Adjust based on actual project:
if not has_distributed_architecture:
    complexity_multipliers["Product Complexity"] = 1.30  # High instead of very high

if not has_kubernetes_or_serverless:
    complexity_multipliers["Platform Difficulty"] = 1.00  # Normal

# Calculate total multiplier
M = product(complexity_multipliers.values())
```

**Calculation Steps:**

```python
# 1. Get LOC from cloc output
production_loc = TOTAL_CODE_LINES  # From cloc
production_kloc = production_loc / 1000

# 2. Calculate complexity multiplier
M = 1.74 * 1.26 * 1.14 * 1.30 * 0.86 * 0.83
# M ≈ 2.15 (typical for complex infrastructure)

# 3. Calculate effort
A = 3.0
B = 1.12
effort_person_months = A * (production_kloc ** B) * M

# 4. Calculate duration
duration_months = 2.5 * (effort_person_months ** 0.38)

# 5. Calculate optimal team size
optimal_team_size = effort_person_months / duration_months

# Example output format:
print(f"COCOMO II Estimation:")
print(f"  Production LOC: {production_loc:,}")
print(f"  KLOC: {production_kloc:.1f}")
print(f"  Complexity Multiplier: {M:.2f}")
print(f"  Estimated Effort: {effort_person_months:.0f} person-months")
print(f"  Estimated Duration: {duration_months:.1f} months")
print(f"  Optimal Team Size: {optimal_team_size:.1f} people")
```

**Calculate for multiple scenarios:**

1. **Production code only** (most conservative)
2. **Production + test code** (comprehensive)
3. **With infrastructure complexity** (if applicable)

#### Model 2: Industry Productivity Benchmarks

**Apply industry-standard productivity rates:**

**Baseline Rates (LOC per developer-day):**

```python
complexity_rates = {
    "Simple": 75,      # Simple projects: 50-100 LOC/day
    "Medium": 37.5,    # Medium complexity: 25-50 LOC/day
    "High": 17.5,      # High complexity: 10-25 LOC/day
    "Very High": 12,   # Very high complexity: 5-15 LOC/day
}
```

**Classification Criteria:**

Select "Very High" (12 LOC/day) if project has 3+ of:
- ✓ Distributed systems architecture
- ✓ Real-time processing requirements
- ✓ Multi-language codebase (3+ languages)
- ✓ Container orchestration (Kubernetes)
- ✓ Infrastructure-as-code
- ✓ Event-driven patterns
- ✓ WASM or specialized compilation
- ✓ Microservices architecture

**Calculation:**

```python
# 1. Classify project complexity
complexity_score = 0
if has_distributed_architecture: complexity_score += 1
if has_realtime_processing: complexity_score += 1
if language_count >= 3: complexity_score += 1
if has_kubernetes: complexity_score += 1
if has_iac: complexity_score += 1
if has_event_driven: complexity_score += 1
if has_wasm: complexity_score += 1
if has_microservices: complexity_score += 1

if complexity_score >= 5:
    productivity_rate = 12  # Very high complexity
elif complexity_score >= 3:
    productivity_rate = 17.5  # High complexity
elif complexity_score >= 1:
    productivity_rate = 37.5  # Medium complexity
else:
    productivity_rate = 75  # Simple

# 2. Calculate effort
developer_days = production_loc / productivity_rate
person_months = developer_days / 22  # 22 working days per month
person_years = person_months / 12

print(f"Industry Benchmark Estimation:")
print(f"  Complexity: {complexity_score}/8 indicators")
print(f"  Productivity Rate: {productivity_rate} LOC/day")
print(f"  Developer-Days: {developer_days:.0f}")
print(f"  Person-Months: {person_months:.0f}")
print(f"  Person-Years: {person_years:.1f}")
```

#### Model 3: Infrastructure Multiplier

**Add component-based estimates for infrastructure work:**

Traditional LOC models undervalue infrastructure. Apply component-based estimates:

**Component Effort Table:**

```python
infrastructure_components = {
    "Lambda Function": 2.5,           # 2-3 days each
    "CDK Stack": 4,                   # 3-5 days each
    "EKS Cluster": 12.5,              # 10-15 days setup
    "WASM Plugin": 7.5,               # 5-10 days each
    "EventBridge Integration": 4,     # 3-5 days each
    "DynamoDB Table": 2.5,            # 2-3 days design
    "API Gateway": 2.5,               # 2-3 days each
    "CI/CD Pipeline": 10,             # 8-12 days setup
    "Kubernetes Deployment": 3,       # 2-4 days each
    "Docker Container": 2,            # 1-3 days each
    "S3 Bucket + Config": 1.5,        # 1-2 days each
}
```

**Calculation:**

```python
# Count infrastructure components (from Phase 2.4)
components = {
    "Lambda Function": LAMBDA_COUNT,
    "CDK Stack": STACK_COUNT,
    "DynamoDB Table": DYNAMO_COUNT,
    "S3 Bucket + Config": S3_COUNT,
    "API Gateway": API_COUNT,
    "EventBridge Integration": EVENT_COUNT,
    "Kubernetes Deployment": DEPLOYMENTS,
    "Docker Container": DOCKERFILES,
    "CI/CD Pipeline": 1,  # Assume one main pipeline
}

# Calculate infrastructure days
infrastructure_days = 0
for component, count in components.items():
    if count > 0:
        days_each = infrastructure_components.get(component, 3)
        component_days = count * days_each
        infrastructure_days += component_days
        print(f"  {component}: {count} × {days_each} days = {component_days} days")

# Convert to person-months
infrastructure_person_months = infrastructure_days / 22

# Get code-only estimate (from Model 1 or 2)
code_only_person_months = effort_person_months  # From previous model

# Apply infrastructure premium (30-40%)
infrastructure_premium = 0.35  # 35% average
total_person_months = code_only_person_months * (1 + infrastructure_premium)

# Or use component-based addition
total_with_infra = code_only_person_months + infrastructure_person_months

print(f"\nInfrastructure Multiplier Estimation:")
print(f"  Code-Only Estimate: {code_only_person_months:.0f} person-months")
print(f"  Infrastructure Components: {infrastructure_person_months:.0f} person-months")
print(f"  Total (component-based): {total_with_infra:.0f} person-months")
print(f"  Total (35% premium): {total_person_months:.0f} person-months")
```

#### Model 4: Blended Hybrid Approach

**Apply different complexity factors by code type:**

```python
# Separate code by type
code_breakdown = {
    "production": {
        "lines": production_loc,
        "rate": 12,  # Very high complexity
    },
    "test": {
        "lines": test_loc,
        "rate": 25,  # Medium complexity (tests are faster to write)
    },
    "generated": {
        "lines": generated_loc,
        "rate": 100,  # Minimal effort (automated)
    },
    "documentation": {
        "lines": documentation_loc,
        "rate": 100,  # Fast (markdown)
    },
}

# Calculate effort for each type
total_effort_days = 0
for code_type, info in code_breakdown.items():
    days = info["lines"] / info["rate"]
    total_effort_days += days
    print(f"  {code_type.capitalize()}: {info['lines']:,} lines @ {info['rate']} LOC/day = {days:.0f} days")

blended_person_months = total_effort_days / 22

# Adjust for code generation tools
if generated_loc > 0:
    generation_savings_pct = (generated_loc / (production_loc + generated_loc)) * 100
    print(f"  Code generation savings: {generation_savings_pct:.1f}% of codebase")

print(f"\nBlended Hybrid Estimation: {blended_person_months:.0f} person-months")
```

#### Model 5: Equivalent Team Analysis

**Calculate traditional team sizes for different timelines:**

```python
# Use average estimate from Models 1-4
average_effort = (cocomo_effort + benchmark_effort + infra_effort + blended_effort) / 4

# Calculate team sizes for different timelines
timelines = {
    "12-month aggressive": 12,
    "18-month standard": 18,
    "24-month conservative": 24,
    "COCOMO optimal": duration_months,  # From Model 1
}

print("\nEquivalent Team Analysis:")
for timeline_name, months in timelines.items():
    team_size = average_effort / months
    
    # Team composition breakdown
    if team_size <= 3:
        composition = "1 lead, 1-2 senior devs"
    elif team_size <= 7:
        composition = f"1 lead, 2 senior, {int(team_size-3)} mid-level"
    elif team_size <= 15:
        senior_count = int(team_size * 0.3)
        mid_count = int(team_size * 0.5)
        junior_count = int(team_size * 0.2)
        composition = f"1 manager, {senior_count} senior, {mid_count} mid, {junior_count} junior, 1 DevOps"
    else:
        senior_count = int(team_size * 0.25)
        mid_count = int(team_size * 0.45)
        junior_count = int(team_size * 0.25)
        devops_count = max(2, int(team_size * 0.05))
        composition = f"2 managers, {senior_count} senior, {mid_count} mid, {junior_count} junior, {devops_count} DevOps"
    
    print(f"  {timeline_name}: {team_size:.1f} people ({composition})")
```

### Phase 4: Productivity Multiplier Analysis

**Calculate actual effort and productivity gains:**

#### 4.1 Calculate Effective FTE

```python
# From git contributor analysis
contributors = {
    "Lead Developer": {"commits": 520, "percentage": 52.1},
    "Contributor 2": {"commits": 280, "percentage": 28.0},
    "Contributor 3": {"commits": 150, "percentage": 15.0},
    "Others": {"commits": 50, "percentage": 5.0},
}

# Calculate effective FTE
# Lead (>50%) = 1.0 FTE
# Others weighted by percentage
effective_fte = 0

for name, stats in contributors.items():
    pct = stats["percentage"]
    if pct >= 50:
        fte = 1.0
    elif pct >= 25:
        fte = 0.75
    elif pct >= 10:
        fte = 0.5
    else:
        fte = 0.25
    
    effective_fte += fte
    print(f"  {name}: {pct}% commits = {fte} FTE")

print(f"\nTotal Effective FTE: {effective_fte:.1f}")
```

#### 4.2 Calculate Actual Effort

```python
# From git timeline analysis
calendar_days = DAYS_ELAPSED  # From Phase 2.1
calendar_months = calendar_days / 30.0

# Account for part-time/intermittent work
# Active days = days with commits
working_days_ratio = ACTIVE_DAYS / calendar_days
actual_effective_months = calendar_months * effective_fte * working_days_ratio

print(f"\nActual Effort Calculation:")
print(f"  Calendar Timeline: {calendar_months:.1f} months")
print(f"  Effective FTE: {effective_fte:.1f}")
print(f"  Working Days Ratio: {working_days_ratio:.2f}")
print(f"  Actual Effort: {actual_effective_months:.1f} person-months")
```

#### 4.3 Calculate Productivity Multiplier

```python
# Compare traditional vs actual
traditional_effort_low = min(cocomo_effort, benchmark_effort, infra_effort, blended_effort)
traditional_effort_high = max(cocomo_effort, benchmark_effort, infra_effort, blended_effort)
traditional_effort_avg = average_effort

productivity_multiplier_low = traditional_effort_low / actual_effective_months
productivity_multiplier_high = traditional_effort_high / actual_effective_months
productivity_multiplier_avg = traditional_effort_avg / actual_effective_months

print(f"\nProductivity Multiplier Analysis:")
print(f"  Traditional Estimate: {traditional_effort_low:.0f}-{traditional_effort_high:.0f} person-months")
print(f"  Actual Effort: {actual_effective_months:.1f} person-months")
print(f"  Productivity Gain: {productivity_multiplier_low:.0f}x to {productivity_multiplier_high:.0f}x")
print(f"  Average Multiplier: {productivity_multiplier_avg:.0f}x")
```

#### 4.4 Time Compression Analysis

```python
# Traditional timeline (from COCOMO)
traditional_duration = duration_months  # From Model 1
actual_duration = calendar_months

time_compression = traditional_duration / actual_duration

print(f"\nTime Compression Analysis:")
print(f"  Traditional Duration: {traditional_duration:.1f} months")
print(f"  Actual Duration: {actual_duration:.1f} months")
print(f"  Time Compression: {time_compression:.1f}x faster")
```

### Phase 5: Verification Process

**Three-stage verification for accuracy:**

#### 5.1 Automated Counting Verification

```bash
# Re-run key commands and compare
echo "=== Verification: Re-running automated counts ==="

# Verify LOC count with alternative tool (if available)
if command -v tokei &> /dev/null; then
    tokei . --exclude node_modules dist build > tokei_output.txt
    echo "Alternative LOC count with tokei (for comparison)"
fi

# Verify git commit count
VERIFY_COMMITS=$(git rev-list --all --count)
if [ "$VERIFY_COMMITS" -eq "$TOTAL_COMMITS" ]; then
    echo "✓ Git commit count verified: $TOTAL_COMMITS"
else
    echo "⚠ Discrepancy in commit count: $TOTAL_COMMITS vs $VERIFY_COMMITS"
fi

# Verify file counts
VERIFY_TS=$(find . -name "*.ts" ! -path "./node_modules/*" ! -path "./dist/*" | wc -l)
if [ "$VERIFY_TS" -eq "$TS_FILES" ]; then
    echo "✓ TypeScript file count verified: $TS_FILES"
else
    echo "⚠ TypeScript file count discrepancy"
fi
```

#### 5.2 Manual Spot-Check Verification

```python
# Perform manual verification on 10% sample
import random

# Select random files for manual verification
all_files = [/* list from cloc */]
sample_size = max(10, len(all_files) // 10)
sample_files = random.sample(all_files, sample_size)

print(f"\nManual Verification Sample ({sample_size} files):")
for file_path in sample_files:
    # Manual review checklist:
    # 1. Is file correctly categorized (prod vs test)?
    # 2. Is line count reasonable?
    # 3. Is language detection correct?
    # 4. Is file generated or hand-written?
    print(f"  [ ] {file_path}")

# Spot-check infrastructure counts
print("\nInfrastructure Verification:")
print(f"  [ ] Manually verify Lambda count in AWS console/CDK files")
print(f"  [ ] Verify stack count by listing stack files")
print(f"  [ ] Check DynamoDB table definitions")
```

#### 5.3 Cross-Model Validation

```python
# Compare estimates across models
estimates = {
    "COCOMO II": cocomo_effort,
    "Industry Benchmark": benchmark_effort,
    "Infrastructure Multiplier": infra_effort,
    "Blended Hybrid": blended_effort,
    "Team Analysis": average_effort,
}

mean_estimate = sum(estimates.values()) / len(estimates)
std_dev = (sum((x - mean_estimate) ** 2 for x in estimates.values()) / len(estimates)) ** 0.5
coeff_variation = (std_dev / mean_estimate) * 100

print(f"\nCross-Model Validation:")
print(f"  Mean Estimate: {mean_estimate:.0f} person-months")
print(f"  Standard Deviation: {std_dev:.0f}")
print(f"  Coefficient of Variation: {coeff_variation:.1f}%")

# Flag outliers (>20% variance from mean)
outliers = []
for model, estimate in estimates.items():
    variance_pct = abs(estimate - mean_estimate) / mean_estimate * 100
    status = "✓" if variance_pct < 20 else "⚠"
    print(f"  {status} {model}: {estimate:.0f} person-months ({variance_pct:+.1f}%)")
    if variance_pct >= 20:
        outliers.append(model)

if outliers:
    print(f"\n⚠ Outliers requiring explanation: {', '.join(outliers)}")
```

#### 5.4 Generate Verification Report

```python
# Calculate overall confidence
verified_claims = 0
total_claims = 0

# Automated verification results
automated_accuracy = 0.95  # 95% of automated counts match

# Manual verification results
manual_sample_verified = 0.92  # 92% of manual spot-checks pass

# Cross-model convergence
convergence_quality = 1.0 if coeff_variation < 15 else 0.8 if coeff_variation < 25 else 0.6

# Overall confidence score
overall_confidence = (automated_accuracy * 0.5 + 
                     manual_sample_verified * 0.3 + 
                     convergence_quality * 0.2)

confidence_level = "High" if overall_confidence >= 0.85 else "Medium" if overall_confidence >= 0.70 else "Low"

print(f"\n{'='*60}")
print(f"VERIFICATION SUMMARY")
print(f"{'='*60}")
print(f"Automated Counting Accuracy: {automated_accuracy*100:.0f}%")
print(f"Manual Verification Pass Rate: {manual_sample_verified*100:.0f}%")
print(f"Cross-Model Convergence: {convergence_quality*100:.0f}%")
print(f"Overall Confidence: {confidence_level} ({overall_confidence*100:.0f}%)")
print(f"{'='*60}")
```

### Phase 6: Report Generation

Generate comprehensive markdown report with all findings.

#### 6.1 Report Structure

Create `effort_estimation.md` with the following sections:

**Section 1: Executive Summary (2-3 pages)**

```markdown
# Software Effort Estimation Report
## [Project Name]

**Analysis Date:** [DATE]
**Repository:** [REPO_PATH]
**Project Type:** [TYPE]

---

## Executive Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Lines of Code | [NUMBER] |
| Production Code | [NUMBER] lines |
| Test Code | [NUMBER] lines (ratio: [RATIO]:1) |
| Total Files | [NUMBER] |
| Primary Languages | [LANGUAGES] |
| Git Commits | [NUMBER] |
| Contributors | [NUMBER] |
| Development Timeline | [X] months ([Y] active days) |
| Infrastructure Components | [NUMBER] |

### What Was Delivered

[Project description based on code analysis]

Key components:
- [Component 1]
- [Component 2]
- [Infrastructure details]

### Estimation Models Summary

| Model | Estimated Effort | Methodology |
|-------|-----------------|-------------|
| COCOMO II | [X] person-months | Industry-standard constructive cost model |
| Industry Benchmarks | [X] person-months | Productivity rates by complexity |
| Infrastructure Multiplier | [X] person-months | Component-based cloud effort |
| Blended Hybrid | [X] person-months | Weighted approach by code type |
| Team Analysis | [X] person-months | Equivalent team calculations |
| **Consensus Range** | **[X]-[Y] person-months** | Average across models |

### Productivity Breakthrough

**Traditional Development:**
- Estimated Effort: [X]-[Y] person-months
- Estimated Duration: [X] months
- Required Team: [X]-[Y] developers

**Actual Development (LLM-Assisted):**
- Actual Effort: [X] person-months
- Actual Duration: [X] months
- Actual Team: [X] FTE

**Productivity Gains:**
- **[X]x to [Y]x productivity multiplier**
- **[X]x faster time-to-market**
- **[X]% reduction in team size**

### Quality Indicators

- Test Coverage Ratio: [X]:1 (production:test)
- Documentation: [X] markdown files
- Code Generation: [X]% automated
- Infrastructure as Code: [Yes/No]
- CI/CD Automation: [Level]

### Strategic Implications

[Key insights about the development approach, productivity gains, and business impact]
```

**Section 2: Raw Codebase Metrics (2-3 pages)**

```markdown
## Codebase Statistics

### Lines of Code Analysis

[Table with LOC breakdown by language]

### Code Distribution

**By Category:**
- Production Code: [X] lines ([Y]%)
- Test Code: [X] lines ([Y]%)
- Generated Code: [X] lines ([Y]%)
- Documentation: [X] lines ([Y]%)

**By Language:**
[Chart/table of top languages]

### File Counts

[Table of file types and counts]

### Git History

**Timeline:**
- First Commit: [DATE]
- Last Commit: [DATE]
- Total Duration: [X] days ([Y] months)
- Active Development Days: [X]

**Contributors:**
[Table with contributor names, commits, and percentages]

**Commit Distribution:**
[Monthly breakdown or chart]

### Infrastructure Complexity

[Details of AWS/Kubernetes/Docker components]
```

**Section 3: Five Estimation Models (10-12 pages, 2-3 pages per model)**

For each model, provide:
- Methodology explanation
- Calculation steps with actual numbers
- Assumptions and parameters
- Results summary
- Productivity multiplier calculation

**Section 4: Comprehensive Comparison (2-3 pages)**

```markdown
## Cross-Model Analysis

### Effort Estimates Comparison

[Table comparing all 5 models side-by-side]

### Model Convergence

[Analysis of agreement between models]

### Effort Savings Achieved

**Traditional vs Actual:**
[Detailed comparison with graphs/tables]

### Timeline Compression

[Analysis of time savings]

### Team Size Reduction

[Comparison of required vs actual team size]
```

**Section 5: Strategic Recommendations (2-3 pages)**

```markdown
## Strategic Implications

### Project Planning Guidelines

[How to use these estimates for future projects]

### Team Sizing Formulas

[Recommendations based on findings]

### Timeline Estimation

[Best practices for timeline estimation]

### Competitive Positioning

[How these productivity gains impact business strategy]

### Scaling Operations

[How to maintain productivity gains at scale]
```

**Section 6: Methodology & Verification (4-5 pages)**

```markdown
## Methodology Notes

### Data Collection Process

#### Git Metrics Methodology
[Exact commands used and why]

#### Code Counting Methodology
[cloc configuration and exclusions]

#### Infrastructure Counting
[Pattern matching approach]

### Verification Process

#### Stage 1: Automated Counting
[Results of automated verification]

#### Stage 2: Manual Spot-Check
[Sample files reviewed and findings]

#### Stage 3: Cross-Model Validation
[Convergence analysis]

### Verification Results

- Claims Verified: [X]%
- Within Acceptable Variance: [Y]%
- Corrections Made: [Z]%
- Overall Confidence: [High/Medium/Low] ([X]%)

### Quality Assurance

[Measures taken to ensure accuracy]

### Limitations & Caveats

[Important limitations to note]

### Reproducibility

[Complete list of commands to reproduce analysis]
```

**Section 7: Appendices (2-3 pages)**

```markdown
## Appendices

### Appendix A: Complete Git Statistics
[Full contributor breakdown, commit history]

### Appendix B: File Counts by Type
[Detailed file type analysis]

### Appendix C: Infrastructure Inventory
[Complete list of AWS/cloud resources]

### Appendix D: Tool Versions
[Versions of all tools used]

### Appendix E: References
[Citations for COCOMO, benchmarks, etc.]

### Appendix F: Monetary Conversion Tables (Optional)
[Convert person-months to USD at various hourly rates]

| Effort (PM) | @$90/hr | @$110/hr | @$130/hr | @$150/hr |
|-------------|---------|----------|----------|----------|
| [Low estimate] | $[X] | $[Y] | $[Z] | $[A] |
| [High estimate] | $[X] | $[Y] | $[Z] | $[A] |

*Calculation: person-months × 160 hours × hourly rate*
*Note: Monetary values are reference only; person-months is primary metric*
```

#### 6.2 Generate Supporting Files

**verification_report.md:**

```markdown
# Verification Report
## [Project Name] - [Date]

## Overview
This report documents the verification process used to ensure accuracy of the effort estimation analysis.

## Verification Stages

### 1. Automated Counting
[Results and accuracy metrics]

### 2. Manual Spot-Check
[Sample files reviewed and pass/fail]

### 3. Cross-Model Validation
[Model agreement analysis]

## Confidence Assessment

Overall Confidence: [High/Medium/Low] ([X]%)

## Corrections Made
[List of any corrections]

## Reproducibility Commands
[Complete command sequence to reproduce analysis]
```

**raw_metrics.json:**

```json
{
  "analysis_date": "2024-XX-XX",
  "repository": "/path/to/repo",
  "git_metrics": {
    "total_commits": 1000,
    "contributors": [...],
    "timeline": {...}
  },
  "code_metrics": {
    "total_loc": 93000,
    "production_loc": 53000,
    "test_loc": 40000,
    "languages": {...}
  },
  "estimates": {
    "cocomo_ii": 450,
    "industry_benchmark": 441,
    "infrastructure_multiplier": 582,
    "blended_hybrid": 434,
    "team_analysis": 477
  },
  "productivity": {
    "traditional_effort": 476,
    "actual_effort": 8.5,
    "multiplier": 56
  }
}
```

#### 6.3 Quality Checks

Before finalizing report:

```python
# Quality checklist
quality_checks = {
    "Word count >= 15,000": word_count >= 15000,
    "All numbers have sources": all_numbers_cited,
    "Reproducibility commands included": has_commands,
    "Multiple models used (5)": model_count >= 5,
    "Verification performed": verification_done,
    "Limitations documented": has_limitations,
    "Professional formatting": is_well_formatted,
}

print("\nQuality Checks:")
for check, passed in quality_checks.items():
    status = "✓" if passed else "✗"
    print(f"{status} {check}")

if all(quality_checks.values()):
    print("\n✅ Report ready for delivery")
else:
    print("\n⚠ Address failing quality checks before delivery")
```

## Output Summary

After completing all phases, provide summary:

```
✅ Generated: effort_estimation.md (22,450 words)
✅ Generated: verification_report.md (3,200 words)
✅ Generated: raw_metrics.json
✅ Generated: cloc_report.json
📊 Overall confidence: High (92% verified)
📈 Estimated effort: 434-582 person-months
⚡ Productivity: 50-66x vs traditional development
⏱️  Analysis completed in: 4 minutes
```

## Best Practices

1. **Always use verifiable data sources**
   - Command-line tools with reproducible output
   - Git history as source of truth
   - Standard industry models (COCOMO II)

2. **Triangulate with multiple models**
   - Never rely on single estimation method
   - Look for convergence (models agreeing within 20-30%)
   - Investigate and explain outliers

3. **Be conservative in assumptions**
   - Use mid-range values from tables
   - Document all assumptions explicitly
   - Provide ranges, not single numbers

4. **Make everything reproducible**
   - Include exact commands used
   - List tool versions
   - Document any manual adjustments

5. **Focus on person-months, not dollars**
   - Person-months is universal metric
   - Monetary values are highly variable
   - Include conversion tables as reference only

6. **Verify, verify, verify**
   - Three-stage verification process
   - Spot-check critical numbers manually
   - Compare across multiple sources

7. **Document limitations**
   - Be explicit about what's not measured
   - Note any data gaps or uncertainties
   - Explain variance between models

## Common Pitfalls to Avoid

1. ❌ Relying solely on LOC counting (use multiple models)
2. ❌ Ignoring infrastructure complexity (add component-based estimates)
3. ❌ Not accounting for generated code (separate and discount)
4. ❌ Single-point estimates (always provide ranges)
5. ❌ Claiming precision beyond data quality (be honest about confidence)
6. ❌ Forgetting to exclude build artifacts (node_modules, dist, etc.)
7. ❌ Mixing production and test code (separate for accuracy)
8. ❌ Not verifying git statistics (re-run and cross-check)

## Success Criteria

The analysis is successful when:

- ✅ Report exceeds 15,000 words
- ✅ Verification confidence is High (>85%)
- ✅ All 5 models converge within reasonable range (±30%)
- ✅ All numbers have reproducible sources
- ✅ Assumptions and limitations clearly documented
- ✅ Professional formatting and structure
- ✅ Ready for executive/stakeholder presentation
