"""Models for the formula-viz app."""

from dataclasses import dataclass, field
from typing import Any, Optional

from fastf1.mvapi.data import CircuitInfo
from pandas import Timedelta


@dataclass
class SectorTimes:
    """Sector times for a driver."""

    sector1: Timedelta
    sector2: Timedelta
    sector3: Timedelta


@dataclass
class SectorsInfo:
    """Sector information for a driver."""

    sector1_loc: tuple[float, float, float]
    sector2_loc: tuple[float, float, float]
    sector3_loc: tuple[float, float, float]

    sector_1_idx: int
    sector_2_idx: int
    sector_3_idx: int


@dataclass
class LineData:
    """Line data containing points for line A and line B."""

    a_points: list[tuple[float, float, float]]
    b_points: list[tuple[float, float, float]]


@dataclass
class TrackData:
    """Track data containing inner, outer, and curb points."""

    inner_points: list[tuple[float, float, float]]
    inner_trace_line: Optional[LineData]

    outer_points: list[tuple[float, float, float]]
    outer_trace_line: Optional[LineData]

    inner_curb_points: list[tuple[float, float, float]]
    outer_curb_points: list[tuple[float, float, float]]


@dataclass(frozen=True)
class Driver:
    """Represent a Formula 1 driver with identifying information."""

    last_name: str
    abbrev: str
    headshot_url: str
    year: int
    session: str
    team: str
    driver_color: str

    def __str__(self) -> str:
        """Return a string representation of the Driver.

        Returns:
            A string with the driver's last name and abbreviation.

        """
        return f"{self.last_name} ({self.abbrev}, {self.year}, {self.session}, {self.team}, {self.driver_color})"

    def __hash__(self) -> int:
        """Return a hash value for the Driver.

        Returns:
            An integer hash value based on the driver's immutable attributes.

        """
        return hash(
            (
                self.last_name,
                self.abbrev,
                self.headshot_url,
                self.year,
                self.session,
                self.team,
                self.driver_color,
            )
        )


@dataclass
class AppState:
    """Holds all state variables used during rendering to make data flow explicit."""

    # Common state variables for all renderers
    track_data: Optional[TrackData] = None
    driver_dfs: dict[Driver, Any] = field(default_factory=dict)
    driver_sector_times: dict[Driver, SectorTimes] = field(default_factory=dict)
    sectors_info: Optional[SectorsInfo] = None

    driver_objs: dict[Driver, Any] = field(default_factory=dict)
    drivers_in_order: list[Driver] = field(default_factory=list)
    driver_colors: list[str] = field(default_factory=list)
    start_finish_line_idx: int = 0
    num_frames: int = 0
    camera_obj: Any = None
    focused_driver: Driver | None = None
    car_rankings: list[list[tuple[Driver, float]]] = field(default_factory=list)
    circuit_info: Optional[CircuitInfo] = None

    drivers_in_color_order: list[Driver] = field(default_factory=list)
