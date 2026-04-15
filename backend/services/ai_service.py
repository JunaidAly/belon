"""Hugging Face AI service — Falcon-7B default, OLMo / GPT-NeoX / BLOOM fallback."""
from __future__ import annotations
import time
import logging
from typing import Optional
from huggingface_hub import InferenceClient
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)

# Prompt templates per action type
PROMPTS: dict[str, str] = {
    "email_draft": """You are an expert B2B sales AI. Write a concise, personalized re-engagement email.

Context:
- Company: {company_name}
- Deal value: ${deal_value}
- Days stalled: {days_stalled}
- Last action: {last_action}
- Contact name: {contact_name}

Write a short (3 paragraphs max), genuine, non-pushy re-engagement email.
Subject line on first line. Then email body. No placeholders like [NAME].

Output:""",

    "lead_score": """You are a B2B lead scoring expert. Score this lead 0-100 and explain why.

Lead data:
- Company: {company_name}
- Title: {title}
- Email: {email}
- Company size: {company_size}
- Industry: {industry}
- Engagement: {engagement_actions}
- Source: {source}

Respond with:
SCORE: [0-100]
TIER: [A/B/C/D]
REASONING: [2-3 sentences]
NEXT_ACTION: [specific recommended action]

Output:""",

    "deal_analysis": """You are a senior sales strategist. Analyze this deal and identify risks and opportunities.

Deal:
- Company: {company_name}
- Value: ${deal_value}
- Stage: {stage}
- Days in stage: {days_in_stage}
- Health score: {health_score}/100
- Last activity: {last_activity}
- Stakeholders engaged: {stakeholders}

Provide:
RISK_LEVEL: [Critical/High/Medium/Low]
KEY_RISKS: [bullet list of top 3 risks]
OPPORTUNITIES: [bullet list of top 2 opportunities]
RECOMMENDED_ACTIONS: [numbered list of immediate next steps]

Output:""",

    "sequence_generate": """You are an expert sales outreach strategist. Create a 3-email follow-up sequence.

Context:
- Prospect: {company_name}
- Deal stage: {stage}
- Value: ${deal_value}
- Last touchpoint: {last_touchpoint}

Generate 3 emails:
EMAIL 1 (Day 1):
Subject: [subject]
Body: [body]

EMAIL 2 (Day 4):
Subject: [subject]
Body: [body]

EMAIL 3 (Day 9):
Subject: [subject]
Body: [body]

Output:""",

    "churn_prediction": """You are a customer success AI. Assess churn risk for this account.

Account:
- Company: {company_name}
- ARR: ${arr}
- Days since champion contact: {days_since_contact}
- Contract renewal: {days_to_renewal} days
- Health score: {health_score}/100
- Recent signals: {signals}

Provide:
CHURN_RISK: [Critical/High/Medium/Low]
PROBABILITY: [0-100%]
PRIMARY_REASON: [main churn driver]
SAVE_ACTIONS: [numbered list of 3 actions to prevent churn]

Output:""",

    "pipeline_forecast": """You are a revenue forecasting AI. Predict close probability and timing.

Pipeline summary:
- Total deals: {total_deals}
- Total value: ${total_value}
- Average health score: {avg_health}
- Deals by stage: {stage_breakdown}
- Historical close rate: {close_rate}%

Provide:
FORECAST_AMOUNT: [$amount expected to close this quarter]
CONFIDENCE: [High/Medium/Low]
KEY_DEALS: [top 3 most likely to close]
RISKS: [top 3 risks to forecast]

Output:""",

    "re_engagement": """You are a sales AI. Create a personalized re-engagement message.

Contact:
- Name: {contact_name}
- Company: {company_name}
- Last interaction: {last_interaction}
- Interest area: {interest_area}

Write a brief (2 paragraph), warm re-engagement message that references their specific situation.
No generic templates. Be specific and human.

Output:""",

    "enrichment": """You are a B2B research AI. Enrich this company profile.

Known data:
- Company name: {company_name}
- Website: {website}
- Industry: {industry}

Based on company name and industry, provide likely:
COMPANY_SIZE: [1-10 / 11-50 / 51-200 / 201-1000 / 1000+]
TECH_STACK: [likely technologies used]
PAIN_POINTS: [top 3 pain points for this type of company]
BUYER_PERSONA: [typical buyer title and role]
TALKING_POINTS: [3 value proposition angles]

Output:"""
}


