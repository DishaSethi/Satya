# Satya: E-commerce AI Governance & Guardrail System

Satya is an enterprise-grade intelligent governance platform designed to monitor e-commerce catalogs and buyer interactions in real-time. By leveraging a multi-agent LangGraph Swarm, OpenAI's CLIP model, Groq's ultra-low latency inference, and Gemini's advanced multimodal vision, Satya ensures a safe, transparent, and counterfeit-free marketplace.

---

## 🌐 Live Environments
* **Frontend Dashboard:** [satya-demo-frontend.vercel.app](https://satya-demo-frontend.vercel.app/)
* **Backend Gateway Base:** `https://satya-backend-api-hqhsbwddb9g2fec2.centralindia-01.azurewebsites.net`

---

## 🏗️ Technical Architecture Diagram

```mermaid
graph TD
    %% Define Engineering Color Palette
    classDef ui fill:#f9fafb,stroke:#e5e7eb,stroke-width:2px,color:#1f2937
    classDef api fill:#e0f2fe,stroke:#7dd3fc,stroke-width:2px,color:#0369a1
    classDef broker fill:#ffedd5,stroke:#fdba74,stroke-width:2px,color:#c2410c
    classDef ai fill:#f3e8ff,stroke:#d8b4fe,stroke-width:2px,color:#6b21a8
    classDef db fill:#d1fae5,stroke:#6ee7b7,stroke-width:2px,color:#047857
    classDef alert fill:#fee2e2,stroke:#fca5a5,stroke-width:2px,color:#b91c1c
    classDef warning fill:#fef3c7,stroke:#fcd34d,stroke-width:2px,color:#b45309

    %% 1. CLIENT INTERFACES
    subgraph Tier1 [1. Client Interfaces]
        direction LR
        Seller["🛒 Seller Catalog Portal<br>Uploads products & images"]:::ui
        Customer["📦 Customer Review Module<br>Submits text & unboxing photos"]:::ui
    end

    %% 2. FASTAPI GATEWAY ENGINE
    subgraph Tier2 [2. FastAPI Gateway Engine]
        direction LR
        IngestAPI["Ingestion Router"]:::api
        ReviewAPI["Async Review Router"]:::api
    end

    %% 3. SECURITY GUARDRAILS & EVENT BROKERS
    subgraph Tier3 [3. Security Guardrails & Event Brokers]
        CosineCheck{"CLIP Cosine Similarity<br>> 0.96?"}:::broker
        IPLookup{"Brand IP Lookup<br>Protected Asset?"}:::broker
        Queue["Background Event Broker<br>Azure Service Bus"]:::broker
    end

    %% 4. LANGGRAPH AGENTIC SWARM
    subgraph Tier4 [4. LangGraph Agentic Swarm]
        direction TB
        State["Shared State Machine Object<br>{vision_score, sentiment, intent, seller_history}"]:::ai

        Vision["👁️ Vision Node<br>Gemini 1.5 Pro Vision<br>Calculates vector discrepancy"]:::ai
        Pulse["🧠 Pulse Node<br>Groq LPU<br>Analyzes sentiment & deception"]:::ai

        Exec["🤖 Executive Node<br>Llama / Groq Router<br>Queries DB for historical trends"]:::ai

        ActionRed["Action: Critical Mismatch<br>Apply UI Warning & Degrade Trust"]:::alert
        ActionYellow["Action: Anomalous Spike<br>Route to Admin Panel"]:::warning
        ActionGreen["Action: Verified Pass<br>Increment Trust Score +1"]:::db
    end

    %% 5. DATA STORAGE LAYER
    subgraph Tier5 [5. Data Storage Layer]
        DB[("Azure Database for PostgreSQL<br>pgvector Enabled + HNSW Indexing")]:::db
    end

    %% Edge Connections & Routing
    Seller --> IngestAPI
    Customer --> ReviewAPI

    %% Phase 1: Ingestion Flow
    IngestAPI -->|Extract CLIP Vector| CosineCheck
    CosineCheck -->|True| IPLookup
    CosineCheck -->|False| DB
    IPLookup -->|Block/Flag Transactions| DB

    %% Phase 2: Async Review Flow
    ReviewAPI --> Queue
    Queue --> State

    %% Phase 3: Swarm Execution
    State --> Vision
    State --> Pulse
    Vision --> Exec
    Pulse --> Exec
    Exec -.->|Fetch Aggregate History| DB

    Exec -->|Critical Mismatch Path| ActionRed
    Exec -->|Anomalous Spike Path| ActionYellow
    Exec -->|Verified Pass Path| ActionGreen

    ActionRed --> DB
    ActionYellow --> DB
    ActionGreen --> DB
```


## 🧠 Architecture Deep Dive
Satya operates on a dual-pipeline architecture designed to handle high-throughput catalog ingestion and asynchronous, AI-heavy customer review analysis.

### Phase 1: Real-Time Ingestion & IP Protection
When a seller uploads a new product via the **Seller Catalog Portal**, the image is instantly processed by an **OpenAI CLIP Vector Model**.
* The system generates a highly dimensional embedding and executes a `pgvector` **Cosine Similarity Check** against the existing catalog.
* If a visual match exceeds the `>0.96` threshold, the **Brand IP Lookup** guardrail is triggered to verify if the original asset is visually protected. Unauthorized duplicates (IP Theft) are blocked or flagged in real-time before reaching the marketplace.

### Phase 2: The Agentic Swarm Pipeline
When a customer submits a review via the **Customer Review Module**, the payload is pushed to an **Azure Service Bus Queue** to prevent UI blocking. This awakens the LangGraph Swarm, which hydrates a **Shared State Machine** and executes parallel tasks:
* **👁️ Vision Node (Powered by Gemini):** Analyzes the customer's unboxing photo against the seller's original catalog image, detecting visual discrepancies, bait-and-switch tactics, or damaged goods.
* **🧠 Pulse Node (Powered by Groq):** Provides ultra-low latency NLP inference. It tokenizes the review text to extract sentiment, frustration levels, and deception matrices.
* **🤖 Executive Node:** Acting as the final decision router, it ingests the Multimodal data (Vision + Pulse) and actively queries the PostgreSQL database for the seller's historical aggregate metrics.

Based on the Executive Node's ruling, the system executes one of three final paths: **Critical Mismatch** (auto-applies a warning patch to the product UI and docks trust scores), **Anomalous Spike** (routes to Human Admin), or **Verified Pass** (rewards the seller).

-

## 🛠️ Technology Stack

### ☁️ Cloud Infrastructure (Microsoft Azure Native)
* **Azure App Service:** Fully managed hosting for the FastAPI web service backend.
* **Azure Database for PostgreSQL:** Relational data integrity powered by the `pgvector` extension for HNSW indexed vector similarity search.
* **Azure Service Bus:** High-throughput enterprise message broker handling the asynchronous AI event queue.
* **Azure Blob Storage:** Secure, scalable object storage for ingesting and serving product catalog images and customer unboxing assets.

### 🧠 AI & Intelligence Layer
* **LangChain & LangGraph:** Multi-agent state machine orchestration.
* **OpenAI CLIP:** Real-time visual embedding extraction for IP theft detection.
* **Google Gemini API:** Heavy multimodal vision analysis for unboxing reviews.
* **Groq API:** Blistering fast LLM inference powering the NLP Pulse Agent and Executive Router.

### 💻 Core Application Frameworks
* **Backend:** Python, FastAPI, `asyncpg`.
* **Frontend:** React, Vite, Tailwind CSS, Axios (Deployed on Vercel).

---

## 🚀 Setup & Execution

### Prerequisites
* Python 3.10+
* Node.js (v18+)
* PostgreSQL Database (with `pgvector` extension enabled)
### 1. Backend Setup

Clone the repository and navigate to the backend directory:
```bash
git clone https://github.com/DishaSethi/Satya.git
cd Satya/backend

Create and activate a virtual environment:

Bash
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
Install the required Python dependencies:

Bash
pip install -r requirements.txt
Set up your environment variables. Create a .env file in the backend folder:

Code snippet
DATABASE_URL="postgresql://user:password@azure-host:5432/dbname"
GEMINI_API_KEY="your_gemini_key"
GROQ_API_KEY="your_groq_key"
Start the FastAPI server:

Bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
2. Frontend Setup
Open a new terminal window and navigate to the frontend directory:

Bash
cd Satya/frontend
Install npm packages:

Bash
npm install
Start the Vite development server:

Bash
npm run dev
