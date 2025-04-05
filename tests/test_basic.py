"""
Basic tests for the Upsonic agent framework.
"""

import sys
sys.path.append(".")

def test_import():
    """Test that we can import the main module."""
    from src.main import framework
    assert framework is not None
    
def test_task_class():
    """Test the Task class."""
    from src.agent_base import Task
    task = Task("Test task", context=["test context"])
    assert task.description == "Test task"
    assert task.context == ["test context"] 