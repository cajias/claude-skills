# dev-process

Process skills for the stretch of work between "we agreed to build this" and "it is
built and verified": authoring the design and plan documents, executing the resulting
milestone plan to green, and writing the documentation and READMEs that ship with it.
Also carries two cross-cutting habits — stating targets positively so agents read the
intent, and a coordinated playbook for schema drift between a validator and its
producers.

## Skills

| Skill                    | Purpose                                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------------------- |
| `create-readme`          | Write a README.md for the project.                                                                |
| `design-phase-artifacts` | Produce a C4 architecture overview plus five Notion design artifacts grounded in real code.       |
| `design-plan-docs`       | Generate the layered design doc set under `docs/design/`, with traceability and Mermaid diagrams. |
| `documentation-writer`   | Diataxis-guided technical writing for software documentation.                                     |
| `iterative-build-loop`   | Drive a milestone plan to test-verified done, then consolidate learnings into skills and hooks.   |
| `schema-drift-playbook`  | Fix validator-versus-data drift in three coordinated parts: relaxation, migration, producer fix.  |
| `state-the-target`       | State the target positively in specs, PRDs, design docs, and agent prompts.                       |

## Typical order

```text
design-plan-docs  ->  iterative-build-loop  ->  documentation-writer / create-readme
```
