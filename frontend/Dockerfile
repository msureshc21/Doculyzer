FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* /app/
RUN npm ci

COPY . /app

EXPOSE 5173

# Dev server (good for portfolio demo via docker-compose).
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

