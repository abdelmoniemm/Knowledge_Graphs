## Running the Application

This guide explains how to set up and run the application on Windows



## Prerequisites
Before running the project, make sure you have installed:

**GraphDB** (download from Ontotext
, run locally at http://localhost:7200)
 Create a repository, e.g. bachelor2025

**Docker Desktop** (needed for YARRRML and RMLMapper containers)
Ensure Docker Desktop is running before executing the mapping pipeline.

**Python 3.10+** (for Flask backend)

**Node.js 18+ & npm** (for React frontend)

**An OpenAI API key** (for NL → SPARQL feature)

## Clone the Repository
```bash
git clone https://github.com/abdelmoniemm/Knowledge_Graphs.git
cd YOUR_REPO
```

## Environment Setup

Create a .env file in the flask-server/ folder:
```bash
# GraphDB configuration
GRAPHDB_BASE=http://localhost:7200
GRAPHDB_REPO=

# OpenAI configuration
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini
```

## Install the backend (flask)
```bash
cd flask-server
python -m venv venv
source venv/bin/activate      # on Linux/Mac
venv\Scripts\activate         # on Windows PowerShell
```

**make sure you installed all libraries and dependencies required to run the back end""

needed for schwarz enviroment
```bash
-m pip install flask python-dotenv flask-cors requests --proxy http://se1-mwg-p03.schwarz:8054
-m pip install requests --proxy http://se1-mwg-p03.schwarz:8054   
-m pip install Flask --proxy http://se1-mwg-p03.schwarz:8054
-m pip3 install Flask --proxy http://se1-mwg-p03.schwarz:8054
-m pip install openai --proxy http://se1-mwg-p03.schwarz:8054
```
           
>> 
## run the backend

python server.py
It should start at http://127.0.0.1:5000

## Install Frontend (React)

```bash
cd ../client
npm install
npm start
```

**for schwarz enviroment**
schwarzit.jfrog.io/ui/packages


This starts the React UI at http://localhost:3000



