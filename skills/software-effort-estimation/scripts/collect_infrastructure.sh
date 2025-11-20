#!/bin/bash
# Collect infrastructure inventory
# Usage: ./collect_infrastructure.sh [repository_path] [output_file]

set -e

REPO_PATH="${1:-.}"
OUTPUT_FILE="${2:-infrastructure.txt}"

cd "$REPO_PATH"

echo "=== INFRASTRUCTURE INVENTORY ===" > "$OUTPUT_FILE"
echo "Repository: $REPO_PATH" >> "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Detect project type
echo "Project Type Detection:" >> "$OUTPUT_FILE"
HAS_CDK=$(find . -name "cdk.json" -o -name "*-stack.ts" 2>/dev/null | wc -l)
HAS_K8S=$(find . -path "*/k8s/*.yaml" -o -name "deployment.yaml" 2>/dev/null | wc -l)
HAS_DOCKER=$(find . -name "Dockerfile*" ! -path "./node_modules/*" 2>/dev/null | wc -l)

if [ "$HAS_CDK" -gt 0 ]; then
  echo "  - AWS CDK project detected" >> "$OUTPUT_FILE"
fi
if [ "$HAS_K8S" -gt 0 ]; then
  echo "  - Kubernetes deployment detected" >> "$OUTPUT_FILE"
fi
if [ "$HAS_DOCKER" -gt 0 ]; then
  echo "  - Docker containerization detected" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# AWS CDK Components
if [ "$HAS_CDK" -gt 0 ]; then
  echo "AWS CDK Components:" >> "$OUTPUT_FILE"
  
  LAMBDA_COUNT=$(grep -r "new lambda.NodejsFunction\|new lambda.Function" --include="*.ts" --include="*.js" 2>/dev/null | wc -l)
  echo "  Lambda functions: $LAMBDA_COUNT" >> "$OUTPUT_FILE"
  
  STACK_COUNT=$(grep -r "extends cdk.Stack\|extends Stack" --include="*.ts" --include="*.js" 2>/dev/null | wc -l)
  echo "  CDK stacks: $STACK_COUNT" >> "$OUTPUT_FILE"
  
  DYNAMO_COUNT=$(grep -r "new dynamodb.Table\|new Table" --include="*.ts" --include="*.js" 2>/dev/null | grep -i dynamodb | wc -l)
  echo "  DynamoDB tables: $DYNAMO_COUNT" >> "$OUTPUT_FILE"
  
  S3_COUNT=$(grep -r "new s3.Bucket" --include="*.ts" --include="*.js" 2>/dev/null | wc -l)
  echo "  S3 buckets: $S3_COUNT" >> "$OUTPUT_FILE"
  
  API_COUNT=$(grep -r "new apigateway\|new RestApi\|new HttpApi" --include="*.ts" --include="*.js" 2>/dev/null | wc -l)
  echo "  API Gateways: $API_COUNT" >> "$OUTPUT_FILE"
  
  EVENT_COUNT=$(grep -r "new events.Rule\|new Rule" --include="*.ts" --include="*.js" 2>/dev/null | grep -i event | wc -l)
  echo "  EventBridge rules: $EVENT_COUNT" >> "$OUTPUT_FILE"
  
  echo "" >> "$OUTPUT_FILE"
fi

# Kubernetes Resources
if [ "$HAS_K8S" -gt 0 ]; then
  echo "Kubernetes Resources:" >> "$OUTPUT_FILE"
  
  K8S_MANIFESTS=$(find . -type f -name "*.yaml" -path "*/k8s/*" 2>/dev/null | wc -l)
  echo "  Total manifests: $K8S_MANIFESTS" >> "$OUTPUT_FILE"
  
  DEPLOYMENTS=$(grep -r "kind: Deployment" --include="*.yaml" 2>/dev/null | wc -l)
  echo "  Deployments: $DEPLOYMENTS" >> "$OUTPUT_FILE"
  
  SERVICES=$(grep -r "kind: Service" --include="*.yaml" 2>/dev/null | wc -l)
  echo "  Services: $SERVICES" >> "$OUTPUT_FILE"
  
  CONFIGMAPS=$(grep -r "kind: ConfigMap" --include="*.yaml" 2>/dev/null | wc -l)
  echo "  ConfigMaps: $CONFIGMAPS" >> "$OUTPUT_FILE"
  
  echo "" >> "$OUTPUT_FILE"
fi

# Docker
if [ "$HAS_DOCKER" -gt 0 ]; then
  echo "Docker:" >> "$OUTPUT_FILE"
  DOCKERFILES=$(find . -name "Dockerfile*" ! -path "./node_modules/*" 2>/dev/null | wc -l)
  echo "  Dockerfiles: $DOCKERFILES" >> "$OUTPUT_FILE"
  
  DOCKER_COMPOSE=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" 2>/dev/null | wc -l)
  echo "  Docker Compose files: $DOCKER_COMPOSE" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
fi

# File type summary
echo "File Type Summary:" >> "$OUTPUT_FILE"

# TypeScript/JavaScript
TS_FILES=$(find . -type f -name "*.ts" ! -path "./node_modules/*" ! -path "./dist/*" ! -path "./build/*" 2>/dev/null | wc -l)
JS_FILES=$(find . -type f -name "*.js" ! -path "./node_modules/*" ! -path "./dist/*" ! -path "./build/*" 2>/dev/null | wc -l)
echo "  TypeScript files: $TS_FILES" >> "$OUTPUT_FILE"
echo "  JavaScript files: $JS_FILES" >> "$OUTPUT_FILE"

# Other languages
GO_FILES=$(find . -type f -name "*.go" ! -path "./vendor/*" 2>/dev/null | wc -l)
PY_FILES=$(find . -type f -name "*.py" ! -path "./.venv/*" ! -path "./venv/*" 2>/dev/null | wc -l)
RS_FILES=$(find . -type f -name "*.rs" ! -path "./target/*" 2>/dev/null | wc -l)

if [ "$GO_FILES" -gt 0 ]; then echo "  Go files: $GO_FILES" >> "$OUTPUT_FILE"; fi
if [ "$PY_FILES" -gt 0 ]; then echo "  Python files: $PY_FILES" >> "$OUTPUT_FILE"; fi
if [ "$RS_FILES" -gt 0 ]; then echo "  Rust files: $RS_FILES" >> "$OUTPUT_FILE"; fi

# Configuration files
YAML_FILES=$(find . -type f \( -name "*.yaml" -o -name "*.yml" \) ! -path "./node_modules/*" ! -path "./vendor/*" 2>/dev/null | wc -l)
JSON_FILES=$(find . -type f -name "*.json" ! -path "./node_modules/*" ! -path "./dist/*" 2>/dev/null | wc -l)
MD_FILES=$(find . -type f -name "*.md" ! -path "./node_modules/*" 2>/dev/null | wc -l)

echo "  YAML files: $YAML_FILES" >> "$OUTPUT_FILE"
echo "  JSON files: $JSON_FILES" >> "$OUTPUT_FILE"
echo "  Markdown files: $MD_FILES" >> "$OUTPUT_FILE"

echo ""
echo "Infrastructure inventory saved to: $OUTPUT_FILE"
