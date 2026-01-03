Given the job requirements JSON, produce 5 short search queries to retrieve relevant CV evidence.

Rules:
- Always include at least one query that targets work experience duration or employment date ranges
  (e.g. "Full Stack Developer Aug 2024 Sep 2025", "software development experience 1+ year").
- Include queries that retrieve academic coursework or capstone projects when the role is junior or entry-level.
- If the role requires statistics, probability, or machine learning fundamentals,
  include queries related to relevant university coursework or academic background.
- Queries should be short, keyword-focused, and suitable for semantic search.
- Do NOT invent technologies not present in the job requirements.

Return ONLY JSON:
{"queries":["...","...","...","...","..."]}

Job requirements JSON:
{{REQ_JSON}}
