# How to use:

```xml
<message>
    <img src="[url-here]"/>
    
    <heading> WELCOME </heading>
    <br/>
    <p> This is an example of what this templater can do </p>
    <br/>
    <p for="i in range(count)"> 
        Try to change "count" in context #{i}
    </p>
    <p if="not count"> Ok, now there is nothing... </p>
    
    <inline-keyboard>
        <button callback_data="delete"> Ok. </button>
    </inline-keyboard>
</message>
```

```python
import template
from template_for_aiogram import aiogram_syntax

template.set_default_syntax(aiogram_syntax)

msg = template.render('example.xml', {'count': 3})
```

Designed to be used with aiogram

```python
import asyncio

import aiogram
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message

import template
from template_for_aiogram import aiogram_syntax


storage = MemoryStorage()
dispatcher = aiogram.Dispatcher(storage)
bot = aiogram.Bot(token='token', parse_mode='HTML')


@dispatcher.message(Command(commands=['start']))
async def start_handler(message: Message):
    msg = template.render('example.xml', {'count': 3})
    await msg.send()


async def main():
    template.set_default_syntax(aiogram_syntax)
    await dispatcher.start_polling(bot)
    
asyncio.run(main())
```

To see how you can extend its functionality check `templater_for_aiogram`
