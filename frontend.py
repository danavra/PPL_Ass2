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
    """
    General dropdown menu for the form
    """
    def __init__(self, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs, orientation='vertical')
        self.button = Button(text='Select ', font_size=30, size_hint_y=0.15, on_release=self.drop_down)  # main button
        self.add_widget(self.button)
        self.dropdown = DropDown()
        self.dropdown.bind(on_select=self.select)
        self.tag = None  # name for the options group
        self.selected = False  # has selected value
        self.options = {}  # the options to select(keys) and their actual values (values)

    @property
    def text(self):
        """
        :return: the text selected in the menu. if non text selected return empty string
        """
        return self.button.text if self.selected else 'No {}'.format(self.tag) if self.tag else ''

    @property
    def value(self):
        """
        :return: the actual value selected. if non selected return None
        """
        return self.options[self.button.text] if self.selected else None

    def select(self, instance, x):
        """
        select the option and show it on the main  button, and set selected field to True
        :param instance: obligated for the dropdown object
        :param x: the selected text from options
        """
        setattr(self.button, 'text', x)
        self.selected = True

    def reset(self):
        """
        reset the dropdown menu
        """
        setattr(self.button, 'text', 'Select {}'.format(self.tag if self.tag else ''))
        self.selected = False

    def set_tag(self, tag):
        """
        sets the tag (the options group name)
        :param tag: (str) the tag name
        """
        self.tag = tag
        self.button.text += tag

    def drop_down(self, button):
        """
        when main button is released, open the dropdown
        :param button: obligated for the button
        """
        self.dropdown.open(button)

    def set_options(self, options):
        """
        set the options in the menu
        :param options: (dict) dictionary of options like {'text for the user': $actual_value}
        """
        self.options = options
        for option in options.keys():
            btn = Button(text=option, size_hint_y=None, height=44,
                         on_release=lambda b: self.dropdown.select(b.text))
            self.dropdown.add_widget(btn)


class MyGrid(GridLayout):
    """
    For the form being displayed
    """

    location_dd = ObjectProperty(None)  # the location dropdown menu
    min_minutes = ObjectProperty(None)  # the textinput for the minimal trip time
    max_minutes = ObjectProperty(None)  # the textinput for the maximal trip time
    num_of_recommendations = ObjectProperty(None)  # the textinput for required recommendations
    level_dd = ObjectProperty(None)  # the level dropdown menu
    gender_dd = ObjectProperty(None)  # the gender dropdown menu

    def __init__(self, db, **kwargs):
        super(MyGrid, self).__init__(**kwargs)
        self.db = db  # mybackend.Database object

        # Set the location, level and gender dropdown menus
        self.location_dd.set_tag('Location')
        self.location_dd.set_options({x: x for x in db.get_start_points()})
        self.level_dd.set_tag('Level')
        self.level_dd.set_options({'Pro': 1, 'Average Joe': 0, 'Beginner': -1})
        self.gender_dd.set_tag('Gender')
        self.gender_dd.set_options({'Female': 0, 'Male': 1, 'Other': 2})

    def warning_popup(self, message):
        """
        show a warning popup to the user.
        :param message: (str) the message to display
        """
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
        """
        show the results of the trip to the user
        :param locations: (list of dicts) the results of locations and details for the trip (from db)
        :param summarize: (int) how many answer there are in db
        """
        summarize = summarize if summarize is not None else len(locations)
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
        # if summarize:
        #     row = GridLayout(cols=3, spacing=2, size_hint_y=None, size_hint_x=1)
        #     row.add_widget(Label(text='{display}/{all} Records Retrieved'.format(display=len(locations), all=summarize)))
        #     row.add_widget(Label(text=''))
        #     row.add_widget(Label(text=''))
        #     results.add_widget(row)

        for o in locations:
            row = GridLayout(cols=4, spacing=2, size_hint_y=None, size_hint_x=1)
            row.add_widget(Label(text='%d' % i))
            i += 1
            row.add_widget(Label(text=o['destination']))
            row.add_widget(Label(text='%.2f' % o['eta']))
            row.add_widget(Label(text='%.2f' % o['Distance']))
            results.add_widget(row)
        scroll_view.add_widget(results)
        content.add_widget(scroll_view)
        content.add_widget(buttons)

        popup = Popup(
            title='Results:{t} Displaying {recs}/{all} Records'.format(t=' '*30, recs=len(locations), all=summarize),
            content=content,
            auto_dismiss=False
        )
        popup.open()

    def reset(self, popup=None):
        """
        reset all the form
        :param popup: the popup that called the reset
        """
        if popup:
            popup.dismiss()

        self.min_minutes.text = ''
        self.max_minutes.text = ''
        self.num_of_recommendations.text = ''
        self.location_dd.reset()
        self.level_dd.reset()
        self.gender_dd.reset()

    def submit(self):
        """
        check the form, if valid popup the results, else popup warning
        """

        # check if location has been selected
        if not self.location_dd.value:
            self.warning_popup('You must select a start location')
            return

        # check if trip duration has been inserted
        if self.min_minutes.text == '' and self.max_minutes.text == '':
            self.warning_popup('You must enter a time for your trip')
            return
        # complete the second field of duration to be equal to the first if only one has been inserted
        elif self.min_minutes.text == '':
            self.min_minutes.text = self.max_minutes.text
        elif self.max_minutes.text == '':
            self.max_minutes.text = self.min_minutes.text
        # if duration has been inserted not in the right order, correct it
        elif int(self.max_minutes.text) < int(self.min_minutes.text):
            temp = self.min_minutes.text
            self.min_minutes.text = self.max_minutes.text
            self.max_minutes.text = temp

        # auto complete the level if not selected (to Average)
        if self.level_dd.value is None:
            self.level_dd.select(None, 'Average Joe')

        # if recommendation field hasn't been inserted or the value in it is 0 or less popup a warning
        elif self.num_of_recommendations.text != '' and int(self.num_of_recommendations.text) <= 0:
            self.warning_popup('Recommendations number must be greater than 0')
            return

        # arguments dictionary to the db
        kwargs = {'start': self.location_dd.value, 'time_low': int(self.min_minutes.text),
                  'time_high': int(self.max_minutes.text), 'riding_level': self.level_dd.value,
                  'sex': self.gender_dd.value}
        response = self.db.findTrip(**kwargs)  # request the trip from db

        # get the required recommendations number (or all of them if required number is greater)
        n = min(int(self.num_of_recommendations.text) if self.num_of_recommendations.text != '' else len(response),
                len(response))
        ans = response[:n]
        self.results_popup(ans, summarize=len(response))  # popup the results with summarization of the results


class MyApp(App):
    def build(self):
        db = Database()
        return MyGrid(db)


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        MyApp().run()
