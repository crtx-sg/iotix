"""Tests for telemetry value generators."""

import pytest
from src.generators import (
    RandomGenerator,
    SequenceGenerator,
    ConstantGenerator,
    create_generator,
)
from src.models import GeneratorConfig, GeneratorType, Distribution


class TestRandomGenerator:
    """Tests for RandomGenerator."""

    def test_uniform_distribution(self):
        """Test uniform distribution generates values in range."""
        config = GeneratorConfig(
            type=GeneratorType.RANDOM,
            min=0.0,
            max=100.0,
            distribution=Distribution.UNIFORM,
        )
        generator = RandomGenerator(config)

        for _ in range(100):
            value = generator.generate()
            assert 0.0 <= value <= 100.0

    def test_normal_distribution(self):
        """Test normal distribution generates reasonable values."""
        config = GeneratorConfig(
            type=GeneratorType.RANDOM,
            min=0.0,
            max=100.0,
            distribution=Distribution.NORMAL,
            mean=50.0,
            stddev=10.0,
        )
        generator = RandomGenerator(config)

        values = [generator.generate() for _ in range(1000)]
        avg = sum(values) / len(values)

        # Average should be close to mean
        assert 40.0 <= avg <= 60.0

    def test_exponential_distribution(self):
        """Test exponential distribution generates positive values."""
        config = GeneratorConfig(
            type=GeneratorType.RANDOM,
            min=0.0,
            max=100.0,
            distribution=Distribution.EXPONENTIAL,
            rate=0.1,
        )
        generator = RandomGenerator(config)

        for _ in range(100):
            value = generator.generate()
            assert 0.0 <= value <= 100.0


class TestSequenceGenerator:
    """Tests for SequenceGenerator."""

    def test_incrementing_sequence(self):
        """Test incrementing sequence."""
        config = GeneratorConfig(
            type=GeneratorType.SEQUENCE,
            start=0.0,
            step=1.0,
        )
        generator = SequenceGenerator(config)

        assert generator.generate() == 0.0
        assert generator.generate() == 1.0
        assert generator.generate() == 2.0

    def test_decrementing_sequence(self):
        """Test decrementing sequence."""
        config = GeneratorConfig(
            type=GeneratorType.SEQUENCE,
            start=10.0,
            step=-1.0,
        )
        generator = SequenceGenerator(config)

        assert generator.generate() == 10.0
        assert generator.generate() == 9.0
        assert generator.generate() == 8.0

    def test_wrap_around(self):
        """Test sequence wrap around."""
        config = GeneratorConfig(
            type=GeneratorType.SEQUENCE,
            start=0.0,
            step=1.0,
            min=0.0,
            max=2.0,
            wrap=True,
        )
        generator = SequenceGenerator(config)

        assert generator.generate() == 0.0
        assert generator.generate() == 1.0
        assert generator.generate() == 2.0
        assert generator.generate() == 0.0  # Wrapped

    def test_reset(self):
        """Test sequence reset."""
        config = GeneratorConfig(
            type=GeneratorType.SEQUENCE,
            start=5.0,
            step=1.0,
        )
        generator = SequenceGenerator(config)

        generator.generate()
        generator.generate()
        generator.reset()

        assert generator.generate() == 5.0


class TestConstantGenerator:
    """Tests for ConstantGenerator."""

    def test_constant_number(self):
        """Test constant number value."""
        config = GeneratorConfig(
            type=GeneratorType.CONSTANT,
            value=42.0,
        )
        generator = ConstantGenerator(config)

        assert generator.generate() == 42.0
        assert generator.generate() == 42.0

    def test_constant_string(self):
        """Test constant string value."""
        config = GeneratorConfig(
            type=GeneratorType.CONSTANT,
            value="test",
        )
        generator = ConstantGenerator(config)

        assert generator.generate() == "test"

    def test_constant_boolean(self):
        """Test constant boolean value."""
        config = GeneratorConfig(
            type=GeneratorType.CONSTANT,
            value=True,
        )
        generator = ConstantGenerator(config)

        assert generator.generate() is True


class TestCreateGenerator:
    """Tests for generator factory function."""

    def test_create_random_generator(self):
        """Test creating random generator."""
        config = GeneratorConfig(type=GeneratorType.RANDOM, min=0, max=100)
        generator = create_generator(config)
        assert isinstance(generator, RandomGenerator)

    def test_create_sequence_generator(self):
        """Test creating sequence generator."""
        config = GeneratorConfig(type=GeneratorType.SEQUENCE, start=0)
        generator = create_generator(config)
        assert isinstance(generator, SequenceGenerator)

    def test_create_constant_generator(self):
        """Test creating constant generator."""
        config = GeneratorConfig(type=GeneratorType.CONSTANT, value=42)
        generator = create_generator(config)
        assert isinstance(generator, ConstantGenerator)
