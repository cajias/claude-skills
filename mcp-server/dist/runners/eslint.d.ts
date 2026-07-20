export interface EslintMessage {
  ruleId: string | null;
  severity: 1 | 2;
  message: string;
  line: number;
  column: number;
  endLine?: number;
  endColumn?: number;
  fix?: {
    range: [number, number];
    text: string;
  };
}
export interface EslintFileResult {
  filePath: string;
  messages: EslintMessage[];
  errorCount: number;
  warningCount: number;
  fixableErrorCount: number;
  fixableWarningCount: number;
}
export interface EslintIssue extends EslintMessage {
  filePath: string;
}
export declare function runEslint(
  targetPath: string,
  fix: boolean,
): Promise<EslintFileResult[]>;
//# sourceMappingURL=eslint.d.ts.map
