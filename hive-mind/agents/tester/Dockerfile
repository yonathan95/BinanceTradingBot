FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install required packages for hive_mind
RUN pip install fastapi uvicorn pydantic python-dotenv aiohttp sqlalchemy asyncpg alembic aio-pika qdrant-client openai anthropic aiofiles pexpect pyyaml tenacity

# Copy necessary code
COPY agents/tester_agent.py .
COPY agents/common/ ./common/
COPY hive_mind/ /app/hive_mind/

# Set PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Start agent
CMD ["python", "tester_agent.py"] 