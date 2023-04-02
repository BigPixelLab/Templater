import typing
from typing import TypeVar

from aiogram.types import InputFile

T = TypeVar('T')


class TextLayout:
    def __init__(self):
        self._paragraphs: list[str] = []
        self._buffer: list[str] = []

    def _close_paragraph(self):
        if not self._buffer:
            return
        paragraph = ' '.join(self._buffer)
        self._paragraphs.append(paragraph)
        self._buffer.clear()

    def add(self, text: str):
        if not text:
            return
        self._buffer.append(text)

    def add_paragraph(self, text: str):
        self._close_paragraph()
        self._paragraphs.append(text)

    def result(self) -> str:
        self._close_paragraph()
        return '\n'.join(self._paragraphs)


class KeyboardLayout:
    def __init__(self):
        self._rows: list[list] = []
        self._buffer: list = []

    def _close_row(self):
        if not self._buffer:
            return
        self._rows.append(self._buffer)
        self._buffer = []

    def add(self, button):
        self._buffer.append(button)

    def add_row(self, row: list):
        self._close_row()
        self._rows.append(row)

    def result(self) -> list[list]:
        self._close_row()
        return self._rows


def _sub_type(name: str, tp: T) -> T:
    return type(name, (tp,), {})


BlockText = _sub_type('BlockText', str)
InlineText = _sub_type('InlineText', str)
KeyboardLayoutRow = _sub_type('KeyboardLayoutRow', list)

ImageID = _sub_type('ImageID', str)
AnimationID = _sub_type('AnimationID', str)


class ImageFile(typing.NamedTuple):
    input_file: InputFile


class AnimationFile(typing.NamedTuple):
    input_file: InputFile


__all__ = (
    'TextLayout',
    'KeyboardLayout',
    'BlockText',
    'InlineText',
    'KeyboardLayoutRow',
    'ImageID',
    'AnimationID',
    'ImageFile',
    'AnimationFile',
)
