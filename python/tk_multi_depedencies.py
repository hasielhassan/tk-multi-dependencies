# -*- coding: utf-8 -*-
import sys
import time
import random
import traceback

import tank
from tank import TankError
from tank.platform.qt import QtCore, QtGui

from ui import card_form
from ui import dialog_form


class Card(QtGui.QWidget):

    def __init__(self, item_data):
        super(Card, self).__init__()
        self.ui = card_form.Ui_Form()
        self.ui.setupUi(self)

        self.type = item_data['type']
        self.status = item_data['status']
        self.selected = item_data['selected']

        if self.selected:
            state = QtCore.Qt.CheckState(QtCore.Qt.Checked)
        else:
            state = QtCore.Qt.CheckState(QtCore.Qt.Unchecked)
        self.ui.checkBox.setCheckState(state)

        self.ui.checkBox.stateChanged.connect(self.update_selected)

    def update_selected(self, state):

        if state == 0:
            self.selected = False
        else:
            self.selected = True

    def set_status_action(self, action):

        if action == 'checkbox':
            self.ui.statusAction.setCurrentIndex(0)
        elif action == 'success':
            self.ui.statusAction.setCurrentIndex(1)
        else:
            self.ui.statusAction.setCurrentIndex(2)
            self.traceback = action
            self.ui.button_traceback.clicked.connect(self.show_traceback)

    def show_traceback(self):

        QtGui.QMessageBox.information(self, "Reported Error", self.traceback)


class ScanScene(QtCore.QThread):

    result = QtCore.Signal(list)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):

        time.sleep(4)

        items = []

        for i in range(12):

            item = {'type': 'default',
                    'status': random.choice(['published', 'unpublished']),
                    'selected': random.choice([True, False])}
            items.append(item)

        self.result.emit(items)

class PublishItems(QtCore.QThread):

    progress = QtCore.Signal(dict)
    finish = QtCore.Signal(dict)

    def __init__(self, items):
        QtCore.QThread.__init__(self)
        self.items = items

    def run(self):

        errors = []
        success = []

        current_progress = 10
        self.progress_status("Preparing publishing...", current_progress)

        progress_per_item = 90.0 / len(self.items)
        for item in self.items:

            message = 'Publishing Item: %s' % item.type
            current_progress += progress_per_item

            try:
                time.sleep(2)

                "Test" + random.choice([3, "Error", "False"])
                
                item.set_status_action('success')
                success.append(item)
            except:
                item.set_status_action(traceback.format_exc())
                errors.append(item)

            self.progress_status(message, current_progress)

        self.finish.emit({'errors': errors, 'success': success})

    def progress_status(self, message, progress):

        self.progress.emit({'message': message, 'progress': progress})

