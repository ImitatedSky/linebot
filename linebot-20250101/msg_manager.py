import json
from datetime import datetime

from firebase_manager import FirestoreDB

from linebot.exceptions import InvalidSignatureError

# is use from main import line_bot_api, handler

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


def msg_processing(body):
    """
    return reply_token, msg
    """
    try:
        # analysis body
        (
            reply_token,
            msg,
            is_mention,
            user_id,  # 誰傳的
            group_id,
            _today,
        ) = msg_analysis(body)

        if is_mention:
            mentionees = get_mentionees(is_mention)

            for mentionee in mentionees:
                if mentionee["isSelf"]:
                    # 對機器人@
                    pass
                else:
                    # 對其他人@
                    target = mentionee["userId"]
                    analysis_msg(target, msg)

        return "OK", 200
    except InvalidSignatureError:
        return


def msg_analysis(body):
    """
    retrun reply_token, msg, is_mention, user_id, gruop_id
    """
    try:
        json_data = json.loads(body)
        reply_token = json_data["events"][0]["replyToken"]  # 取得 reply token
        msg = json_data["events"][0]["message"]["text"]  # 取得 訊息
        is_mention = json_data["events"][0]["message"].get(
            "mention"
        )  # 如果有 mention 屬性
        user_id = json_data["events"][0]["source"]["userId"]
        gruop_id = json_data["events"][0]["source"]["groupId"]

        _today = datetime.today().strftime("%Y-%m-%d")  # 今天日期 yyyy-mm-dd

        return reply_token, msg, is_mention, user_id, gruop_id, _today
    except InvalidSignatureError:
        return


def get_mentionees(is_mention):
    if is_mention:
        return is_mention.get("mentionees")
    else:
        return None


def analysis_msg(target, msg):
    # 開始讀取訊息
    # 取得@後的訊息
    # dummy_text = "@dummyUser message"
    pass


def fetch_data(collection_name, doc_id):
    db = FirestoreDB(collection_name)
    # 讀取數據
    # db.read_document("2025-01-01-gid")
    return db.read_document(doc_id)


def create_doc(collection_name, doc_id, data):
    db = FirestoreDB(collection_name)

    # 寫入數據
    # db.write_document("2025-01-01", {"myname": {"count": 55, "finish": 45}, "myfriend": {"count": 99, "finish": 99}})
    db.write_document(doc_id, data)


rt, msg, is_mention, user_id, group_id, _today = msg_analysis(
    json.dumps(dummy_data)
)


print(rt)
print(msg)
print(is_mention["mentionees"])
print(user_id)
print(group_id)

print(type(rt))
print(type(is_mention))
