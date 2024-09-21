from typing import Any, Dict, List, Tuple


class Config:
    def __init__(self, yaml_dict: Dict[str, Any]):
        self._read_yaml(yaml_dict)
        self._validate_config()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        instance = cls.__new__(cls)
        instance._read_yaml(data)
        instance._validate_config()
        return instance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track": self.track,
            "year": self.year,
            "render": {
                "should_render": self.should_render,
                "validate_render": self.validate_render,
                "fps": self.fps,
                "samples": self.samples,
                "adaptive_sampling": self.adaptive_sampling,
                "is_4k": self.is_4k,
                "output": self.output,
                "max_cam_distance": self.max_cam_distance,
            },
            "drivers": [{"name": name, "color": color} for name, color in self.drivers],
        }

    def _read_yaml(self, yaml_dict: Dict[str, Any]) -> None:
        self.track = yaml_dict["track"]
        self.year = int(yaml_dict["year"])
        render_settings = yaml_dict["render"]
        self.should_render = render_settings["should_render"]
        self.validate_render = render_settings["validate_render"]
        self.fps = render_settings["fps"]
        self.samples = render_settings["samples"]
        self.adaptive_sampling = render_settings["adaptive_sampling"]
        self.is_4k = render_settings["is_4k"]
        self.output = render_settings["output"]
        self.max_cam_distance = render_settings["max_cam_distance"]
        self.drivers: List[Tuple[str, str]] = [(driver["name"], driver["color"]) for driver in yaml_dict["drivers"]]

    def _validate_config(self):

        if not isinstance(self.track, str):
            raise ValueError(f"Track must be a string, got {type(self.track)}")
        if not isinstance(self.year, int):
            raise ValueError(f"Year must be an integer, got {type(self.year)}")

        if not isinstance(self.should_render, bool):
            raise ValueError(f"Should Render must be a boolean, got {type(self.should_render)}")
        if not isinstance(self.validate_render, bool):
            raise ValueError(f"Validate Render must be a boolean, got {type(self.validate_render)}")
        if not isinstance(self.fps, int):
            raise ValueError(f"FPS must be an integer, got {type(self.fps)}")
        if not isinstance(self.samples, int):
            raise ValueError(f"Samples must be an integer, got {type(self.samples)}")
        if not isinstance(self.adaptive_sampling, bool):
            raise ValueError(f"Adaptive Sampling must be a boolean, got {type(self.adaptive_sampling)}")
        if not isinstance(self.is_4k, bool):
            raise ValueError(f"Is 4k must be a boolean, got {type(self.is_4k)}")
        if not isinstance(self.output, str):
            raise ValueError(f"Output must be a string, got {type(self.output)}")
        if not isinstance(self.max_cam_distance, int):
            raise ValueError(f"Max Cam Distance must be an integer, got {type(self.max_cam_distance)}")

        for driver in self.drivers:
            name, color = driver
            if not isinstance(name, str) or not isinstance(color, str):
                raise ValueError(f"Driver name and color must be strings, got {type(name)} and {type(color)}")
