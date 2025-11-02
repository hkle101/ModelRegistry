"""Pytest fixtures for the model-registry project."""

import pytest


@pytest.fixture
def sample_url():
    return "https://huggingface.co/google/gemma-3-270m"
