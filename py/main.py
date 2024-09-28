import json
import sys

from py.post_render.post_render import HeadToHeadPostRenderer
from py.render.render import HeadToHeadRenderer

if __name__ == "__main__":
    config = json.loads(sys.argv[-1])
    video_type = config["type"]

    renderer = HeadToHeadRenderer(config)
    post_renderer = HeadToHeadPostRenderer(config)

    isolate_module = config["pipeline"]["isolate_module"]
    if type(isolate_module) == bool and not isolate_module:
        renderer.render()
        post_renderer.post_render()
    elif isolate_module == "render":
        renderer.render()
    elif isolate_module == "post_render":
        post_renderer.post_render()
