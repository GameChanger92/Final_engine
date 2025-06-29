"""
path_helper.py

Path utilities for Final Engine project structure.
Provides centralized path management for projects/{id}/data and projects/{id}/outputs structure.
"""

from pathlib import Path

BASE = Path("projects")


def data_path(fname: str, project: str = "default") -> Path:
    """
    Get path to a data file in the specified project.
    
    Parameters
    ----------
    fname : str
        Filename within the data directory
    project : str, optional
        Project ID, defaults to "default"
        
    Returns
    -------
    Path
        Path to the data file: projects/{project}/data/{fname}
    """
    return BASE / project / "data" / fname


def out_path(fname: str, project: str = "default") -> Path:
    """
    Get path to an output file in the specified project.
    
    Parameters
    ----------
    fname : str
        Filename within the outputs directory  
    project : str, optional
        Project ID, defaults to "default"
        
    Returns
    -------
    Path
        Path to the output file: projects/{project}/outputs/{fname}
    """
    return BASE / project / "outputs" / fname


def ensure_project_dirs(project: str = "default") -> None:
    """
    Ensure project data and outputs directories exist.
    
    Parameters
    ----------
    project : str, optional
        Project ID, defaults to "default"
    """
    data_dir = BASE / project / "data"
    outputs_dir = BASE / project / "outputs"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)