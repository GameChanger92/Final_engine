"""
guard_registry.py

Guard Registry System for Final Engine - automatic guard registration and ordering.

Provides decorator-based registration system for guards to enable automatic
discovery and execution without manual sequence management.
"""

import logging
from typing import List, Dict, Any, Callable, Type
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseGuard(ABC):
    """
    Base class for all guards in the Final Engine.

    Provides common interface that all guards must implement.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the guard with any required parameters."""
        pass

    @abstractmethod
    def check(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Check guard conditions and return results.

        Must be implemented by all guard subclasses.

        Returns
        -------
        Dict[str, Any]
            Check results with at minimum: {"passed": bool}

        Raises
        ------
        RetryException
            If guard check fails and retry is needed
        """
        pass


class GuardRegistry:
    """
    Registry for managing guard classes and their execution order.
    """

    def __init__(self):
        self._guards: Dict[int, Type[BaseGuard]] = {}

    def register(self, order: int, guard_class: Type[BaseGuard]) -> None:
        """
        Register a guard class with its execution order.

        Parameters
        ----------
        order : int
            Execution order for the guard (lower numbers execute first)
        guard_class : Type[BaseGuard]
            Guard class to register

        Raises
        ------
        ValueError
            If order is already registered
        """
        if order in self._guards:
            existing_class = self._guards[order]
            raise ValueError(
                f"Guard order {order} already registered by {existing_class.__name__}. "
                f"Cannot register {guard_class.__name__} with the same order."
            )

        self._guards[order] = guard_class
        logger.debug(f"Registered guard {guard_class.__name__} with order {order}")

    def get_sorted_guards(self) -> List[Type[BaseGuard]]:
        """
        Get all registered guards sorted by execution order.

        Returns
        -------
        List[Type[BaseGuard]]
            List of guard classes sorted by order (ascending)
        """
        sorted_orders = sorted(self._guards.keys())
        return [self._guards[order] for order in sorted_orders]

    def get_guard_count(self) -> int:
        """
        Get the total number of registered guards.

        Returns
        -------
        int
            Number of registered guards
        """
        return len(self._guards)

    def clear(self) -> None:
        """Clear all registered guards (primarily for testing)."""
        self._guards.clear()

    def get_registered_orders(self) -> List[int]:
        """
        Get all registered execution orders.

        Returns
        -------
        List[int]
            List of registered orders sorted ascending
        """
        return sorted(self._guards.keys())


# Global registry instance
_registry = GuardRegistry()


def register_guard(order: int) -> Callable[[Type[BaseGuard]], Type[BaseGuard]]:
    """
    Decorator to register a guard class with the global registry.

    Parameters
    ----------
    order : int
        Execution order for the guard (lower numbers execute first)

    Returns
    -------
    Callable[[Type[BaseGuard]], Type[BaseGuard]]
        Decorator function

    Examples
    --------
    >>> @register_guard(order=1)
    ... class MyGuard(BaseGuard):
    ...     def check(self, text):
    ...         return {"passed": True}
    """

    def decorator(guard_class: Type[BaseGuard]) -> Type[BaseGuard]:
        _registry.register(order, guard_class)
        return guard_class

    return decorator


def get_sorted_guards() -> List[Type[BaseGuard]]:
    """
    Get all registered guards sorted by execution order.

    Returns
    -------
    List[Type[BaseGuard]]
        List of guard classes sorted by order (ascending)
    """
    return _registry.get_sorted_guards()


def get_guard_count() -> int:
    """
    Get the total number of registered guards.

    Returns
    -------
    int
        Number of registered guards
    """
    return _registry.get_guard_count()


def clear_registry() -> None:
    """
    Clear all registered guards.

    Primarily used for testing to ensure clean state.
    Also removes guard modules from sys.modules cache to ensure
    decorators are re-executed on subsequent imports.
    """
    import sys

    # Clear the registry
    _registry.clear()

    # Remove guard modules from sys.modules cache to force re-import
    # This ensures decorators are re-executed when modules are imported again
    guard_module_names = [
        "src.plugins.lexi_guard",
        "src.plugins.emotion_guard",
        "src.plugins.schedule_guard",
        "src.plugins.immutable_guard",
        "src.plugins.date_guard",
        "src.plugins.anchor_guard",
        "src.plugins.rule_guard",
        "src.plugins.relation_guard",
        "src.plugins.pacing_guard",
        "src.plugins.critique_guard",
    ]

    for module_name in guard_module_names:
        if module_name in sys.modules:
            sys.modules.pop(module_name)


def get_registered_orders() -> List[int]:
    """
    Get all registered execution orders.

    Returns
    -------
    List[int]
        List of registered orders sorted ascending
    """
    return _registry.get_registered_orders()
