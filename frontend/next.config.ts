import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Next.js 16 auto-generates AGENTS.md/CLAUDE.md on every `next dev`/`next
  // build`; this project deliberately keeps the frontend free of AI-tooling
  // artifacts (see docs/AI_USAGE.md instead).
  agentRules: false,
};

export default nextConfig;
