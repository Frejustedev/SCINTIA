/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // i18n note: the App Router handles locales via routing, not this key.
  // FR is the default; Arabic (RTL) and English are added in a later phase.
};

module.exports = nextConfig;
