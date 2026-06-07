# Integrate It AI 🚀

**Integrate It AI** is an advanced, multi-agent AI pipeline designed to autonomously generate enterprise-grade Python integration connectors between any two SaaS platforms (e.g., Salesforce to Shopify, Stripe to Slack).

Instead of relying on single-shot LLM prompts, this project orchestrates a **4-stage Agentic Pipeline** that performs real-world web searches, mathematically maps fields, and generates robust, resilient code using modern Python standards.

---

## 🧠 The Agentic Pipeline

The system is powered by a FastAPI backend that streams Server-Sent Events (SSE) to a gorgeous React glassmorphism frontend. It executes the following stages sequentially:

### 1. Discovery Agent (Real-World Grounded)
Instead of relying on hallucinated or outdated LLM memory, this agent spins up a background thread and uses `duckduckgo-search` to query the live internet for the official API documentation of the source and target platforms. It extracts the raw developer docs and feeds them into the context window as `<GROUND_TRUTH_CONTEXT>`. This guarantees the generated endpoints are real and accurate.

### 2. Mapping Agent
This agent analyzes the API payloads and generates a precise field-to-field mapping between the two systems. It determines transformations (e.g., `direct`, `format`, `compute`) and calculates mathematical confidence scores for each mapped field.

### 3. Code Generation Agent
The workhorse of the pipeline. It reads the discovered endpoints and the mapping logic to write **production-grade Python code**. It strictly adheres to enterprise standards:
* **`httpx.AsyncClient`** for high-performance async HTTP requests.
* **`pydantic`** for strict data validation of incoming payloads.
* **`tenacity`** for exponential backoff and rate-limit handling.
* Built-in idempotent upserts to prevent data duplication.
* Secure credential extraction via environment variables.

### 4. Walkthrough Agent (Developer Experience)
Finally, a DX (Developer Experience) agent analyzes the generated code and produces a highly structured walkthrough. It visualizes the authentication strategy, lists the exact environment variables (prerequisites) required, provides a step-by-step logic breakdown with code snippets, and outputs the final CLI execution command to run the connector locally.

---

## 💻 Tech Stack

### Frontend
- **React 18** with **Vite**
- **TypeScript**
- **Vanilla CSS** with a custom high-contrast, premium glassmorphism aesthetic.
- **Lucide React** for iconography.

### Backend
- **Python 3.10+**
- **FastAPI** (for REST routes and SSE streaming)
- **Groq API** (Llama 3.1 70B Versatile for blazing fast agent execution)
- **DuckDuckGo-Search** (for real-world API doc grounding)
- **Pydantic** (for strict data structuring)

---

## 🛠️ Setup & Installation

### Prerequisites
You will need Node.js, Python, and a **Groq API Key**.

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic python-dotenv groq duckduckgo-search
   ```
4. Set up your environment variables. Create a `.env` file in the `backend` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

---

## 🎮 Usage
1. Open your browser to `http://localhost:5173`.
2. You will be greeted by the stunning glassmorphism interface.
3. In the input boxes, type your **Source** (e.g., `Stripe`) and **Target** (e.g., `Slack`).
4. Click "Generate Integration".
5. Watch as the agents execute in real-time, streaming their deep thoughts, live web-searches, mappings, and code generation directly to the UI!

---

*Built with ❤️ utilizing Advanced Agentic Coding practices.*
