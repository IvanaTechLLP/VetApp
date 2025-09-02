# frontend/Dockerfile
FROM node:20-alpine as builder
WORKDIR /app

# 1️⃣ Copy only package.json & package-lock.json first
COPY package*.json ./

# 2️⃣ Install dependencies
RUN npm install --legacy-peer-deps

# 3️⃣ Copy the rest of the app
COPY . .

# 4️⃣ Build
RUN npm run build

# 5️⃣ Serve via nginx
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
