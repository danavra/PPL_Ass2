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
from mybackend import Database


class DropDownMenu(BoxLayout):
    def __init__(self, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs, orientation='vertical')
        self.button = Button(text='Select ', font_size=30, size_hint_y=0.15, on_release=self.drop_down)
        self.add_widget(self.button)
        self.dropdown = DropDown()
        self.dropdown.bind(on_select=self.select)
        self.tag = None
        self.selected = False
        self.options = {}

    @property
    def text(self):
        return self.button.text if self.selected else 'No {}'.format(self.tag if self.tag else '')

    @property
    def value(self):
        return self.options[self.button.text] if self.selected else None

    def select(self, instance, x):
        setattr(self.button, 'text', x)
        self.selected = True

    def reset(self):
        setattr(self.button, 'text', 'Select {}'.format(self.tag if self.tag else ''))
        self.selected = False

    def set_tag(self, tag):
        self.tag = tag
        self.button.text += tag

    def drop_down(self, button):
        self.dropdown.open(button)

    def set_options(self, options):
        self.options = options
        for option in options.keys():
            btn = Button(text=option, size_hint_y=None, height=44,
                         on_release=lambda b: self.dropdown.select(b.text))
            self.dropdown.add_widget(btn)


class MyGrid(GridLayout):

    location_dd = ObjectProperty(None)
    min_minutes = ObjectProperty(None)
    max_minutes = ObjectProperty(None)
    num_of_recommendations = ObjectProperty(None)
    level_dd = ObjectProperty(None)
    gender_dd = ObjectProperty(None)

    def __init__(self, db, **kwargs):
        super(MyGrid, self).__init__(**kwargs)
        self.db = db
        self.location_dd.set_tag('Location')
        self.location_dd.set_options({x: x for x in db.get_start_points()})
        self.level_dd.set_tag('Level')
        self.level_dd.set_options({'Pro': 1, 'Average Joe': 0, 'Beginner': -1})
        self.gender_dd.set_tag('Gender')
        self.gender_dd.set_options({'Female': 0, 'Male': 1, 'Irrelevant': 2})

    def popup(self, message, warning=True):
        buttons = GridLayout()
        buttons.cols = 2
        buttons.add_widget(
            # Button(text='Try Again', font_size=40, on_release=lambda btn: self.reset(reset=False, popup=popup))
            Button(text='Try Again', font_size=40, on_release=lambda btn: popup.dismiss())
        )
        buttons.add_widget(
            Button(text='Reset Form', font_size=40, on_release=lambda btn: self.reset(popup=popup))
        )
        content = GridLayout()
        content.cols = 1
        if isinstance(message, str):
            content.add_widget(Label(text=message))
        elif isinstance(message, list):
            lbl_txt = []
            for o in message:
                lbl_txt.append('{dest}: {time} minutes'.format(dest=o['destination'], time=o['eta']))
            content.add_widget(Label(text='\n'.join(lbl_txt)))
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
            self.num_of_recommendations.text = ''
            self.location_dd.reset()
            self.level_dd.reset()

    def submit(self):
        frame = '-'*30
        if self.max_minutes.text == '' or self.min_minutes.text == '':
            self.popup('Please type your time range')

        if int(self.max_minutes.text) < int(self.min_minutes.text):
            self.popup('bad input')
            # temp = self.min_minutes.text
            # self.min_minutes.text = self.max_minutes.text
            # self.max_minutes.text = temp

        elif int(self.num_of_recommendations.text) <= 0:
            self.popup(message='No Recommendations Asked', warning=False)

        else:
            list_message = [frame, 'At: %s' % self.location_dd.text,
                            'Between {0} and {1} minutes'.format(self.min_minutes.text, self.max_minutes.text),
                            'Visiting in %s stations' % self.num_of_recommendations.text,
                            'Level: %s' % self.level_dd.text, 'Gender: %s' % self.gender_dd.text, frame]
            # self.popup('\n'.join(list_message), warning=False)
            start = self.location_dd.value
            minmin = int(self.min_minutes.text)
            maxmin = int(self.max_minutes.text)
            level = self.level_dd.value
            sex = self.gender_dd.value
            ans = self.db.findTrip(self.location_dd.value, int(self.min_minutes.text), int(self.max_minutes.text),
                                   self.level_dd.value, self.gender_dd.value)
            self.popup(ans)


class MyApp(App):
    def build(self):
        db = Database()
        return MyGrid(db)


if __name__ == "__main__":
    MyApp().run()
