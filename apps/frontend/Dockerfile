# Multi-stage build for React frontend
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy all source code
COPY . .

# Accept build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the app
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration from builder stage
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf

# Copy startup script
COPY --from=builder /app/start-nginx.sh /start-nginx.sh
RUN chmod +x /start-nginx.sh

# Expose port (Railway will set $PORT dynamically)
EXPOSE 80

# Start nginx with dynamic port
CMD ["/start-nginx.sh"]
