"""
PROFILE CONFIGURATION — Deepak Singh
India-only · 50%+ match · Top 10 daily
"""

PROFILE = {
    # ── Personal ──────────────────────────────────────────────────
    "name":     "Deepak Singh",
    "email_to": "Deepaksingh.mcpd@gmail.com",

    # ── Target Roles ──────────────────────────────────────────────
    "target_titles": [
        "Principal AI Program Manager",
        "Director AI Program Management",
        "Head of GenAI",
        "Head of Agentic AI",
        "Director Generative AI",
        "VP AI Programs",
        "AI Platform Director",
        "GenAI Delivery Lead",
        "Principal GenAI Architect",
        "Director AI Transformation",
        "AI COE Lead",
        "Enterprise AI Leader",
        "Senior Director AI",
        "Staff AI Program Manager",
        "AI Program Manager",
        "Machine Learning Director",
        "LLM Program Manager",
    ],

    # ── Skills ────────────────────────────────────────────────────
    "skills": [
        "Generative AI", "Agentic AI", "LLM", "RAG",
        "Prompt Engineering", "LangChain", "LangGraph", "CrewAI",
        "Multi-agent", "AI governance", "LLMOps", "MLOps",
        "GPT-4", "Claude", "Llama", "Mistral",
        "PyTorch", "Hugging Face", "Pinecone", "FAISS", "Weaviate",
        "AWS", "Azure", "Azure OpenAI",
        "AI Program Management", "COE", "AI roadmap",
        "OKRs", "Agile", "Scrum", "PRINCE2",
        "Stakeholder Management", "Digital Transformation",
        "BFSI", "Healthcare", "Finance", "Python", "SQL",
    ],

    # ── Experience ────────────────────────────────────────────────
    "min_experience_years": 15,
    "max_experience_years": 30,

    # ── Location — INDIA ONLY ─────────────────────────────────────
    "locations": [
        "India", "Noida", "Delhi", "New Delhi", "NCR",
        "Gurgaon", "Gurugram", "Faridabad", "Noida",
        "Bangalore", "Bengaluru",
        "Hyderabad",
        "Mumbai", "Pune",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "Remote",           # India-based remote roles
    ],
    "remote_ok":      True,
    "india_only":     True,   # hard filter — drop all non-India jobs

    # ── Search Queries (sent to all job APIs) ─────────────────────
    "search_queries": [
        "AI Program Manager",
        "Generative AI Lead",
        "AI Director",
        "GenAI Manager",
        "LLM Program Manager",
        "Agentic AI Manager",
        "AI Transformation Lead",
        "Machine Learning Program Manager",
    ],

    # ── Company Preferences ───────────────────────────────────────
    "preferred_companies": [
        # Big Tech India
        "Google", "Amazon", "Microsoft", "Meta", "Apple",
        # AI-first
        "OpenAI", "Anthropic", "Cohere",
        # Tier-1 IT
        "Infosys", "TCS", "Wipro", "HCL", "Cognizant",
        "Accenture", "Deloitte", "IBM", "Capgemini",
        # BFSI
        "JP Morgan", "Goldman Sachs", "HSBC", "Mastercard",
        "PhonePe", "Razorpay", "Paytm", "HDFC", "ICICI",
        # Analytics
        "EXL Service", "WNS", "Mu Sigma", "Tiger Analytics",
        "Fractal", "LatentView",
    ],
    "excluded_companies": [],

    # ── Scoring ───────────────────────────────────────────────────
    "score_weights": {
        "title_match":        0.40,  # most important
        "skills_match":       0.30,
        "location_match":     0.20,  # high — India-only mode
        "company_preference": 0.07,
        "recency":            0.03,
    },

    # ── Thresholds ────────────────────────────────────────────────
    "min_relevance_score": 0.50,  # 50%+ match only
    "max_jobs_in_email":   10,    # top 10 per day
}
