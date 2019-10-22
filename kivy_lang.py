from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
import cv2
from kivy.clock import Clock
from optical_flow import save_frame,detect_motion
from optical_flow import FIRST_FRAME_SAVE_PATH,NEW_FRAME_SAVE_PATH
import tracking
import global_manager as gm

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
                    text: 'object detection'
                    on_press:root.detect_invasion()

                BubbleButton:
                    id:displace
                    text: 'displacement detection'
                    on_press:root.detect_displacement()
                BubbleButton:
                    id:settings
                    text:"settings"
                    on_release:root.current="setting"

            Image:
                id:myImg
                source:"result/New_Frame.png"


            TextInput:
                id: output
                size_hint_y:0.3

                text: "output:"
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
                spacing:20
                size_hint:1,0.1
                Button:
                    pos_hint:{"top":1}
                    text:"cancel"
                    on_release:root.current="viewer"
                Button:
                    pos_hint:{"top":1}
                    text:"apply"
                    on_press:root.settings()
                    on_release:root.current="viewer"
            GridLayout:
                cols:2
                padding:10,10
                spacing:20
                size_hint:0.8,0.07
                pos_hint:{"center_x":0.5}
                Label:
                    text:"Video URL"
                TextInput:
                    id:url
                    multiline:False
            Label:
                size_hint:1,0.5     

''')


class MyScreenManager(ScreenManager):
    def __init__(self,**kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.obj_play = False  # whether to start detect invasion
        self.disp_play = False  # whether to start detect displacement
        self.videoURL = "rtmp://218.76.43.93:10555/app/live?token=t5b3b3bc71860008"
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
            Clock.schedule_interval(self.start_detect_invasion, 1/100)

    def start_detect_invasion(self,dt):
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
                message = "----WARNING: " + str(what) + "----\n"
                self.ids.output.insert_text(message)

    def stop_detect_invasion(self):
        self.obj_play = False
        self.ids.object.text="detect"
        Clock.unschedule(self.startDetectObj)
        self.capture.release()


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
            if isOverflow:
                self.ids.output.insert_text(message)

    def stop_detect_displacement(self):
        self.disp_play = False
        self.ids.displace.text="detect"
        Clock.unschedule(self.start_detect_displacement)
        self.capture.release()

    def settings(self):
        self.videoURL=self.ids.url.text

        self.ids["output"].text="output"


class TestApp(App):
    def build(self):
        return MyScreenManager()


if __name__=="__main__":
    TestApp().run()