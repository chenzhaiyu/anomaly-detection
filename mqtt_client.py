import paho.mqtt.publish as publish
import time
import json
from mqtt_host import HOST,PORT



def publish_message(topic,message):

    client_id = str(time.time())
    publish.single(topic, message, qos=1, hostname=HOST, port=PORT,
                   client_id=client_id, auth={"username": "browser", "password": "u73igG84"})


if __name__=="__main__":
    while True:
        t={"description": [{"type":"person","value":0.3093232214450836},
                           {"type":"chair","value":0.3093232214450836}],
           "level": 51, "id": 1, "isDevice": 2, "sensorTime": 1531191219}
        publish_message("a0/alarm",json.dumps(t))