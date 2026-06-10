# Complete Setup & Run Instructions

This guide walks you through starting the Neo4j database, running your FastAPI backend, and launching your React frontend.

---

## 1. Start the Neo4j Database (Docker)

Your project uses a Docker container for the Neo4j graph database.

1. Open your terminal and navigate to the `biomedical-graphrag` folder:
   ```bash
   cd "Desktop/drug interaction/biomedical-graphrag"
   ```
2. Start the database in the background using Docker Compose:
   ```bash
   docker compose up -d neo4j
   ```
3. **Verify it's running:**
   - Open your web browser and go to: [http://localhost:7474](http://localhost:7474)
   - **Username:** `neo4j`
   - **Password:** `neo4j123` (configured in your `.env` and `docker-compose.yml`)
   - You can run Cypher queries directly in this browser interface to explore your graph!

---

## 2. Run the FastAPI Backend

The backend serves the API and the static frontend files (in production).

1. Open a **new** terminal window and navigate to the outer `drug interaction` folder:
   ```bash
   cd "Desktop/drug interaction"
   ```
2. Activate your Python virtual environment if you have one (e.g., `source biomedical-graphrag/backend/.venv/bin/activate`).
3. Run the FastAPI server using Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```
4. **Verify the backend:**
   - Open [http://localhost:8000/health](http://localhost:8000/health) in your browser. It should show `{"status":"ok","neo4j":"up"}`.
   - You can also view the interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 3. Run the React Frontend (Development Mode)

While the backend serves the built production files, for development you should use the Vite dev server for hot-reloading.

1. Open a **new** terminal window and navigate to the `frontend` folder:
   ```bash
   cd "Desktop/drug interaction/biomedical-graphrag/frontend"
   ```
2. Install dependencies (if you haven't already):
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. **View the app:**
   - Open the URL provided in the terminal (usually [http://localhost:5173](http://localhost:5173)).
   - The Vite server automatically proxies API requests like `/query/interact` to your backend running on port 8000.

---

## Building for Production

When you're ready to deploy or just want the backend to serve the frontend:
1. In the `frontend` folder, run:
   ```bash
   npm run build
   ```
2. This generates the static HTML/JS/CSS files into the `backend/api/static` folder.
3. Now, if you go to [http://localhost:8000](http://localhost:8000), the FastAPI backend will serve your compiled React app directly!
