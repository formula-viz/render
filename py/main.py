import json
import sys

from py.post_render.post_render import HeadToHeadPostRenderer, RestOfFieldPostRenderer
from py.render.render import HeadToHeadRenderer, RestOfFieldRenderer

from py.render.render_funcs.add_driver_objects import import_crown


def initialize(config):
    if config["type"] == "head-to-head":
        renderer = HeadToHeadRenderer(config)
        post_renderer = HeadToHeadPostRenderer(config)
    else:
        renderer = RestOfFieldRenderer(config)
        post_renderer = RestOfFieldPostRenderer(config)

    return renderer, post_renderer


def trigger(config, renderer, post_renderer):
    isolate_module = config["pipeline"]["isolate_module"]
    if type(isolate_module) == bool and not isolate_module:
        renderer.render()
        post_renderer.post_render()
    elif isolate_module == "render":
        renderer.render()
    elif isolate_module == "post_render":
        post_renderer.post_render()


if __name__ == "__main__":
    config = json.loads(sys.argv[-1])
    video_type = config["type"]

    renderer, post_renderer = initialize(config)
    trigger(config, renderer, post_renderer)
