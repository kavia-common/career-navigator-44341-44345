import json
import os

from src.api.main import app

# PUBLIC_INTERFACE
def generate_openapi_file(output_dir: str = "interfaces", filename: str = "openapi.json") -> str:
    """Generate and write OpenAPI JSON to interfaces/ for the frontend contract."""
    openapi_schema = app.openapi()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    return output_path


if __name__ == "__main__":
    path = generate_openapi_file()
    print(f"Wrote OpenAPI to {path}")
