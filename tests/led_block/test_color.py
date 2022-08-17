import pydantic
import pytest

import led_block


class TestColor:

    def test_is_pydantic_base_model(self):
        color = led_block.Color()
        assert isinstance(color, pydantic.BaseModel)

    class TestProperties:

        def test_red(self):
            test_color = led_block.Color(red=10)
            assert test_color.red == 10

        def test_blue(self):
            test_color = led_block.Color(blue=10)
            assert test_color.blue == 10

        def test_green(self):
            test_color = led_block.Color(green=10)
            assert test_color.green == 10

        class TestAsHtml:

            def test_black_is_000000(self):
                black = led_block.Color(red=0, blue=0, green=0)
                assert black.as_html == '#000000'

            def test_white_is_ffffff(self):
                white = led_block.Color(red=255, blue=255, green=255)
                assert white.as_html == '#ffffff'

            def test_red_is_ff0000(self):
                red = led_block.Color(red=255, blue=0, green=0)
                assert red.as_html == '#ff0000'

            def test_mixed_color(self):
                color = led_block.Color(red=15, green=165, blue=12)
                assert color.as_html == '#0fa50c'

        class TestTextAsHtml:
            def test_black_is_ffffff(self):
                black = led_block.Color(red=0, blue=0, green=0)
                assert black.text_as_html == '#ffffff'

            def test_white_is_000000(self):
                white = led_block.Color(red=255, blue=255, green=255)
                assert white.text_as_html == '#000000'

        class TestAsTuple:

            def test_black_is_0_0_0(self):
                black = led_block.Color(red=0, blue=0, green=0)
                assert black.as_tuple == (0, 0, 0)

            def test_white_is_255_255_255(self):
                black = led_block.Color(red=255, blue=255, green=255)
                assert black.as_tuple == (255, 255, 255)

        class TestIsBlack:

            def test_black_is_true(self):
                black = led_block.Color(red=0, blue=0, green=0)
                assert black.is_black is True

            def test_white_is_false(self):
                black = led_block.Color(red=255, blue=255, green=255)
                assert black.is_black is False

    class TestGetMixedColor:

        @pytest.mark.parametrize("mix_factor", (0, 0.2, 0.8, 1))
        def test_mix_with_itself_is_always_itself(self, mix_factor):
            color_to_mix = led_block.ColorConverter.get_color(led_block.ColorName.LIGHTCYAN)

            new_color = color_to_mix.get_mixed_color(color_to_mix, mixed_factor=mix_factor)

            assert new_color == color_to_mix

        @pytest.mark.parametrize("mix_factor", (0, 0.2, 0.8, 1))
        def test_mix_red_and_blue_to_magenta(self, mix_factor):
            red = led_block.Color(red=255)
            blue = led_block.Color(blue=255)

            mixed_color = red.get_mixed_color(blue, mixed_factor=mix_factor)
            assert mixed_color.red == pytest.approx(255 - mix_factor * 255)
            assert mixed_color.blue == pytest.approx(mix_factor * 255)
            assert mixed_color.green == 0


class TestColorConverter:
    class TestBlack:

        def test_red_is_zero(self):
            assert led_block.ColorConverter.get_color(led_block.ColorName.BLACK).red == 0

        def test_blue_is_zero(self):
            assert led_block.ColorConverter.get_color(led_block.ColorName.BLACK).blue == 0

        def test_green_is_zero(self):
            assert led_block.ColorConverter.get_color(led_block.ColorName.BLACK).green == 0

    class TestColor:

        def test_gets_corresponding_color_object(self):
            cyan = led_block.ColorConverter.get_color(led_block.ColorName.CYAN)
            assert cyan.red == 0
            assert cyan.green == 255
            assert cyan.blue == 255

    class TestGetRandom:

        def test_entry_is_color(self):
            random_color = led_block.ColorConverter.get_random()
            assert isinstance(random_color, led_block.Color)

        def test_excludes_color_if_defined(self):
            forbidden_color = led_block.ColorConverter.get_color(led_block.ColorName.CYAN)
            for _ in range(10000):
                random_color = led_block.ColorConverter.get_random(exclude_color=forbidden_color)
                assert random_color != forbidden_color


class TestLedBlock:

    def test_is_pydantic_base_model(self):
        block = led_block.LedBlock()
        assert isinstance(block, pydantic.BaseModel)

    class TestProperties:

        def test_start(self):
            block = led_block.LedBlock(start=40)
            assert block.start == 40

        def test_end(self):
            block = led_block.LedBlock(end=40)
            assert block.end == 40

        def test_color(self):
            new_color = led_block.ColorConverter.get_color(led_block.ColorName.GREEN)
            block = led_block.LedBlock(color=new_color)
            assert block.color == new_color

        class TestInverted:

            def test_is_false_if_start_less_than_end(self):
                block = led_block.LedBlock(start=20, end=40)
                assert block.inverted is False

            def test_is_true_if_start_greater_than_end(self):
                block = led_block.LedBlock(start=60, end=40)
                assert block.inverted is True

        class TestAbsStart:

            @pytest.mark.parametrize("start, end, result", [
                (0, 10, 0),
                (30, 25, 25)
            ])
            def test_returns_minimum_of_start_and_end(self, start, end, result):
                block = led_block.LedBlock(start=start, end=end)
                assert block.abs_start == result

        class TestNumberOfLeds:

            @pytest.mark.parametrize("start, end, result", [
                (0, 10, 10),
                (30, 25, 5),
                (30, 30, 0),
            ])
            def test_is_the_number_of_leds_between_start_and_end(self, start, end, result):
                block = led_block.LedBlock(start=start, end=end)
                assert block.number_of_leds == result
