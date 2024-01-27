# FROM node:18
# WORKDIR /app

# COPY package.json package.json
# COPY package-lock.json package-lock.json

# RUN npm ci

# COPY . .
# RUN npx browserslist@latest --update-db
# RUN npm run build
# RUN npm install --global http-server

# CMD ["npx", "-y", "http-server", "-p", "8000", "/app/build"]


# FROM node:latest as build
# WORKDIR /app
# COPY package*.json ./
# RUN npm install -g npm@10.4.0
# COPY . ./
# RUN npm run build --prod
# CMD cp -r build result_build

FROM node:13.12.0-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD cp -r build result_build
