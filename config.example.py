import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# NVIDIA API Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "YOUR_NVIDIA_API_KEY_HERE")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
NVIDIA_API_BASE_URL = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")

MAIN_MODEL = NVIDIA_MODEL
GROUP_MODEL = NVIDIA_MODEL
MODEL_NAME = MAIN_MODEL
