import re

# PII patterns
ACCOUNT_NUMBER_PATTERN = re.compile(r'\b\d{10,20}\b')
CARD_NUMBER_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
CVV_PATTERN = re.compile(r'\bcvv[\s:]*\d{3,4}\b', re.IGNORECASE)
PAN_PATTERN = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b')
PHONE_PATTERN = re.compile(r'\b[6-9]\d{9}\b')

# Prompt injection patterns
INJECTION_PATTERNS = [
    r'ignore previous instructions',
    r'ignore all instructions',
    r'you are now',
    r'act as',
    r'pretend you are',
    r'forget you are',
    r'system prompt',
    r'jailbreak',
    r'dan mode',
]


def mask_pii(text: str) -> str:
    """Mask sensitive data in output."""
    text = ACCOUNT_NUMBER_PATTERN.sub(lambda m: m.group()[:4] + '****' + m.group()[-2:], text)
    text = CARD_NUMBER_PATTERN.sub('****-****-****-****', text)
    text = CVV_PATTERN.sub('CVV: ***', text)
    text = PAN_PATTERN.sub(lambda m: m.group()[:2] + '***' + m.group()[-2:], text)
    return text


def check_prompt_injection(text: str) -> bool:
    """Returns True if injection detected."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def sanitize_input(text: str) -> tuple[bool, str]:
    """
    Returns (is_safe, message).
    If not safe, message contains rejection reason.
    """
    if check_prompt_injection(text):
        return False, "I'm sorry, I cannot process that request. Please ask a valid banking question."
    return True, text


def sanitize_output(text: str) -> str:
    """Mask PII in LLM output before sending to user."""
    return mask_pii(text)