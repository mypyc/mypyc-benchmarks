from reporting.data import ScalingItem, infer_scaling_item, add_inferred_scaling_items


item1 = ScalingItem(1.5, 'h1', '3.9', 'h2', '3.9')
item2 = ScalingItem(2.0, 'h2', '3.9', 'h2', '3.10')


def test_infer_scaling_item_trivial() -> None:
    assert infer_scaling_item([item1], 'h1', '3.9', 'h2', '3.9') is item1
    assert infer_scaling_item([item1, item2], 'h1', '3.9', 'h2', '3.9') is item1
    assert infer_scaling_item([item1, item2], 'h2', '3.9', 'h2', '3.10') is item2


def test_infer_scaling_item_two_step() -> None:
    assert infer_scaling_item(
        [item1, item2], 'h1', '3.9', 'h2', '3.10') == ScalingItem(3.0, 'h1', '3.9', 'h2', '3.10')


def test_add_inferred_scaling_items() -> None:
    result = add_inferred_scaling_items([item1, item2])
    assert len(result) == 3
    assert result[0] == item1
    assert result[1] == item2
    assert result[2] == ScalingItem(3.0, 'h1', '3.9', 'h2', '3.10')