class AIService:
    def __init__(self):
        self.client = InferenceClient(token=settings.HUGGINGFACE_API_TOKEN)
        self.default_model = settings.HF_DEFAULT_MODEL
        self.fallback_model = settings.HF_FALLBACK_MODEL

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_model(self, prompt: str, model: str, max_tokens: int = 512) -> str:
        """Call HuggingFace inference API."""
        try:
            response = self.client.text_generation(
                prompt,
                model=model,
                max_new_tokens=max_tokens,
                temperature=0.7,
                repetition_penalty=1.1,
                return_full_text=False,
                stop_sequences=["Human:", "User:", "---"],
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Model {model} failed: {e}")
            raise

    async def run_action(
        self,
        action_type: str,
        context: dict,
        model: Optional[str] = None,
    ) -> dict:
        """Execute an AI action and return structured result."""
        start_ms = int(time.time() * 1000)

        template = PROMPTS.get(action_type)
        if not template:
            raise ValueError(f"Unknown action type: {action_type}")

        # Fill template with context, use placeholder for missing keys
        try:
            prompt = template.format_map({k: context.get(k, "N/A") for k in self._extract_keys(template)})
        except KeyError as e:
            prompt = template  # fallback: use raw template
            logger.warning(f"Missing prompt key {e} for {action_type}")

        use_model = model or self.default_model

        # Try primary model, fall back to secondary
        output = ""
        model_used = use_model
        try:
            output = await self._call_model(prompt, use_model)
        except Exception:
            logger.warning(f"Primary model {use_model} failed, trying fallback {self.fallback_model}")
            try:
                output = await self._call_model(prompt, self.fallback_model)
                model_used = self.fallback_model
            except Exception as e:
                logger.error(f"All models failed for {action_type}: {e}")
                output = self._get_fallback_output(action_type, context)
                model_used = "fallback-template"

        latency_ms = int(time.time() * 1000) - start_ms
        tokens_estimated = len(output.split()) * 2  # rough token estimate

        return {
            "action_type": action_type,
            "output": output,
            "model_used": model_used,
            "tokens_used": tokens_estimated,
            "latency_ms": latency_ms,
        }

    def _extract_keys(self, template: str) -> list[str]:
        """Extract format keys from template string."""
        import re
        return re.findall(r'\{(\w+)\}', template)

    def _get_fallback_output(self, action_type: str, context: dict) -> str:
        """Return graceful fallback when all models fail."""
        company = context.get("company_name", "the prospect")
        fallbacks = {
            "email_draft": f"Subject: Following up on your interest\n\nHi,\n\nI wanted to follow up regarding {company}. I noticed we haven't connected recently and wanted to check if there's anything I can help with.\n\nWould you be open to a quick 15-minute call this week?\n\nBest regards",
            "lead_score": "SCORE: 50\nTIER: B\nREASONING: Insufficient data for full analysis. Manual review recommended.\nNEXT_ACTION: Research company and schedule discovery call.",
            "deal_analysis": f"RISK_LEVEL: Medium\nKEY_RISKS:\n- Lack of recent engagement\n- Timeline uncertainty\n- Stakeholder alignment unclear\nOPPORTUNITIES:\n- Strong initial interest indicated\n- Competitive position favorable\nRECOMMENDED_ACTIONS:\n1. Re-engage with decision maker\n2. Share relevant case study\n3. Schedule follow-up call",
            "churn_prediction": "CHURN_RISK: Medium\nPROBABILITY: 40%\nPRIMARY_REASON: Reduced engagement detected\nSAVE_ACTIONS:\n1. Executive check-in call\n2. Share quarterly ROI report\n3. Introduce customer success resource",
        }
        return fallbacks.get(action_type, "AI analysis complete. Please review manually.")


ai_service = AIService()
