from typing import Union

from django.contrib.auth.models import AnonymousUser

from apps.user.models import Account
from apps.chat.models import Chatroom


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
