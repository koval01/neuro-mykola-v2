from typing import List, Literal

from PIL.Image import Image
from aiogram import Router, F, Bot
from aiogram.types import Message

from aiogram_media_group import media_group_handler
from google.ai.generativelanguage_v1beta import Blob

from src.services import LLM
from src.utils import Media

router: Router = Router()


def sticker_mime(msg: Message) -> Literal["sticker/tgs", "sticker/webm"] | None:
    """
    Determines the MIME type of Telegram sticker based on its properties.

    Args:
        msg (Message): The Telegram message object containing a sticker.

    Returns:
        Literal["sticker/tgs", "sticker/webm"] | None:
            - "sticker/tgs" if the sticker is animated (TGS format).
            - "sticker/webm" if the sticker is a video sticker (WEBM format).
            - None if no sticker is present, or it's not of the above types.
    """
    match msg.sticker:
        case None:
            return None
        case sticker if sticker.is_animated:
            return "sticker/tgs"
        case sticker if sticker.is_video:
            return "sticker/webm"

    return None


MIME_TYPES = {
    'voice': 'audio/ogg',
    'audio': lambda msg: msg.audio.mime_type if msg.audio else None,
    'sticker': sticker_mime
}


def get_mime_type(message: Message) -> str:
    """Determine the MIME type of the media in the message."""
    mime_type = MIME_TYPES.get(message.content_type, lambda msg: None)
    return mime_type(message) if callable(mime_type) else mime_type


async def download_media(bot: Bot, message: Message) -> Image | Blob | None:
    """Download the media from the message and return the Media object."""
    media = getattr(message, message.content_type, None)
    if isinstance(media, list):
        media = media[-1]
    file_id = media.file_id
    mime_type = get_mime_type(message)
    return await Media.download(bot, file_id, mime=mime_type)


async def process_media_messages(messages: List[Message], bot: Bot, llm: LLM) -> None:
    """Process a list of media messages and send them to the LLM."""
    media_files = [await download_media(bot, msg) for msg in messages]
    await llm.answer(messages[0], additional_input=tuple(media_files))


@router.message(F.media_group_id, F.content_type.in_({'photo', 'audio'}))
@media_group_handler
async def album_handler(messages: List[Message], bot: Bot, llm: LLM) -> None:
    """Handle media group messages (albums)."""
    await process_media_messages(messages, bot, llm)


@router.message(F.content_type.in_({'photo', 'sticker', 'voice', 'audio'}))
async def media_handler(message: Message, bot: Bot, llm: LLM) -> None:
    """Handle individual media messages."""
    media_file = await download_media(bot, message)
    await llm.answer(message, additional_input=(media_file,))
