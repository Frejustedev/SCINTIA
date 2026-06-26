# Scintia frontend — Next.js (Phase 0). Multi-stage build.
FROM node:22-alpine AS base
WORKDIR /app

# ── Dependencies ──
FROM base AS deps
COPY package.json ./
# No lockfile committed yet; generate one locally and switch to `npm ci` later.
RUN npm install

# ── Build ──
FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ── Runtime ──
FROM base AS runner
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["npm", "start"]
