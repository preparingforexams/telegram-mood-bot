import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


class _DayOfWeek(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class MemeKind(Enum):
    photo = auto()
    video = auto()
    animation = auto()
    audio = auto()


@dataclass(frozen=True, kw_only=True)
class Meme:
    file_id: str
    kind: MemeKind


def get_meme(at_time: datetime) -> Meme | None:
    day_of_week = _DayOfWeek(at_time.weekday())
    candidates = _MEMES_BY_DAY.get(day_of_week)
    if not candidates:
        return None
    return random.choice(candidates)


_MEMES_BY_DAY = {
    _DayOfWeek.Monday: [
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAAM_YadeyBhYrgqfspOYJI2-"
            "Q0CJBKoAAmS1MRsbNeBI8OUMldl34gMBAAMCAAN4AAMiBA",
        ),
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAANDYxdkpr0njPmQiA1jUPJPyhoz04MAAom-"
            "MRt2lMFIay6HJVncG6kBAAMCAAN5AAMpBA",
        ),
    ],
    _DayOfWeek.Tuesday: [
        Meme(
            kind=MemeKind.animation,
            file_id="CgACAgQAAxkBAANBYxdhE8fUGGNR82Oh-IatiJM3m-gAAvkCAAKjsB1TKszbmqUkSXYpBA",
        ),
    ],
    _DayOfWeek.Wednesday: [
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAAM7YDZLM7l3_"
            "SDr5gU6Uui6HQzT0h0AAk2xMRt69rhJVqsnsDCWduc3tAeeLgADAQADAgADbQADfJACAAEeBA",
        ),
    ],
    _DayOfWeek.Thursday: [
        Meme(
            kind=MemeKind.animation,
            file_id="CgACAgIAAxkBAANEYzMf9xDKJ4ScYBT5JriNNV8L4aAAAiweAAIl4plJ4JCjKfT7dRUpBA",
        ),
    ],
    _DayOfWeek.Friday: [
        Meme(
            kind=MemeKind.audio,
            file_id="AwACAgIAAxkDAANeaQ23Qi7fZEBTFNwHgW_IVbk4olIAAlOAAALhXnBIApVGoujSZ882BA",
        ),
        # Meme(
        #     kind=MemeKind.video,
        #     file_id="BAACAgIAAxkBAAM8YE0YG3NVgZdCH__27kNYL4DTj5MAAnsLAAIFyWhKhR8KzjuNll4eBA",
        # ),
    ],
    _DayOfWeek.Sunday: [
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAANNaINuPaTrEVWJQxJyDiwdluPp4ikAAh3-MRsNR1FLHbovMdCNO-0BAAMCAAN5AAM2BA",
        ),
    ],
}
