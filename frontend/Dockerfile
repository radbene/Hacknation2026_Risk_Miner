# RISK MINER web: static Vite build served by Caddy on :80 (the edge Caddy proxies / → web, /api → api).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
RUN printf ':80 {\n  root * /srv\n  encode gzip\n  @assets path /assets/*\n  header @assets Cache-Control "public, max-age=31536000, immutable"\n  try_files {path} /index.html\n  file_server\n}\n' > /etc/caddy/Caddyfile
EXPOSE 80
