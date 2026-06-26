const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Pin the file-tracing root to this app (another lockfile exists higher up).
  outputFileTracingRoot: path.join(__dirname),
  // i18n note: the App Router handles locales via routing, not this key.
  // FR is the default; Arabic (RTL) and English are added in a later phase.
};

module.exports = nextConfig;
