"""Model pricing table and cost calculation."""

# Pricing per 1 token (input and output) in USD
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-6": {"input": 0.000015, "output": 0.000075},
    "claude-sonnet-4-6": {"input": 0.000003, "output": 0.000015},
    "claude-haiku-4-5": {"input": 0.0000008, "output": 0.000004},
    "gpt-4o": {"input": 0.0000025, "output": 0.00001},
    "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
    "gemini-1.5-pro": {"input": 0.00000125, "output": 0.000005},
}


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Calculate the cost in USD for a given model and token counts.
    
    Args:
        model: Model identifier (e.g., "claude-sonnet-4-6")
        tokens_in: Number of input/prompt tokens
        tokens_out: Number of output/completion tokens
    
    Returns:
        Cost in USD, rounded to 6 decimal places. Returns 0.0 if model not found.
    """
    if model not in PRICING:
        return 0.0
    
    p = PRICING[model]
    cost = tokens_in * p["input"] + tokens_out * p["output"]
    return round(cost, 6)
