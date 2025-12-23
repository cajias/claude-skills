# Example Workflow: Generating README for a Sample Project

This example demonstrates the README Generator plugin workflow on a fictional Node.js library
called `json-validator`.

## Initial Setup

### Project Structure

```text
json-validator/
├── package.json
├── index.js
├── lib/
│   ├── validator.js
│   └── rules.js
├── test/
│   └── validator.test.js
└── README.md (empty or minimal)
```

### package.json

```json
{
  "name": "json-validator",
  "version": "1.2.0",
  "description": "Simple JSON schema validator with custom rules",
  "main": "index.js",
  "scripts": {
    "test": "jest"
  },
  "keywords": ["json", "validator", "schema"],
  "license": "MIT"
}
```

### Existing README.md

```markdown
# json-validator

A JSON validator library.
```

## Workflow Execution

### User Request

```text
Use /dev:review-readme to improve the README for this project. Focus on making it
comprehensive and following best practices.
```

### Iteration 1: Initial Analysis and Generation

#### Context Gathering

The command analyzes the project:

```text
✓ Package manager: npm
✓ Main file: index.js
✓ Entry point exports: validate(), addRule(), removeRule()
✓ Test files present: Yes (Jest)
✓ License: MIT
✓ Dependencies: None (pure JavaScript)
```

#### Initial Evaluation

```text
Current README Score: 25/100

Issues Found:
[CRITICAL]
- Missing Installation section
- Missing Usage examples with code

[HIGH]
- Description too brief (< 50 chars)
- No highlights or key features listed
- No API documentation

[MEDIUM]
- No Contributing section
- No examples section

Current README is minimal and needs substantial improvement.
```

#### Generation Phase

The command generates improved content:

````markdown
# json-validator

Simple and flexible JSON schema validator with support for custom validation rules.

## Highlights

- Zero dependencies - pure JavaScript implementation
- Custom validation rule support
- Clear, descriptive error messages
- Works in Node.js and browsers
- Simple, intuitive API
- Comprehensive test coverage

## Installation

### Via npm

```bash
npm install json-validator
```

### Via yarn

```bash
yarn add json-validator
```

## Usage

### Basic Validation

```javascript
const { validate } = require("json-validator");

const schema = {
  type: "object",
  properties: {
    name: { type: "string" },
    age: { type: "number" },
  },
  required: ["name"],
};

const data = {
  name: "John Doe",
  age: 30,
};

const result = validate(data, schema);
if (result.valid) {
  console.log("Data is valid!");
} else {
  console.log("Validation errors:", result.errors);
}
```

### Custom Rules

```javascript
const { addRule } = require("json-validator");

// Add a custom email validation rule
addRule("email", (value) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value);
});

const schema = {
  type: "object",
  properties: {
    email: { type: "email" },
  },
};
```

## API

### `validate(data, schema)`

Validates data against a JSON schema.

**Parameters:**

- `data` (any): The data to validate
- `schema` (Object): The JSON schema to validate against

**Returns:** Object with:

- `valid` (Boolean): Whether validation passed
- `errors` (Array): Array of validation error messages

### `addRule(name, validator)`

Adds a custom validation rule.

**Parameters:**

- `name` (String): Name of the custom rule
- `validator` (Function): Validation function that returns Boolean

### `removeRule(name)`

Removes a custom validation rule.

**Parameters:**

- `name` (String): Name of the rule to remove

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details.
````

#### Post-Generation Evaluation

```text
Updated README Score: 88/100

Improvements:
✓ Added Installation section with npm and yarn
✓ Added comprehensive Usage section with 2 code examples
✓ Added complete API documentation
✓ Added Highlights section with 6 key features
✓ Added Contributing section
✓ Expanded description

Remaining Issues:
[MEDIUM]
- Could add more advanced examples
- Could add troubleshooting section

Score exceeds threshold (88 >= 85) and no critical issues remain.
Status: COMPLETE
```

### Final Output

#### Summary

```text
README Generation Complete!

Status: Complete
Final Score: 88/100
Iterations: 1

Changes Made:
- Added Highlights section with 6 key features
- Added Installation section (npm and yarn methods)
- Created Usage section with 2 code examples
- Added complete API documentation for 3 functions
- Added Contributing and License sections
- Expanded project description

Quality Breakdown:
- Essential Sections: 100/100 ✓
- Content Quality: 85/100
- Code Examples: 90/100
- Formatting: 75/100

The README now meets all essential requirements and follows best practices.
Minor improvements could include additional examples and troubleshooting guidance.
```

## Example with Multiple Iterations

### Scenario: More Complex Project

Let's say the initial README had more issues:

#### Iteration 1

```text
Score: 35 → 68
Changes:
- Added Installation section
- Added basic Usage example
- Added minimal API docs

Remaining Issues:
- Usage examples not comprehensive
- API documentation incomplete
- No code examples for advanced features
```

#### Iteration 2

```text
Score: 68 → 82
Changes:
- Expanded Usage section with advanced example
- Completed API documentation
- Added parameter descriptions and return types

Remaining Issues:
- Could improve code example output
- Missing FAQ section (optional)
```

#### Iteration 3

```text
Score: 82 → 87
Changes:
- Enhanced code examples with expected output
- Added inline comments to examples
- Improved formatting consistency

Status: COMPLETE (87 >= 85 threshold)
```

## Different Mode Examples

### Mode: Generate (From Scratch)

Used when no README exists:

```text
User: "Generate a complete README for this project from scratch."

Result: Creates full README with all sections based on codebase analysis.
```

### Mode: Sections (Targeted)

Used to focus on specific sections:

```text
User: "Use the README Generator to improve just the Installation and Usage sections."

Config: sections_to_generate: ["installation", "usage"]

Result: Only modifies specified sections, leaves everything else unchanged.
```

### Mode: Improve with Preserved Sections

Used to protect certain content:

```text
User: "Improve the README but don't change the Contributing or Acknowledgments sections."

Config: preserve_sections: ["contributing", "acknowledgments"]

Result: Updates all sections except the preserved ones.
```

## Tips for Best Results

1. **Provide context**: If the project has special requirements, mention them:

   ```text
   "This is a library for financial calculations. Ensure examples emphasize precision."
   ```

2. **Specify priorities**: If certain sections are more important:

   ```text
   "Focus on comprehensive API documentation and usage examples."
   ```

3. **Review generated content**: The command aims for quality, but manual review of technical
   details is recommended.

4. **Iterate as needed**: If the first result isn't perfect, you can run the command again or
   request specific improvements.

## Common Issues and Solutions

### Issue: Generic examples

**Problem**: Code examples are too simple or don't show real use cases.

**Solution**: The command tries to analyze tests and actual code usage. If examples are still
generic, you can provide specific use cases to include.

### Issue: Missing project-specific details

**Problem**: Some project-specific information can't be inferred from code.

**Solution**: After generation, review and add project-specific details like deployment
instructions, environment requirements, or domain-specific considerations.

### Issue: Score plateaus below threshold

**Problem**: Score improves but doesn't reach the threshold.

**Solution**: The command will stop at max_iterations. Review remaining issues in the report and
address manually or adjust the threshold.
