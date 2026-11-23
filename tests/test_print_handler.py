from PrintLabelMS.print_handler import mm_to_device_pixels


def test_mm_to_device_pixels_at_600dpi():
    assert mm_to_device_pixels(10, 600) == 236
    assert mm_to_device_pixels(-1, 600) == -24
    assert mm_to_device_pixels(0, 600) == 0


def test_mm_to_device_pixels_at_300dpi():
    assert mm_to_device_pixels(10, 300) == 118
    assert mm_to_device_pixels(-5, 300) == -59
