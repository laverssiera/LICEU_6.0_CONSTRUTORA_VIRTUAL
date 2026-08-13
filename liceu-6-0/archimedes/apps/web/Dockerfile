FROM node:20-alpine

WORKDIR /app/cv-frontend

COPY cv-frontend/package.json /app/cv-frontend/package.json
COPY cv-frontend/package-lock.json /app/cv-frontend/package-lock.json
RUN npm install

COPY cv-frontend /app/cv-frontend

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
