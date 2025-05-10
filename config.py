import os

class Config:
    # Secret key for session management
    SECRET_KEY = 'dev-secret-key-12345'
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    DEBUG = True

    # OpenRouter configuration
    OPENROUTER_API_KEY = "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"
    OPENROUTER_MODEL_NAME = "deepseek/deepseek-chat-v3-0324"
