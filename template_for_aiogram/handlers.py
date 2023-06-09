import re
from typing import Union

from aiogram.types import InputFile, InlineKeyboardMarkup, WebAppInfo, LoginUrl, CallbackGame, InlineKeyboardButton, \
    ReplyKeyboardMarkup, KeyboardButtonPollType, KeyboardButton

from message_render import MessageRenderList, MessageRender
from template.dev import *
from .scopes import *
from .types import *


@register([DOCUMENT])
def messages(tag: Tag) -> MessageRenderList:
    """
        Список сообщений

        ::

            │ <messages>
            │     ... MESSAGES Scope ...
            │ </messages>
            └── DOCUMENT Scope

    """
    return MESSAGES.parse(tag.element, tag.context)


@register([DOCUMENT, MESSAGES])
def message(tag: Tag, *, requires: ConvertBy[str2list] = None) -> MessageRender:
    """
        Сообщение.

        ::

            │ <message>
            │     ... MESSAGE Scope ...
            │ </message>
            └── DOCUMENT/MESSAGES Scope

        Аргументы::

            <message[ requires: list[str]/>
            requires - Переменные окружения необходимые для отображения.
                Проверит наличие до parsing-а.

    """
    requires = requires or []

    if expected := set(requires) - set(tag.context.keys()):
        raise ParsingError(f'Template requires additional {expected} context variables')

    return MESSAGE.parse(tag.element, tag.context)


@register([MESSAGE, ELEMENT])
def template(tag: Tag, *, src: str, __rem: dict):
    """
        Встраивает набор элементов из шаблона.

        ::

            │ <template/>
            └── MESSAGE/ELEMENT Scope

        Аргументы::

            <template src: str{ arguments}/>
            src - Путь к файлу шаблона.
            arguments - Аргументы, требующиеся шаблону.

        Пример использования::

            template.xml
            │ <template requires="firstname,surname">
            │     <p> Привет, {surname} {firstname}! </p>
            │ </template>

            main.xml
            │ <message>
            │     <template src="template.xml" firstname="Иван" surname="Иванов"/>
            │ </message>

            Результат интерпретируется как:
            │ <message>
            │     <p> Привет, Иванов Иван! </p>
            │ </message>


    """

    from xml.dom import minidom
    document = minidom.parse(src)
    tmpl: minidom.Element = document.childNodes[0]

    # Enforcing correct syntax

    if tmpl.tagName != 'template':
        raise ParsingError(f'Expected template file at "{src}"')

    if unexpected := set(tmpl.attributes.keys()) - {'requires'}:
        raise ParsingError(f'{tag.element.tagName}: Got unexpected arguments {unexpected}')

    # Checking if there is any mismatch in required and provided arguments

    try:
        required = set(str2list(tmpl.attributes['requires'].value))
    except KeyError:
        required = set()
    provided = set(__rem)

    if unprovided := required - provided:
        raise ParsingError(f'{tag.element.tagName}: Arguments {unprovided} were expected, but not provided')
    if unexpected := provided - required:
        raise ParsingError(f'{tag.element.tagName}: Got unexpected arguments {unexpected}')

    # Processing template elements

    for element in tmpl.childNodes:
        tag.process(element, ReadOnlyDict(__rem))


SPACING_PATTERN = re.compile(r'\s+')


@register_text([MESSAGE, ELEMENT, NO_HTML])
def _text_(tag: Tag) -> BlockText:
    """ Не обрамлённый в теги текст """
    words = re.split(SPACING_PATTERN, tag.element.nodeValue)
    result = ' '.join(words).strip().format_map(tag.context)
    return InlineText(result)


@register([MESSAGE, ELEMENT])
def heading(tag: Tag) -> BlockText:
    """
        Заголовок. Содержимое переводится в верхний регистр
        и обрамляется в <b> теги.

        Тип текста: Block

        ::

            │ <heading/>
            │     ... NO_HTML Scope ...
            │ <heading/>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <heading> Hello! </heading>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<b>HELLO!</b>')

    """
    return BlockText(f'<b>{NO_HTML.parse(tag.element, tag.context).upper()}</b>')


@register([MESSAGE, ELEMENT])
def p(tag: Tag) -> BlockText:
    """
        Параграф.

        Тип текста: Block

        ::

            │ <p/>
            │     ... ELEMENT Scope ...
            │ <p/>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <p> Hello! </p>
            │     <p> Hello! </p>
            │     <p> Hello! </p>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('Hello!\\nHello!\\nHello!')

    """
    return BlockText(ELEMENT.parse(tag.element, tag.context))


