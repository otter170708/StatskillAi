import uvicorn
import os
import sys

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("==================================================================")
    print("Starting StatSkill AI (iGOT Karmayogi AI Augmentation Layer)...")
    print("Local Web App & API: http://localhost:8000")
    print("OpenAPI Swagger Docs: http://localhost:8000/docs")
    print("==================================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
