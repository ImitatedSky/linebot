import json
import os
from datetime import datetime

import pytz
from firebase_manager import FirestoreDB

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError

timezone = pytz.timezone("Asia/Taipei")
# 使用 main.py 中的 line_bot_api 和 handler
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))

dummy_data = {
    "destination": "U1234567890abcdef",
    "events": [
        {
            "type": "message",
            "message": {
                "type": "text",
                "id": "1234567890",
                "text": "@dummyUser message",
                "mention": {
                    "mentionees": [
                        {
                            "index": 0,
                            "length": 9,
                            "userId": "Uabcdef123456",
                            "type": "user",
                            "isSelf": False,
                        }
                    ]
                },
            },
            "timestamp": 1735638940592,
            "source": {
                "type": "group",
                "groupId": "Cabcdef123456",
                "userId": "U0987654321abcdef",
            },
            "replyToken": "randomreplytoken123456",
        }
    ],
}

today_type = ["Today", "today", "TOday", "TODay", "TODAy", "TODAY", "今天", "今日"]
total_type = ["Total", "total", "TOtal", "TOTal", "TOTA", "TOTAL", "全部", "總計"]


def msg_processing(body):
    """
    回傳 reply_token, msg
    """
    try:
        # 分析 body
        (
            reply_token,
            msg,
            is_mention,
            user_id,  # 誰傳的
            group_id,
            _today,
        ) = msg_analysis(body)

        # print(f"Time: {datetime.now()}, body: {body}")

        if msg.startswith("#add"):
            # 加入群組
            create_or_update_group_data(group_id, user_id)
            return (
                reply_token,
                f"已加入群組,\n members:\n {get_all_group_members(group_id)}",
            )

        _today = datetime.now(timezone).strftime("%Y-%m-%d")
        # 如果有 @mention
        if is_mention:
            mentionees = get_mentionees(is_mention)
            for mentionee in mentionees:
                if mentionee["isSelf"]:
                    # 對機器人@
                    pass
                elif mentionee["type"] == "all":
                    print(f"@all: {msg}")
                    # 對全體@
                    if len(msg.split()) > 1:  # 檢查 msg.split() 的長度
                        new_msg = msg.split()[1]
                        if new_msg.startswith("+"):
                            print(f"log: update_all_counts")
                            num = int(new_msg[1:])
                            update_all_counts(group_id, num)
                elif mentionee["type"] == "user":
                    # 對其他人@
                    target = mentionee["userId"]
                    new_msg = msg.split()[1]
                    if new_msg.startswith("+"):
                        num = int(new_msg[1:])
                        update_count(target, group_id, num)
                    elif new_msg.startswith("-"):
                        num = int(new_msg[1:])
                        update_finish(target, group_id, num)
                    else:
                        return (
                            reply_token,
                            f"今日統計({_today}):\n {get_today_count(group_id)}",
                        )

        # 如果startwith是今天
        if msg.startswith(tuple(today_type)):
            data = get_today_count(group_id)
            return reply_token, f"今日統計({_today}):\n {data}"
        if msg.startswith(tuple(total_type)):
            data = get_total_count(group_id)
            return reply_token, f"總計:\n {data}"

        # 去除空白
        msg = msg.strip()

        # 如果開頭是 + 或 -
        if msg.startswith("+"):
            num = int(msg[1:])
            update_count(user_id, group_id, num)
        elif msg.startswith("-"):
            num = int(msg[1:])
            update_finish(user_id, group_id, num)

        return reply_token, f"今日統計({_today}):\n {get_today_count(group_id)}"
    except InvalidSignatureError:
        return None


def msg_analysis(body):
    """
    回傳 reply_token, msg, is_mention, user_id, group_id, _today
    """
    try:
        json_data = json.loads(body)
        reply_token = json_data["events"][0]["replyToken"]  # 取得 reply token
        msg = json_data["events"][0]["message"]["text"]  # 取得 訊息
        is_mention = json_data["events"][0]["message"].get(
            "mention"
        )  # 如果有 mention 屬性
        user_id = json_data["events"][0]["source"]["userId"]
        group_id = json_data["events"][0]["source"]["groupId"]

        # _today = datetime.today().strftime("%Y-%m-%d")  # 今天日期 yyyy-mm-dd
        _today = datetime.now(timezone).strftime("%Y-%m-%d")  # 今天日期 yyyy-mm-dd

        return reply_token, msg, is_mention, user_id, group_id, _today
    except InvalidSignatureError:
        return None


def get_user_profile(user_id, group_id):
    try:
        # 沒認證過的官方帳號不能主動抓沒加機器人的群組成員資料
        profile = line_bot_api.get_profile(user_id)
        # print(f"Display name: {profile.display_name}, User ID: {profile.user_id}")

    except Exception:
        # print(f"get_profile error: {e}")
        # 改抓群組成員資料
        profile = line_bot_api.get_group_member_profile(group_id, user_id)

    return profile