@register([MESSAGE, ELEMENT])
def br(_) -> BlockText:
    """
        Пустая строка.

        Тип текста: Block

        ::

            │ <br/>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <p> Hello </p>
            │     <br/>
            │     <p> World! </p>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('Hello\\n\\nWorld!')

    """
    return BlockText()


@register([MESSAGE, ELEMENT])
def span(tag: Tag) -> InlineText:
    """
        Часть текста.

        Тип текста: Inline

        ::

            │ <span>
            │     ... ELEMENT Scope ...
            │ </span>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <span> Hello </span>
            │     <span> World! </span>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('Hello World!')

    """
    return InlineText(ELEMENT.parse(tag.element, tag.context))


@register([NO_HTML], name='span')
def span_no_html(tag: Tag) -> InlineText:
    """
        Часть no-html текста.

        Тип текста: Inline

        ::

            │ <span>
            │     ... NO_HTML Scope ...
            │ </span>
            └── NO_HTML Scope

        Пример использования::

            main.xml
            │ <message>
            │     <heading> Hello <span> World! </span> </heading>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<b>HELLO WORLD!</b>')

    """
    return InlineText(NO_HTML.parse(tag.element, tag.context))


@register([MESSAGE, ELEMENT])
def a(tag: Tag, *, href: str) -> InlineText:
    """
        Ссылка.

        Тип текста: Inline

        ::

            │ <a>
            │     ... NO_HTML Scope ...
            │ </a>
            └── MESSAGE/ELEMENT Scope

        Аргументы::

            <a href: str/>
            href - Web-ссылка.

        Пример использования::

            main.xml
            │ <message>
            │     <a href="www.google.com"> Search </a>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<a href="www.google.com">Search</a>')

    """
    return InlineText(f'<a href="{href}">{NO_HTML.parse(tag.element, tag.context)}</a>')


@register([MESSAGE, ELEMENT])
def b(tag: Tag) -> InlineText:
    """
        Жирный шрифт.

        Тип текста: Inline

        ::

            │ <b>
            │     ... ELEMENT Scope ...
            │ </b>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <b> Hello World! </b>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<b>Hello World!</b>')

    """
    return InlineText(f'<b>{ELEMENT.parse(tag.element, tag.context)}</b>')


@register([MESSAGE, ELEMENT])
def i(tag: Tag) -> InlineText:
    """
        Курсив.

        Тип текста: Inline

        ::

            │ <i>
            │     ... ELEMENT Scope ...
            │ </i>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <i> Hello World! </i>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<i>Hello World!</i>')

    """
    return InlineText(f'<i>{ELEMENT.parse(tag.element, tag.context)}</i>')


@register([MESSAGE, ELEMENT])
def u(tag: Tag) -> InlineText:
    """
        Подчёркнутый текст.

        Тип текста: Inline

        ::

            │ <u>
            │     ... ELEMENT Scope ...
            │ </u>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <u> Hello World! </u>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<u>Hello World!</u>')

    """
    return InlineText(f'<u>{ELEMENT.parse(tag.element, tag.context)}</u>')


@register([MESSAGE, ELEMENT])
def code(tag: Tag) -> InlineText:
    """
        Моноширинный копируемый текст.

        Тип текста: Inline

        ::

            │ <code>
            │     ... NO_HTML Scope ...
            │ </code>
            └── MESSAGE/ELEMENT Scope

        Пример использования::

            main.xml
            │ <message>
            │     <code> Hello World! </code>
            │ </message>

            >>> render('main.xml', {})
            MessageRender('<code>Hello World!</code>')

    """
    return InlineText(f'<code>{NO_HTML.parse(tag.element, tag.context)}</code>')


@register([MESSAGE])
def img(_, *, src: str) -> Union[ImageID, ImageFile]:
    """
        Изображение.

        ::

            │ <img/>
            └── MESSAGE Scope

        Аргументы::

            <img src: (str|InputFile)/>
            src - InputFile, File-ID или uri-изображения.

    """
    # InputFile can be provided via context vars
    if isinstance(src, InputFile):
        return ImageFile(src)

    if isinstance(src, str):
        return ImageID(src)

    raise ParsingError(f'img.src expected "str" or "InputFile", got "{type(src)}"')


@register([MESSAGE])
def anim(_, *, src: str) -> Union[AnimationID, AnimationFile]:
    """
        Анимация.

        ::

            │ <anim/>
            └── MESSAGE Scope

        Аргументы::

            <anim src: (str|InputFile)/>
            src - InputFile, File-ID или uri-анимации.

    """
    # InputFile can be provided via context vars
    if isinstance(src, InputFile):
        return AnimationFile(src)

    if isinstance(src, str):
        return AnimationID(src)

    raise ParsingError(f'anim.src expected "str" or "InputFile", got "{type(src)}"')


