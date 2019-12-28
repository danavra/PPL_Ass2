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
from kivy.uix.scrollview import ScrollView

from mybackend import Database
import warnings
import os


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
        self.gender_dd.set_options({'Female': 0, 'Male': 1, 'Other': 2})

    def warning_popup(self, message):
        buttons = GridLayout(cols=2, size_hint_y=0.25)
        buttons.add_widget(Button(text='Try Again', font_size=40, on_release=lambda btn: popup.dismiss()))
        buttons.add_widget(Button(text='Reset Form', font_size=40, on_release=lambda btn: self.reset(popup=popup)))

        content = GridLayout()
        content.cols = 1
        content.add_widget(Label(text=message))
        content.add_widget(buttons)

        popup = Popup(title='Warning', content=content, auto_dismiss=False)
        popup.open()

    def results_popup(self, locations, summarize=None):
        buttons = GridLayout(cols=1, size_hint_y=0.25)
        buttons.add_widget(Button(text='OK', font_size=40, on_release=lambda btn: self.reset(popup=popup)))

        content = GridLayout()
        content.cols = 1
        scroll_view = ScrollView()
        results = GridLayout(cols=4, size_hint_y=0.25)
        results.add_widget(Label(text='Number'))
        results.add_widget(Label(text='Destination'))
        results.add_widget(Label(text='Time(minutes)'))
        results.add_widget(Label(text='Distance(KM)'))
        content.add_widget(results)
        i = 1
        results = GridLayout(cols=1, spacing=10, size_hint_y=None, size_hint_x=1)
        results.bind(minimum_height=results.setter('height'))
        for o in locations:
            row = GridLayout(cols=4, spacing=2, size_hint_y=None, size_hint_x=1)
            row.add_widget(Label(text='%d' % i))
            i += 1
            row.add_widget(Label(text=o['destination']))
            row.add_widget(Label(text='%.2f' % o['eta']))
            row.add_widget(Label(text='%.2f' % o['Distance']))
            results.add_widget(row)
        if summarize:
            row = GridLayout(cols=3, spacing=2, size_hint_y=None, size_hint_x=1)
            row.add_widget(Label(text='{display}/{all} Records Retrieved'.format(display=len(locations), all=summarize)))
            row.add_widget(Label(text=''))
            row.add_widget(Label(text=''))
            results.add_widget(row)
        scroll_view.add_widget(results)
        content.add_widget(scroll_view)
        content.add_widget(buttons)

        popup = Popup(title='Results', content=content, auto_dismiss=False)
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
            self.gender_dd.reset()

    def submit(self):
        if not self.location_dd.value:
            self.warning_popup('You must select a start location')
            return
        if self.min_minutes.text == '' and self.max_minutes.text == '':
            self.warning_popup('You must enter a time for your trip')
            return
        elif self.min_minutes.text == '':
            self.min_minutes.text = self.max_minutes.text
        elif self.max_minutes.text == '':
            self.max_minutes.text = self.min_minutes.text
        elif int(self.max_minutes.text) < int(self.min_minutes.text):
            temp = self.min_minutes.text
            self.min_minutes.text = self.max_minutes.text
            self.max_minutes.text = temp

        if self.level_dd.value is None:
            self.level_dd.select(None, 'Average Joe')

        elif self.num_of_recommendations.text != '' and int(self.num_of_recommendations.text) <= 0:
            self.warning_popup('Recommendations number must be greater than 0')
            return

        kwargs = {'start': self.location_dd.value, 'time_low': int(self.min_minutes.text),
                  'time_high': int(self.max_minutes.text), 'riding_level': self.level_dd.value,
                  'sex': self.gender_dd.value}
        response = self.db.findTrip(**kwargs)
        n = min(int(self.num_of_recommendations.text) if self.num_of_recommendations.text != '' else -1, len(response))
        ans = response[:n]
        self.results_popup(ans, summarize=len(response))


class MyApp(App):
    def build(self):
        db = Database()
        return MyGrid(db)


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        MyApp().run()
