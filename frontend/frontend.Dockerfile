FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
ENV PUPPETEER_SKIP_DOWNLOAD=true
RUN npm install --legacy-peer-deps
COPY . .
# Empty — browser calls same-origin via Next.js rewrites proxy
ENV NEXT_PUBLIC_API_URL=
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
ENV PORT=80
ENV NODE_ENV=production
EXPOSE 80
CMD ["npm", "start"]
