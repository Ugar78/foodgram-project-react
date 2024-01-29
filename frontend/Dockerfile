# build env
# FROM node:13.12.0-alpine as build
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
# RUN npm install -g npm@10.4.0
# RUN npm ci --force
COPY . .
RUN npm run build
RUN npm install --global http-server

CMD ["npx", "-y", "http-server", "-p", "9000", "/app/build"]


# CMD cp -r build result_build