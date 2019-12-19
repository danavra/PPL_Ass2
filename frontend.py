import kivy
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
import pandas as pd
from kivy.uix.popup import Popup


class MyDropDown(BoxLayout):

    def __init__(self, **kwargs):
        super(MyDropDown, self).__init__(**kwargs, orientation='vertical')
        self.button = Button(text='Choose Location', font_size=30, size_hint_y=0.15, on_release=self.drop_down)
        self.add_widget(self.button)
        self.dropdown = DropDown()
        self.dropdown.bind(on_select=lambda instance, x: setattr(self.button, 'text', x))
        for option in self.get_options():
            btn = Button(text=option, size_hint_y=None, height=44, on_release=lambda btn: self.dropdown.select(btn.text))
            # btn.text=option
            # btn.bind(on_release=lambda btn:self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)

    @property
    def text(self):
        return self.button.text if self.button.text != 'Choose Location' else 'No Location'

    def set_selection(self, text):
        self.button.text = text

    def reset(self):
        setattr(self.button, 'text', 'Choose Location')

    def dropdown_select(self, btn):
        self.dropdown.select(btn.text)

    def drop_down(self, button):
        self.dropdown.open(button)

    def get_options(self):
        data = pd.read_csv('BikeShare.csv')
        ans = list(set(data['StartStationName']))
        ans.sort()
        return ans


class MyGrid(GridLayout):

    mdd = ObjectProperty(None)
    min_minutes = ObjectProperty(None)
    max_minutes = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MyGrid, self).__init__(**kwargs)

    def popup(self, text, warning=True):
        buttons = GridLayout()
        buttons.cols = 2
        buttons.add_widget(
            Button(text='Try Again', font_size=40, on_release=lambda btn: self.reset(reset=False, popup=popup))
        )
        buttons.add_widget(
            Button(text='Reset Form', font_size=40, on_release=lambda btn: self.reset(popup=popup))
        )
        content = GridLayout()
        content.cols = 1
        content.add_widget(Label(text=text))
        content.add_widget(
            buttons if warning else Button(text='OK', font_size=40, on_release=lambda btn: self.reset(popup=popup))
        )

        popup = Popup(title='Test popup', content=content, auto_dismiss=False)
        popup.open()

    def reset(self, reset=True, popup=None):
        if popup:
            popup.dismiss()
        if reset:
            self.min_minutes.text = ''
            self.max_minutes.text = ''
            self.mdd.reset()

    def btn(self):
        frame = '-'*30
        if int(self.max_minutes.text) < int(self.min_minutes.text):
            # self.popup('bad input')
            temp = self.min_minutes.text
            self.min_minutes.text = self.max_minutes.text
            self.max_minutes.text = temp
        else:
            message = '{0}\nAt: {1}\nBetween {2} and {3} minutes tour\n{0}'.format(frame,
                                                                                   self.mdd.text,
                                                                                   self.min_minutes.text,
                                                                                   self.max_minutes.text)
            self.popup(message, warning=False)


class MyApp(App):
    def build(self):
        return MyGrid()


if __name__ == "__main__":
    MyApp().run()
