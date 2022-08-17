import asyncio

import pydantic
import pytest

import strip


class TestStrip:

    def test_is_pydantic_base_model(self):
        test_strip = strip.Strip()
        assert isinstance(test_strip, pydantic.BaseModel)

    @pytest.mark.asyncio
    async def test_run_tests(self):
        is_called = False

        async def _check_colored_after_1_second(colored_strip: strip.Strip):
            nonlocal is_called

            await asyncio.sleep(1)
            assert any(led != (0, 0, 0) for led in colored_strip._strip)
            is_called = True

        test_strip = strip.Strip()

        await asyncio.gather(test_strip.run_tests(), _check_colored_after_1_second(test_strip))

        assert is_called