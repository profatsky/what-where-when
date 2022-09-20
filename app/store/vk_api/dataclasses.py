from dataclasses import dataclass


@dataclass
class Action:
    type: str
    label: str
    payload: str


@dataclass
class Button:
    action: Action


@dataclass
class Keyboard:
    one_time: bool
    buttons: list[list[Button]]


@dataclass
class Message:
    peer_id: int
    text: str
    keyboard: Keyboard | None
    attachment: str | None


@dataclass
class UpdateObject:
    id: int
    user_id: int
    peer_id: int
    body: str
    event_type: str


@dataclass
class Update:
    type: str
    object: UpdateObject
