# window.py
#
# Copyright 2022 Dimitris Psathas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import numpy as np
import matplotlib.pyplot as plt
import scipy.stats
import os
import shutil
from gi.repository import Gtk, Gio


@Gtk.Template(resource_path='/com/dpsoftware/gaussian/window.ui')
class GaussianWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'GaussianWindow'

    grid = Gtk.Template.Child()
    calc_btn = Gtk.Template.Child()
    clear_btn = Gtk.Template.Child()
    save_btn = Gtk.Template.Child()
    mean_entry = Gtk.Template.Child()
    dev_entry = Gtk.Template.Child()
    score_entry = Gtk.Template.Child()
    prob_entry = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.calc_btn.set_label('Calculate')
        self.calc_btn.connect('clicked', self.calculation)
        self.clear_btn.set_label('Clear')
        self.clear_btn.set_tooltip_text('Clear all fields')
        self.clear_btn.connect('clicked', self.clear_entries)
        self.save_btn.set_label('Save')
        self.save_btn.set_tooltip_text('Save plotted image to disk')
        self.save_btn.connect('clicked', self.save_image)

        self.mean_entry.connect('activate', self.calculation)
        self.mean_entry.connect('changed', self.validate)
        self.dev_entry.connect('activate', self.calculation)
        self.dev_entry.connect('changed', self.validate)
        self.score_entry.connect('activate', self.calculation)
        self.score_entry.connect('changed', self.validate)
        self.prob_entry.connect('activate', self.calculation)
        self.prob_entry.connect('changed', self.validate)

        settings = Gio.Settings.new("com.dpsoftware.gaussian")
        self.mean_entry.set_text(str(settings.get_int("mean")))
        self.dev_entry.set_text(str(settings.get_int("dev")))
        self.set_focus(self.score_entry)

        self.save_btn.set_visible(False)
        self.filename = ''

        self.set_default_size(480, 224)

    def validate(self, widget):
        text = widget.get_text()
        if len(text):
            try:
                num = float(text)
            except ValueError:
                new_num = text[:len(text)-1]
                widget.set_text(new_num)

    def calculation(self, widget):
        if self.mean_entry.get_text_length != 0 and self.dev_entry.get_text_length != 0:
            try:
                mean = int(self.mean_entry.get_text())
                dev = int(self.dev_entry.get_text())
                if self.score_entry.get_text_length() == 0:
                    prob = float(self.prob_entry.get_text())
                    score = scipy.stats.norm.ppf(prob, mean, dev)
                    self.score_entry.set_text(str(int(round(score))))
                    self.plot(mean, dev, score, prob)
                elif self.prob_entry.get_text_length() == 0:
                    score = int(self.score_entry.get_text())
                    prob = scipy.stats.norm.cdf(score, mean, dev)
                    self.prob_entry.set_text(str(round(prob, 6)))
                    self.plot(mean, dev, score, prob)
                else:
                    self.show_error(self, 'Only one out of 4 values must be left empty.')
                settings = Gio.Settings.new("com.dpsoftware.gaussian")
                settings.set_int("mean", mean)
                settings.set_int("dev", dev)
            except ValueError:
                self.show_error(self, 'Invalid values entered.')
        else:
            self.show_error(self, 'Invalid values entered.')

    def plot(self, mean, dev, score, prob):
        for _ in range(12):
            self.grid.remove_row(4)

        z1 = (0 - mean) / dev
        z2 = (score - mean) / dev

        x = np.arange(z1, z2, 0.001)
        x_all = np.arange(-10, 10, 0.001)
        y = scipy.stats.norm.pdf(x, 0, 1)
        y2 = scipy.stats.norm.pdf(x_all, 0, 1)

        fig, ax = plt.subplots(figsize=(9, 7))
        ax.plot(x_all, y2)

        ax.fill_between(x, y, 0, alpha=0.3, color='b')
        ax.fill_between(x_all, y2, 0, alpha=0.1)
        ax.set_xlim([-4, 4])
        ax.set_xlabel(f'# of Standard Deviations Outside the Mean\n'
                      f'Standard Score: {score}\nCumulative Probability: {prob}')
        ax.set_yticklabels([])
        ax.set_title('Normal Gaussian Curve')

        plt.grid(True)

        image_path = os.path.expanduser('~') + '/.cache/gaussian'
        if os.path.exists(image_path):
            shutil.rmtree(image_path)
        os.makedirs(image_path)
        self.filename = image_path + '/normal_curve.png'
        plt.savefig(self.filename, dpi=300, bbox_inches='tight')
        if os.path.exists(self.filename):
            self.grid.insert_row(4)
            img_widget = Gtk.Image.new_from_file(self.filename)
            self.grid.attach(img_widget, 0, 4, 2, 12)
        plt.close()

        self.save_btn.set_visible(True)

    def clear_entries(self, widget):
        for entry in [self.mean_entry, self.dev_entry, self.score_entry, self.prob_entry]:
            entry.set_text('')
        for _ in range(12):
            self.grid.remove_row(4)
        self.set_default_size(480, 224)
        self.save_btn.set_visible(False)

    def save_image(self, widget):
        if os.path.exists(self.filename):
            shutil.copyfile(self.filename, os.path.expanduser('~') + '/normal_curve.png')
            if os.path.exists('normal_curve.png'):
                dialog = Gtk.MessageDialog(
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text='Image saved successfully at home directory',
                    transient_for=self
                )
                dialog.present()
                dialog.connect('response', lambda self, dialog: self.destroy())
            else:
                show_error(self, 'No image to save, please try again.')
        else:
            show_error(self, 'No image to save, please try again.')

    def show_error(self, parent, msg):
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=msg,
            transient_for=parent
        )
        dialog.present()
        dialog.connect('response', lambda self, dialog: self.destroy())


class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.props.program_name = 'Gaussian'
        self.props.version = "0.1.0"
        self.props.authors = ['Dimitris Psathas']
        self.props.website_label = 'https://github.com/dimitris47/gaussian'
        self.props.copyright = '2022 Dimitris Psathas'
        self.props.logo_icon_name = 'com.dpsoftware.gaussian'
        self.props.modal = True
        self.set_transient_for(parent)

