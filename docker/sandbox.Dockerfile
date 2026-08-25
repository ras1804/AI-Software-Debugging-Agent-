FROM python:3.12-slim
RUN pip install --no-cache-dir pytest ruff
RUN useradd --create-home --uid 10001 runner
WORKDIR /workspace
USER runner
CMD ["python", "-m", "pytest"]
