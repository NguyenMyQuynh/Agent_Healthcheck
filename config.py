FLEET_SERVERS = {
    1: {
        "FLEET_URL": "hsoc.***",
        "FLEET_PORT": "***",
        "FLEET_USERNAME": "***",
        "FLEET_PASSWORD": "***",
    },
    2: {
        "FLEET_URL": "***.cloud.es.io", #https://cloud.elastic.co/home
        "FLEET_PORT": "9243",
        "FLEET_USERNAME": "***",
        "FLEET_PASSWORD": "***",
    },
}

THEHIVE_SERVER = "192.168.**.***"
THEHIVE_PORT = "9000"
THEHIVE_TOKEN = "***"

TELEGRAM_TOKEN = "***:***"
TELEGRAM_ID = "-***"

# Chat vs BotFather để tạo bot: search BotFather trên thanh search và gõ /start , /newbot, nhập tên bot, nhập username bot(format: *_bot) ==> nhận được token  
 
# Add bot vừa tạo vào group(search trên thanh search username bot), khỏi động bot /your_id@usernameOfBot  
 
# Lấy chat id tại https://api.telegram.org/bot[TOKEN]/getUpdates 
 
# Gửi canh báo dùng curl: curl -X POST "https://api.telegram.org/bot[TOKEN]/sendMessage" -d "chat_id=[CHAT_ID]&text=[MY_MESSAGE_TEXT]" 
# (hoặc có thể gửi trực tiếp thông qua parameter url hoặc thư viện python-telegram-bot)
