"""
test_guard_registry.py

Comprehensive test suite for the Guard Registry System.
Tests registration, ordering, and auto-discovery functionality.
"""

import pytest

from src.core.guard_registry import (
    BaseGuard,
    GuardRegistry,
    clear_registry,
    get_guard_count,
    get_registered_orders,
    get_sorted_guards,
    register_guard,
)


class TestGuardRegistry:
    """Test class for guard registry functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Clear registry to ensure clean state
        clear_registry()

    def teardown_method(self):
        """Clean up after each test."""
        # Clear registry after each test
        clear_registry()

    def test_guard_registry_basic_registration(self):
        """Test basic guard registration functionality."""
        registry = GuardRegistry()

        class TestGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        # Register a guard
        registry.register(1, TestGuard)

        # Verify registration
        assert registry.get_guard_count() == 1
        assert registry.get_registered_orders() == [1]

        guards = registry.get_sorted_guards()
        assert len(guards) == 1
        assert guards[0] == TestGuard

    def test_guard_registry_multiple_guards_ordering(self):
        """Test that multiple guards are sorted by order."""
        registry = GuardRegistry()

        class Guard1(BaseGuard):
            def check(self):
                return {"passed": True}

        class Guard2(BaseGuard):
            def check(self):
                return {"passed": True}

        class Guard3(BaseGuard):
            def check(self):
                return {"passed": True}

        # Register guards in non-sequential order
        registry.register(3, Guard3)
        registry.register(1, Guard1)
        registry.register(2, Guard2)

        # Verify correct ordering
        guards = registry.get_sorted_guards()
        assert len(guards) == 3
        assert guards[0] == Guard1
        assert guards[1] == Guard2
        assert guards[2] == Guard3

        assert registry.get_registered_orders() == [1, 2, 3]

    def test_guard_registry_duplicate_order_error(self):
        """Test that registering duplicate orders raises ValueError."""
        registry = GuardRegistry()

        class Guard1(BaseGuard):
            def check(self):
                return {"passed": True}

        class Guard2(BaseGuard):
            def check(self):
                return {"passed": True}

        # Register first guard
        registry.register(1, Guard1)

        # Attempt to register second guard with same order
        with pytest.raises(ValueError) as exc_info:
            registry.register(1, Guard2)

        assert "already registered" in str(exc_info.value)
        assert "Guard1" in str(exc_info.value)
        assert "Guard2" in str(exc_info.value)

    def test_register_guard_decorator(self):
        """Test the @register_guard decorator functionality."""
        # Clear registry first
        clear_registry()

        @register_guard(order=5)
        class DecoratedGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        # Verify decorator registered the guard
        assert get_guard_count() == 1
        guards = get_sorted_guards()
        assert len(guards) == 1
        assert guards[0] == DecoratedGuard

    def test_register_guard_decorator_multiple_guards(self):
        """Test multiple guards registered with decorators maintain order."""
        clear_registry()

        @register_guard(order=10)
        class LastGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        @register_guard(order=1)
        class FirstGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        @register_guard(order=5)
        class MiddleGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        # Verify correct ordering
        guards = get_sorted_guards()
        assert len(guards) == 3
        assert guards[0] == FirstGuard
        assert guards[1] == MiddleGuard
        assert guards[2] == LastGuard

        assert get_registered_orders() == [1, 5, 10]

    def test_guard_registry_clear_functionality(self):
        """Test registry clear functionality."""

        @register_guard(order=1)
        class TestGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        # Verify guard is registered
        assert get_guard_count() == 1

        # Clear registry
        clear_registry()

        # Verify registry is empty
        assert get_guard_count() == 0
        assert get_sorted_guards() == []
        assert get_registered_orders() == []

    def test_base_guard_abstract_interface(self):
        """Test that BaseGuard cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseGuard()

    def test_base_guard_subclass_implementation(self):
        """Test that BaseGuard subclass must implement check method."""

        class IncompleteGuard(BaseGuard):
            pass  # Missing check method implementation

        with pytest.raises(TypeError):
            IncompleteGuard()

    def test_base_guard_valid_subclass(self):
        """Test that valid BaseGuard subclass can be instantiated."""

        class ValidGuard(BaseGuard):
            def check(self, text="test"):
                return {"passed": True, "text": text}

        # Should be able to instantiate
        guard = ValidGuard()

        # Should be able to call check method
        result = guard.check()
        assert result["passed"] is True

    def test_actual_guard_imports_and_registration(self):
        """Test that actual guards are properly registered when imported."""
        clear_registry()

        # Import actual guards to trigger registration
        # Note: These imports are necessary for the test, not unused
        import src.plugins.anchor_guard  # noqa: F401
        import src.plugins.critique_guard  # noqa: F401
        import src.plugins.date_guard  # noqa: F401
        import src.plugins.emotion_guard  # noqa: F401
        import src.plugins.immutable_guard  # noqa: F401
        import src.plugins.lexi_guard  # noqa: F401
        import src.plugins.pacing_guard  # noqa: F401
        import src.plugins.relation_guard  # noqa: F401
        import src.plugins.rule_guard  # noqa: F401
        import src.plugins.schedule_guard  # noqa: F401

        # Verify all 10 guards are registered
        assert get_guard_count() == 10

        # Verify correct ordering
        expected_orders = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert get_registered_orders() == expected_orders

        # Verify guard classes are in correct order (by their numerical order values)
        guards = get_sorted_guards()
        expected_guard_names = [
            "DateGuard",  # order=1
            "AnchorGuard",  # order=2
            "RuleGuard",  # order=3
            "LexiGuard",  # order=4
            "ScheduleGuard",  # order=5
            "EmotionGuard",  # order=6
            "ImmutableGuard",  # order=7
            "RelationGuard",  # order=8
            "PacingGuard",  # order=9
            "CritiqueGuard",  # order=10
        ]

        actual_guard_names = [guard.__name__ for guard in guards]
        assert actual_guard_names == expected_guard_names

    def test_guard_registry_empty_state(self):
        """Test guard registry behavior when empty."""
        clear_registry()

        assert get_guard_count() == 0
        assert get_sorted_guards() == []
        assert get_registered_orders() == []

    def test_guard_registry_large_order_numbers(self):
        """Test registry with large order numbers."""
        clear_registry()

        @register_guard(order=1000)
        class HighOrderGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        @register_guard(order=1)
        class LowOrderGuard(BaseGuard):
            def check(self):
                return {"passed": True}

        guards = get_sorted_guards()
        assert guards[0] == LowOrderGuard
        assert guards[1] == HighOrderGuard

        orders = get_registered_orders()
        assert orders == [1, 1000]

    def test_guard_class_instantiation_with_params(self):
        """Test that guard classes can be instantiated with parameters."""
        clear_registry()

        @register_guard(order=1)
        class ParameterizedGuard(BaseGuard):
            def __init__(self, project="default", param1=None):
                super().__init__()
                self.project = project
                self.param1 = param1

            def check(self, data):
                return {"passed": True, "project": self.project, "param1": self.param1}

        guards = get_sorted_guards()
        guard_class = guards[0]

        # Test instantiation with default parameters
        guard1 = guard_class()
        result1 = guard1.check("test")
        assert result1["project"] == "default"
        assert result1["param1"] is None

        # Test instantiation with custom parameters
        guard2 = guard_class(project="custom", param1="value")
        result2 = guard2.check("test")
        assert result2["project"] == "custom"
        assert result2["param1"] == "value"
