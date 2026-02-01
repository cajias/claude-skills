---
name: typescript-eslint-object-injection-fix
description: |
  Fix ESLint security/detect-object-injection warnings in TypeScript when building
  dynamic objects from user input or external data. Use when: (1) ESLint shows
  "Generic Object Injection Sink" warnings, (2) using bracket notation like
  obj[key] = value, (3) iterating over headers, query params, or form data to
  build objects. Prevents prototype pollution vulnerabilities using Object.create(null)
  and Object.defineProperty pattern instead of disabling the lint rule.
author: Claude Code
version: 1.0.0
date: 2026-01-27
---

# TypeScript ESLint Object Injection Fix

## Problem
When dynamically building objects from external data (headers, query parameters, form data),
ESLint's `security/detect-object-injection` rule flags code like `obj[key] = value` as a
potential security vulnerability, warning about "Generic Object Injection Sink" that could
lead to prototype pollution attacks.

## Context / Trigger Conditions

**Exact error messages:**
```
Generic Object Injection Sink
security/detect-object-injection
```

**Common scenarios:**
1. Iterating over HTTP headers and storing them in an object
2. Processing query parameters or form data into a structured object
3. Aggregating data from multiple sources into a single result object
4. Any code using bracket notation with external/untrusted keys: `obj[key] = value`

**Example problematic code:**
```typescript
const headers: Record<string, string> = {};
response.headers.forEach((value, key) => {
  headers[key] = value;  // ⚠️ ESLint warning here
});
```

## Solution

Use `Object.create(null)` to create objects without a prototype chain, combined with
`Object.defineProperty` for safe property assignment:

### Pattern 1: Simple Key-Value Assignment
```typescript
// Instead of:
const headers: Record<string, string> = {};
response.headers.forEach((value, key) => {
  headers[key] = value;  // ❌ ESLint warning
});

// Use:
let headers: Record<string, string> = Object.create(null);
response.headers.forEach((value, key) => {
  Object.defineProperty(headers, key, {
    value,
    enumerable: true,
    configurable: true,
    writable: true,
  });
});
```

### Pattern 2: Conditional Property Creation
```typescript
// For objects built conditionally:
const aggregated: Record<string, string[]> = Object.create(null);

for (const [key, value] of Object.entries(data)) {
  if (!Object.prototype.hasOwnProperty.call(aggregated, key)) {
    Object.defineProperty(aggregated, key, {
      value: [],
      enumerable: true,
      configurable: true,
      writable: true,
    });
  }

  // Safe to access now - use Object.getOwnPropertyDescriptor
  const descriptor = Object.getOwnPropertyDescriptor(aggregated, key);
  const values = descriptor?.value as string[];
  if (values && !values.includes(value)) {
    values.push(value);
  }
}
```

### Pattern 3: Returning the Safe Object
```typescript
function filterHeaders(headers: Record<string, string>): Record<string, string> {
  const filtered: Record<string, string> = Object.create(null);

  for (const [key, value] of Object.entries(headers)) {
    if (isAllowed(key)) {
      Object.defineProperty(filtered, key, {
        value,
        enumerable: true,
        configurable: true,
        writable: true,
      });
    }
  }

  return filtered;  // Safe to return - no prototype
}
```

## Why This Works

### The Security Issue
Normal objects (`{}`) inherit from `Object.prototype`, which means keys like `__proto__`,
`constructor`, or `prototype` can be manipulated to pollute the prototype chain:

```typescript
const obj = {};
obj['__proto__'].polluted = true;
// Now ALL objects have polluted === true
```

### The Solution
`Object.create(null)` creates an object with NO prototype chain:
- No inherited properties
- No `__proto__` access point
- Cannot pollute other objects
- Still works with `Object.entries()`, `Object.keys()`, etc.

`Object.defineProperty` ensures properties are created safely with explicit descriptors,
preventing accidental prototype access.

## Verification

