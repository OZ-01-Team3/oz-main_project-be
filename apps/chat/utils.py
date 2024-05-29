import base64
import json
import logging
from typing import Any, Optional, Union

import redis
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django_redis import get_redis_connection

from apps.chat.models import Chatroom, Message
from apps.user.models import Account

logger = logging.getLogger(__name__)
redis_conn = get_redis_connection("default")


def check_entered_chatroom(chatroom: Chatroom, user: Union[Account, AnonymousUser]) -> bool:
    """
    만약 유저가 borrower이면 borrower_status의 값을 반환해서 채팅방에 존재하는지 나갔는지를 판단
    만약 유저가 lender이면 lender_status의 값을 반환해서 채팅방에 존재하는지 나갔는지를 판단
    유저가 둘다 속하지 않는다면 잘못된 접근으로 판단하고 False를 반환
    """
    if chatroom.borrower == user:
        return chatroom.borrower_status
    elif chatroom.lender == user:
        return chatroom.lender_status
    else:
        return False


def change_entered_status(chatroom: Chatroom, user: Union[Account, AnonymousUser]) -> None:
    """
    채팅방에 참여해 있는 유저의 역할을 파악하고, 그에 맞는 status를 False로 변경(False는 나가기한 상태)
    """
    if chatroom.borrower == user:
        chatroom.borrower_status = False
    if chatroom.lender == user:
        chatroom.lender_status = False
    chatroom.save()


def delete_chatroom(chatroom: Chatroom) -> bool:
    """
    채팅방에 참여한 둘 중 한명이라도 나간 상태라면,
    해당 유저가 나가기를 눌렀을 때 채팅방에 남아있는 유저가 없기 때문에 채팅방을 삭제함.
    """
    if not chatroom.borrower_status or not chatroom.lender_status:
        chatroom.delete()
        return True
    return False


def check_opponent_online(chat_group_name: str) -> bool:
    """django-redis를 사용해서 그룹에 속한 멤버의 수를 가져옴"""
    redis_conn = get_redis_connection("default")
    if redis_conn.zcard(f"asgi:group:{chat_group_name}") == 2:
        return True
    return False


def get_group_name(chatroom_id: int) -> str:
    # 채팅방 id를 사용하여 고유한 그룹 이름 구성
    return f"chat_{chatroom_id}"


def decode_image(image_data: str) -> ContentFile[Any]:
    # Base64 문자열 디코딩
    format, imgstr = image_data.split(";base64,")
    ext = format.split("/")[-1]

    return ContentFile(base64.b64decode(imgstr), name="image." + ext)


def cashe_set_chat_message(chat_group_name: str, data: dict[str, Any]) -> None:
    # Redis에 메시지를 json형식으로 직렬화하여 저장
    try:
        key = f"{chat_group_name}_messages"
        redis_conn.lpush(key, json.dumps(data))
    except Exception as e:
        raise ValueError(str(e))


def save_redis_to_postgres(chat_group_name: str) -> None:
    # 메시지 수가 100개를 초과하면 저장된 메시지를 역직렬화해서 불러온 뒤 DB에 저장
    key = f"{chat_group_name}_messages"

    with redis_conn.pipeline() as pipe:
        while True:
            try:
                # watch로 모니터링 시작
                pipe.watch(key)
                if pipe.llen(key) > 100:
                    messages = [json.loads(msg) for msg in pipe.lrange(key, 0, -1)]
                    for msg in messages:
                        # 메시지 데이터에 이미지가 존재하면 디코딩 후 파일로 변환해서 db의 image필드로 s3에 저장될 수 있도록함
                        if "image" in msg:
                            msg["image"] = decode_image(msg["image"])
                        msg.pop("nickname", None)
                    bulk_messages = [Message(**msg) for msg in messages]
                    # 트랜잭션 시작
                    with transaction.atomic():
                        Message.objects.bulk_create(bulk_messages)
                        # 데이터베이스에 저장되고나면 redis에 남은 메시지들을 지움
                        pipe.delete(key)
                break
            except redis.WatchError as e:
                logger.error("예외 발생: %s", e, exc_info=True)
                continue
            except Exception as e:
                logger.error("예외 발생: %s", e, exc_info=True)
                break


def save_remaining_messages_to_postgres(chat_group_name: str) -> None:
    # Redis에서 남은 메시지 가져와 DB에 저장
    key = f"{chat_group_name}_messages"
    remaining_messages = redis_conn.lrange(key, 0, -1)
    if remaining_messages:
        messages = [json.loads(msg) for msg in remaining_messages]
        for msg in messages:
            # 메시지 데이터에 이미지가 존재하면 디코딩 후 파일로 변환해서 db의 image필드로 s3에 저장될 수 있도록함
            if msg.get("image"):
                msg["image"] = decode_image(msg["image"])
            msg.pop("nickname", None)
        bulk_messages = [Message(**msg) for msg in messages]
        Message.objects.bulk_create(bulk_messages)

    # Redis 캐시 삭제
    redis_conn.delete(key)


