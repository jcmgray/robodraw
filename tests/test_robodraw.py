from robodraw import Drawing


def test_drawing_create():
    d = Drawing()
    assert isinstance(d, Drawing)
