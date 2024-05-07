import uuid


def uuid4_generator(length: int) -> str:
    return uuid.uuid4().hex[:length]
