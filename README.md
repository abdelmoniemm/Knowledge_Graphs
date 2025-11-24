# Hierarchical Aggregation and Drilldown of Data Quality Scores

This project implements a pipeline to transform JSON data into RDF, load it into a Knowledge Graph, and query it using natural language.

**Major Changes:**
* **Triple Store:** Switched from GraphDB to **Apache Jena Fuseki** (running via Docker).
* **LLM:** Switched from OpenAI to **Google Gemini** (via Google GenAI SDK).

---

## Prerequisites

Before running the project, ensure you have:

1.  **Docker Desktop** (Required for the Triple Store and RMLMapper).
2.  **Python 3.10+** (For the Flask backend).
3.  **Node.js 18+ & npm** (For the React frontend).
4.  **A Google Gemini API Key** (Get one here: [Google AI Studio](https://aistudio.google.com/)).

---

## 1. Database Setup (Apache Jena Fuseki)

We use Docker to run the triple store.

1.  **Create a `docker-compose.yml` file** in the root directory:

    ```yaml
    version: '3.8'
    services:
      fuseki:
        image: stain/jena-fuseki:latest
        # Platform flag ensures compatibility with Apple Silicon (M1/M2/M3)
        platform: linux/amd64
        container_name: fuseki-server
        ports:
          - "3030:3030"
        environment:
          - ADMIN_PASSWORD=admin
        volumes:
          - ./fuseki-data:/fuseki
    ```

2.  **Start the Database:**
    ```bash
    docker-compose up -d
    ```

3.  **Create the Dataset (Crucial Step):**
    * Open your browser to [http://localhost:3030](http://localhost:3030).
    * Login with user: `admin`, password: `admin`.
    * Click **"manage datasets"** -> **"add new dataset"**.
    * **Dataset Name:** `bachelor2025`
    * **Dataset Type:** Select **Persistent (TDB2)**.
    * Click **"create dataset"**.

    > **Note:** If you encounter "Unauthorized" (401) errors during import, ensure your `fuseki-data/shiro.ini` is configured to allow anonymous access or that your backend is sending credentials. The recommended development setting in `shiro.ini` is `/** = anon`.

---

## 2. Environment Setup

Create a `.env` file in the `flask-server/` folder:

```ini
# Fuseki Configuration
GRAPHDB_BASE=http://localhost:3030
GRAPHDB_REPO=bachelor2025

# Google Gemini Configuration
# Ensure no spaces or quotes around the key
GEMINI_API_KEY=AIzaSy......
GEMINI_MODEL=gemini-2.5-flash
````

-----

## 3\. Install & Run Backend (Flask)

```bash
cd flask-server
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

**Install Dependencies:**

```bash
pip install flask flask-cors requests python-dotenv google-generativeai
```

**Run the Server:**

```bash
python server.py
```

*The backend will start at http://127.0.0.1:5000*

-----

## 4\. Install & Run Frontend (React)

```bash
cd client
npm install
npm start
```

*The UI will start at http://localhost:3000*

-----

## Usage Guide

1.  **Build RDF:**

      * Go to the Dashboard.
      * Upload your `.json` file.
      * Click **"Run pipeline"** (Generates `output.ttl`).
      * Click **"Import to GraphDB"** (Loads data into Fuseki).

2.  **Explore Data:**

      * Use the preset queries buttons to view standard reports.

3.  **GenAI Query Builder:**

      * Click **"Try GenAI Query Builder"**.
      * Ask questions in natural language, e.g., *"Which database has the lowest average score?"*
      * The system uses Gemini to generate a SPARQL query and runs it against Fuseki.

-----

## Troubleshooting

  * **Docker Platform Error:** If you see "image platform does not match host", ensure the `platform: linux/amd64` line is present in your `docker-compose.yml`.
  * **Fuseki 404/500 Errors:** Ensure you manually created the dataset `bachelor2025` in the Fuseki UI (Step 1.3).
  * **Gemini 401 "Credentials Missing":**
      * Check that `GEMINI_API_KEY` is set in `.env`.
      * Ensure the "Generative Language API" is enabled in your Google Cloud Console.
      * The code uses `transport="rest"` to bypass gRPC firewall issues.
