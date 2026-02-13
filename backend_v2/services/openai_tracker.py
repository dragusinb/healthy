"""OpenAI API usage tracking service."""
from datetime import datetime, timedelta, timezone
from typing import Optional

# Model pricing per 1M tokens (as of Jan 2025)
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
}


def calculate_cost(model: str, tokens_input: int, tokens_output: int) -> float:
    """Calculate estimated cost in USD based on model and tokens."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])
    input_cost = (tokens_input / 1_000_000) * pricing["input"]
    output_cost = (tokens_output / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def log_openai_call(
    model: str,
    purpose: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    user_id: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    Log an OpenAI API call to the database.

    Args:
        model: The model used (e.g., "gpt-4o", "gpt-4o-mini")
        purpose: What the call was for (document_parsing, profile_extraction, health_analysis)
        tokens_input: Number of input tokens
        tokens_output: Number of output tokens
        user_id: Optional user ID for attribution
        success: Whether the call succeeded
        error_message: Error message if failed
    """
    try:
        # Import here to avoid circular imports
        try:
            from backend_v2.database import SessionLocal
            from backend_v2.models import OpenAIUsageLog
        except ImportError:
            from database import SessionLocal
            from models import OpenAIUsageLog

        db = SessionLocal()
        try:
            total_tokens = tokens_input + tokens_output
            cost = calculate_cost(model, tokens_input, tokens_output)

            log_entry = OpenAIUsageLog(
                timestamp=datetime.now(timezone.utc),
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                model=model,
                purpose=purpose,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                total_tokens=total_tokens,
                cost_usd=cost,
                user_id=user_id,
                success=success,
                error_message=error_message
            )

            db.add(log_entry)
            db.commit()

        finally:
            db.close()

    except Exception as e:
        # Don't let tracking errors break the main flow
        print(f"Warning: Failed to log OpenAI usage: {e}")


def track_openai_response(response, model: str, purpose: str, user_id: Optional[int] = None):
    """
    Extract usage from OpenAI response and log it.

    Args:
        response: The OpenAI API response object
        model: The model used
        purpose: What the call was for
        user_id: Optional user ID
    """
    try:
        usage = response.usage
        log_openai_call(
            model=model,
            purpose=purpose,
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
            user_id=user_id,
            success=True
        )
    except Exception as e:
        # Log with zero tokens if we can't extract usage
        log_openai_call(
            model=model,
            purpose=purpose,
            user_id=user_id,
            success=True
        )
        print(f"Warning: Could not extract usage from response: {e}")


def get_usage_summary(days: int = 30) -> dict:
    """
    Get OpenAI usage summary for the admin dashboard.

    Args:
        days: Number of days to include

    Returns:
        Dictionary with usage statistics
    """
    from sqlalchemy import func

    try:
        try:
            from backend_v2.database import SessionLocal
            from backend_v2.models import OpenAIUsageLog
        except ImportError:
            from database import SessionLocal
            from models import OpenAIUsageLog

        db = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            # Total stats
            totals = db.query(
                func.count(OpenAIUsageLog.id).label("total_calls"),
                func.sum(OpenAIUsageLog.tokens_input).label("total_input_tokens"),
                func.sum(OpenAIUsageLog.tokens_output).label("total_output_tokens"),
                func.sum(OpenAIUsageLog.total_tokens).label("total_tokens"),
                func.sum(OpenAIUsageLog.cost_usd).label("total_cost")
            ).filter(OpenAIUsageLog.timestamp >= cutoff).first()

            # By model
            by_model = db.query(
                OpenAIUsageLog.model,
                func.count(OpenAIUsageLog.id).label("calls"),
                func.sum(OpenAIUsageLog.total_tokens).label("tokens"),
                func.sum(OpenAIUsageLog.cost_usd).label("cost")
            ).filter(
                OpenAIUsageLog.timestamp >= cutoff
            ).group_by(OpenAIUsageLog.model).all()

            # By purpose
            by_purpose = db.query(
                OpenAIUsageLog.purpose,
                func.count(OpenAIUsageLog.id).label("calls"),
                func.sum(OpenAIUsageLog.total_tokens).label("tokens"),
                func.sum(OpenAIUsageLog.cost_usd).label("cost")
            ).filter(
                OpenAIUsageLog.timestamp >= cutoff
            ).group_by(OpenAIUsageLog.purpose).all()

            # Daily breakdown
            daily = db.query(
                OpenAIUsageLog.date,
                func.count(OpenAIUsageLog.id).label("calls"),
                func.sum(OpenAIUsageLog.total_tokens).label("tokens"),
                func.sum(OpenAIUsageLog.cost_usd).label("cost")
            ).filter(
                OpenAIUsageLog.timestamp >= cutoff
            ).group_by(OpenAIUsageLog.date).order_by(OpenAIUsageLog.date.desc()).limit(30).all()

            # Errors count
            errors = db.query(func.count(OpenAIUsageLog.id)).filter(
                OpenAIUsageLog.timestamp >= cutoff,
                OpenAIUsageLog.success == False
            ).scalar()

            return {
                "period_days": days,
                "totals": {
                    "calls": totals.total_calls or 0,
                    "input_tokens": totals.total_input_tokens or 0,
                    "output_tokens": totals.total_output_tokens or 0,
                    "total_tokens": totals.total_tokens or 0,
                    "cost_usd": round(totals.total_cost or 0, 4)
                },
                "by_model": [
                    {"model": m.model, "calls": m.calls, "tokens": m.tokens or 0, "cost": round(m.cost or 0, 4)}
                    for m in by_model
                ],
                "by_purpose": [
                    {"purpose": p.purpose, "calls": p.calls, "tokens": p.tokens or 0, "cost": round(p.cost or 0, 4)}
                    for p in by_purpose
                ],
                "daily": [
                    {"date": d.date, "calls": d.calls, "tokens": d.tokens or 0, "cost": round(d.cost or 0, 4)}
                    for d in daily
                ],
                "errors": errors or 0
            }

        finally:
            db.close()

    except Exception as e:
        return {
            "error": str(e),
            "period_days": days,
            "totals": {"calls": 0, "tokens": 0, "cost_usd": 0},
            "by_model": [],
            "by_purpose": [],
            "daily": [],
            "errors": 0
        }
