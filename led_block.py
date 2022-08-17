import asyncio
import enum
import math
import random
import typing

import fastapi
import fastapi.templating
import pydantic

import strip

RED = 'red'
GREEN = 'green'
BLUE = 'blue'


class ColorName(enum.Enum):
    BLACK = 'black'
    WHITE = 'white'

    LIGHTRED = 'light_red'
    RED = 'red'
    DARKRED = 'dark_red'

    BLUE = 'blue'
    DARKBLUE = 'dark_blue'

    GREEN = 'green'
    LIGHTGREEN = 'light_green'
    DARKGREEN = 'dark_green'

    YELLOW = 'yellow'
    LIGHTYELLOW = 'light_yellow'
    DARKYELLOW = 'dark_yellow'

    CYAN = 'cyan'
    LIGHTCYAN = 'light_cyan'
    DARKCYAN = 'dark_cyan'

    MAGENTA = 'magenta'
    LIGHTMAGENTA = 'light_magenta'


class Color(pydantic.BaseModel):  # pylint: disable=no-member
    red: int = pydantic.Field(ge=0, le=255, default=0)
    green: int = pydantic.Field(ge=0, le=255, default=0)
    blue: int = pydantic.Field(ge=0, le=255, default=0)

    @property
    def as_html(self):
        return f'#{self.red:02x}{self.green:02x}{self.blue:02x}'

    @property
    def text_as_html(self):
        if self.red + self.green + self.blue < 200:
            return '#ffffff'

        return '#000000'

    @property
    def as_tuple(self) -> tuple[int, int, int]:
        return self.red, self.green, self.blue

    @staticmethod
    def get_random_color():
        return Color(
            red=random.randint(0, 255),
            green=random.randint(0, 255),
            blue=random.randint(0, 255)
        )

    @property
    def is_black(self) -> bool:
        return not self.red and not self.green and not self.blue

    def get_mixed_color(self, color2: 'Color', mixed_factor: float = 0.5):
        mixed_factor = max(0.0, min(mixed_factor, 1.0))

        def check_value(value):
            return max(0, min(math.floor(value), 255))

        return Color(red=check_value(self.red + (color2.red - self.red) * mixed_factor),
                     green=check_value(self.green + (color2.green - self.green) * mixed_factor),
                     blue=check_value(self.blue + (color2.blue - self.blue) * mixed_factor))


class ColorConverter:
    _color_codes = {
        ColorName.BLACK: Color.parse_obj({}),
        ColorName.WHITE: Color.parse_obj({RED: 100, GREEN: 100, BLUE: 100}),

        ColorName.LIGHTRED: Color.parse_obj({'red': 255}),
        ColorName.RED: Color.parse_obj({'red': 160}),
        ColorName.DARKRED: Color.parse_obj({'red': 80}),

        ColorName.BLUE: Color.parse_obj({'blue': 255}),
        ColorName.DARKBLUE: Color.parse_obj({'blue': 139}),

        ColorName.GREEN: Color.parse_obj({'green': 160}),
        ColorName.LIGHTGREEN: Color.parse_obj({'green': 255}),
        ColorName.DARKGREEN: Color.parse_obj({'green': 80}),

        ColorName.YELLOW: Color.parse_obj({'red': 160, 'green': 160}),
        ColorName.LIGHTYELLOW: Color.parse_obj({'red': 255, 'green': 255}),
        ColorName.DARKYELLOW: Color.parse_obj({'red': 139, 'green': 139}),

        ColorName.CYAN: Color.parse_obj({'green': 255, 'blue': 255}),
        ColorName.LIGHTCYAN: Color.parse_obj({'red': 224, 'green': 255, 'blue': 255}),
        ColorName.DARKCYAN: Color.parse_obj({'green': 139, 'blue': 139}),

        ColorName.MAGENTA: Color.parse_obj({'red': 160, 'blue': 160}),
        ColorName.LIGHTMAGENTA: Color.parse_obj({'red': 255, 'blue': 255}),

    }

    _available_colors = list(_color_codes.values())

    @staticmethod
    def get_color(color_name: ColorName) -> Color:
        return ColorConverter._color_codes.get(color_name, None)

    @classmethod
    def get_random(cls, exclude_color: Color = None) -> Color:
        color = random.choice(cls._available_colors)
        while exclude_color and color == exclude_color:
            color = random.choice(cls._available_colors)

        return color


class BlockProgram(enum.Enum):
    STOP = 'stop'
    FIXED = 'fixed'
    COLOR_RUN = 'color_run'
    FADING = 'fading'
    RANDOM = 'random'


class LedBlock(pydantic.BaseModel):  # pylint: disable=no-member
    start: int = pydantic.Field(default=0, ge=0)
    end: int = pydantic.Field(default=10, ge=0)
    color: Color = Color(red=0, green=0, blue=0)

    @property
    def inverted(self) -> bool:
        return self.start > self.end

    @property
    def abs_start(self) -> int:
        return min(self.start, self.end)

    @property
    def number_of_leds(self) -> int:
        return abs(self.end - self.start)


