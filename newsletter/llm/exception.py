class LLMError(Exception):
    pass


class LLMAuthenticationError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMServiceUnavailableError(LLMError):
    pass
