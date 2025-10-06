# Setup Instructions

## Environment Variables

You can configure the application using either `.env` file or shell environment variables in `~/.zshrc`.

### Option 1: Using ~/.zshrc (Recommended for personal use)

Add these lines to your `~/.zshrc`:

```bash
# ClickHouse Configuration for chat-with-data
export CLICKHOUSE_HOST="your_host.clickhouse.cloud"
export CLICKHOUSE_PASSWORD="your_password"
export CLICKHOUSE_USER="default"
export CLICKHOUSE_DATABASE="default"

# OpenAI Configuration
export OPENAI_API_KEY="your_openai_api_key"
```

After adding, reload your shell:
```bash
source ~/.zshrc
```

### Option 2: Using .env file (Recommended for projects)

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# ClickHouse Configuration
CLICKHOUSE_HOST=your_host.clickhouse.cloud
CLICKHOUSE_PASSWORD=your_password
CLICKHOUSE_USER=default
CLICKHOUSE_DATABASE=default
```

### Verify Configuration

Test that your configuration works:

```bash
python main.py --test-connection
```

You should see: `✓ Connection successful!`

## Current Configuration

Your ClickHouse credentials are now stored in:
- `~/.zshrc` - Environment variables (✓ configured)

The application no longer has hardcoded credentials in `config.py`.

## Security Note

- Never commit credentials to git
- `.env` is in `.gitignore`
- `~/.zshrc` is outside the project directory
- Use environment variables for production deployments
