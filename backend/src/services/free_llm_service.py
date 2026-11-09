"""
Free LLM API Integration Service for Insightia.
Provides zero-cost, high-speed LLM integration supporting:
1. Google Gemini API (gemini-2.0-flash / gemini-1.5-flash via GEMINI_API_KEY or GOOGLE_API_KEY)
2. Groq Cloud API (llama-3.3-70b-versatile / mixtral-8x7b-32768 via GROQ_API_KEY)
3. OpenRouter Free Tier (meta-llama/llama-3.3-70b-instruct:free via OPENROUTER_API_KEY)
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Insightia Copilot, an enterprise-grade AI analytics and business intelligence assistant.
You specialize in conversational data exploration, automated insight discovery, and grounded intelligence.

LANGUAGES SUPPORTED:
- English
- Hindi (Devanagari)
- Hinglish (Roman Hindi, e.g. "Missing values clean karo", "Sales ka trend kya hai?", "Outliers kaunse columns me hain?")
Always match the language, tone, and script used by the user. If the user asks in Hinglish, reply naturally in Hinglish.

STRICT GROUNDING RULE:
- You must NEVER invent, hallucinate, or guess summary numbers or statistics.
- Base all statements strictly on the provided dataset context, schema, and statistics.
- If data is missing or ambiguous, state it clearly.

RESPONSE FORMAT:
You MUST respond with valid, parseable JSON matching this schema:
{
  "reply": "Plain humanized answer explaining the finding in the requested language (Hinglish/English/Hindi)",
  "action_taken": "clean | filter | calculate | none",
  "chart_config": {
    "type": "bar | line | scatter | pie",
    "title": "Title of the chart",
    "x_axis": "Column or dimension name",
    "y_axis": "Metric name",
    "data": [
      {"name": "...", "value": 123}
    ]
  }
}
Note: If no chart is applicable, set "chart_config": null.
"""


