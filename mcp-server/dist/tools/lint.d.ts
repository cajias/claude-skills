export interface LintInput {
  path: string;
  language?: "typescript" | "python" | "auto";
}
export interface LintIssue {
  file: string;
  line: number;
  column: number;
  rule: string;
  message: string;
  severity: "error" | "warning";
  fixable: boolean;
  claudeFixable: boolean;
}
export interface LintResult {
  issues: LintIssue[];
  summary: {
    errors: number;
    warnings: number;
    fixable: number;
    claudeFixable: number;
    total: number;
  };
}
export declare function lint(input: LintInput): Promise<LintResult>;
//# sourceMappingURL=lint.d.ts.map
