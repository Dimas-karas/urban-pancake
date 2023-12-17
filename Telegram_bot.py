# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 17:37:26 2023

@author: Mary
"""


#импорт библиотек
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.utils.markdown import hbold
from ultralytics import YOLO
from PIL import Image

from aiogram.fsm.context import FSMContext


from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from aiogram.fsm.state import StatesGroup, State

#FSM
class Form(StatesGroup):
    name = State()

#model
def load_model(path_to_model):
    return YOLO(path_to_model)

nano = load_model('C:/Users/Mary/.spyder-py3/defect_detect/Nano_final.pt')
small = load_model('C:/Users/Mary/.spyder-py3/defect_detect/Small_final.pt')
medium = load_model('C:/Users/Mary/.spyder-py3/defect_detect/Medium_final.pt')

def get_prediction(model,user,
                   path_to_images='example.bmp',
                   show_images=False,
                   save_images=False,
                   return_marks_dict=True,
                   ):
    results = model(path_to_images)

    def process_photo(image, result):
        im_array = result.plot()
        im = Image.fromarray(im_array[..., ::-1])
        if show_images:
            im.show()
        if save_images:
            im.save(f"{image.split('.')[0]}{user}_new.jpg")

        ans = [{'class': result.names[int(class_)],
                'x': int(xywh[0]),
                'y': int(xywh[1])}
                for class_, xywh in zip(result.boxes.cls, result.boxes.xywh)]
        
        return ans
        

    if isinstance(path_to_images, str):
        result = process_photo(path_to_images, results[0])
        if len(result) == 0:
            return 'Нет дефектов'
        
        ans = "На фото обнаружены следующие дефекты:\n"
        for mark in result:
            ans += f"{mark['class']} по координатам \n x: {mark['x']}, y: {mark['y']}\n"
        return ans

    marks_dict = {image: process_photo(image, r) for image, r in zip(path_to_images, results)}

    return marks_dict


# Bot token может быть получен у https://t.me/BotFather
TOKEN = 'TOKEN'

dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


#команда /start
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/start` command
    """
    main_kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Маленькая"),
                KeyboardButton(text="Средняя"),
                KeyboardButton(text="Большая"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите модель",
        selective=True
    )
    await state.set_state(Form.name)
    await message.answer(f"Здравствуйте, {hbold(message.from_user.full_name)}! Выберите пожалуйста модель, которая будет использоваться для детекции производственных дефектов. По умолчанию используется 'Средняя'.", reply_markup=main_kb)

#Хэндлер текста
@dp.message(F.text)
async def text_handler(message: types.Message, state: FSMContext) -> None:

    if (message.text=="Маленькая" or message.text=="Средняя" or message.text=="Большая"):
        await state.update_data(model_name=message.text)
        
    try:
        await message.answer("Пришлите, пожалуйста, фото для детекции производственных дефектов. Прикрепите фото как ДОКУМЕНТ, это улучшает качество детекции! Если Вы пользуетесь ботом в мобильном приложении, это можно сделать отправив его как файл. Чтобы выбрать модель, напишите команду /start")
    except TypeError:
        await message.answer("Пришлите, пожалуйста, фото для детекции производственных дефектов. Прикрепите фото как ДОКУМЕНТ, это улучшает качество детекции! Если Вы пользуетесь ботом в мобильном приложении, это можно сделать отправив его как файл. Чтобы выбрать модель, напишите команду /start")

#Хэндлер фото
@dp.message(F.photo)
async def handle_photo(message: types.Message) -> None:
    """
    Handler for processing photo messages
    """
    await message.answer('Пришлите, пожалуйста, файл без сжатия! Это повысит качество детекции. Прикрепите фото как ДОКУМЕНТ. Если Вы пользуетесь ботом в мобильном приложении, это можно сделать отправив его как файл.')

#Хэндлер документов        
@dp.message(F.document)
async def handle_doc(message: types.Message, state: FSMContext):
    document = message.document
    name = document.file_name
    await bot.download(document, destination=f'C:/Users/Mary/.spyder-py3/defect_detect/{name}')
    await message.answer('Детектирую дефекты...')
    
    # results = model(name)

    # for r in results:
    #     im_array = r.plot()  # plot a BGR numpy array of predictions
    #     im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
    #     im.save(f"{name.split('.')[0]}_new.jpg")
    
    user_choice = await state.get_data()
    print(user_choice)
    k=user_choice['model_name']
    if k == "Маленькая":
        model_type = nano
    elif k == "Средняя":
        model_type = small
    elif k == "Большая":
        model_type = medium
    else:
        model_type = small
    user = message.from_user.id
    results = get_prediction(model_type, user, name, show_images=False, save_images=True,)
    await message.answer(results)
    path_var = f"{name.split('.')[0]}{user}_new.jpg"
    photo = FSInputFile(path_var)
    await bot.send_photo(chat_id=message.chat.id, photo=photo)




async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())