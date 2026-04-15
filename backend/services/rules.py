def match_rule(message: str, rules: list[dict]) -> str | None:
    """Returns reply_template of first matching keyword rule, or None."""
    message_lower = message.lower()
    for rule in rules:
        if rule["keyword"].lower() in message_lower:
            return rule["reply_template"]
    return None
