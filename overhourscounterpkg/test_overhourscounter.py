from overhourscounterpkg.overhourscounter import progresive_hours_counter


def test_progressive_hours_counter():
    assert progresive_hours_counter(1000, 1) == 1150


def test_progressive_hours_counter_2():
    assert progresive_hours_counter(1000, 5) == 2000


def test_progressive_hours_counter_3():
    assert progresive_hours_counter(1000, 7) == 3000


def test_progressive_hours_counter_4():
    assert progresive_hours_counter(729.24, 4) == 1239.708
