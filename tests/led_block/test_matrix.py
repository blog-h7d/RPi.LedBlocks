import asyncio
import typing

import pydantic
import pytest

import led_block
import strip


class TestLedMatrix:

    def test_is_pydantic_base_model(self):
        matrix = led_block.LedMatrix()
        assert isinstance(matrix, pydantic.BaseModel)

    class TestInit:

        def test_is_added_to_known_blocks(self):
            matrix = led_block.LedMatrix(name='new_name')
            assert led_block.known_blocks['new_name'] == matrix

        def test_sets_strip_obj_if_provided(self):
            matrix = led_block.LedMatrix(strip_obj=strip.Strip())

            assert matrix._strip

    class TestProperties:

        def test_name(self):
            matrix = led_block.LedMatrix(name='name')
            assert matrix.name == 'name'

        def test_rows(self):
            matrix = led_block.LedMatrix(rows=40)
            assert matrix.rows == 40

        def test_cols(self):
            matrix = led_block.LedMatrix(cols=10)
            assert matrix.cols == 10

        def test_blocks(self):
            block = led_block.LedBlock()
            matrix = led_block.LedMatrix(blocks=[[block, block]])
            assert len(matrix.blocks[0]) == 2

        def test_strip_name(self):
            matrix = led_block.LedMatrix(strip_name='Name')
            assert matrix.strip_name == 'Name'

        class TestAllBlocks:

            def test_is_generator_returning_all_blocks(self):
                block = led_block.LedBlock()
                matrix = led_block.LedMatrix(blocks=[[block, block]])
                all_blocks = matrix.all_blocks

                assert next(all_blocks) == block
                assert next(all_blocks) == block

                with pytest.raises(StopIteration):
                    next(all_blocks)

    @pytest.mark.asyncio
    class TestRunProgram:
        _last_future: typing.Coroutine = None

        async def mock_run_new_task(self, future):
            TestLedMatrix.TestRunProgram._last_future = future

        async def test_stop_calls_run_stop(self, monkeypatch):
            monkeypatch.setattr(led_block.LedMatrix, '_run_new_task', self.mock_run_new_task)

            matrix = led_block.LedMatrix()
            await matrix.run_program(led_block.BlockProgram.STOP)
            await asyncio.sleep(0.1)

            assert self._last_future.__name__ == '_run_stop'

        async def test_random_calls_run_random(self, monkeypatch):
            monkeypatch.setattr(led_block.LedMatrix, '_run_new_task', self.mock_run_new_task)

            matrix = led_block.LedMatrix()
            await matrix.run_program(led_block.BlockProgram.RANDOM)
            await asyncio.sleep(0.1)

            assert self._last_future.__name__ == '_run_random'

        async def test_random_with_two_colors_calls_run_random_with_color(self, monkeypatch):
            monkeypatch.setattr(led_block.LedMatrix, '_run_new_task', self.mock_run_new_task)

            matrix = led_block.LedMatrix()
            await matrix.run_program(led_block.BlockProgram.RANDOM, colors=[
                led_block.ColorConverter.get_color(led_block.ColorName.GREEN),
                led_block.ColorConverter.get_color(led_block.ColorName.CYAN),
            ])
            await asyncio.sleep(0.1)

            assert self._last_future.__name__ == '_run_random_with_color'

        async def test_color_run_calls_run_color_run(self, monkeypatch):
            monkeypatch.setattr(led_block.LedMatrix, '_run_new_task', self.mock_run_new_task)

            matrix = led_block.LedMatrix()
            await matrix.run_program(led_block.BlockProgram.COLOR_RUN)
            await asyncio.sleep(0.1)

            assert self._last_future.__name__ == '_run_color_run'

        async def test_fading_calls_run_fading(self, monkeypatch):
            monkeypatch.setattr(led_block.LedMatrix, '_run_new_task', self.mock_run_new_task)

            matrix = led_block.LedMatrix()
            await matrix.run_program(led_block.BlockProgram.FADING)
            await asyncio.sleep(0.1)

            assert self._last_future.__name__ == '_run_fading'

    @pytest.mark.asyncio
    class TestStopActTask:

        async def test_cancel_actual_running_task_after_1_second(self):
            async def mock_task():
                while True:
                    await asyncio.sleep(0.1)

            matrix = led_block.LedMatrix()
            matrix._act_task = asyncio.create_task(mock_task())

            await asyncio.gather(matrix._stop_act_task(), asyncio.sleep(1.1))
            assert matrix._act_task.cancelled()

    @pytest.mark.asyncio
    class TestTasks:

        @staticmethod
        def get_matrix_with_black_blocks() -> led_block.LedMatrix:
            return led_block.LedMatrix(blocks=[[
                led_block.LedBlock(start=1, end=5),
                led_block.LedBlock(start=1, end=5),
                led_block.LedBlock(start=1, end=5)
            ], [
                led_block.LedBlock(start=1, end=5),
                led_block.LedBlock(start=1, end=5),
                led_block.LedBlock(start=1, end=5),
            ]])

        @staticmethod
        def get_matrix_with_colored_blocks() -> led_block.LedMatrix:
            return led_block.LedMatrix(blocks=[[
                led_block.LedBlock(start=1, end=5, color=led_block.Color(green=100)),
                led_block.LedBlock(start=1, end=5, color=led_block.Color(blue=100)),
                led_block.LedBlock(start=1, end=5, color=led_block.Color(red=100))
            ], [
                led_block.LedBlock(start=1, end=5, color=led_block.Color(green=100)),
                led_block.LedBlock(start=1, end=5, color=led_block.Color(blue=100)),
                led_block.LedBlock(start=1, end=5, color=led_block.Color(red=100)),
            ]])

        @staticmethod
        async def call_stop(matrix, wait_time=0.1):
            await asyncio.sleep(wait_time)
            matrix._is_running = False

        class TestRunStop:

            async def test_sets_all_blocks_to_black(self):
                matrix = TestLedMatrix.TestTasks.get_matrix_with_colored_blocks()

                await matrix._run_stop()

                assert all(block.color.is_black for block in matrix.all_blocks)

        class TestRunFixed:

            async def test_sets_all_blocks_to_color(self):
                matrix = TestLedMatrix.TestTasks.get_matrix_with_colored_blocks()

                color = led_block.Color(red=100, green=50)

                await matrix._run_fixed(color)

                assert all(block.color == color for block in matrix.all_blocks)

        class TestRunRandom:

            async def test_set_at_least_one_block_to_a_color(self):
                matrix = TestLedMatrix.TestTasks.get_matrix_with_black_blocks()
                matrix._is_running = True
                await asyncio.gather(matrix._run_random(), TestLedMatrix.TestTasks.call_stop(matrix))

                assert any(not block.color.is_black for block in matrix.all_blocks)

        class TestRunRandomWithColor:

            async def test_ha_all_blocks_in_colors(self):
                matrix = TestLedMatrix.TestTasks.get_matrix_with_black_blocks()

                red = led_block.Color(red=200)
                blue = led_block.Color(blue=200)

                matrix._is_running = True
                await asyncio.gather(matrix._run_random_with_color(red, blue),
                                     TestLedMatrix.TestTasks.call_stop(matrix, wait_time=0.3))

                assert all(block.color in [red, blue] for block in matrix.all_blocks)

    class TestGetDistance:

        @pytest.mark.parametrize("start, end, result", [
            (0, 4, 4),
            (0, 6, 4),
            (3, 5, 2),
            (3, 0, 3),
            (3, 8, 5),
            (8, 5, 3),
            (9, 0, 1),
            (3, 3, 0),

        ])
        def test_with_size_10(self, start, end, result):
            assert led_block.LedMatrix.get_distance(start, end, 10) == result


