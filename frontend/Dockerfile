FROM node:18
WORKDIR /app

RUN npm install -g npm@10.4.0

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm ci

COPY . .
RUN npm run build
RUN npm install --global http-server

CMD ["npx", "-y", "http-server", "-p", "8000", "/app/build"]


# FROM node:13.12.0-alpine as build
# WORKDIR /app
# COPY package*.json ./
# RUN npm install -g npm@10.4.0
# COPY . ./
# RUN npm run build
# CMD cp -r build result_build
