from collections import namedtuple
from dataclasses import dataclass
from enum import Enum


class DayOfWeek(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


MemeKindParams = namedtuple("MemeKindParams", ["body_key", "method"])


class MemeKind(MemeKindParams, Enum):
    photo = MemeKindParams("photo", "sendPhoto")
    video = MemeKindParams("video", "sendVideo")
    animation = MemeKindParams("animation", "sendAnimation")


@dataclass
class Meme:
    file_id: str
    kind: MemeKind


_MEMES_BY_DAY = {
    DayOfWeek.Monday: [
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
    DayOfWeek.Tuesday: [
        Meme(
            kind=MemeKind.animation,
            file_id="CgACAgQAAxkBAANBYxdhE8fUGGNR82Oh-IatiJM3m-gAAvkCAAKjsB1TKszbmqUkSXYpBA",
        ),
    ],
    DayOfWeek.Wednesday: [
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAAM7YDZLM7l3_"
                    "SDr5gU6Uui6HQzT0h0AAk2xMRt69rhJVqsnsDCWduc3tAeeLgADAQADAgADbQADfJACAAEeBA",
        ),
    ],
    DayOfWeek.Thursday: [
        Meme(
            kind=MemeKind.animation,
            file_id="CgACAgIAAxkBAANEYzMf9xDKJ4ScYBT5JriNNV8L4aAAAiweAAIl4plJ4JCjKfT7dRUpBA",
        ),
    ],
    DayOfWeek.Friday: [
        Meme(
            kind=MemeKind.video,
            file_id="BAACAgIAAxkBAAM8YE0YG3NVgZdCH__27kNYL4DTj5MAAnsLAAIFyWhKhR8KzjuNll4eBA",
        ),
    ],
}
