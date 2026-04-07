"""
Standard server entry point expected by openenv validate.
"""
import uvicorn
from backend.main import app

def main():
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
