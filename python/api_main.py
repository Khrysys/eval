from fastapi import FastAPI
from uvicorn import Server, Config
from asyncio import run
import app

fastapi = FastAPI()

fastapi.include_router(app.app)

if __name__ == '__main__':
    run(Server(Config(
        fastapi,
        port=8000,
        host='0.0.0.0'              
    )).serve())