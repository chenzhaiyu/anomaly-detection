import paho.mqtt.client as mqtt
import time
import alarm_speaker


# HOST = "cloud.bdsmc.net"
HOST="iot.eclipse.org"
PORT = 1883

def client_loop():
    client = mqtt.Client("1")
    client.username_pw_set("browser", "u73igG84")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(HOST, PORT, 60)
    client.loop_forever()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("a0/alarm")
    client.subscribe("hb/nx/100000000001")
    client.subscribe("a0/alarm-displacement")


def on_message(client, userdata, msg):
    print(msg.topic+" "+msg.payload.decode("utf-8"))
    if msg.topic=="a0/alarm":
        warning_dict=eval(msg.payload)
        for item in warning_dict["description"]:
            alarm_speaker.warn_object(item["type"])
    elif msg.topic=="a0/alarm-displacement":
        alarm_speaker.warn_change()
    else:
        pass

if __name__ == "__main__":
    client_loop()
