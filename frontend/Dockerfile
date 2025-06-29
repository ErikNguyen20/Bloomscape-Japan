# Use Node
FROM node:22

# Set workdir
WORKDIR /app

# Copy package.json + lockfile
COPY package*.json ./

# Install deps
RUN npm install

# Copy rest of the app
COPY . .

# Expose Vite dev port
EXPOSE 5173

# Start dev server (or `npm run build` + serve for prod)
CMD ["npm", "run", "dev"]
