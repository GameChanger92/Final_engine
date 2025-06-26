"""
context_builder.py

임시(placeholder) 버전:
씬 리스트를 받아서 번호가 매겨진 컨텍스트 문자열을 반환합니다.
나중에 실제 로직으로 교체할 예정입니다.
"""


def make_context(scenes: list[str]) -> str:
    """
    Convert a list of scenes into a numbered context string with placeholder sections.

    Parameters
    ----------
    scenes : list[str]
        List of scene descriptions

    Returns
    -------
    str
        Formatted context string with placeholders and numbered scenes
    """
    # Add placeholder sections
    context_parts = [
        "[Character Info: TO BE ADDED]",
        "[Previous Episode: TO BE ADDED]",
        "[Vector Search: TO BE ADDED]",
        "",  # Empty line separator
    ]

    # Add numbered scenes
    for i, scene in enumerate(scenes, 1):
        context_parts.append(f"{i}. {scene}")

    return "\n".join(context_parts)
