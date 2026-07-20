export interface FixInput {
  path: string;
  language?: "typescript" | "python" | "auto";
}
export interface FixResult {
  fixed: {
    eslint: number;
    prettier: number;
    total: number;
  };
  files: string[];
}
export declare function fix(input: FixInput): Promise<FixResult>;
//# sourceMappingURL=fix.d.ts.map
