# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

#Future ideas (just possibilities):
#   New preset folder type - FTP - load/save files from ftp
#   Encrypted files - option to store password locally (for remote/ftp files), or require password to access preset folder

import os
import shutil
import kivy
from snu.app import *
from snu.button import *
from snu.label import *
from snu.layouts import *
from snu.textinput import *
from snu.recycleview import *
from snu.popup import ConfirmPopupContent, InputPopupContent, NormalPopup
from kivy.logger import Logger
from kivy.base import EventLoop
from kivy.utils import platform
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.properties import ObjectProperty, ListProperty
from kivy.core.clipboard import Clipboard
from kivy.utils import platform
from kivy.metrics import cm
app = None


class EditScreen(Screen):
    def on_enter(self):
        app.load_clipboards(edit=True)

    def on_leave(self):
        app.load_clipboards()


class PresetFolder(BoxLayout):
    path = StringProperty()


class ClipPreset(RecycleItem, BoxLayout):
    edit = BooleanProperty(False)
    adder = BooleanProperty(False)
    viewtype = StringProperty('item')  #'heading' or 'item' or 'adder-item' or 'adder-heading'
    text = StringProperty('')
    clipboard = StringProperty('')
    hidden = BooleanProperty(False)
    section = StringProperty('')
    section_folder = StringProperty('')
    path = StringProperty('')

    def click(self):
        if self.viewtype == 'adder-item':
            app.add_preset('item', self.path)
            return
        if self.viewtype == 'adder-heading':
            app.add_preset('heading', self.path)
            return
        if self.edit:
            app.edit_preset(self)
            return

        if self.viewtype == 'heading':
            if app.ctrl_pressed:
                app.instant_add(self.path, self.section)
            elif app.shift_pressed:
                app.toggle_hide_section(self.text, hide_others=True)
            else:
                app.toggle_hide_section(self.text)
        else:
            if app.ctrl_pressed:
                app.instant_add(self.section_folder, self.section)
            else:
                app.set_clipboard(self.clipboard)


class NormalLabelClickable(ButtonBehavior, NormalLabel):
    pass


class LeftNormalLabelClickable(ButtonBehavior, LeftNormalLabel):
    pass


class ClipHistoryPreset(RecycleItem, BoxLayout):
    text = StringProperty('')
    index = NumericProperty(0)


class ClipHistoryPresetShort(RecycleItem, BoxLayout):
    text = StringProperty('')
    index = NumericProperty(0)


class MainScreen(BoxLayout):
    pass


