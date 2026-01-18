"""Modal deployment configuration."""
import modal

# Create Modal stub
stub = modal.Stub("investment-research-ai")

# Define Docker image with dependencies using Poetry
image = (
    modal.Image.debian_slim(python_version="3.11")
    .poetry_install_from_file("pyproject.toml")
)

# Define secrets (set in Modal dashboard)
secrets = [
    modal.Secret.from_name("openai-secret"),
    modal.Secret.from_name("anthropic-secret"),
    modal.Secret.from_name("supabase-secret"),
    modal.Secret.from_name("cohere-secret"),
    modal.Secret.from_name("langsmith-secret"),
]


# Deploy ASGI app
@stub.function(
    image=image,
    secrets=secrets,
    cpu=2.0,
    memory=4096,
    timeout=300,
    keep_warm=1,
    allow_concurrent_inputs=10,
)
@modal.asgi_app()
def fastapi_app():
    """Create and return FastAPI app."""
    from src.api.main import app
    return app


# Background job: Daily evaluations
@stub.function(
    image=image,
    secrets=secrets,
    schedule=modal.Period(days=1),
)
def run_daily_evaluations():
    """Run evaluation suite daily."""
    print("Running daily evaluations...")
    # To be implemented


# CLI entrypoint
@stub.local_entrypoint()
def main():
    """Local entrypoint for testing."""
    import uvicorn
    from src.api.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)
