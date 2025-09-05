# 💬 AI Chatbot Integration for Wix + Azure

## Overview
Build an AI-powered chat assistant for your Wix site that:
- Answers product-specific questions using data in Bioboer's Azure-hosted database.
- Provides practical, context-aware farming suggestions.
- Stays within strict product-knowledge boundaries (no general advice).
- Logs & categorizes user questions for later review.

---

## 🧱 Architecture Components

### 1. Wix Frontend
- Use a **Custom Element** or **iFrame** to embed a React/HTML chat UI.
- The chat frontend should POST user queries to an external API and render AI responses.

### 2. External API Backend
- Host on **Azure Function App**, **Node.js (Express)**, or **.NET Web API**.
- Responsibilities:
  - Fetch relevant data from Azure SQL.
  - Construct prompt for LLM (include guardrails + product context).
  - Call **OpenAI / Azure OpenAI API**.
  - Return response to frontend.
  - Log message, response, and categorized intent to a logging DB table.

### 3. Azure SQL Database
- Tables:
  - `Products`: Your existing product data.
  - `ChatLogs`: To store queries, responses, timestamps, and category labels.

### 4. Language Model (LLM)
- Use **Azure OpenAI** (preferred) or **OpenAI API**.
- Inject product info + user scenario into prompt.
- Add strict scope prompt, e.g.:

```txt
You are a Bioboer assistant. You ONLY respond to questions about Bioboer products and their farming applications. Do NOT provide general farming, medical, legal, or unrelated advice.
