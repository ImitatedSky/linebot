
import json

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage


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
                     "isSelf": False
                  }
               ]
            }
         },
         "timestamp": 1735638940592,
         "source": {
            "type": "group",
            "groupId": "Cabcdef123456",
            "userId": "U0987654321abcdef"
         },
         "replyToken": "randomreplytoken123456"
      }
   ]
}




def msg_analysis(body):
    '''
    retrun reply_token, msg, is_mention, user_id, gruop_id
    '''
    try:
        json_data = json.loads(body)
        reply_token = json_data["events"][0][
            "replyToken"
        ]  # 取得 reply token
        msg = json_data["events"][0]["message"]["text"]  # 取得 訊息
        is_mention = json_data["events"][0]["message"].get("mention") # 如果有 mention 屬性
        user_id = json_data["events"][0]["source"]["userId"]
        gruop_id = json_data["events"][0]["source"]["groupId"]

        return reply_token, msg, is_mention, user_id, gruop_id
    except InvalidSignatureError as e:
        return 
    
def get_mentionees(is_mention):
    if is_mention:
        return is_mention.get("mentionees")
    else:
        return None
    
rt , msg , is_mention , user_id , group_id = msg_analysis(json.dumps(dummy_data))


print(rt)
print(msg)
print(is_mention["mentionees"])
print(user_id)
print(group_id)

print(type(rt))
print(type(is_mention))