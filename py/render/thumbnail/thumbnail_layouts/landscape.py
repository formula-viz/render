import bpy
import math

from py.render.thumbnail.thumbnail_layouts.abstract_layout import LayoutConfigurer

class LandscapeConfigurer(LayoutConfigurer):
    def position_camera(self, camera_obj: bpy.types.Object):
        camera_obj.location = (-7.08, 23.16, 9.08)
        camera_obj.rotation_euler = (
            math.radians(73),
            math.radians(0),
            math.radians(-177),
        )

    def position_cars(self, cars: list[bpy.types.Object]) -> None:
        two_car_positions = [
            (-6.52, 14.27, 6.56),
            (-4.82, 11.7, 4.97),
        ]
        two_car_rotations = [
            (math.radians(0), math.radians(21), math.radians(-185)),
            (math.radians(2), math.radians(-27), math.radians(-167)),
        ]

        three_car_positions = [
            (-4.34, 11.77, 4.42),
            (-6.52, 13.1, 5.27),
            (-6, 12.35, 6.6),
        ]
        three_car_rotations = [
            (math.radians(3), math.radians(-9), math.radians(-183)),
            (0, math.radians(21), math.radians(-185)),
            (math.radians(-5), math.radians(-14), math.radians(-169)),
        ]

        # Set positions and rotations based on number of cars
        if len(cars) == 2:
            for i, car in enumerate(cars):
                car.location = two_car_positions[i]
                car.rotation_euler = two_car_rotations[i]
        else:
            for i, car in enumerate(cars):
                car.location = three_car_positions[i]
                car.rotation_euler = three_car_rotations[i]


    def position_formula_viz_car(self, formula_viz_car_obj: bpy.types.Object):
        formula_viz_car_obj.location = (-0.3, 0.13, -1)
        formula_viz_car_obj.scale = (0.01, 0.01, 0.01)
        formula_viz_car_obj.rotation_euler = (math.radians(-80), 0, 0)

    def position_driver_image(self, driver_plane: bpy.types.Object):
        driver_plane.location = (0.18, -0.04, -0.9)
        driver_plane.rotation_euler = (0, 0, 0)
        driver_plane.scale = (0.45, 0.45, 0.45)