After applying the fix:
1. ESLint warnings should disappear
2. Run: `npm run lint` or `eslint .` - should pass
3. Tests should still pass (no functional change)
4. Verify in REPL that object has no prototype:
   ```javascript
   const obj = Object.create(null);
   console.log(Object.getPrototypeOf(obj));  // null
   ```

## Common Mistakes to Avoid

### ❌ Don't just disable the rule
```typescript
// eslint-disable-next-line security/detect-object-injection
headers[key] = value;  // Still vulnerable!
```

### ❌ Don't forget Object.create(null)
```typescript
const obj = {};  // Still has prototype!
Object.defineProperty(obj, key, { value });
```

### ❌ Don't use direct bracket notation on safe objects
```typescript
const obj: Record<string, string> = Object.create(null);
obj[key] = value;  // ⚠️ ESLint will still warn!
```

### ✅ Do use Object.defineProperty consistently
```typescript
const obj: Record<string, string> = Object.create(null);
Object.defineProperty(obj, key, {
  value,
  enumerable: true,
  configurable: true,
  writable: true,
});
```

## Real-World Example

From the MCP Multiplexer header handling code:

**Before (with warnings):**
```typescript
export function aggregateResponseHeaders(headerSets: Record<string, string>[]): Record<string, string> {
  const aggregated: Record<string, string[]> = {};

  for (const headers of headerSets) {
    const filtered = filterResponseHeaders(headers);
    for (const [key, value] of Object.entries(filtered)) {
      if (!aggregated[key]) {
        aggregated[key] = [];
      }
      if (!aggregated[key].includes(value)) {
        aggregated[key].push(value);
      }
    }
  }

  const result: Record<string, string> = {};
  for (const [key, values] of Object.entries(aggregated)) {
    result[key] = values.join(', ');
  }

  return result;
}
```

**After (safe, no warnings):**
```typescript
export function aggregateResponseHeaders(headerSets: Record<string, string>[]): Record<string, string> {
  const aggregated: Record<string, string[]> = Object.create(null);

  for (const headers of headerSets) {
    const filtered = filterResponseHeaders(headers);
    for (const [key, value] of Object.entries(filtered)) {
      if (!Object.prototype.hasOwnProperty.call(aggregated, key)) {
        Object.defineProperty(aggregated, key, {
          value: [],
          enumerable: true,
          configurable: true,
          writable: true,
        });
      }
      const descriptor = Object.getOwnPropertyDescriptor(aggregated, key);
      const values = descriptor?.value as string[];
      if (values && !values.includes(value)) {
        values.push(value);
      }
    }
  }

  const result: Record<string, string> = Object.create(null);
  for (const [key, values] of Object.entries(aggregated)) {
    Object.defineProperty(result, key, {
      value: values.join(', '),
      enumerable: true,
      configurable: true,
      writable: true,
    });
  }

  return result;
}
```

## When to Use This Pattern

**Always use when:**
- Building objects from HTTP headers
- Processing query parameters or form data
- Aggregating data from multiple untrusted sources
- Creating lookup tables from external input
- Any dynamic key assignment from user-controlled data

**Can skip when:**
- Keys are hardcoded string literals
- Building objects from trusted internal data only
- Using Maps instead of plain objects (Map is prototype-safe)

## Notes

- This pattern works with all TypeScript versions
- No runtime performance penalty (V8 optimizes this pattern)
- Compatible with JSON.stringify() - produces identical output
- `Object.entries()` and `Object.keys()` still work on null-prototype objects
- Alternative: Use `Map<string, T>` instead of `Record<string, T>` when possible
  (Maps don't have this issue but require `.get()/.set()` instead of bracket notation)

## References

- [OWASP: Prototype Pollution](https://owasp.org/www-community/vulnerabilities/Prototype_Pollution)
- [MDN: Object.create()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create)
- [MDN: Object.defineProperty()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty)
- [eslint-plugin-security: detect-object-injection](https://github.com/eslint-community/eslint-plugin-security/blob/main/docs/rules/detect-object-injection.md)
