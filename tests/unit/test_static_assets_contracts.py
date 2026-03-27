from app.ports.image_renderer import ImageRenderer
from app.ports.repository import StaticAssetsRepository


def test_static_assets_contracts_expose_required_methods() -> None:
    for method_name in (
        "json_exists",
        "image_exists",
        "load_document",
        "save_document",
        "save_image",
        "build_image_url",
    ):
        assert hasattr(StaticAssetsRepository, method_name)

    assert hasattr(ImageRenderer, "render")
