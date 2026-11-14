import sys
import os
import uvicorn

# 1. Force the project root into the Python Path
# This ensures that 'apps' can be found regardless of how the script is started.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Successfully added {project_root} to sys.path")

# 2. Start the server programmatically
if __name__ == "__main__":
    print("Starting Runners Sin Edad Server...")
    uvicorn.run(
        "apps.runners_sin_edad.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