class FreeLLMService:
    """Async client connector for free-tier LLM providers."""

    @classmethod
    def get_api_credentials(cls) -> Dict[str, Optional[str]]:
        """Retrieve available API keys from environment."""
        return {
            "gemini": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
        }

    @classmethod
    def build_dataset_context(cls, df: pd.DataFrame, dataset_name: str = "Dataset") -> str:
        """Create a compact, grounded summary of the active DataFrame for LLM prompting."""
        total_rows, total_cols = df.shape
        col_summaries: List[str] = []
        numeric_summaries: List[str] = []

        for col in df.columns:
            s = df[col]
            nulls = int(s.isna().sum())
            if pd.api.types.is_numeric_dtype(s):
                clean_s = s.dropna()
                mean_v = round(float(clean_s.mean()), 2) if len(clean_s) > 0 else 0
                med_v = round(float(clean_s.median()), 2) if len(clean_s) > 0 else 0
                min_v = round(float(clean_s.min()), 2) if len(clean_s) > 0 else 0
                max_v = round(float(clean_s.max()), 2) if len(clean_s) > 0 else 0
                col_summaries.append(f"- {col} (numeric): {nulls} nulls, range [{min_v} to {max_v}]")
                numeric_summaries.append(f"  {col}: mean={mean_v}, median={med_v}, min={min_v}, max={max_v}")
            elif pd.api.types.is_datetime64_any_dtype(s):
                col_summaries.append(f"- {col} (datetime): {nulls} nulls")
            else:
                top_vals = s.value_counts(dropna=True).head(3).to_dict()
                col_summaries.append(f"- {col} (categorical): {nulls} nulls, sample values: {top_vals}")

        # Top 3 correlations if numeric columns available
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        corr_summary = "None calculated."
        if len(num_cols) >= 2:
            try:
                corr = df[num_cols].corr().unstack().sort_values(ascending=False)
                pairs = []
                for (c1, c2), v in corr.items():
                    if c1 < c2 and not np.isnan(v):
                        pairs.append(f"{c1} vs {c2}: r={v:.2f}")
                        if len(pairs) >= 3:
                            break
                if pairs:
                    corr_summary = ", ".join(pairs)
            except Exception:
                pass

        context = f"""
DATASET CONTEXT:
Dataset Name: {dataset_name}
Total Records: {total_rows:,} rows, {total_cols} columns
Missing Cells: {int(df.isna().sum().sum()):,}
Duplicate Rows: {int(df.duplicated().sum()):,}

COLUMNS & TYPES:
{chr(10).join(col_summaries[:15])}

NUMERIC SUMMARY STATISTICS:
{chr(10).join(numeric_summaries[:8])}

TOP CORRELATIONS:
{corr_summary}
"""
        return context.strip()

    @classmethod
    async def call_gemini(cls, api_key: str, user_query: str, context: str) -> Optional[Dict[str, Any]]:
        """Call Google Gemini Free API using gemini-2.0-flash / gemini-1.5-flash."""
        models = ["gemini-2.0-flash", "gemini-1.5-flash"]
        user_prompt = f"{context}\n\nUSER QUERY:\n\"{user_query}\"\n\nRespond strictly in valid JSON format matching the schema."

        async with httpx.AsyncClient(timeout=20.0) as client:
            for model in models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    payload = {
                        "system_instruction": {
                            "parts": [{"text": SYSTEM_PROMPT}]
                        },
                        "contents": [
                            {"parts": [{"text": user_prompt}]}
                        ],
                        "generationConfig": {
                            "response_mime_type": "application/json",
                            "temperature": 0.2
                        }
                    }
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return cls.clean_and_parse_json(text)
                    else:
                        logger.warning(f"Gemini {model} returned {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    logger.warning(f"Gemini {model} request failed: {e}")
        return None

    @classmethod
    async def call_groq(cls, api_key: str, user_query: str, context: str) -> Optional[Dict[str, Any]]:
        """Call Groq Cloud free high-speed API (llama-3.3-70b-versatile)."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        user_prompt = f"{context}\n\nUSER QUERY:\n\"{user_query}\"\n\nRespond strictly in valid JSON format matching the schema."
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    return cls.clean_and_parse_json(text)
                else:
                    logger.warning(f"Groq API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Groq request failed: {e}")
        return None

    @classmethod
    async def call_openrouter(cls, api_key: str, user_query: str, context: str) -> Optional[Dict[str, Any]]:
        """Call OpenRouter Free Tier."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        user_prompt = f"{context}\n\nUSER QUERY:\n\"{user_query}\"\n\nRespond strictly in valid JSON format matching the schema."
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    return cls.clean_and_parse_json(text)
        except Exception as e:
            logger.warning(f"OpenRouter request failed: {e}")
        return None

    @classmethod
    def clean_and_parse_json(cls, text: str) -> Optional[Dict[str, Any]]:
        """Clean markdown wrapping or JSON code blocks and parse."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                # Ensure minimum keys exist
                if "reply" not in data:
                    data["reply"] = data.get("explanation", data.get("answer", str(data)))
                if "action_taken" not in data:
                    data["action_taken"] = "calculate" if data.get("chart_config") else "none"
                return data
        except Exception as e:
            logger.warning(f"Could not parse LLM JSON: {e} | Text: {text[:100]}")
        return None

    @classmethod
    async def query_free_llm(
        cls,
        user_query: str,
        df: pd.DataFrame,
        dataset_name: str = "Dataset"
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to query available free LLM APIs in priority order:
        1. Gemini
        2. Groq
        3. OpenRouter
        Returns parsed structured JSON or None if unavailable.
        """
        creds = cls.get_api_credentials()
        context = cls.build_dataset_context(df, dataset_name=dataset_name)

        # 1. Google Gemini
        if creds["gemini"] and creds["gemini"].strip():
            logger.info("Calling Google Gemini Free API...")
            res = await cls.call_gemini(creds["gemini"].strip(), user_query, context)
            if res:
                return res

        # 2. Groq Cloud
        if creds["groq"] and creds["groq"].strip():
            logger.info("Calling Groq Cloud Free API...")
            res = await cls.call_groq(creds["groq"].strip(), user_query, context)
            if res:
                return res

        # 3. OpenRouter
        if creds["openrouter"] and creds["openrouter"].strip():
            logger.info("Calling OpenRouter Free API...")
            res = await cls.call_openrouter(creds["openrouter"].strip(), user_query, context)
            if res:
                return res

        return None