def get_last_message(chatroom_id: int) -> Optional[dict[str, Any]]:
    key = f"{get_group_name(chatroom_id)}_messages"
    # 만약 redis에 채팅 메시지가 존재하면 레디스에서 마지막 채팅내용을 가져옴
    if redis_conn.exists(key):
        stored_last_message = redis_conn.lrange(key, -1, -1)
        last_message: dict[str, Any] = json.loads(stored_last_message[0])

        return last_message
    # redis에 채팅내용이없으면 데이터베이스에서 마지막 채팅내용을 가져옴
    messages = Message.objects.filter(chatroom_id=chatroom_id)
    if messages:
        from apps.chat.serializers import MessageSerializer

        return MessageSerializer(messages.order_by("-created_at").first()).data

    return None


def get_chatroom_message(chatroom_id: int) -> Any:
    from apps.chat.serializers import MessageSerializer

    key = f"{get_group_name(chatroom_id)}_messages"
    if redis_conn.exists(key):
        stored_message_num = redis_conn.llen(key)
        # 레디스에 저장된 메시지가 30개가 넘으면 가장 마지막에 저장된 메시지부터 30개를 가져옴
        if stored_message_num >= 30:
            stored_messages = redis_conn.lrange(key, 0, 29)
            messages = [json.loads(msg) for msg in stored_messages]
            return messages

        # 30개가 넘지않으면 레디스에 저장된 메시지들을 가져오고
        stored_messages = redis_conn.lrange(key, 0, stored_message_num - 1)
        messages = [json.loads(msg) for msg in stored_messages]

        # 데이터베이스에서 30 - stored_message_num을 뺀 개수만큼 가져옴
        db_messages = Message.objects.filter(chatroom_id=chatroom_id).order_by("-created_at")

        # db에 저장된 메시지가 없으면 레디스에 캐싱된 메시지만 가져옴
        if not db_messages.exists():
            return messages

        # 디비에 저장된 메시지가 30-stored_message_num 보다 많으면 슬라이싱해서 필요한 만큼의 데이터를 가져옴
        if len(db_messages) >= 30 - stored_message_num:
            serialized_messages = MessageSerializer(db_messages[: 30 - stored_message_num], many=True).data
            return messages + serialized_messages

        # 디비에 저장된 메시지가 30-stored_message_num 보다 적으면 db에 저장된 채팅방의 모든 메시지를 가져옴
        serialized_messages = MessageSerializer(db_messages, many=True).data
        return messages + serialized_messages

    # 레디스에 해당 채팅방 그룹 네임으로 지정된 키값이 없으면 데이터베이스에서 채팅 메시지를 가져옴
    db_messages = Message.objects.filter(chatroom_id=chatroom_id)
    if db_messages:
        if db_messages.count() >= 30:
            serialized_messages = MessageSerializer(db_messages[:30], many=True).data
            return serialized_messages

        serialized_messages = MessageSerializer(db_messages, many=True).data
        return serialized_messages

    # 어디에도 데이터가 존재하지않으면 None을 반환
    return None


def read_messages_at_postgres(user_id: int, chatroom_id: int) -> None:
    """
    postgres db에 저장된 메시지들 중 읽음상태가 아닌 것들을 읽음처리
    """
    messages = Message.objects.filter(~Q(sender_id=user_id), chatroom_id=chatroom_id)
    if messages:
        # bulk_update 메서드를 사용하여 한 번에 여러 개체를 업데이트, 안읽은 메시지들을 읽음처리
        filter_condition = Q(status=True, id__in=messages.values_list("id", flat=True))
        Message.objects.filter(filter_condition).update(status=False)


def read_messages_at_redis(nickname: str, chatroom_id: int) -> None:
    """
    redis에 저장된 메시지들 중 읽음상태가 아닌 것들을 읽음처리
    메시지를 읽음 처리 중에 다른 메시지가 입력되면 메시지의 순서가 보장되지 않기 때문에
    하나의 트랜잭션으로 키를 지우는것과 다시 입력하는 것을 묶음
    """
    key = f"{get_group_name(chatroom_id=chatroom_id)}_messages"
    if redis_conn.exists(key):
        with redis_conn.pipeline() as pipe:
            while True:
                try:
                    # WATCH를 사용하여 키를 모니터링
                    pipe.watch(key)
                    # MULTI 시작
                    pipe.multi()

                    # 메시지 가져오기
                    stored_messages = redis_conn.lrange(key, 0, -1)
                    messages = [json.loads(msg) for msg in stored_messages]

                    # 메시지 업데이트
                    for msg in messages:
                        if msg["status"] and msg["nickname"] != nickname:
                            msg["status"] = False

                    # 기존 키 삭제
                    pipe.delete(key)
                    # 업데이트된 메시지 다시 저장
                    for msg in messages:
                        pipe.rpush(key, json.dumps(msg))

                    # 트랜잭션 실행
                    pipe.execute()
                    break
                except redis.WatchError as e:
                    logger.error("예외 발생: %s", e, exc_info=True)
                    continue
                except Exception as e:
                    logger.error("예외 발생: %s", e, exc_info=True)
                    break


def get_unread_message_count_at_redis(chatroom_id: int, nickname: str) -> int:
    key = f"{get_group_name(chatroom_id=chatroom_id)}_messages"
    count = 0
    if redis_conn.exists(key):
        stored_messages = redis_conn.lrange(key, 0, -1)
        messages = [json.loads(msg) for msg in stored_messages]
        for msg in messages:
            if msg["status"] and msg["nickname"] != nickname:
                count += 1

    return count