class Dialog(QtGui.QWidget):

    def __init__(self, app):
        super(Dialog, self).__init__()

        self._app = app

        self.ui = dialog_form.Ui_Form()
        self.ui.setupUi(self)

        self.scaned_items = []

        self.ui.button_publish_rescan.clicked.connect(self.start_scan)
        self.ui.button_select_unpublished.clicked.connect(self.select_unpublished)
        self.ui.button_publish_selected.clicked.connect(self.collect_selected_to_publish)
        self.ui.button_publish_al.clicked.connect(self.collect_all_to_publish)
        self.ui.checkbox_publish_ones.stateChanged.connect(self.filter_published_items)
        self.ui.checkbox_unpublish_ones.stateChanged.connect(self.filter_unpublished_items)

        #start scene scan
        self.start_scan()


    def start_scan(self):

        self.ui.stackedWidget.setCurrentIndex(0)

        self.ui.button_publish_rescan.setEnabled(False)
        self.ui.button_select_unpublished.setEnabled(False)
        self.ui.button_publish_al.setEnabled(False)
        self.ui.button_publish_selected.setEnabled(False)
        self.ui.checkbox_unpublish_ones.setEnabled(False)
        self.ui.checkbox_publish_ones.setEnabled(False)

        self.scan_scene_thread = ScanScene()
        self.scan_scene_thread.result.connect(self.scan_success)
        self.scan_scene_thread.start()

    def scan_success(self, data):

        scroll_layout = self.ui.scrollAreaWidgetContents.layout()

        #Ensure clear all stored items
        del self.scaned_items[:]

        for i in reversed(range(scroll_layout.count())): 
            widgetToRemove = scroll_layout.itemAt( i ).widget()
            # remove it from the layout list
            scroll_layout.removeWidget( widgetToRemove )
            # remove it from the gui
            widgetToRemove.setParent( None )

        for item in data:
            card_container = Card(item)
            card_container.set_status_action('checkbox')
            self.scaned_items.append(card_container)

            #Only show the item if the filters match
            if self.ui.checkbox_unpublish_ones.checkState() and card_container.status == 'unpublished':
                self.ui.scrollAreaWidgetContents.layout().addWidget(card_container)
            elif self.ui.checkbox_publish_ones.checkState() and card_container.status == 'published':
                self.ui.scrollAreaWidgetContents.layout().addWidget(card_container)

        self.ui.stackedWidget.setCurrentIndex(1)

        self.ui.button_publish_rescan.setEnabled(True)
        self.ui.button_select_unpublished.setEnabled(True)
        self.ui.button_publish_al.setEnabled(True)
        self.ui.button_publish_selected.setEnabled(True)
        self.ui.checkbox_unpublish_ones.setEnabled(True)
        self.ui.checkbox_publish_ones.setEnabled(True)

    def select_unpublished(self):

        for card in self.scaned_items:

            if card.status == 'unpublished':
        
                state = QtCore.Qt.CheckState(QtCore.Qt.Checked)
                card.ui.checkBox.setCheckState(state)

    def filter_published_items(self, state):

        if state == 0:
            #Remove published cards
            self.remove_cards_from_Scroll('published')
        else:
            self.add_cards_to_scroll('published')

    def filter_unpublished_items(self, state):

        if state == 0:
            #Remove unpublished cards
            self.remove_cards_from_Scroll('unpublished')
        else:
            self.add_cards_to_scroll('unpublished')

    def add_cards_to_scroll(self, status):

        for card in self.scaned_items:
            if card.status == status:
                self.ui.scrollAreaWidgetContents.layout().addWidget(card)

    def remove_cards_from_Scroll(self, status):

        scroll_layout = self.ui.scrollAreaWidgetContents.layout()

        for i in reversed(range(scroll_layout.count())):
            widgetToRemove = scroll_layout.itemAt( i ).widget()
            if widgetToRemove.status == status:
                # remove it from the layout list
                scroll_layout.removeWidget( widgetToRemove )
                # remove it from the gui
                widgetToRemove.setParent( None )

    def collect_selected_to_publish(self):

        items_to_publish = []

        for card in self.scaned_items:
            if card.selected:
                items_to_publish.append(card)

        self.publish_items(items_to_publish)

    def collect_all_to_publish(self):

        self.publish_items(self.scaned_items)

    def publish_items(self, items):

        self.ui.button_publish_rescan.setEnabled(False)
        self.ui.button_select_unpublished.setEnabled(False)
        self.ui.button_publish_al.setEnabled(False)
        self.ui.button_publish_selected.setEnabled(False)
        self.ui.checkbox_unpublish_ones.setEnabled(False)
        self.ui.checkbox_publish_ones.setEnabled(False)

        self.publish_thread = PublishItems(items)
        self.publish_thread.progress.connect(self.update_progress)
        self.publish_thread.finish.connect(self.publish_finish)

        self.ui.stackedWidget.setCurrentIndex(2)

        self.publish_thread.start()

    def update_progress(self, data):

        self.ui.progressBar.setValue(data['progress'])
        self.ui.statusMessage.setText(data['message'])

    def publish_finish(self, data):

        if len(data['errors']) != 0:

            self.ui.stackedWidget.setCurrentIndex(3)

            for item in data['errors']:
                self.ui.scrollAreaWidgetContentsErrors.layout().addWidget(item)

            for item in data['success']:
                self.ui.scrollAreaWidgetContentsErrors.layout().addWidget(item)

        else:
            self.ui.stackedWidget.setCurrentIndex(4)

        self.ui.button_publish_rescan.setEnabled(True)