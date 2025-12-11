"""Telemetry value generators for virtual devices."""

import math
import random
from abc import ABC, abstractmethod
from typing import Any

from .models import GeneratorConfig, Distribution


class ValueGenerator(ABC):
    """Abstract base class for telemetry value generators."""

    @abstractmethod
    def generate(self) -> Any:
        """Generate the next value."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the generator to initial state."""
        pass


class RandomGenerator(ValueGenerator):
    """Generate random values with various distributions."""

    def __init__(self, config: GeneratorConfig):
        self.min_val = config.min if config.min is not None else 0.0
        self.max_val = config.max if config.max is not None else 100.0
        self.distribution = config.distribution
        self.mean = config.mean
        self.stddev = config.stddev
        self.rate = config.rate

    def generate(self) -> float:
        if self.distribution == Distribution.UNIFORM:
            return random.uniform(self.min_val, self.max_val)

        elif self.distribution == Distribution.NORMAL:
            mean = self.mean if self.mean is not None else (self.min_val + self.max_val) / 2
            stddev = self.stddev if self.stddev is not None else (self.max_val - self.min_val) / 6
            value = random.gauss(mean, stddev)
            return max(self.min_val, min(self.max_val, value))

        elif self.distribution == Distribution.EXPONENTIAL:
            rate = self.rate if self.rate is not None else 1.0
            value = random.expovariate(rate)
            return max(self.min_val, min(self.max_val, value))

        return random.uniform(self.min_val, self.max_val)

    def reset(self) -> None:
        pass


class SequenceGenerator(ValueGenerator):
    """Generate sequential values with optional wrapping."""

    def __init__(self, config: GeneratorConfig):
        self.start = config.start if config.start is not None else 0.0
        self.step = config.step
        self.min_val = config.min
        self.max_val = config.max
        self.wrap = config.wrap
        self.current = self.start

    def generate(self) -> float:
        value = self.current
        self.current += self.step

        if self.wrap and self.max_val is not None:
            if self.step > 0 and self.current > self.max_val:
                self.current = self.min_val if self.min_val is not None else self.start
            elif self.step < 0 and self.min_val is not None and self.current < self.min_val:
                self.current = self.max_val

        return value

    def reset(self) -> None:
        self.current = self.start


class ConstantGenerator(ValueGenerator):
    """Generate a constant value."""

    def __init__(self, config: GeneratorConfig):
        self.value = config.value

    def generate(self) -> Any:
        return self.value

    def reset(self) -> None:
        pass


class ReplayGenerator(ValueGenerator):
    """Replay values from a data file."""

    def __init__(self, config: GeneratorConfig):
        self.data_file = config.data_file
        self.loop = config.loop_replay
        self.data: list[Any] = []
        self.index = 0
        self._load_data()

    def _load_data(self) -> None:
        """Load data from file."""
        if self.data_file:
            try:
                import json
                with open(self.data_file, "r") as f:
                    self.data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self.data = []

    def generate(self) -> Any:
        if not self.data:
            return None

        value = self.data[self.index]
        self.index += 1

        if self.index >= len(self.data):
            if self.loop:
                self.index = 0
            else:
                self.index = len(self.data) - 1

        return value

    def reset(self) -> None:
        self.index = 0


class SineWaveGenerator(ValueGenerator):
    """Generate values following a sine wave pattern."""

    def __init__(
        self,
        min_val: float = 0.0,
        max_val: float = 100.0,
        period_ms: int = 60000,
        phase: float = 0.0,
    ):
        self.min_val = min_val
        self.max_val = max_val
        self.period_ms = period_ms
        self.phase = phase
        self.tick = 0

    def generate(self) -> float:
        amplitude = (self.max_val - self.min_val) / 2
        offset = self.min_val + amplitude
        angle = (2 * math.pi * self.tick / self.period_ms) + self.phase
        self.tick += 1
        return offset + amplitude * math.sin(angle)

    def reset(self) -> None:
        self.tick = 0


def create_generator(config: GeneratorConfig) -> ValueGenerator:
    """Factory function to create a generator from configuration."""
    generators = {
        "random": RandomGenerator,
        "sequence": SequenceGenerator,
        "constant": ConstantGenerator,
        "replay": ReplayGenerator,
    }

    generator_class = generators.get(config.type.value)
    if generator_class:
        return generator_class(config)

    # Default to random generator
    return RandomGenerator(config)
