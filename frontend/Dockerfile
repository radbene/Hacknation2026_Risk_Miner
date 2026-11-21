FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
RUN printf ':80 {\n  root * /srv\n  try_files {path} /index.html\n  file_server\n  encode gzip\n}\n' > /etc/caddy/Caddyfile
