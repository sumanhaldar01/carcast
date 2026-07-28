FROM node:24-alpine
WORKDIR /app
RUN npm install -g npm@12.0.1
COPY package*.json ./
RUN npm install --omit=dev
COPY src ./src
USER node
EXPOSE 4000
CMD ["npm","start"]
