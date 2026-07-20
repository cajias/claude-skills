# typescript-eslint-object-injection-fix

Fix ESLint security/detect-object-injection warnings in TypeScript when building
dynamic objects from user input or external data. Use when: (1) ESLint shows
"Generic Object Injection Sink" warnings, (2) using bracket notation like
obj[key] = value, (3) iterating over headers, query params, or form data to
build objects. Prevents prototype pollution vulnerabilities using Object.create(null)
and Object.defineProperty pattern instead of disabling the lint rule.
