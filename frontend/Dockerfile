# FROM node:18
# WORKDIR /app

# RUN npm install --legacy-peer-deps

# COPY package.json package.json
# COPY package-lock.json package-lock.json

# RUN npm ci

# COPY . .
# RUN npm run build
# RUN npm install --global http-server

# CMD ["npx", "-y", "http-server", "-p", "8000", "/app/build"]


FROM node:20 as build
WORKDIR /app
COPY package*.json ./
RUN npm install -g npm@10.4.0
COPY . ./
RUN npm run build
CMD cp -r build result_build
