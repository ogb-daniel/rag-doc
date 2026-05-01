from opentelemetry import metrics

meter = metrics.get_meter("rag-platform", version="1.0.0")

# llm metrics
llm_requests_total = meter.create_counter(
    name="llm.requests.total",
    description="Total number of LLM API calls",
)
llm_failures_total = meter.create_counter(
    name="llm.failures.total",
    description="Total number of failed LLM API calls",
)
llm_request_duration = meter.create_histogram(
    name="llm.request.duration",
    description="Time spent waiting for LLM response",
    unit="s",
)
llm_tokens_used = meter.create_counter(
    name="llm.tokens.used",
    description="Total tokens consumed by LLM calls",
)

# rag metrics

embedding_cache_total = meter.create_counter(
    name="embedding.cache.total",
    description="Embedding cache lookups",
)
retrieval_duration = meter.create_histogram(
    name="retrieval.duration",
    description="Time spent on vector retrieval from Qdrant",
    unit="s",
)
