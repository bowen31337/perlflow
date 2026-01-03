# PearlFlow Demo Web Dockerfile
# Multi-stage build for optimized Next.js app

# Stage 1: Builder
FROM node:20-alpine as builder

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copy monorepo root files
COPY ../../package.json ../../pnpm-workspace.yaml ./
COPY ../../turbo.json ./

# Copy workspace packages
COPY ../../packages/chat-ui/package.json ./packages/chat-ui/
COPY ../../packages/chat-ui/src ./packages/chat-ui/src
COPY ../../packages/chat-ui/tsconfig.json ./packages/chat-ui/

# Copy demo-web files
COPY ./package.json ./
COPY ./src ./src
COPY ./public ./public 2>/dev/null || true
COPY ./next.config.js ./postcss.config.js ./tailwind.config.ts ./tsconfig.json ./ ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build chat-ui package first
RUN pnpm --filter @pearlflow/chat-ui run build

# Build demo-web
RUN pnpm run build

# Stage 2: Runner
FROM node:20-alpine as runner

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Copy built artifacts from builder
COPY --from=builder --chown=nextjs:nodejs /app/apps/demo-web/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/apps/demo-web/package.json ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/demo-web/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/apps/demo-web/public ./public

# Copy chat-ui dist
COPY --from=builder --chown=nextjs:nodejs /app/packages/chat-ui/dist ./node_modules/@pearlflow/chat-ui/dist
COPY --from=builder --chown=nextjs:nodejs /app/packages/chat-ui/package.json ./node_modules/@pearlflow/chat-ui/
COPY --from=builder --chown=nextjs:nodejs /app/packages/chat-ui/src/types ./node_modules/@pearlflow/chat-ui/src/types

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start Next.js
CMD ["pnpm", "start"]
