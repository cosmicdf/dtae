FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm ci --only=production

COPY tsconfig.json ./
COPY src ./src
RUN npm run build

EXPOSE 3100

CMD ["node", "dist/index.js"]