def get_mentionees(is_mention):
    if is_mention:
        return is_mention.get("mentionees")
    else:
        return None


def fetch_data(collection_name, doc_id):
    db = FirestoreDB(collection_name)
    # 讀取數據
    return db.read_document(doc_id)


def create_doc(collection_name, doc_id, data):
    db = FirestoreDB(collection_name)
    # 寫入數據
    db.write_document(doc_id, data)


def update_doc(collection_name, doc_id, data):
    db = FirestoreDB(collection_name)
    # 更新數據
    db.update_document(doc_id, data)


def create_or_update_group_data(group_id, user_id):
    group_db = FirestoreDB("group")
    group_data = group_db.read_document(group_id)

    user_name = get_user_profile(user_id, group_id).display_name

    if not group_data:
        # 如果 group document 不存在，創建它
        group_data = {}
        create_doc("group", group_id, group_data)

    # 確保 groupmember collection 存在
    groupmember_data = group_db.read_document(
        f"{group_id}/groupmember/{user_id}"
    )
    if not groupmember_data:
        # 如果成員 document 不存在，創建它
        groupmember_data = {
            "name": user_name,
            "total_counts": 0,
            "finish_counts": 0,
        }
        create_doc(f"group/{group_id}/groupmember", user_id, groupmember_data)


def update_count(user_id, group_id, num):
    _today = datetime.now(timezone).strftime("%Y-%m-%d")
    doc_id = f"{_today}"
    data = fetch_data("group", f"{group_id}")
    user_name = get_user_profile(user_id, group_id).display_name

    groupmember_data = fetch_data(f"group/{group_id}/groupmember", user_id)

    if not data:
        data = {}

    if doc_id in data:
        if user_name in data[doc_id]:
            data[doc_id][user_name]["count"] += num
        else:
            data[doc_id][user_name] = {"count": num, "finish": 0}
    else:
        data[doc_id] = {user_name: {"count": num, "finish": 0}}

    groupmember_data["total_counts"] += num

    update_doc(f"group/{group_id}/groupmember", user_id, groupmember_data)
    update_doc("group", f"{group_id}", data)


def update_finish(user_id, group_id, num):
    _today = datetime.now(timezone).strftime("%Y-%m-%d")
    doc_id = f"{_today}"
    data = fetch_data("group", f"{group_id}")
    user_name = get_user_profile(user_id, group_id).display_name

    groupmember_data = fetch_data(f"group/{group_id}/groupmember", user_id)

    if not data:
        data = {}

    if doc_id in data:
        if user_name in data[doc_id]:
            data[doc_id][user_name]["finish"] += num
        else:
            data[doc_id][user_name] = {"count": 0, "finish": num}
    else:
        data[doc_id] = {user_name: {"count": 0, "finish": num}}

    groupmember_data["finish_counts"] += num

    update_doc(f"group/{group_id}/groupmember", user_id, groupmember_data)
    update_doc("group", f"{group_id}", data)


def update_all_counts(group_id, num):
    print(f"log: update_all_counts function")
    _today = datetime.now(timezone).strftime("%Y-%m-%d")
    doc_id = f"{_today}"
    data = fetch_data("group", f"{group_id}")

    group_data = get_all_group_members(group_id)

    if not data:
        data = {}

    for user_id, user_info in group_data.items():
        user_name = user_info["name"]
        groupmember_data = user_info

        if doc_id in data:
            if user_name in data[doc_id]:
                data[doc_id][user_name]["count"] += num
            else:
                data[doc_id][user_name] = {"count": num, "finish": 0}
        else:
            data[doc_id] = {user_name: {"count": num, "finish": 0}}

        groupmember_data["total_counts"] += num

        update_doc(f"group/{group_id}/groupmember", user_id, groupmember_data)
    update_doc("group", f"{group_id}", data)


def get_all_group_members(group_id):
    """
    return dict
    ex: {'id1': {'name': 'name1', 'total_counts': 100, 'finish_counts': 90}, ...}
    """
    group_db = FirestoreDB(f"group/{group_id}/groupmember")

    return group_db.read_collection()


def get_today_count(group_id):
    _today = datetime.now(timezone).strftime("%Y-%m-%d")
    doc_id = f"{_today}"
    data = fetch_data("group", f"{group_id}")

    if doc_id in data:
        result = ""
        for user, info in data[doc_id].items():
            result += f"{user}: {info}\n"
        return result
    else:
        return "今日尚無任何紀錄"


def get_total_count(group_id):
    group_db = FirestoreDB(f"group/{group_id}/groupmember")
    data = group_db.read_collection()

    result = ""
    for userid, info in data.items():
        result += f"{userid}: {info}\n"
    return result
