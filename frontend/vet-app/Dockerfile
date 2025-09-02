# frontend/vet-app/Dockerfile
FROM node:20-alpine as builder
WORKDIR /app

# copy package files
COPY package*.json ./

# install dependencies
RUN npm install --legacy-peer-deps

# copy rest of the app
COPY . .

# build React app
RUN npm run build

# serve via nginx
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
