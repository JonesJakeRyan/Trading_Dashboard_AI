# Multi-stage build for React frontend
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files (build context is repo root)
COPY ./apps/frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code (including nginx.conf)
COPY ./apps/frontend/ ./

# Build the app
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration from builder stage
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Railway will set $PORT)
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
