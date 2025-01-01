# google cloud function: linebot-default

import base64
import hashlib
import hmac
import json
import os

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TextSendMessage

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
channel_secret = os.environ.get("CHANNEL_SECRET")
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))


def linebot(request):
    if request.method == "POST":
        if "X-Line-Signature" not in request.headers:
            return "Error: Invalid source", 403
        else:
            # get X-Line-Signature header value
            x_line_signature = request.headers["X-Line-Signature"]

            # get body value
            body = request.get_data(as_text=True)
            # print(body)

            # decode body
            hash = hmac.new(
                channel_secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            signature = base64.b64encode(hash).decode("utf-8")

            # Compare x-line-signature request header and the signature
            if x_line_signature == signature:
                try:
                    json_data = json.loads(body)
                    handler.handle(body, x_line_signature)
                    reply_token = json_data["events"][0][
                        "replyToken"
                    ]  # 取得 reply token
                    msg = json_data["events"][0]["message"]["text"]  # 取得 訊息

                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(
                            text=body
                            )
                    )

                    return "OK", 200
                except InvalidSignatureError as e:
                    print(e)
            else:
                return "Invalid signature", 403
    else:
        return "Method not allowed", 400

