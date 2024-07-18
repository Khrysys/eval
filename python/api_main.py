from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from uvicorn import Server, Config
from asyncio import run
import app

fastapi = FastAPI()

fastapi.mount('/api', app.app)

fastapi.mount('/', StaticFiles(directory='/var/loader'))

if __name__ == '__main__':
    run(Server(Config(
        fastapi,
        port=8000,
        host='0.0.0.0'              
    )).serve())