# AI Newsletter

This project is a personal AI-powered tool for scraping news from several news and social media platform such as X and Reddit.

## Setup

First, clone this repository into your system.

```bash
git clone https://github.com/outday29/ai_newsletter
```

Install the necessary dependencies.

```bash
pip install -r requirements.txt
```

Set environment variables by explicitly setting them or creating a `.env` file. Each environment variable is optional and may be omitted if you do not wish to support the platform.

```txt
TOGETHER_API_KEY="optional_together_api_key"
FIREWORKS_API_KEY="optional_fireworks_api_key"
OPENAI_API_KEY="optional_openai_api_key"
REDDIT__PERSONAL_USE_SCRIPT="your_reddit_use_script"
REDDIT__CLIENT_SECRET="your_reddit_client_secret"
REDDIT__USER_AGENT="your_reddit_user_agent"
REDDIT__USERNAME="your_reddit_username"
REDDIT__PASSWORD="your_reddit_pwd"
```

After that, start the Streamlit app.

```bash
streamlit run main.py
```