@register([MESSAGE], name='inline-keyboard')
def inline_keyboard(tag: Tag) -> InlineKeyboardMarkup:
    """
        Inline-клавиатура.

        ::

            │ <inline-keyboard>
            │     ... INLINE_KEYBOARD ...
            │ </inline-keyboard>
            └── MESSAGE Scope

    """
    layout = INLINE_KEYBOARD.parse(tag.element, tag.context)
    return InlineKeyboardMarkup(inline_keyboard=layout)


@register([INLINE_KEYBOARD], name='row')
def row_inline_keyboard(tag: Tag) -> KeyboardLayoutRow:
    """
        Строка inline-клавиатуры.

        ::

            │ <row>
            │     ... INLINE_KEYBOARD_ROW ...
            │ </row>
            └── INLINE_KEYBOARD Scope

    """
    return INLINE_KEYBOARD_ROW.parse(tag.element, tag.context)


@register([INLINE_KEYBOARD, INLINE_KEYBOARD_ROW], name='button')
def button_inline_keyboard(tag: Tag, *, text: str = None, url: str = None, callback_data: str = None,
                           web_app: WebAppInfo = None, login_url: LoginUrl = None,
                           switch_inline_query: str = None, switch_inline_query_current_chat: str = None,
                           callback_game: CallbackGame = None, pay: bool = False) \
        -> InlineKeyboardButton:
    """
        Кнопка inline-клавиатуры.

        ::

            │ <button>
            │     ... NO_HTML ...
            │ </button>
            └── INLINE_KEYBOARD/INLINE_KEYBOARD_ROW Scope

        Аргументы::

            <button[ text: str][ url: str][ callback_data: str][ web_app: WebAppInfo][ login_url: LoginUrl]
                [ switch_inline_query: str][ switch_inline_query_current_chat: str]
                [ callback_game: CallbackGame][ pay: bool]/>

    """

    if text is None:
        text = NO_HTML.parse(tag.element, tag.context)

    return InlineKeyboardButton(
        text=text, url=url, callback_data=callback_data, web_app=web_app, login_url=login_url,
        switch_inline_query=switch_inline_query, switch_inline_query_current_chat=switch_inline_query_current_chat,
        callback_game=callback_game, pay=pay
    )


@register([MESSAGE], name='reply-keyboard')
def reply_keyboard(tag: Tag, *, resize_keyboard: bool = None, one_time_keyboard: bool = None,
                   input_field_placeholder: str = None, selective: bool = None) -> ReplyKeyboardMarkup:
    """
        Reply-клавиатура.

        ::

            │ <reply-keyboard>
            │     ... REPLY_KEYBOARD ...
            │ </reply-keyboard>
            └── MESSAGE Scope

        Аргументы::

            <reply-keyboard[ resize_keyboard: bool][ one_time_keyboard: bool][ input_field_placeholder: str]
                [ selective: bool]/>

    """

    layout = REPLY_KEYBOARD.parse(tag.element, tag.context)
    return ReplyKeyboardMarkup(
        keyboard=layout, resize_keyboard=resize_keyboard, one_time_keyboard=one_time_keyboard,
        input_field_placeholder=input_field_placeholder, selective=selective
    )


@register([REPLY_KEYBOARD], name='row')
def row_reply_keyboard(tag: Tag) -> KeyboardLayoutRow:
    """
        Строка reply-клавиатуры.

        ::

            │ <row>
            │     ... REPLY_KEYBOARD_ROW ...
            │ </row>
            └── REPLY_KEYBOARD Scope

    """
    return REPLY_KEYBOARD_ROW.parse(tag.element, tag.context)


@register([REPLY_KEYBOARD, REPLY_KEYBOARD_ROW], name='button')
def button_reply_keyboard(tag: Tag, *, text: str = None, request_contact: bool = None, request_location: bool = None,
                          request_poll: KeyboardButtonPollType = None, web_app: WebAppInfo = None) -> KeyboardButton:
    """
        Кнопка reply-клавиатуры.

        ::

            │ <button>
            │     ... NO_HTML ...
            │ </button>
            └── REPLY_KEYBOARD/REPLY_KEYBOARD_ROW Scope

        Аргументы::

            <button[ text: str][ request_contact: bool][ request_location: bool]
                [ request_poll: KeyboardButtonPollType][ web_app: WebAppInfo]/>

    """

    if text is None:
        text = NO_HTML.parse(tag.element, tag.context)

    return KeyboardButton(
        text=text, request_contact=request_contact, request_location=request_location, request_poll=request_poll,
        web_app=web_app
    )
