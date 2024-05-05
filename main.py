import os
import uvicorn

PORT = int(os.getenv("PORT", 8000))
HOST = '0.0.0.0'

if __name__ == "__main__":
    uvicorn.run("api.index:app", host=HOST, port=PORT, reload=True)