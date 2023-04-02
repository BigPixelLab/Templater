""" ... """
import dataclasses
import typing

import aiogram.types
import aiogram.exceptions


@dataclasses.dataclass
class MessageRender:
    """ ... """
    text: str
    photo: typing.Optional[typing.Union[str, aiogram.types.InputFile]] = None
    animation: typing.Optional[typing.Union[str, aiogram.types.InputFile]] = None
    keyboard: typing.Optional[typing.Union[aiogram.types.InlineKeyboardMarkup,
                                           aiogram.types.ReplyKeyboardMarkup]] = None

    def validate(self):
        """ ... """
        if self.photo and self.animation:
            raise ValueError('Message can not contain both a photo and an animation at the same time')

    async def send(self, chat_id: int, bot: aiogram.Bot = None):
        """ Отправляет сообщение в указанный чат """

        self.validate()

        bot = bot or aiogram.Bot.get_current()
        config = {}

        if self.keyboard:
            config['reply_markup'] = self.keyboard

        if self.photo:
            if self.text:
                config['caption'] = self.text

            message = await bot.send_photo(
                chat_id,
                photo=self.photo,
                **config
            )

            return message

        if self.animation:
            if self.text:
                config['caption'] = self.text

            message = await bot.send_animation(
                chat_id,
                animation=self.animation,
                **config
            )

            return message

        if self.text:
            config['text'] = self.text

        return await bot.send_message(chat_id, **config)

    async def edit(self, message: aiogram.types.Message, bot: aiogram.Bot = None):
        """ Редактирует указанное сообщение """

        self.validate()

        bot = bot or aiogram.Bot.get_current()
        config = {}

        if self.keyboard:
            config['reply_markup'] = self.keyboard

        if not message.photo and not message.animation and self.text:
            return await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=self.text,
                **config
            )

        if self.photo and message.photo:
            message = await bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.message_id,
                media=aiogram.types.InputMediaPhoto(
                    media=self.photo,
                    caption=self.text
                ),
                **config
            )

            return message

        elif self.animation and message.animation:
            message = await bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.message_id,
                media=aiogram.types.InputMediaAnimation(
                    media=self.animation,
                    caption=self.text
                ),
                **config
            )

            return message

        elif self.photo or self.animation:
            raise ValueError('Render must have the same media type as a message')

        return await bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.message_id,
            caption=self.text,
            **config
        )


class MessageRenderList(list[MessageRender]):
    """ ... """

    async def send(self, chat_id: int, bot: aiogram.Bot = None) -> list[typing.Optional[aiogram.types.Message]]:
        """ Отправляет все сообщения в указанный чат """
        sent_messages = []
        for message in self:
            try:
                sent_message = await message.send(chat_id, bot=bot)
            except aiogram.exceptions.TelegramForbiddenError:
                sent_message = None
            sent_messages.append(sent_message)
        return sent_messages

    def extract(self) -> typing.Optional[MessageRender]:
        """ Если список содержит единственное сообщение - возвращает его.
           None если пусто и ошибка, если больше одного """
        if len(self) == 1:
            return self[0]
        if not self:
            return
        raise ValueError('Can not extract from MessageRenderList, '
                         'because it contains more than one MessageRender')


__all__ = (
    'MessageRender',
    'MessageRenderList'
)