known_blocks: dict[str, 'LedMatrix'] = {}


class LedMatrix(pydantic.BaseModel):  # pylint: disable=no-member
    name: str = 'default'
    rows: int = 10
    cols: int = 5
    blocks: list[list[LedBlock]] = []
    strip_name: str = 'default'

    _strip: strip.Strip = None
    _act_task: asyncio.Task = None
    _is_running: bool = False

    def __init__(self, strip_obj: strip.Strip = None, **data):
        if 'blocks' in data \
                and isinstance(data['blocks'], list) \
                and all(isinstance(content, list) for content in data['blocks']) \
                and all(isinstance(content, list) for rows in data['blocks'] for content in rows):
            data['blocks'] = [[{'start': col[0], 'end': col[1]} for col in row] for row in data['blocks']]

        super().__init__(**data)

        self._strip = strip_obj
        known_blocks[self.name] = self

    @property
    def running_task(self) -> str:
        if not self._act_task or self._act_task.done():
            return 'No running task'
        return f'Running task: {self._act_task.get_name()}'

    @property
    def all_blocks(self) -> typing.Generator[LedBlock, None, None]:
        for row in self.blocks:
            for block in row:
                yield block

    async def run_program(self, program: BlockProgram, colors: list[Color] = None):
        match program:
            case BlockProgram.STOP:
                asyncio.create_task(self._run_new_task(self._run_stop()))

            case BlockProgram.FIXED:
                if colors and not colors[0].is_black:
                    color = colors[0]
                else:
                    color = ColorConverter.get_random(exclude_color=ColorConverter.get_color(ColorName.BLACK))

                asyncio.create_task(self._run_new_task(self._run_fixed(color)))

            case BlockProgram.RANDOM:
                if colors and len(colors) > 1 and not colors[0].is_black and not colors[1].is_black:
                    asyncio.create_task(self._run_new_task(self._run_random_with_color(colors[0], colors[1])))

                else:
                    asyncio.create_task(self._run_new_task(self._run_random()))

            case BlockProgram.COLOR_RUN:
                if colors and not colors[0].is_black:
                    color = colors[0]
                else:
                    color = ColorConverter.get_random(exclude_color=ColorConverter.get_color(ColorName.BLACK))

                if colors and len(colors) > 1 and not colors[1].is_black:
                    color2 = colors[1]
                else:
                    color2 = ColorConverter.get_random(exclude_color=ColorConverter.get_color(ColorName.BLACK))

                asyncio.create_task(self._run_new_task(self._run_color_run(color, color2)))

            case BlockProgram.FADING:
                if colors and not colors[0].is_black:
                    color = colors[0]
                else:
                    color = ColorConverter.get_random(exclude_color=ColorConverter.get_color(ColorName.BLACK))

                if colors and len(colors) > 1:
                    color2 = colors[1]
                else:
                    color2 = ColorConverter.get_random(exclude_color=ColorConverter.get_color(ColorName.BLACK))

                asyncio.create_task(self._run_new_task(self._run_fading(color, color2)))

    async def _run_new_task(self, task: typing.Coroutine):
        if not self._is_running:
            if self._strip:
                await self._strip.switch_on()

        if self._act_task:
            await self._stop_act_task()

        self._is_running = True
        self._act_task = asyncio.create_task(task)

    async def _stop_act_task(self):
        counter = 10  # Wait maximum 1 seconds and cancel afterwards
        while self._act_task and not self._act_task.done() and counter > 0:
            self._is_running = False
            await asyncio.sleep(0.1)
            counter -= 1

        self._act_task.cancel()

    async def _run_stop(self):
        for block in self.all_blocks:
            block.color = ColorConverter.get_color(ColorName.BLACK)

        await self._update_strip()
        self._is_running = False

        if self._strip:
            await self._strip.switch_off()

    async def _run_fixed(self, color: Color):
        for block in self.all_blocks:
            block.color = color

        if self._strip:
            self._strip.update_strip()

        self._is_running = False

    async def _run_random(self):
        count = 0
        while self._is_running:
            if not count:
                row = random.choice(self.blocks)
                cell = random.choice(row)  # type: LedBlock
                cell.color = ColorConverter.get_random(exclude_color=cell.color)

                if self._strip:
                    self._strip.set_colors(
                        color=cell.color.as_tuple,
                        start_index=cell.abs_start,
                        length=cell.number_of_leds
                    )
                    self._strip.update_strip()

            await asyncio.sleep(0.05)
            count = (count + 1) % 20

        self._is_running = False

    async def _run_random_with_color(self, color, color2):
        for block in self.all_blocks:
            random_bool = random.random() < 0.5
            block.color = color if random_bool else color2

            await self._update_strip()

        while self._is_running:
            row = random.choice(self.blocks)
            cell = random.choice(row)  # type: LedBlock
            cell.color = color2 if cell.color == color else color

            if self._strip:
                self._strip.set_colors(
                    color=cell.color.as_tuple,
                    start_index=cell.abs_start,
                    length=cell.number_of_leds
                )
                self._strip.update_strip()

            await asyncio.sleep(0.5)

        self._is_running = False

    async def _run_color_run(self, color: Color, color2: Color):
        max_index = self.rows + self.cols - 1

        for index in range(max_index // 2):
            for (i, j) in self._get_indices_by_sum_value(index):
                self.blocks[i][j].color = color
            await self._update_strip()
            await asyncio.sleep(0.5)

        while self._is_running:
            for index in range(max_index):
                for (i, j) in self._get_indices_by_sum_value((index + max_index // 2) % max_index):
                    self.blocks[i][j].color = color
                for (i, j) in self._get_indices_by_sum_value(index):
                    self.blocks[i][j].color = color2
                await self._update_strip()
                await asyncio.sleep(0.5)

        self._is_running = False

    def _get_indices_by_sum_value(self, sum_value) -> typing.Generator[tuple[int, int], None, None]:
        return ((i, j) for i in range(self.rows) for j in range(self.cols) if i + j == sum_value)

    async def _run_fading(self, color: Color, color2: Color):
        while self._is_running:
            for start_position in range(10):
                row_targets = [self.get_distance(start_position, i, self.rows) * 2 for i in range(self.rows)]
                for time in range(10):  # for a smoother fading effect
                    for row_index, row in enumerate(self.blocks):
                        mixed_factor = \
                            (row_targets[row_index]
                             - time / 10 * (row_targets[(row_index + 1) % self.rows] - row_targets[row_index])) \
                            / self.rows
                        new_color = color.get_mixed_color(color2=color2, mixed_factor=mixed_factor)

                        for block in row:
                            block.color = new_color

                    await self._update_strip()
                    await asyncio.sleep(0.2)

        self._is_running = False

    async def _update_strip(self):
        if not self._strip:
            return

        for block in self.all_blocks:
            self._strip.set_colors(
                color=block.color.as_tuple,
                start_index=block.abs_start,
                length=block.number_of_leds
            )

        self._strip.update_strip()

    @staticmethod
    def get_distance(start: int, end: int, size: int):
        if start < end:
            return min(abs(end - start), abs(start + size - end))

        return min(abs(size + end - start), abs(start - end))

    class Config:
        underscore_attrs_are_private = True


router = fastapi.APIRouter(prefix="/block")
templates = fastapi.templating.Jinja2Templates(directory="templates")


@router.get('/', tags=['UI'])
def show_blocks(request: fastapi.Request):
    return templates.TemplateResponse("blocks.html", {
        "request": request,
        "blocks": known_blocks.values()
    })


@router.get('/{block_id}/', tags=['UI'])
def show_block(
        request: fastapi.Request,
        block_id: str = fastapi.Path(default='default')
):
    if not (matrix := known_blocks.get(block_id, None)):
        raise fastapi.HTTPException(status_code=404, detail=f'Block {block_id} is unknown. '
                                                            f'Valid block names are: {", ".join(known_blocks.keys())}')

    return templates.TemplateResponse("matrix.html", {
        'request': request,
        'matrix': matrix,
        'do_reload': True,
    })


@router.post('/{block_id}/', response_class=fastapi.responses.RedirectResponse, status_code=302)
async def set_program(
        block_id: str = fastapi.Path(title='Identifier of block', example='default'),
        program: BlockProgram = fastapi.Query(default=BlockProgram.RANDOM),
        color1: ColorName = fastapi.Query(default=ColorName.BLACK),
        color2: ColorName = fastapi.Query(default=ColorName.BLACK),
):
    if not (matrix := known_blocks.get(block_id, None)):
        raise fastapi.HTTPException(status_code=404, detail=f'Block {block_id} is unknown. '
                                                            f'Valid block names are: {", ".join(known_blocks.keys())}')

    await matrix.run_program(program, colors=[ColorConverter.get_color(color1), ColorConverter.get_color(color2)])

    return router.url_path_for('show_block', **{'block_id': block_id})


@router.get('/{block_id}/colors/')
def get_act_colors(
        block_id: str = fastapi.Path(title='Identifier of block', example='default'),
):
    if not (matrix := known_blocks.get(block_id, None)):
        raise fastapi.HTTPException(status_code=404, detail=f'Block {block_id} is unknown. '
                                                            f'Valid block names are: {", ".join(known_blocks.keys())}')

    return [[(block.color.as_html, block.color.text_as_html) for block in row] for row in matrix.blocks]
