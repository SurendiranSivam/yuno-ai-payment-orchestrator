FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

# --hostname 0.0.0.0 required for Docker container accessibility
CMD ["npm", "run", "dev"]
