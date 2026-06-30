#!/usr/bin/env node
/**
 * Run the frontend's prettier (with prettier-plugin-tailwindcss) on the given files.
 *
 * prettier 3 resolves config plugins relative to its working directory, so we run
 * from ``frontend/`` (where node_modules holds the plugin) and pass absolute paths.
 * Used by the pre-commit ``prettier`` hook; cross-platform (Node only).
 */
const path = require("path");
const { execFileSync } = require("child_process");

const repoRoot = path.join(__dirname, "..");
const frontendDir = path.join(repoRoot, "frontend");
const prettierBin = path.join(frontendDir, "node_modules", "prettier", "bin", "prettier.cjs");

const files = process.argv.slice(2).map((f) => path.resolve(repoRoot, f));
if (files.length === 0) process.exit(0);

execFileSync(process.execPath, [prettierBin, "--write", "--ignore-unknown", ...files], {
  cwd: frontendDir,
  stdio: "inherit",
});
