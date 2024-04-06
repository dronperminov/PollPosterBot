import json
import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    chat_id: int
    is_stopped: bool
    title: str
    options: List[str]
    weekday: int
    time: str

    @classmethod
    def from_json(cls: "Config", data: dict) -> "Config":
        return Config(
            chat_id=data["chat_id"],
            is_stopped=data.get("is_stopped", True),
            title=data.get("title", "Придёшь завтра на игры?"),
            options=data.get("options", ["Да", "Нет", "+/-"]),
            weekday=data.get("weekday", 3),
            time=data.get("time", "10:00")
        )

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "is_stopped": self.is_stopped,
            "title": self.title,
            "options": self.options,
            "weekday": self.weekday,
            "time": self.time
        }

    def weekday_text(self) -> str:
        return ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"][self.weekday]

    @staticmethod
    def read(path: str) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            return Config.from_json(json.load(f))

    def save(self, save_dir: str = "configs") -> None:
        with open(os.path.join(save_dir, f"config_{self.chat_id}.json"), "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
