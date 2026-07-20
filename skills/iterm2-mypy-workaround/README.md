# iterm2-mypy-workaround

Fix mypy "Name iterm2.Session is not defined" or "Name iterm2.Window is not defined"
errors in iterm-c4 project. Use when: (1) mypy fails with name-defined errors on
iterm2 types despite ignore_missing_imports=true in pyproject.toml, (2) working with
the iTerm2 Python API in type-annotated code. The iterm2 package lacks proper type
stubs, requiring a specific import + type-ignore pattern.
