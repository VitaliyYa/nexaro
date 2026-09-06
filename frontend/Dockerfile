# Multi-stage Dockerfile for SmartRent Frontend
# Stage 1: Build SPA with Node.js + Vite
# Stage 2: Serve static files with Nginx
#
# NOTE: This Dockerfile must be built from the REPOSITORY ROOT (not frontend/)
# so that the schemas/ directory is available for TypeScript codegen.
# Example: docker build -f frontend/Dockerfile -t smartrent-frontend .

# ---------------------------------------------------------------------------
# Stage 1 — Build: compile TypeScript and bundle SPA
# ---------------------------------------------------------------------------
FROM node:24-alpine AS build

WORKDIR /app

# Copy schemas first (needed for codegen:types, lives at repo root)
COPY schemas/ /schemas/

# Copy dependency files for Docker layer caching
COPY frontend/package.json frontend/package-lock.json ./

# Install all dependencies (including devDependencies for build tools)
RUN npm ci

# Copy frontend source code
COPY frontend/ .

# Vite embeds VITE_* env vars at build time — pass via build args
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_API_BASE_URL=/api/v1

# Generate TypeScript types from SSOT JSON Schemas, then build
# codegen.js references ../../schemas — adjust symlink for Docker context
RUN ln -s /schemas /app/schemas && npm run codegen:types && npm run build

# ---------------------------------------------------------------------------
# Stage 2 — Serve: minimal Nginx image with compiled static files
# ---------------------------------------------------------------------------
FROM nginx:1-alpine AS runtime

# Remove default Nginx config and content
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy custom Nginx config for SPA routing
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built SPA from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Nginx runs as non-root by default in nginx:1-alpine (worker: nginx user)
CMD ["nginx", "-g", "daemon off;"]
