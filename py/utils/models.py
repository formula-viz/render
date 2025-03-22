"""Models for the F1 data."""


class Driver:
    """Represent a Formula 1 driver with identifying information."""

    def __init__(
        self,
        last_name: str,
        abbrev: str,
        headshot_url: str,
        year: int,
        session: str,
        team: str,
        driver_color: str
    ):
        """Initialize a Driver object with identifying information.

        Args:
            last_name: The last name of the driver
            abbrev: The three-letter abbreviation used to identify the driver in F1
            headshot_url: The URL of the driver's head shot image
            year: The year of the driver's participation in F1
            session: The session of the driver's participation in F1

        """
        self.last_name = last_name
        self.abbrev = abbrev
        self.headshot_url = headshot_url
        self.year = year
        self.session = session
        self.team = team
        self.driver_color = driver_color

    def __str__(self) -> str:
        """Return a string representation of the Driver.

        Returns:
            A string with the driver's last name and abbreviation.

        """
        return f"{self.last_name} ({self.abbrev}, {self.year}, {self.session}, {self.team}, {self.driver_color})"
