# Build Stage
FROM node:18 as build
WORKDIR /app

# Preinstall specific typescript to avoid peer conflict
COPY package.json package-lock.json* ./
RUN npm install typescript@4.9.5 --save-dev
RUN npm install

# Copy all app code
COPY . .

# Build static site
RUN npm run build

# Production Stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

