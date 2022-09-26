import config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import telegram
import json
import requests
import threading

from datetime import datetime
from thehive4py.api import TheHiveApi 
from thehive4py.models import Alert

# Get agent's status
def AgentStatus(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):    
    auth = (FLEET_USERNAME, FLEET_PASSWORD)

    request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agent_status", auth=auth, verify=False)
    result = json.loads(request.text)

    online = result['results']['online']
    offline = result['results']['offline']

    return (online, offline)

# Get offline agent's info
def OfflineAgentInfo(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):
    auth = (FLEET_USERNAME, FLEET_PASSWORD)

    request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agents", auth=auth, verify=False)
    result = json.loads(request.text)

    offline_agents = []
    for agent in result['list']:
        status = agent['status']
        # if status == 'offline':
        if status != 'healthy' and status != 'online':
            hostname = agent['local_metadata']['host']['hostname']
            ip = agent['local_metadata']['host']['ip']
            os = agent['local_metadata']['os']['full']
            status = status
            last_checkin = agent['last_checkin']
            offline_agents.append((hostname, ip, os, status, last_checkin))

    return offline_agents

def SendAlertToTheHive(THEHIVE_SERVER, THEHIVE_PORT, THEHIVE_TOKEN, alert):
    api = TheHiveApi(f"http://{THEHIVE_SERVER}:{THEHIVE_PORT}", THEHIVE_TOKEN) 
    alert = Alert(
        title='Anomal hostname', 
        description=alert, 
        type='external', 
        source=f'instance-{str(datetime.now())}', 
        sourceRef='alert-ref',
    ) 
   
    api.create_alert(alert) 

def SendAlertToTelegram(TELEGRAM_TOKEN, TELEGRAM_ID, alert):
    telegram_alert = telegram.Bot(TELEGRAM_TOKEN)
    telegram_alert.send_message(chat_id=TELEGRAM_ID, text=alert, parse_mode='Markdown')

def main():
    alert = ""
    for i in config.FLEET_SERVERS:
        online, offline = AgentStatus(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])
        alert += "<<<<< "
        alert += f"FLEET_SERVER: {config.FLEET_SERVERS[i]['FLEET_URL']} >>>>>\n\n"

        if offline == 0:
            alert += f"Agents online: {online},\t agent offline: {offline} ✅\n\n"
        else:
            alert += f"Agents online: {online},\t agent offline: {offline} ❌\n\n"
            alert += "Information of offline agents:\n"

        print(f"FLEET_SERVER: {config.FLEET_SERVERS[i]['FLEET_URL']}")
        print("Number of online agents: ", online)
        print("Number of offline agents: ", offline)

        offline_agents = OfflineAgentInfo(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])

        for i, agent in enumerate(offline_agents):
            hostname, ips, os, status, last_checkin = agent
            ip_list = []
            for ip in ips:
                if ip[0:2] == "10" or ip[0:6] == "172.16" or ip[0:7] == "192.168":
                    ip_list.append(ip)
            
            alert += f"{i + 1}.\t"
            alert += f"Hostname: {hostname},\t"
            alert += f"IP: {ip_list},\t"
            alert += f"OS: {os},\t"
            alert += f"Status: {status},\t"
            alert += f"Last checkin: {last_checkin}\n\n"
      
    SendAlertToTheHive(config.THEHIVE_SERVER, config.THEHIVE_PORT, config.THEHIVE_TOKEN, alert)
    SendAlertToTelegram(config.TELEGRAM_TOKEN, config.TELEGRAM_ID, alert)

main()
