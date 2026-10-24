FROM node:24.12.0-bookworm-slim AS dependencies
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

FROM dependencies AS quality
RUN npm run typecheck
CMD ["sh", "-ec", "npm run lint && npm test && npm run format:check"]

FROM dependencies AS build
RUN npm run build

FROM node:24.12.0-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN mkdir -p /app/.data/discovery && chown -R node:node /app
COPY --from=build --chown=node:node /app/.next-production/standalone ./
COPY --from=build --chown=node:node /app/.next-production/static ./.next-production/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
