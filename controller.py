import asyncio
import json
import os
import typing

import fastapi
import fastapi.staticfiles
import fastapi.templating

import led_block
import strip

app = fastapi.FastAPI()
app.include_router(led_block.router, tags=['blocks'])
app.mount("/static", fastapi.staticfiles.StaticFiles(directory="static"), name="static")

templates = fastapi.templating.Jinja2Templates(directory="templates")


class DataInitialize:
    strips_data: list[dict]
    blocks_data: list[dict]

    _is_initialized = False
    _available_strips: dict[str, strip.Strip] = {}
    _blocks: list[led_block.LedMatrix] = []

    @classmethod
    async def initialize(cls):
        cls._initialize_config()
        cls._init_strips()
        cls._init_blocks()
        cls._is_initialized = True

    @classmethod
    def _initialize_config(cls, config_file: str = 'default.config.json'):

        full_config_path: str = os.path.join('config', config_file)
        with open(full_config_path, 'r', encoding='utf-8') as data:
            json_data = json.load(data)

            if 'strips' in json_data:
                cls.strips_data = json_data['strips']
            else:
                raise ValueError(f'missing entry strips in {config_file}')

            if 'blocks' in json_data:
                cls.blocks_data = json_data['blocks']
            else:
                raise ValueError(f'missing entry areas in {config_file}')

    @classmethod
    def _init_strips(cls):
        for strip_data in cls.strips_data:
            if (identifier := strip_data['identifier']) not in cls._available_strips:
                cls._available_strips[identifier] = strip.Strip(**strip_data)

    @classmethod
    def _init_blocks(cls):
        for bdata in cls.blocks_data:
            strip_name = bdata.get('strip_name', 'default')
            if strip_name in cls._available_strips:
                _blocks = led_block.LedMatrix(cls._available_strips[strip_name], **bdata)

    @classmethod
    async def shutdown(cls):
        for available_strip in cls._available_strips.values():
            await available_strip.switch_off()

    @classmethod
    async def wait_for_initialize(cls):
        while not cls._is_initialized:
            print('Initialising strips')
            await asyncio.sleep(0.1)
        return True

    @classmethod
    def strips(cls) -> typing.Generator[strip.Strip, None, None]:
        for available_strip in cls._available_strips.values():
            yield available_strip


@app.on_event("startup")
async def _start_server():
    await DataInitialize.initialize()


@app.on_event("shutdown")
async def _stop_server():
    await DataInitialize.shutdown()


@app.get("/")
def show_main_page(request: fastapi.Request):
    return templates.TemplateResponse("index.html", {
        'request': request,
        'blocks': led_block.known_blocks.values()
    })


@app.get("/status/")
def show_status_page(request: fastapi.Request):
    return templates.TemplateResponse("status.html", {
        'request': request,
    })


@app.get("/test/")
async def start_tests():
    for strip in DataInitialize.strips():
        asyncio.create_task(strip.run_tests())
    return {'started': 'successful'}
