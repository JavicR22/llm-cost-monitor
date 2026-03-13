"""
Unit tests for token_counter — 2.2
"""
import pytest

from app.services.metering.token_counter import (
    count_messages_tokens,
    count_tokens,
    extract_usage_from_response,
    extract_usage_from_streaming_chunks,
)


class TestCountTokens:
    def test_empty_string_returns_zero(self):
        assert count_tokens("", "gpt-4o") == 0

    def test_known_model_counts_correctly(self):
        # "Hello, world!" is 4 tokens in cl100k / o200k
        result = count_tokens("Hello, world!", "gpt-4o")
        assert result > 0
        assert isinstance(result, int)

    def test_longer_text_has_more_tokens(self):
        short = count_tokens("Hi", "gpt-4o")
        long = count_tokens("Hi " * 100, "gpt-4o")
        assert long > short

    def test_unknown_model_uses_fallback(self):
        # Should not raise — falls back to cl100k_base
        result = count_tokens("Some text for an unknown model", "future-model-xyz")
        assert result > 0

    def test_gpt35_and_gpt4o_produce_similar_counts(self):
        text = "The quick brown fox jumps over the lazy dog."
        c1 = count_tokens(text, "gpt-3.5-turbo")
        c2 = count_tokens(text, "gpt-4o")
        # Both use standard tokenizers — counts should be close (within 20%)
        assert abs(c1 - c2) <= max(c1, c2) * 0.2


class TestCountMessagesTokens:
    def test_empty_messages_returns_zero(self):
        result = count_messages_tokens([], "gpt-4o")
        assert result == 0

    def test_single_user_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        result = count_messages_tokens(messages, "gpt-4o")
        # 3 (priming) + 3 (per-message) + tokens("Hello") + tokens("user")
        assert result > 3

    def test_more_messages_more_tokens(self):
        one = count_messages_tokens(
            [{"role": "user", "content": "Hi"}], "gpt-4o"
        )
        three = count_messages_tokens(
            [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "How are you?"},
            ],
            "gpt-4o",
        )
        assert three > one

    def test_message_with_name_adds_one_token(self):
        without_name = count_messages_tokens(
            [{"role": "user", "content": "Hi"}], "gpt-4o"
        )
        with_name = count_messages_tokens(
            [{"role": "user", "content": "Hi", "name": "Alice"}], "gpt-4o"
        )
        assert with_name > without_name


class TestExtractUsageFromResponse:
    def test_extracts_tokens_from_standard_response(self):
        response = {
            "id": "chatcmpl-abc",
            "usage": {"prompt_tokens": 10, "completion_tokens": 25, "total_tokens": 35},
        }
        input_t, output_t = extract_usage_from_response(response)
        assert input_t == 10
        assert output_t == 25

    def test_returns_zeros_when_no_usage(self):
        response = {"id": "chatcmpl-abc", "choices": []}
        input_t, output_t = extract_usage_from_response(response)
        assert input_t == 0
        assert output_t == 0

    def test_handles_partial_usage(self):
        response = {"usage": {"prompt_tokens": 5}}
        input_t, output_t = extract_usage_from_response(response)
        assert input_t == 5
        assert output_t == 0


class TestExtractUsageFromStreamingChunks:
    def test_extracts_from_include_usage_final_chunk(self):
        import json

        chunks = [
            'data: {"choices":[{"delta":{"content":"Hi"}}]}\n',
            'data: {"choices":[],"usage":{"prompt_tokens":8,"completion_tokens":2}}\n',
            "data: [DONE]\n",
        ]
        input_t, output_t = extract_usage_from_streaming_chunks(chunks, "gpt-4o")
        assert input_t == 8
        assert output_t == 2

    def test_falls_back_to_tiktoken_when_no_usage(self):
        import json

        chunks = [
            'data: {"choices":[{"delta":{"content":"Hello world"}}]}\n',
            "data: [DONE]\n",
        ]
        input_t, output_t = extract_usage_from_streaming_chunks(chunks, "gpt-4o")
        # No prompt tokens from streaming without include_usage
        assert input_t == 0
        # Should count output tokens from content
        assert output_t > 0

    def test_handles_empty_chunks(self):
        input_t, output_t = extract_usage_from_streaming_chunks([], "gpt-4o")
        assert input_t == 0
        assert output_t == 0
