"""
PROFILE CONFIGURATION -- Rahul Malik
AVP Global Technology | Digital Transformation Leader
India only * 50%+ match * Top 10 daily
"""

PROFILE = {
    # Personal
    "name":     "Rahul Malik",
    #"email_to": "rahul.malik@yahoo.com",
    "email_to": "deepaksingh.mcpd@gmail.com",

    # Target Roles -- Oracle/ERP/Digital Transformation senior leadership
    "target_titles": [
        "AVP Digital Transformation",
        "VP Digital Transformation",
        "VP Technology",
        "VP Enterprise Applications",
        "Director Digital Transformation",
        "Director Enterprise Technology",
        "Head of Digital Transformation",
        "Head of Enterprise Applications",
        "Head of ERP",
        "Director ERP Cloud",
        "Oracle Cloud Practice Head",
        "ERP Transformation Lead",
        "Head of GenAI",
        "Director AI Transformation",
        "Director IT Programs",
        "Senior Director Technology",
        "Global Technology Director",
        "COE Head Technology",
        "CTO",
        "CIO",
        "Chief Digital Officer",
        "VP IT",
        "GM Technology",
    ],

    # Skills -- Oracle/Salesforce/Cloud/AI stack from resume
    "skills": [
        # Oracle stack (core expertise)
        "Oracle Fusion Cloud", "Oracle EBS", "Oracle ERP",
        "Oracle EPM", "Oracle Cloud", "OCI", "Oracle Fusion",
        "Oracle Analytics Cloud", "Oracle EBS R12", "APEX",
        # Salesforce
        "Salesforce", "Salesforce Revenue Cloud",
        # AI and GenAI
        "Generative AI", "LLM", "OCI Generative AI", "Cohere",
        "Azure OpenAI", "AI modernization", "GenAI",
        "document AI", "RAG", "AI automation",
        # Integration and Architecture
        "OIC", "API-led architecture", "enterprise integration",
        "multi-cloud", "cloud migration", "ERP modernization",
        "SaaS", "PaaS", "WebLogic",
        # Leadership and Governance
        "COE Setup", "digital transformation",
        "program governance", "vendor management",
        "P&L management", "product strategy",
        "change management", "stakeholder management",
        "Agile", "Scrum",
        # Domain
        "Supply Chain", "Finance", "Procurement", "HR",
        "P2P", "O2C", "H2R", "ERP",
    ],

    # Experience
    "min_experience_years": 15,
    "max_experience_years": 30,

    # Location -- INDIA ONLY
    "locations": [
        "India", "Faridabad", "Haryana",
        "Noida", "Delhi", "New Delhi", "NCR",
        "Gurgaon", "Gurugram",
        "Bangalore", "Bengaluru",
        "Hyderabad", "Mumbai", "Pune",
        "Chennai", "Kolkata", "Ahmedabad",
        "Remote",
    ],
    "remote_ok":  True,
    "india_only": True,

    # Search Queries -- Oracle + GenAI + Transformation focus
    "search_queries": [
        "Digital Transformation Director India",
        "VP Technology Oracle Cloud India",
        "Head Enterprise Applications India",
        "ERP Transformation Lead India",
        "Director IT Programs India",
        "Oracle Fusion Director India",
        "GenAI Enterprise Lead India",
        "COE Head Technology India",
    ],

    # Preferred Companies
    "preferred_companies": [
        "EXL Service", "WNS", "Genpact", "Mphasis",
        "Oracle", "SAP", "Infosys", "HCL Technologies",
        "TCS", "Wipro", "Cognizant", "Capgemini",
        "Deloitte", "Accenture", "IBM", "PwC", "KPMG", "EY",
        "Salesforce", "Microsoft", "Google", "Amazon",
        "Tata Motors", "Mahindra", "Bajaj", "Maruti Suzuki",
        "Airtel", "Jio", "HDFC", "ICICI", "Axis Bank",
    ],
    "excluded_companies": [],

    # Scoring
    "score_weights": {
        "title_match":        0.40,
        "skills_match":       0.30,
        "location_match":     0.20,
        "company_preference": 0.07,
        "recency":            0.03,
    },

    # Thresholds
    "min_relevance_score": 0.50,
    "max_jobs_in_email":   10,
}
