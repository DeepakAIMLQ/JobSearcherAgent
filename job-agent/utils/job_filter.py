"""
Job Filter -- strict India-only, 50%+ match
"""
import re, logging
from datetime import datetime, timezone
from typing import List, Dict, Any
logger = logging.getLogger(__name__)

AI_KEYWORDS    = {"ai","ml","machine learning","artificial intelligence","llm","nlp",
                  "deep learning","agentic","generative","genai","gen ai","data science",
                  "language model","transformer","neural","gpt","rag","langchain",
                  "langgraph","crewai","mlops","llmops","oracle","erp","sap",
                  "digital transformation","cloud","salesforce","enterprise"}

LEVEL_KEYWORDS = {"principal","staff","director","head","senior","lead","vp",
                  "vice president","chief","manager","architect",
                  "program manager","product manager","avp","svp","gm","cto","cio"}

INDIA_LOCS = {
    "india","noida","delhi","new delhi","ncr","gurgaon","gurugram","faridabad",
    "bangalore","bengaluru","hyderabad","mumbai","pune","chennai","kolkata",
    "ahmedabad","jaipur","chandigarh","kochi","coimbatore","indore","bhopal",
    "lucknow","nagpur","surat","vadodara","mysore","navi mumbai","thane",
    "greater noida","ghaziabad","mohali","trivandrum","vizag","visakhapatnam",
    "india remote","india eligible",
}

# Only drop these EXPLICIT non-India location strings
NON_INDIA_EXPLICIT = [
    "united states only","us only","usa only","uk only","europe only",
    "eu only","canada only","australia only","north america only",
    # Explicit non-India cities that commonly appear
    ", ny", ", ca", ", tx", ", wa", ", ma",  # US state codes
    "london, uk","berlin, germany","paris, france",
    "toronto, canada","sydney, australia","singapore",
    "dubai, uae", "amsterdam, netherlands",
    "latam","latin america","central america",
]


class JobFilter:

    def __init__(self, profile: Dict[str, Any]):
        self.profile    = profile
        self.tgt_titles = [t.lower() for t in profile.get("target_titles", [])]
        self.skills     = [s.lower() for s in profile.get("skills", [])]
        self.pref_cos   = [c.lower() for c in profile.get("preferred_companies", [])]
        self.excl_cos   = [c.lower() for c in profile.get("excluded_companies", [])]
        self.remote_ok  = profile.get("remote_ok", True)
        self.india_only = profile.get("india_only", True)
        self.min_score  = profile.get("min_relevance_score", 0.50)
        self.max_jobs   = profile.get("max_jobs_in_email", 10)
        self.weights    = profile.get("score_weights", {
            "title_match":0.40,"skills_match":0.30,"location_match":0.20,
            "company_preference":0.07,"recency":0.03,
        })

    def apply(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        stats = {"passed":0,"low_score":0,"non_india":0,"excluded_co":0}
        for job in jobs:
            if self._is_excluded_company(job):
                stats["excluded_co"] += 1
                continue
            if self.india_only and self._is_not_india(job):
                stats["non_india"] += 1
                continue
            score, breakdown = self._score(job)
            if score < self.min_score:
                stats["low_score"] += 1
                continue
            job["relevance_score"] = round(score, 3)
            job["score_breakdown"] = breakdown
            stats["passed"] += 1
            results.append(job)
        logger.info(
            "  Filter: %d passed | %d low score | %d non-India | %d excluded",
            stats["passed"], stats["low_score"], stats["non_india"], stats["excluded_co"]
        )
        return results

    def rank(self, jobs):
        return sorted(jobs, key=lambda j: j.get("relevance_score",0), reverse=True)[:self.max_jobs]

    def _is_not_india(self, job: Dict) -> bool:
        is_remote = job.get("is_remote", False)
        loc = (job.get("location") or "").lower().strip()

        # Remote = India eligible
        if is_remote and self.remote_ok: return False
        if "remote" in loc and self.remote_ok: return False

        # Confirmed India = keep
        if "india" in loc: return False
        for city in INDIA_LOCS:
            if city in loc: return False

        # Blank/worldwide = keep (benefit of doubt)
        if not loc or loc in ("worldwide","anywhere","global"): return False

        # Explicit non-India = drop
        for bad in NON_INDIA_EXPLICIT:
            if bad in loc: return True

        # Unknown = keep
        return False

    def _is_excluded_company(self, job: Dict) -> bool:
        return any(e in (job.get("company") or "").lower() for e in self.excl_cos)

    def _score(self, job: Dict) -> tuple:
        t = self._title_score(job.get("title","").lower())
        blob = (job.get("title","") + " " + job.get("description","") + " " +
                " ".join(job.get("skills",[]))).lower()
        s = self._skills_score(blob)
        loc = (job.get("location","") + (" remote" if job.get("is_remote") else "")).lower()
        l = self._location_score(loc)
        c = 1.0 if any(p in (job.get("company") or "").lower() for p in self.pref_cos) else 0.5
        r = self._recency_score(job.get("posted_at",""))
        w = self.weights
        total = (t*w.get("title_match",0.40) + s*w.get("skills_match",0.30) +
                 l*w.get("location_match",0.20) + c*w.get("company_preference",0.07) +
                 r*w.get("recency",0.03))
        return total, {"title":round(t,2),"skills":round(s,2),"location":round(l,2),
                       "company":round(c,2),"recency":round(r,2)}

    def _title_score(self, title: str) -> float:
        if not title: return 0.0
        best = 0.0
        for target in self.tgt_titles:
            tw = set(re.split(r"\W+", target)) - {""}
            jw = set(re.split(r"\W+", title)) - {""}
            if tw: best = max(best, len(tw & jw) / len(tw))
        if best >= 0.5: return min(1.0, best + 0.1)
        ai = any(k in title for k in AI_KEYWORDS)
        lv = any(k in title for k in LEVEL_KEYWORDS)
        return min((0.40 if ai else 0) + (0.35 if lv else 0), 0.75)

    def _skills_score(self, text: str) -> float:
        if not text or not self.skills: return 0.0
        matches = sum(1 for s in self.skills if s in text)
        return min(1.0, matches / max(1, len(self.skills) * 0.30))

    def _location_score(self, location: str) -> float:
        if not location: return 0.7
        if "remote" in location and self.remote_ok: return 1.0
        if "india" in location: return 1.0
        for city in INDIA_LOCS:
            if city in location: return 1.0
        if location.strip() in ("worldwide","anywhere","global",""): return 0.6
        return 0.3

    def _recency_score(self, posted_at: str) -> float:
        if not posted_at: return 0.5
        try:
            posted = datetime.fromisoformat(posted_at.replace("Z","+00:00"))
            if posted.tzinfo is None: posted = posted.replace(tzinfo=timezone.utc)
            h = (datetime.now(timezone.utc) - posted).total_seconds() / 3600
            if h<=24: return 1.0
            if h<=72: return 0.8
            if h<=168: return 0.6
            if h<=720: return 0.4
            return 0.2
        except: return 0.5
