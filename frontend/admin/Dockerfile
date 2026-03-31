FROM node:20-alpine as builder
WORKDIR /app
COPY frontend/admin/package.json frontend/admin/package-lock.json* ./
RUN npm ci --silent
COPY frontend/admin/. ./
RUN npm run build

FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/admin/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
