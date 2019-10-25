from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
import cv2
from kivy.clock import Clock
from optical_flow import save_frame,detect_motion
from optical_flow import FIRST_FRAME_SAVE_PATH,NEW_FRAME_SAVE_PATH
import tracking
import global_manager as gm
import mqtt_client
import time
import json
import threads_manager
from kivy.core.window import Window
Builder.load_string('''
<MyScreenManager>
    Screen: 
        name:"viewer" 
        BoxLayout:
            id:bl
            spacing:10
            orientation:"vertical"
            canvas:
                Color:
                    rgb: 0.8, 0.8, 0.8
                Rectangle:
                    size:self.size
                    pos:self.pos  
            Bubble:
                size_hint:(1,0.1)
                pos_hint:{ 'top': 1}
                orientation:"horizontal"
                background_color:0.6,0.6,0.6
                show_arrow:False
                BubbleButton:
                    id:object
                    text: 'Object Detection'
                    on_press:root.detect_invasion()
                    font_size:"22sp"

                BubbleButton:
                    id:displace
                    text: 'Displacement Detection'
                    on_press:root.detect_displacement()
                    font_size:"22sp"
                BubbleButton:
                    id:settings
                    text:"Settings"
                    on_release:root.current="setting"
                    font_size:"22sp"

            Image:
                id:myImg
                source:"result/New_Frame.png"


            TextInput:
                id: output
                size_hint_y:0.3
                foreground_color: [255, 0, 0, 1]
                text: "output:"
                font_size:"25sp"
    Screen:
        name:"setting"
        BoxLayout:
            spacing:10
            orientation:"vertical"
            canvas:
                Color:
                    rgb: 0.8, 0.8, 0.8
                Rectangle:
                    size:self.size
                    pos:self.pos  
            BoxLayout:
                orientation:"horizontal"
                padding:40,10
                spacing:80
                size_hint:1,0.05
                Button:
                    pos_hint:{"top":1,"center_x":0.3}
                    text:"cancel"
                    on_release:root.current="viewer"
                Button:
                    pos_hint:{"top":1,"center_x":0.7}
                    text:"apply"
                    on_press:root.settings()
                    on_release:root.current="viewer"
            GridLayout:
                cols:2
                padding:50,10
                spacing:20
                size_hint:1,0.15
                
                Label:
                    text:"Video URL"
                TextInput:
                    id:url
                    multiline:False
                    hint_text:"rtmp://0.0.0.0/app/live?token=t5b4553603a90059"
                    
                Label:
                    text:"MQTT HOST"
                TextInput:
                    id:host
                    multiline:False
                    hint_text:"cloud.bdsmc.net"
                Label:
                    text:"MQTT PORT"
                TextInput:
                    id:host
                    multiline:False
                    hint_text:"1883"
                
            Label:
                size_hint:1,0.3     

''')
def build_message():
    sensorTime = int(time.time())

    isDevice = 2

    id = int('100000000001', 16)

    level = 51

    what = gm.global_manager.get_value("what")

    # confidence value
    value = gm.global_manager.get_value('confidence')

    # concatenate objects and confidence as description
    objects = {}
    description = []

    for i in range(len(what)):
        objects.clear()
        objects['type'] = what[i]
        objects['value'] = value[i]

        description.append(objects)

    message = {'isDevice': isDevice, 'id': id, 'sensorTime': sensorTime, 'level': level,
               'description': description}
    return message

class MyScreenManager(ScreenManager):
    def __init__(self,**kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.obj_play = False  # whether to start detect invasion
        self.disp_play = False  # whether to start detect displacement
        self.videoURL = "rtmp://0.0.0.0/app/live?token=t5b4553603a90059"
        self.ids.output.insert_text('\n')
        self.capture = None
        self.frame_id = 0

    def detect_invasion(self):
        self.ids.myImg.source = NEW_FRAME_SAVE_PATH
        if self.obj_play:
            self.stop_detect_invasion()
        else:
            self.obj_play=True
            self.capture = cv2.VideoCapture(self.videoURL)
            self.frame_id = 0
            self.message_id = 0
            Clock.schedule_interval(self.start_detect_invasion, 1/100)

    def start_detect_invasion(self, dt):
        self.ids["object"].text = "pause"
        status, frame = self.capture.read()
        if status:
            if self.frame_id % 1 == 0:
                try:
                    tracking.tracking_core(frame, self.frame_id)
                    self.ids.myImg.reload()
                except:
                    pass
            self.frame_id = self.frame_id + 1
            what = gm.global_manager.get_value("what")
            if what and len(what) >= 1:
                output_message = "----WARNING: " + str(what) + "----\n"
                self.ids.output.insert_text(output_message)

                message=build_message()

                self.thread = threads_manager.MyThread(mqtt_client.publish_message, args=("a0/alarm", json.dumps(message)))
                self.thread.start()

            if self.frame_id % 600 == 0:
                alive_message = 'a'
                self.thread = threads_manager.MyThread(mqtt_client.publish_message, args=("hb/nx/100000000001", alive_message))
                self.thread.start()

    def stop_detect_invasion(self):
        self.obj_play = False
        self.ids.object.text="detect"
        Clock.unschedule(self.start_detect_invasion)
        self.capture.release()
        self.thread.join()

    def detect_displacement(self):
        self.ids.myImg.source = "result/flow.png"
        self.updateThresh = True
        self.updateTimes = 0
        self.frame_id = 0
        self.thresh = 0.0
        if self.disp_play == True:
            self.stop_detect_displacement()
        else:
            self.capture = cv2.VideoCapture(self.videoURL)
            self.disp_play = True
            self.ids["displace"].text = "pause"
            status,frame=self.capture.read()
            if status:
                save_frame(True, frame)
            Clock.schedule_interval(self.start_detect_displacement, 1 / 10)

    def start_detect_displacement(self, dt):
        # global capture
        status, frame = self.capture.read()

        isOverflow = False

        if status:
            if self.frame_id % 100 == 0:
                try:
                    save_frame(False, frame)

                    self.thresh, isOverflow = detect_motion(FIRST_FRAME_SAVE_PATH, NEW_FRAME_SAVE_PATH, self.thresh,
                                                            self.updateThresh)

                    print('\nThreshold: ' + str(self.thresh) + '\n')
                    self.ids.myImg.reload()
                except:
                    pass
                self.updateTimes += 1
                # update threshold based on the first five frames
                if self.updateTimes > 5:
                    self.updateThresh = False
            self.frame_id += 1
            message = "----WARNING: obvious displacement ----\n"
            self.thread = threads_manager.MyThread(mqtt_client.publish_message, args=("a0/alarm-displacement", json.dumps(message)))
            self.thread.start()

            if isOverflow:
                self.ids.output.insert_text(message)

    def stop_detect_displacement(self):
        self.thread.join()
        self.disp_play = False
        self.ids.displace.text="detect"
        Clock.unschedule(self.start_detect_displacement)
        self.capture.release()

    def settings(self):
        self.videoURL=self.ids.url.text

        self.ids["output"].text="output"


class TestApp(App):
    def build(self):
        Window.size=(1200,800)
        self.title="Video Detection"
        return MyScreenManager()


if __name__=="__main__":
    TestApp().run()