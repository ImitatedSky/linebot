import json
import os
from datetime import datetime

from firebase_manager import FirestoreDB

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError

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

        print(f"Time: {datetime.now()}, body: {body}")

        if msg.startswith("#add"):
            # 加入群組
            create_or_update_group_data(group_id, user_id)
            return reply_token, "已更新群組資料."

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
                        return reply_token, f"已處理訊息: {new_msg}"

        # 如果startwith是今天
        if msg.startswith(tuple(today_type)):
            data = get_today_count(group_id)
            return reply_token, f"今日統計:\n {data}"

        # 去除空白
        msg = msg.strip()

        # 如果開頭是 + 或 -
        if msg.startswith("+"):
            num = int(msg[1:])
            update_count(user_id, group_id, num)
        elif msg.startswith("-"):
            num = int(msg[1:])
            update_finish(user_id, group_id, num)

        return reply_token, f"已處理訊息: {msg}"
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

        _today = datetime.today().strftime("%Y-%m-%d")  # 今天日期 yyyy-mm-dd

        return reply_token, msg, is_mention, user_id, group_id, _today
    except InvalidSignatureError:
        return None


def get_user_profile(user_id, group_id):
    try:
        # 沒認證過的官方帳號不能主動抓沒加機器人的群組成員資料
        profile = line_bot_api.get_profile(user_id)
        # print(f"Display name: {profile.display_name}, User ID: {profile.user_id}")

    except Exception as e:
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
    data = group_db.read_document(group_id)

    if data:
        user_name = get_user_profile(user_id, group_id).display_name
        if user_name not in data:
            data[user_id] = {"name": user_name}
            group_db.update_document(group_id, data)
    else:
        user_name = get_user_profile(user_id, group_id).display_name
        data = {user_id: {"name": user_name}}
        create_doc("group", group_id, data)


def update_count(user_id, group_id, num):
    _today = datetime.today().strftime("%Y-%m-%d")
    doc_id = f"{_today}-{group_id}"
    data = fetch_data("count", doc_id)
    user_name = get_user_profile(user_id, group_id).display_name

    if data:
        number = data.get(user_name, {}).get("count", 0)
        finish = data.get(user_name, {}).get("finish", 0)
        data[user_name] = {"count": number + num, "finish": finish}
    else:
        data = {user_name: {"count": num, "finish": 0}}
        create_doc("count", doc_id, data)

    update_doc("count", doc_id, data)


def update_finish(user_id, group_id, num):
    _today = datetime.today().strftime("%Y-%m-%d")
    doc_id = f"{_today}-{group_id}"
    data = fetch_data("count", doc_id)
    user_name = get_user_profile(user_id, group_id).display_name

    if data:
        number = data.get(user_name, {}).get("count", 0)
        finish = data.get(user_name, {}).get("finish", 0)
        data[user_name] = {"count": number, "finish": finish + num}
    else:
        data = {user_name: {"count": 0, "finish": num}}
        create_doc("count", doc_id, data)

    update_doc("count", doc_id, data)


def update_all_counts(group_id, num):
    print(f"log: update_all_counts function")
    _today = datetime.today().strftime("%Y-%m-%d")
    doc_id = f"{_today}-{group_id}"
    data = fetch_data("count", doc_id)

    group_data = get_all_group_members(group_id)

    if not data:
        data = {}

    for user_id, user_info in group_data.items():
        user_name = user_info["name"]
        count = data.get(user_name, {}).get("count", 0)
        finish = data.get(user_name, {}).get("finish", 0)
        data[user_name] = {"count": count + num, "finish": finish}
    print(f"log: update_all_counts data: {data}")
    update_doc("count", doc_id, data)
    print(f"log: update_all_counts done")


def get_all_group_members(group_id):
    """
    return dict
    ex: {'id1': {'name': 'name1'}, 'id2': {'name': 'name2'}}
    """
    group_db = FirestoreDB("group")
    members = group_db.read_document(group_id)
    return members


def get_today_count(group_id):
    """
    獲取當天的計數
    return dict
    ex: {'user1': {'count': 10, 'finish': 2}, 'user2': {'count': 5, 'finish': 1}}
    """
    _today = datetime.today().strftime("%Y-%m-%d")
    doc_id = f"{_today}-{group_id}"
    data = fetch_data("count", doc_id)

    # 更好觀看的格式
    if data:
        result = ""
        for user, info in data.items():
            result += f"{user}: {info}\n"
        return result
    else:
        return "今日尚無任何紀錄"
