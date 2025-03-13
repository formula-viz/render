"""Models for the F1 data."""


class Driver:
    """Represent a Formula 1 driver with identifying information."""

    def __init__(self, last_name: str, abbrev: str):
        """Initialize a Driver object with identifying information.

        Args:
            last_name: The last name of the driver
            abbrev: The three-letter abbreviation used to identify the driver in F1

        """
        self.last_name = last_name
        self.abbrev = abbrev

    def __str__(self) -> str:
        """Return a string representation of the Driver.

        Returns:
            A string with the driver's last name and abbreviation.

        """
        return f"{self.last_name} ({self.abbrev})"
