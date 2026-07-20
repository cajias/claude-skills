import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
import { execa } from "execa";
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const SUPPORTED_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".json", ".md"];
function isSupportedFile(path) {
  return SUPPORTED_EXTENSIONS.some((ext) => path.endsWith(ext));
}
function getGlobPattern(resolvedPath) {
  if (isSupportedFile(resolvedPath)) {
    return resolvedPath;
  }
  return `${resolvedPath}/**/*.{ts,tsx,js,jsx,json,md}`;
}
function getWorkingDirectory(resolvedPath) {
  if (resolvedPath.endsWith(".ts") || resolvedPath.endsWith(".js")) {
    return dirname(resolvedPath);
  }
  return resolvedPath;
}
function parseUnformattedFiles(output) {
  const unformatted = [];
  const lines = output.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    // Skip header lines, empty lines, and status messages
    if (
      !trimmed ||
      trimmed.startsWith("Checking") ||
      trimmed.startsWith("All") ||
      trimmed.startsWith("[")
    ) {
      continue;
    }
    unformatted.push(trimmed);
  }
  return unformatted;
}
export async function runPrettier(targetPath, write) {
  const resolvedPath = resolve(targetPath);
  const prettierBin = resolve(__dirname, "../../node_modules/.bin/prettier");
  const args = [getGlobPattern(resolvedPath)];
  args.push(write ? "--write" : "--check");
  args.push("--ignore-unknown");
  try {
    const { stdout, stderr, exitCode } = await execa(prettierBin, args, {
      reject: false,
      cwd: getWorkingDirectory(resolvedPath),
    });
    if (exitCode === 0) {
      return { unformatted: [] };
    }
    const output = stdout || stderr || "";
    return { unformatted: parseUnformattedFiles(output) };
  } catch (error) {
    console.error("Prettier error:", error);
    return { unformatted: [] };
  }
}
//# sourceMappingURL=prettier.js.map
