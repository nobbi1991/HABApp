class Threshold:
    def __init__(self, threshold1: float, threshold2: float) -> None:
        """This is a simple Schmitt Trigger implementation.
        If the value is > upper_threshold is_higher will return true.
        The return value will stay true until the value goes below the lower threshold.

        :param threshold1:
        :param threshold2:
        """
        vals = sorted([threshold1, threshold2])
        self.lower_threshold = vals[0]
        self.upper_threshold = vals[1]
        assert self.lower_threshold < self.upper_threshold

        self.__threshold = self.upper_threshold

    def is_on(self, value: float) -> bool:
        self.check_value(value)
        return self.__threshold == self.lower_threshold

    def is_off(self, value: float) -> bool:
        return not self.is_on(value)

    @property
    def current_threshold(self) -> float:
        return self.__threshold

    def check_value(self, value: float) -> float:
        if value > self.upper_threshold:
            self.__threshold = self.lower_threshold

        if value < self.lower_threshold:
            self.__threshold = self.upper_threshold

        return self.__threshold

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (int, float)):
            return NotImplemented

        return self.check_value(other) < other

    def __le__(self, other: bool) -> bool:
        if not isinstance(other, (int, float)):
            return NotImplemented

        return self.check_value(other) <= other

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, (int, float)):
            return NotImplemented

        return self.check_value(other) >= other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, (int, float)):
            return NotImplemented

        return self.check_value(other) > other
