import json
import re
import threading

from sqlalchemy.orm import Session
from starlette.responses import PlainTextResponse

from app import services
from app.database.models import Code
from app.database.session import session_scope
from app.modules import get_module
from app.modules.notify.WXBizMsgCrypt3 import WXBizMsgCrypt
from app.services import is_exist_server
from app.core.config import get_settings
from app.utils import has_number, get_true_code
from app.api.services.isubscribe import download_subscribe
from telebot.types import BotCommand
from app.utils.log import logger
import xmltodict

from app.version import AL_VERSION


def get_message(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    settings = get_settings()
    token = settings.WECHAT_TOKEN
    encode_aes_key = settings.WECHAT_ENCODING_AES_KEY
    corp_id = settings.WECHAT_CORP_ID
    crypt = WXBizMsgCrypt(token, encode_aes_key, corp_id)
    ret, sReplyEchoStr = crypt.VerifyURL(msg_signature, timestamp, nonce, echostr)
    logger.error(ret)
    logger.error(sReplyEchoStr)
    logger.error(sReplyEchoStr[3:])
    return PlainTextResponse(sReplyEchoStr)


def post_message(msg_signature: str, timestamp: str, nonce: str, xml_data,
                 session: Session):
    settings = get_settings()
    token = settings.WECHAT_TOKEN
    encode_aes_key = settings.WECHAT_ENCODING_AES_KEY
    corp_id = settings.WECHAT_CORP_ID
    crypt = WXBizMsgCrypt(token, encode_aes_key, corp_id)
    try:
        ret, xml_content = crypt.DecryptMsg(xml_data, msg_signature, timestamp, nonce)
        if ret == 0:
            data_dict = xmltodict.parse(xml_content)
            msg = data_dict['xml']['Content']
            logger.error(msg)
            do_sub(msg, 'wx', session)
    except Exception as e:
        return PlainTextResponse("")
    # 处理解析后的数据 (这里简单返回解析后的数据)
    return PlainTextResponse("")


def do_sub(msg, channel, session: Session):
    settings = get_settings()
    split_text = re.split(r'[,|\n\r\s]', msg)
    filtered_msg = [s for s in split_text if s.strip()]
    for msg in filtered_msg:
        if len(msg) == len(msg.encode()) and has_number(msg):
            code_no = get_true_code(msg)
            if code_no:
                if not is_exist_server(code_no):
                    code = session.get(Code,code_no)
                    if code:
                        if code.status != 'SUBSCRIBE':
                            code.status = 'SUBSCRIBE'
                            code.filter = json.dumps(settings.DEFAULT_FILTER)
                            session.commit()
                            session.refresh(code)
                            threading.Thread(
                                target=lambda: services.send_subscribe_message(code.code, code.title,
                                                                               code.banner)).start()
                        threading.Thread(
                            target=lambda: services.run_sub(code.code)).start()
                    else:
                        code = services.search_code(code_no)
                        if code:
                            code.filter = json.dumps(settings.DEFAULT_FILTER)
                            code.status = 'SUBSCRIBE'
                            session.add(code)
                            session.commit()
                            session.refresh(code)
                            threading.Thread(
                                target=lambda: services.send_subscribe_message(code.code, code.title,
                                                                               code.banner)).start()
                            threading.Thread(
                                target=lambda: services.run_sub(code.code)).start()
                        else:
                            threading.Thread(
                                target=lambda: services.reply_text_msg(channel,
                                                                       f"番号:{code_no},未找到有效的影片")).start()
                else:
                    threading.Thread(
                        target=lambda: services.reply_text_msg(channel, f"番号:{code_no},已存在于媒体库")).start()
            else:
                threading.Thread(
                    target=lambda: services.reply_text_msg(channel, f"番号:{msg},不是有效的")).start()
        else:
            threading.Thread(
                target=lambda: services.reply_text_msg(channel, f"番号:{msg},不是有效的")).start()


def create_tg_bot():
    module = get_module()
    bot = module.telegram.bot

    if bot:
        # 设置命令列表
        commands = [
            {'command': 'start', 'description': '获取欢迎信息'},
            {'command': 'subscribe', 'description': '获取当前订阅列表'},
            {'command': 'download_subscribe', 'description': '下载订阅'},
            {'command': 'version', 'description': '查看当前版本'}
        ]
        try:
            bot_commands = [BotCommand(cmd['command'], cmd['description']) for cmd in commands]
            bot.set_my_commands(bot_commands)
            logger.info("成功设置命令列表")
        except Exception as e:
            logger.error(f"设置命令列表失败: {str(e)}")

        @bot.message_handler(commands=['start', 'version', 'subscribe', 'download_subscribe'])
        def handle_commands(message):
            if message.text.startswith('/start'):
                help_text = "欢迎使用订阅机器人！\n\n" \
                            "直接发送番号进行订阅\n"
            elif message.text.startswith('/version'):
                from app.api.services.iconfig import get_latest_version
                latest_version, changes = get_latest_version()
                help_text = f"当前版本：{AL_VERSION}\n" \
                            f"最新版本：{latest_version if latest_version else '获取失败'}"
            elif message.text.startswith('/subscribe'):
                with session_scope() as session:
                    subs = get_subscribe_list(session)
                    if subs:
                        help_text = "当前订阅列表：\n\n" + "\n".join(
                            [f"{i + 1}. {s['code']} - {s['title']}\n" for i, s in enumerate(subs)])
                    else:
                        help_text = "当前没有订阅"
            elif message.text.startswith('/download_subscribe'):
                threading.Thread(
                    target=lambda: download_subscribe()).start()
                help_text = "已开始下载订阅，请稍后查看下载状态"
            else:  # /help
                help_text = "机器人使用帮助：\n\n" \
                            "1. 直接发送番号进行订阅\n" \
                            "2. 使用 /start 查看欢迎信息\n" \
                            "3. 使用 /version 查看当前版本\n" \
                            "4. 使用 /subscribe 查看当前订阅"

            threading.Thread(
                target=lambda: module.telegram.reply_text_message(message.chat.id, help_text,
                                                                  message.message_id)).start()

        @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            module = get_module()
            if module.telegram.whitelist:
                if message.from_user.id not in module.telegram.whitelist:
                    threading.Thread(
                        target=lambda: module.telegram.send_text_message(message.chat.id,
                                                                         "只允许白名单用户订阅")).start()
                    return
            with session_scope() as session:
                do_sub(message.text, 'tg', session)
                session.close()

        threading.Thread(
            target=lambda: bot.infinity_polling(long_polling_timeout=30, logger_level=None)).start()


def get_subscribe_list(session: Session):
    """Get list of currently subscribed codes"""
    codes = session.query(Code).filter(Code.status == 'SUBSCRIBE').all()
    return [{'code': code.code, 'title': code.title} for code in codes]


create_tg_bot()
