FROM node:20-alpine

WORKDIR /app/cheerleader-ui

COPY package.json package-lock.json ./
RUN npm install

COPY . ./
RUN npm run build