class InstantAddPresetContent(GridLayout):
    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(InstantAddPresetContent, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class SnuClipboardManager(NormalApp):
    icon = 'data/icon_small.png'
    tray = None
    tray_thread = None
    window_minimized = BooleanProperty(False)
    shift_pressed = BooleanProperty(False)
    ctrl_pressed = BooleanProperty(False)
    alt_pressed = BooleanProperty(False)
    window_leave_timeout = ObjectProperty(allownone=True)
    on_top = BooleanProperty(False)
    window_min_width = NumericProperty(130)
    window_title = 'Snu Clipboard Manager'
    window_width_target = NumericProperty(200)
    modify_mode = BooleanProperty(False)
    clipboard_updater = ObjectProperty(allownone=True)
    current_clipboard = StringProperty('')
    clipboard_folder = StringProperty('')
    clipboard_folders = ListProperty()
    clipboard_data = ListProperty()
    clipboard_data_display = ListProperty()
    clipboard_history = ListProperty()
    hiddens = ListProperty()
    main_history_length = NumericProperty(1)
    data_directory = StringProperty('')
    show_undo = BooleanProperty(True)
    show_strip = BooleanProperty(False)
    max_history = NumericProperty(20)

    preset_type = StringProperty()
    preset_element = StringProperty()
    preset_second_element = StringProperty()

    edit_type = StringProperty()
    edit_path = StringProperty()
    edit_name = StringProperty()
    edit_name_original = StringProperty()
    edit_section = StringProperty()
    edit_content = StringProperty()

    def rescale_interface(self, *_, force=False):
        """Called when the window changes resolution, calculates variables dependent on screen size"""

        self.store_window_size()

        if Window.width != self.last_width:
            self.last_width = Window.width
            self.popup_x = min(Window.width, 640)

        if (Window.height != self.last_height) or force:
            self.last_height = Window.height
            self.button_scale = int(float(cm(0.85)) * (int(self.config.get("Settings", "buttonsize")) / 100))
            self.text_scale = int((self.button_scale / 3) * int(self.config.get("Settings", "textsize")) / 100)
            self.display_border = self.button_scale / 3
            self.display_padding = self.button_scale / 4

    def get_application_config(self, **kwargs):
        if platform == 'win':
            self.data_directory = os.getenv('APPDATA') + os.path.sep + "Snu Clipboard Manager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'linux':
            self.data_directory = os.path.expanduser('~') + os.path.sep + ".snuclipboardmanager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'macosx':
            self.data_directory = os.path.expanduser('~') + os.path.sep + ".snuclipboardmanager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'android':
            self.data_directory = self.user_data_dir
        else:
            self.data_directory = os.path.sep
        config_file = os.path.realpath(os.path.join(self.data_directory, "snuclipboardmanager.ini"))
        return config_file

    def on_config_change(self, config, section, key, value):
        self.load_config_values()
        self.rescale_interface(force=True)

    def load_config_values(self):
        self.show_undo = self.config.getboolean("Settings", 'showundo')
        self.show_strip = self.config.getboolean("Settings", 'showstrip')
        max_history = int(self.config.get("Settings", 'max_history'))
        if max_history < 1:
            self.max_history = 1
        else:
            self.max_history = max_history
        main_history_length = int(self.config.get("Settings", "main_history_length"))
        if main_history_length > self.max_history:
            self.main_history_length = self.max_history
        elif main_history_length < 1:
            self.main_history_length = 1
        else:
            self.main_history_length = main_history_length

    def load_clipboards(self, edit=False):
        self.load_hiddens()
        self.clipboard_data = []
        if edit:
            self.clipboard_data.append({'text': 'Add Section', 'viewtype': 'adder-heading', 'hidden': False, 'section': self.clipboard_folder, 'path': self.clipboard_folder})
        if os.path.isdir(self.clipboard_folder):
            sections = os.listdir(self.clipboard_folder)
            for section in sections:
                if section in self.hiddens and not edit:
                    hidden = True
                else:
                    hidden = False
                section_folder = os.path.join(self.clipboard_folder, section)
                if os.path.isdir(section_folder):
                    self.clipboard_data.append({'text': section, 'viewtype': 'heading', 'hidden': hidden, 'section': section, 'path': section_folder, 'section_folder': self.clipboard_folder})
                    if edit:
                        self.clipboard_data.append({'text': 'Add Item', 'viewtype': 'adder-item', 'hidden': hidden, 'section': section, 'path': section_folder, 'section_folder': self.clipboard_folder})
                    for file in os.listdir(section_folder):
                        fullpath = os.path.join(section_folder, file)
                        if os.path.isfile(fullpath):
                            with open(fullpath, 'r') as datafile:
                                try:
                                    data = datafile.read()
                                except:
                                    continue
                            self.clipboard_data.append({'text': os.path.splitext(file)[0], 'viewtype': 'item', 'clipboard': data, 'hidden': hidden, 'section': section, 'path': fullpath, 'section_folder': section_folder})
        self.update_display_clipboards()

    def toggle_hide_section(self, section, hide_others=False):
        for data in self.clipboard_data:
            if data['section'] == section:
                if hide_others:
                    data['hidden'] = False
                else:
                    data['hidden'] = not data['hidden']
            elif hide_others:
                data['hidden'] = True
        self.save_hiddens()
        self.root.ids.presets.refresh_from_data()
        self.update_display_clipboards()

    def update_display_clipboards(self, *_):
        data = []
        for clip in self.clipboard_data:
            if not clip['hidden'] or clip['viewtype'] == 'heading':
                data.append(clip)
        self.clipboard_data_display = data

    def clear_history(self):
        self.clipboard_history = self.clipboard_history[:1]

    def remove_history_item(self, index):
        if index > 0:
            self.clipboard_history.pop(index)

    def set_history_item(self, index):
        try:
            history_item = self.clipboard_history.pop(index)
        except:
            return
        self.clipboard_history.insert(0, history_item)
        self.set_clipboard(history_item['text'], skip_history=True)

    def set_clipboard_from_widget(self, widget):
        if widget.focus:
            self.set_clipboard(widget.text, overwrite_history=True)

    def set_clipboard(self, text, skip_history=False, overwrite_history=False):
        #Sets a preset to the clipboard
        if text and text != self.current_clipboard:
            Clipboard.copy(text)
            if overwrite_history:
                if len(self.clipboard_history) == 0:
                    self.clipboard_history.append({'text': text})
                else:
                    self.clipboard_history[0]['text'] = text
                self.current_clipboard = text
                self.refresh_history_areas()
            if skip_history:
                self.current_clipboard = text

    def refresh_history_areas(self):
        self.root.ids.historyFull.refresh_from_data()
        self.root.ids.historyShort.refresh_from_data()

    def update_current_clipboard(self, *_):
        #Sets the current clipboard to a local variable

        clipboard = Clipboard.paste()
        if clipboard and self.current_clipboard != clipboard:
            self.current_clipboard = clipboard
            self.clipboard_history.insert(0, {'text': clipboard})
            self.clipboard_history = self.clipboard_history[:self.max_history]

    def undo_clipboard(self, *_):
        self.set_history_item(1)

    def strip_clipboard(self, *_):
        Clipboard.copy(self.current_clipboard.strip())

    def settings_mode(self, heading=''):
        self.close_settings()
        if self.modify_mode:
            self.modify_mode = False
            if self.root.ids.editArea.current == 'edit':
                self.load_clipboards()
        else:
            self.modify_mode = True
            if self.root.ids.editArea.current == 'edit':
                self.load_clipboards(edit=True)
        self.size_window()

    def delete_preset(self, preset):
        self.preset_type = preset.viewtype
        self.preset_element = preset.path

        if preset.viewtype == 'heading':
            confirm_text = "This entire section of presets will be deleted permanently"
        else:
            confirm_text = "This single preset will be deleted permanently"
        if self.popup:
            self.popup.dismiss()
            self.popup = None
        content = ConfirmPopupContent(text=confirm_text, yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        content.bind(on_answer=self.delete_preset_answer)
        self.popup = NormalPopup(title="Confirm Delete ", content=content, size_hint=(1, None), size=(1000, self.button_scale * 4))
        self.popup.open()

    def delete_preset_answer(self, instance, answer):
        self.popup.dismiss()
        self.popup = None
        if answer == 'yes':
            if self.preset_type == 'item':
                if os.path.isfile(self.preset_element):
                    os.remove(self.preset_element)
                    self.load_clipboards(edit=True)
            elif self.preset_type == 'heading':
                if os.path.isdir(self.preset_element):
                    shutil.rmtree(self.preset_element)
                    self.load_clipboards(edit=True)

    def edit_preset(self, preset):
        if preset.viewtype == 'item':
            self.edit_type = preset.viewtype
            self.edit_path = preset.path
            self.edit_name = preset.text
            self.edit_name_original = preset.text
            self.edit_section = preset.section_folder
            self.edit_content = preset.clipboard
            self.root.ids.editContentArea.focus = True
        elif preset.viewtype == 'heading':
            self.preset_type = 'heading'
            self.preset_element = preset.section_folder
            self.preset_second_element = preset.text
            content = InputPopupContent(text="Rename folder to:", input_text=preset.text, hint='Folder Name')
            content.bind(on_answer=self.rename_folder_answer)
            self.popup = NormalPopup(title="Rename Folder", content=content, size_hint=(1, None), size=(1000, self.button_scale * 5))
            self.popup.open()

    def rename_folder_answer(self, instance, answer):
        new_name = instance.ids["input"].text.strip(' ')
        self.popup.dismiss()
        self.popup = None
        if not new_name:
            return
        if answer == 'yes':
            old_path = os.path.join(self.preset_element, self.preset_second_element)
            new_path = os.path.join(self.preset_element, new_name)
            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    if self.edit_section == old_path:
                        self.edit_path = os.path.join(new_path, self.edit_name_original) + '.txt'
                        self.edit_section = new_path
                    self.load_clipboards(edit=True)
                except Exception as e:
                    app.message_popup(text="Unable to rename folder: "+str(e), title="Warning")

    def save_edit(self):
        if not self.edit_path or not self.edit_name or not self.edit_section:
            return
        new_file = os.path.join(self.edit_section, self.edit_name) + '.txt'
        if new_file != self.edit_path:
            #rename file
            try:
                os.rename(self.edit_path, new_file)
                self.edit_path = new_file
            except Exception as e:
                app.message_popup(text="Unable to save edit: "+str(e), title="Warning")
                return
        try:
            file = open(self.edit_path, "w")
            file.write(self.edit_content)
            file.close()
            self.load_clipboards(edit=True)
        except Exception as e:
            app.message_popup(text="Unable to write to file: "+str(e), title="Warning")

    def instant_add(self, path, section):
        if self.popup:
            self.popup.dismiss()
            self.popup = None
        if not self.modify_mode:
            self.settings_mode()
        self.edit_type = 'item'
        self.edit_path = path
        self.edit_name = ''
        self.edit_name_original = ''
        self.edit_section = section
        self.edit_content = self.current_clipboard

        content = InstantAddPresetContent()
        content.bind(on_answer=self.instant_add_preset_answer)
        self.popup = NormalPopup(title='Create File', content=content, size_hint=(1, 1), size=(1000, 2000))
        self.popup.open()

    def instant_add_preset_answer(self, instance, answer):
        self.popup.dismiss()
        self.popup = None
        if answer == 'yes':
            filename = os.path.join(self.edit_path, self.edit_name) + '.txt'
            if os.path.exists(filename):
                self.message_popup(text="File already exists!", title="Warning")
                return
            file = open(filename, 'w')
            file.write(self.edit_content)
            file.close()
            self.load_clipboards()

    def add_preset(self, preset_type, preset_location):
        self.preset_type = preset_type
        self.preset_element = preset_location
        if preset_type == 'heading':
            input_text = "Add a folder with the name:"
            hint_text = "Folder Name"
            title_text = "Create Folder"
        else:
            input_text = "Add a preset with the name:"
            hint_text = "Preset Name"
            title_text = "Create File"
        if self.popup:
            self.popup.dismiss()
            self.popup = None

        content = InputPopupContent(text=input_text, hint=hint_text)
        content.bind(on_answer=self.add_preset_answer)
        self.popup = NormalPopup(title=title_text, content=content, size_hint=(1, None), size=(1000, self.button_scale * 5))
        self.popup.open()

    def add_preset_answer(self, instance, answer):
        preset_name = instance.ids['input'].text.strip(' ')
        self.popup.dismiss()
        self.popup = None
        if not preset_name:
            return
        if answer == 'yes':
            preset_type = self.preset_type
            preset_location = self.preset_element
            if preset_type == 'heading':
                path = os.path.join(preset_location, preset_name)
                try:
                    os.makedirs(path)
                except Exception as e:
                    app.message_popup(text="Unable to create folder: "+str(e), title="Warning")
                self.load_clipboards(edit=True)
            else:
                filename = os.path.join(preset_location, preset_name) + '.txt'
                if not os.path.isfile(filename):
                    try:
                        file = open(filename, 'w+')
                        file.close()
                        self.edit_type = preset_type
                        self.edit_path = filename
                        self.edit_name = preset_name
                        self.edit_name_original = preset_name
                        self.edit_section = preset_location
                        self.edit_content = ''
                        self.root.ids.editContentArea.focus = True
                    except Exception as e:
                        app.message_popup(text="Unable to create file: "+str(e), title="Warning")
                    self.load_clipboards(edit=True)
                else:
                    app.message_popup(text="File already exists!", title="Warning")

    def load_clipboard_folders(self):
        folders = [self.clipboard_folder]
        folder_items = self.config.items("PresetsPaths")
        for key, folder in folder_items:
            if folder not in folders:
                folders.append(folder)
        folders_data = []
        for folder in folders:
            if folder:
                folders_data.append({'path': folder})
        self.clipboard_folders = folders_data

    def save_clipboard_folders(self):
        self.config.remove_section("PresetsPaths")
        self.config.add_section("PresetsPaths")
        for index, folder_item in enumerate(self.clipboard_folders):
            folder = folder_item['path']
            self.config.set("PresetsPaths", str(index), folder)

    def remove_presets_folder(self, path):
        for index, preset in enumerate(self.clipboard_folders):
            if preset['path'] == path:
                self.clipboard_folders.pop(index)
                self.save_clipboard_folders()

    def set_presets_folder(self, path):
        self.save_hiddens()
        self.clipboard_folder = path
        self.config.set("Settings", "presetsfolder", path)
        self.load_clipboards()

    def add_presets_folder(self, *_):
        self.not_on_top()
        from plyer import filechooser
        try:
            filechooser.choose_dir(on_selection=self.add_presets_folder_finish, title='Select A Presets Directory')
        except:
            #Filechooser can fail if user selects root
            if self.config.getboolean("Settings", "alwaysontop"):
                self.always_on_top()
            pass

    def add_presets_folder_finish(self, path):
        if self.config.getboolean("Settings", "alwaysontop"):
            self.always_on_top()
        path = path[0]
        if path:
            if path not in self.clipboard_folders:
                self.clipboard_folders.append({'path': path})
                self.save_clipboard_folders()
                self.set_presets_folder(path)
            else:
                self.message("Path Already Added")
        else:
            self.message("No Path Found")

    def browse_presets(self):
        try:
            import webbrowser
            webbrowser.open(self.clipboard_folder)
        except:
            pass

    def size_window(self, *_):
        Window.left = self.window_left
        Window.top = self.window_top
        height = self.window_height
        width = int(self.button_scale * 4 * (float(self.config.get("Settings", "normalwidth")) / 100))
        if width < self.window_min_width:
            width = self.window_min_width
        if self.modify_mode:
            self.window_width_target = width
            width = int(self.button_scale * 17 * (float(self.config.get("Settings", "expandedwidth")) / 100))
            Window.size = width, height
        else:
            Window.size = width, height
            self.window_width_target = Window.width

    def on_button_scale(self, *_):
        self.size_window()

    def save_hiddens(self):
        if not self.clipboard_folder:
            return
        hiddens = []
        for data in self.clipboard_data:
            if data['hidden'] and data['viewtype'] == 'heading':
                section = data['section']
                if section not in hiddens:
                    hiddens.append(section)

        hiddens_filename = os.path.join(self.clipboard_folder, 'hiddens.txt')
        try:
            hiddens_file = open(hiddens_filename, 'w')
        except:
            return
        for hidden in hiddens:
            hiddens_file.write(hidden+'\n')
        hiddens_file.close()

    def load_hiddens(self):
        hiddens = []
        hiddens_filename = os.path.join(self.clipboard_folder, 'hiddens.txt')
        try:
            hiddens_file = open(hiddens_filename, 'r')
        except:
            self.hiddens = []
            return
        lines = hiddens_file.readlines()
        hiddens_file.close()
        for line in lines:
            line = line.strip('\n')
            if line:
                hiddens.append(line)
        self.hiddens = hiddens

    def build_config(self, config):
        """Setup config file if it is not found"""

        window_height, window_width, window_top, window_left = self.get_window_size()
        config.setdefaults(
            'Settings', {
                'buttonsize': 100,
                'textsize': 100,
                'expandedwidth': 100,
                'normalwidth': 100,
                'alwaysontop': 1,
                'minimizestart': 0,
                'minimizetray': 0,
                'showtray': 1,
                'auto_shrink': 0,
                'auto_expand': 0,
                'showundo': 1,
                'showstrip': 0,
                'presetsfolder': '',
                'max_history': 20,
                'main_history_length': 1,
                'window_height': window_height,
                'window_top': window_top,
                'window_left': window_left,
                'window_width': window_width
            })
        config.setdefaults(
            'PresetsPaths', {}
        )

    def build_settings(self, settings):
        """Kivy settings dialog panel
        settings types: title, bool, numeric, options, string, path"""

        settingspanel = []
        settingspanel.append({
            "type": "label",
            "title": "        Basic Behavior"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Max Clipboard History",
            "desc": "Number of entries to keep in clipboard history. Defaluts to 20.",
            "section": "Settings",
            "key": "max_history"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Auto-Shrink Window",
            "desc": "Automatically shrink the window when the mouse leaves.",
            "section": "Settings",
            "key": "auto_shrink"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Auto-Expand Window",
            "desc": "Automatically expand the window when the mouse enters.",
            "section": "Settings",
            "key": "auto_expand"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Minimize On Startup",
            "desc": "Automatically minimize the program as soon as it starts.",
            "section": "Settings",
            "key": "minimizestart"
        })
        if platform == 'win':
            settingspanel.append({
                "type": "bool",
                "title": "Always-On-Top",
                "desc": "Sets the window to always-on-top mode on startup.  Changing requires a program restart.",
                "section": "Settings",
                "key": "alwaysontop"
            })
            settingspanel.append({
                "type": "bool",
                "title": "Show Tray Icon",
                "desc": "A tray icon will be shown with options.  Changing requires program restart.",
                "section": "Settings",
                "key": "showtray"
            })
            settingspanel.append({
                "type": "bool",
                "title": "Minimize To Tray",
                "desc": "Minimize to tray when minimizing the window.  Only available when tray icon is enabled.",
                "section": "Settings",
                "key": "minimizetray"
            })

        settingspanel.append({
            "type": "label",
            "title": "        Main Window Appearance"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Show Undo Clipboard Button",
            "desc": "Shows a button to undo the clipboard to the previous state.",
            "section": "Settings",
            "key": "showundo"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Show Strip Clipboard Button",
            "desc": "Shows a button to remove all formatting and extra spaces from clipboard text.",
            "section": "Settings",
            "key": "showstrip"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "History In Main Window",
            "desc": "Number of history elements to show in main window. Defaults to 1.",
            "section": "Settings",
            "key": "main_history_length"
        })

        settingspanel.append({
            "type": "label",
            "title": "        Interface Scaling"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Shrunk Width Scale",
            "desc": "Scale of the window when it is in normal mode. Expects a percentage, defaults to 100",
            "section": "Settings",
            "key": "normalwidth"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Expanded Width Scale",
            "desc": "Scale of the window when it is in expanded mode. Expects a percentage, defaults to 100",
            "section": "Settings",
            "key": "expandedwidth"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Button Scale",
            "desc": "Button scale, expects a percentage, defaults to 100.",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Text Scale",
            "desc": "Font scale, expects a percentage, defaults to 100.",
            "section": "Settings",
            "key": "textsize"
        })
        settings.add_json_panel('Settings', self.config, data=json.dumps(settingspanel))

    def build(self):
        global app
        app = self
        if platform == 'win' and self.config.getboolean("Settings", "showtray"):
            #setup system tray
            from infi.systray import SysTrayIcon
            tray_menu = (("Toggle Minimize", None, self.tray_click), ("Undo Clipboard", None, self.undo_clipboard), ("Strip Clipboard", None, self.strip_clipboard), )
            icon_file = kivy.resources.resource_find('icon.ico')
            self.tray = SysTrayIcon(icon_file, 'Snu Clipboard Manager', tray_menu, on_quit=self.tray_quit)
            self.tray.start()
        else:
            self.tray = None

        self.clipboard_folder = self.config.get("Settings", "presetsfolder")
        self.load_clipboard_folders()
        self.load_clipboards()
        Window.bind(on_key_down=self.key_down)
        Window.bind(on_key_up=self.key_up)
        Window.bind(on_cursor_leave=self.window_exited)
        Window.bind(on_cursor_enter=self.window_entered)
        Window.bind(on_minimize=self.on_minimize)
        Window.bind(on_restore=self.on_restore)
        return MainScreen()

    def tray_quit(self, tray):
        Clock.schedule_once(self.stop)

    def tray_click(self, tray):
        if self.window_minimized:
            Clock.schedule_once(self.restore)
        else:
            Clock.schedule_once(self.minimize)

    def restore(self, *_):
        Window.restore()

    def minimize(self, *_):
        Window.minimize()

    def on_restore(self, window):
        self.window_minimized = False
        Window.show()

    def on_minimize(self, window):
        self.window_minimized = True
        if self.config.getboolean("Settings", "minimizetray") and self.tray is not None:
            Window.hide()

    def window_exited(self, window):
        self.window_leave_timeout = Clock.schedule_once(self.window_exited_finish, 1)

    def window_entered(self, window):
        self.window_entered_finish()
        if self.window_leave_timeout is not None:
            self.window_leave_timeout.cancel()
            self.window_leave_timeout = None

    def window_exited_finish(self, *_):
        if self.config.getboolean("Settings", 'auto_shrink'):
            if self.modify_mode and self.popup is None and self.root.ids.editArea.current != 'edit':
                self.settings_mode()

    def window_entered_finish(self, *_):
        if self.config.getboolean("Settings", 'auto_expand'):
            if not self.modify_mode:
                self.settings_mode()

    def on_start(self):
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        self.load_config_values()
        Window.set_title(self.window_title)
        if self.config.getboolean("Settings", "alwaysontop"):
            self.always_on_top()
        self.load_window_size()
        self.clipboard_updater = Clock.schedule_interval(self.update_current_clipboard, 0.1)
        if not self.clipboard_folder:
            self.root.ids.editArea.current = 'select'
            self.modify_mode = True
            Clock.schedule_once(self.add_presets_folder)
        else:
            self.modify_mode = False
        self.size_window()
        if self.config.getboolean("Settings", "minimizestart"):
            self.minimize()

    def always_on_top(self, *_):
        #Set on top mode
        self.on_top = True
        from KivyOnTop import register_topmost
        register_topmost(Window, self.window_title)

    def not_on_top(self, *_):
        self.on_top = False
        from KivyOnTop import unregister_topmost
        unregister_topmost(Window, self.window_title)

    def toggle_on_top(self):
        if self.on_top:
            self.not_on_top()
        else:
            self.always_on_top()

    def get_window_size(self):
        #Get window size
        if platform == 'win':
            SPI_GETWORKAREA = 48
            SM_CXSCREEN = 0
            SM_CYSCREEN = 1  #The height of the screen of the primary display monitor, in pixels.
            SM_CYCAPTION = 4  #The height of a caption area, in pixels.
            SM_CYBORDER = 6  #The height of a window border, in pixels.
            SM_CYFIXEDFRAME = 8  #The thickness of the frame around the perimeter of a window that has a caption but is not sizable, in pixels.

            from win32api import GetSystemMetrics
            taskbar_height = GetSystemMetrics(SPI_GETWORKAREA)
            screen_height = GetSystemMetrics(SM_CYSCREEN)
            screen_width = GetSystemMetrics(SM_CXSCREEN)
            window_frame_size = GetSystemMetrics(SM_CYFIXEDFRAME) + GetSystemMetrics(SM_CYBORDER)
            window_left_offset = window_frame_size
            window_top_offset = GetSystemMetrics(SM_CYCAPTION) + window_frame_size
            window_height = screen_height - window_top_offset - window_left_offset - taskbar_height
            window_width = screen_width - window_left_offset - window_left_offset
            return window_height, window_width, window_top_offset, window_left_offset
        else:
            return 680, self.window_min_width, 30, 5

    def on_pause(self):
        self.save_hiddens()
        self.config.write()
        return True

    def on_stop(self):
        if not (self.modify_mode and self.root.ids.editArea.current == 'edit'):
            self.save_hiddens()
        self.config.write()
        if self.tray is not None:
            self.tray.shutdown()

    def toggle_area(self, area):
        self.close_settings()
        if not self.modify_mode:
            self.root.ids.editArea.current = area
            self.modify_mode = True
            if area == 'edit':
                self.load_clipboards(edit=True)
            self.size_window()
        else:
            if self.root.ids.editArea.current == area:
                self.modify_mode = False
                self.load_clipboards()
                self.size_window()
            else:
                self.root.ids.editArea.current = area
                if area == 'edit':
                    self.load_clipboards(edit=True)

    def text_input_active(self):
        """Checks if any 'NormalInput' or 'FloatInput' widgets are currently active (being typed in).
        Returns: True or False
        """

        input_active = False
        for widget in self.root.walk(restrict=True):
            if widget.__class__.__name__ == 'NormalInput' or widget.__class__.__name__ == 'FloatInput' or widget.__class__.__name__ == 'IntegerInput':
                if widget.focus:
                    input_active = True
                    break
        return input_active

    def hook_keyboard(self, window, scancode, *_):
        """This function receives keyboard events"""

        #print(scancode)
        if scancode == 282:
            #f1 key
            if not self.modify_mode:
                self.settings_mode()
        if scancode == 27:
            #escape key
            if self.popup:
                self.popup.content.dispatch('on_answer', 'no')
                return True
        if scancode == 13:
            #enter key
            if self.popup:
                self.popup.content.dispatch('on_answer', 'yes')
        if scancode == 96:
            #tilde key
            if self.alt_pressed or self.ctrl_pressed or not self.text_input_active():
                self.settings_mode()
        if scancode == 283:
            #f2 key
            self.toggle_area('history')
        if scancode == 284:
            #f3 key
            self.toggle_area('edit')
        if scancode == 285:
            #f4 key
            self.toggle_area('select')
        if scancode == 97:
            #a key
            if self.alt_pressed:
                self.toggle_on_top()
        if scancode == 109:
            #m key
            if self.alt_pressed:
                self.minimize()

    def key_down(self, key, scancode=None, *_):
        """Intercepts various key presses and sends commands to the current screen."""

        del key
        if scancode == 307 or scancode == 308:
            #alt keys
            self.alt_pressed = True
        if scancode == 305 or scancode == 306:
            #ctrl keys
            self.ctrl_pressed = True
        if scancode == 303 or scancode == 304:
            #shift keys
            self.shift_pressed = True

    def key_up(self, key, scancode=None, *_):
        """Checks for the shift key released."""

        del key
        if scancode == 307 or scancode == 308:
            self.alt_pressed = False
        if scancode == 305 or scancode == 306:
            self.ctrl_pressed = False
        if scancode == 303 or scancode == 304:
            self.shift_pressed = False


if __name__ == '__main__':
    SnuClipboardManager().run()
