# syntax=docker/dockerfile:1

FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
ARG VITE_MAPBOX_ACCESS_TOKEN
ARG VITE_DEFAULT_CENTER_LAT
ARG VITE_DEFAULT_CENTER_LNG
ARG VITE_DEFAULT_ZOOM
ENV VITE_MAPBOX_ACCESS_TOKEN=$VITE_MAPBOX_ACCESS_TOKEN
ENV VITE_DEFAULT_CENTER_LAT=$VITE_DEFAULT_CENTER_LAT
ENV VITE_DEFAULT_CENTER_LNG=$VITE_DEFAULT_CENTER_LNG
ENV VITE_DEFAULT_ZOOM=$VITE_DEFAULT_ZOOM

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
