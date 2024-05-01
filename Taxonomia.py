from random import randint
import xerox
import sys
from math import sqrt
from time import sleep
from tabulate import tabulate
import urllib

import taxoniq
import pyinaturalist
import wikipedia
import webbrowser

from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

def lowest_commonality(taxon1, taxon2):
    pass

def taxon_to_message(taxon):
    try:
        guess_message = f"{str(taxon.rank)[5:]}: {taxon.scientific_name} ({taxon.common_name})"
    except:
        guess_message = f"{str(taxon.rank)[5:]}: {taxon.scientific_name}"
    return guess_message
def str_with_plus(num):
    if num > 0:
        return '+' + str(num)
    else:
        return str(num)

def get_image_hint(taxon):
    try:
        name = taxon.common_name
    except:
        name = taxon.scientific_name
    observations = pyinaturalist.get_observations(taxon_name=taxon.scientific_name, photos=True)["results"]
    print(name, len(observations))
    if observations:
        image_url = observations[randint(0, len(observations)-1)]["taxon"]["default_photo"]["medium_url"]
        return image_url

class OpeningDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.target = 0

        self.setWindowTitle("Taxonomia")

        self.vert_layout = QVBoxLayout()
        self.horizontal_layout = QHBoxLayout()
        self.vert_layout.addLayout(self.horizontal_layout)

        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_line_update)
        self.horizontal_layout.addWidget(self.line_edit)

        self.button = QPushButton('Enter genus-code')
        self.button.setShortcut(QKeySequence(Qt.Key_Return))
        self.button.setDisabled(True)
        self.button.clicked.connect(self.on_enter)
        self.horizontal_layout.addWidget(self.button)

        self.random_button = QPushButton('Pick random')
        self.random_button.clicked.connect(self.on_random)
        self.vert_layout.addWidget(self.random_button)

        self.setLayout(self.vert_layout)
    def on_line_update(self):
        try:
            self.target = taxoniq.Taxon(sqrt(int(self.line_edit.text())))
            if self.target.rank == taxoniq.Rank.genus:
                self.button.setDisabled(False)
        except:
            self.button.setDisabled(True)
    def on_enter(self):
        self.close()
    def on_random(self):
        done = False
        fail_count = 0
        while not done:
            fail_count += 1
            try:
                self.target = taxoniq.Taxon(randint(0, 100000000))
                if self.target.rank == taxoniq.Rank.genus:
                    sci = self.target.scientific_name
                    com = self.target.common_name
                    done = True
            except:
                done = False
        self.close()

class WinDialog(QDialog):
    def __init__(self, try_list, solution):
        super().__init__()
        self.setWindowTitle("Taxonomia")
        self.vert_layout = QVBoxLayout()
        self.setLayout(self.vert_layout)

        self.try_list = try_list
        self.solution = solution

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.vert_layout.addWidget(self.text_edit)

        self.copy_button = QPushButton("Share on Discord")
        self.copy_button.setStyleSheet("background-color: #f0f0f0; color: #000000; border: 1px solid #808080;")
        self.copy_button.pressed.connect(self.copy_score)
        self.vert_layout.addWidget(self.copy_button)

        message = f"""<table style="border: 1px solid black; border-collapse: collapse;">
                    <caption style="font-size: 40px; font-weight: bold;" align="center">You Win!</caption>
                    <p align="center">You needed {len(self.try_list)} tries.</p>
                      <tr>
                        <th style="border: 1px solid black; padding: 8px;">Try Nr.</th>
                        <th style="border: 1px solid black; padding: 8px;">Tried Name</th>
                        <th style="border: 1px solid black; padding: 8px;">Commonality</th>
                        <th style="border: 1px solid black; padding: 8px;">Accuracy</th>
                        <th style="border: 1px solid black; padding: 8px;">Progress</th>
                      </tr>"""
        for try_set in try_list:
            message += "<tr>"
            for element in try_set:
                if try_set == try_list[-1]:
                    message += f"""<td style="border: 1px solid black; padding: 8px;"><b>{element}</b></td>"""
                else:
                    message += f"""<td style="border: 1px solid black; padding: 8px;">{element}</td>"""
            message += "</tr>"
        message += "</table>"
        self.text_edit.setText(message)
        self.setGeometry(600, 200, 600, 600)


    def copy_score(self):
        # self.adjustSize()
        table = tabulate(self.try_list, headers=["Try Nr.", "Tried Name", "Commonality", "Accuracy", "Progress"])
        genus_code = str(self.solution.tax_id**2)
        message = f"""I won Taxonomia!!! 
genus-code: **{genus_code}**
It took me **{len(self.try_list)} tries**. can you beat me?
Download [Taxonomia on Github](https://github.com/Hexogrammer/Taxonomia)

Guess history:
||`{table}`||"""
        xerox.copy(message, xsel=True)
        self.copy_button.setText("Copied")
        self.copy_button.setDisabled(True)
        QTimer.singleShot(1000, lambda: [self.copy_button.setText("Share on Discord"), self.copy_button.setDisabled(False)])

class HintDialog(QDialog):
    def __init__(self, last_correct_name, next_correct_rank, image_url):
        super().__init__()
        self.setWindowTitle("Taxonomia")
        self.setWindowModality(Qt.NonModal)
        self.vert_layout = QVBoxLayout()
        self.setLayout(self.vert_layout)
        self.vert_layout.addWidget(QLabel(f"Random species of the correct {next_correct_rank} (after {last_correct_name})."))

        data = urllib.request.urlopen(image_url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.vert_layout.addWidget(self.image_label)
        print(image_url)
        print(pixmap)
        print(self.image_label)

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taxonomia")

        self.tries = 0
        self.try_list = []
        self.next_correct = None
        self.last_correct = None
        self.last_ind = 0
        self.last_accuracy = 1

        self.main_layout = QHBoxLayout()

        self.vert_layout = QVBoxLayout()
        self.main_layout.addLayout(self.vert_layout)

        self.horizontal_layout = QHBoxLayout()

        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_text_update)
        self.horizontal_layout.addWidget(self.line_edit)

        self.enter_button = QPushButton("Enter")
        self.enter_button.setShortcut(QKeySequence(Qt.Key_Return))
        self.enter_button.setDisabled(True)
        self.enter_button.clicked.connect(self.on_enter)
        self.horizontal_layout.addWidget(self.enter_button)

        self.hint_button = QPushButton("Hint")
        self.hint_button.clicked.connect(self.give_hint)
        self.horizontal_layout.addWidget(self.hint_button)

        self.vert_layout.addLayout(self.horizontal_layout)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.vert_layout.addWidget(self.text_edit)

        self.giveup_button = QPushButton("Give up (looser)")
        self.giveup_button.clicked.connect(self.on_giveup)
        self.vert_layout.addWidget(self.giveup_button)

        self.wiki_button = QPushButton("Open on Wikipedia")
        self.wiki_button.clicked.connect(self.open_wiki)
        self.vert_layout.addWidget(self.wiki_button)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Tree view")
        self.tree_items = [QTreeWidgetItem(["Root"])]
        self.tree.insertTopLevelItems(0, self.tree_items)
        self.main_layout.addWidget(self.tree)

        self.setLayout(self.main_layout)
        self.setGeometry(600, 200, 700, 700)

        self.dialog = OpeningDialog()
        self.dialog.exec()
        if self.dialog.target:
            self.target = self.dialog.target
        else:
            self.close()
            exit()

    def on_text_update(self):
        guess_text = self.line_edit.text()
        guess_species = None
        try:
            guess_species = taxoniq.Taxon(scientific_name=guess_text)
            self.enter_button.setDisabled(False)
        except:
            self.enter_button.setDisabled(True)
    def on_enter(self):
        self.text_edit.append("---------------------")
        guess_text = self.line_edit.text()
        self.line_edit.clear()
        guess_species = taxoniq.Taxon(scientific_name=guess_text)
        if guess_species:
            self.tries += 1
            self.text_edit.append("Try " + str(self.tries) + ": " + guess_text)
            ind = 0
            for target_clade, guess_clade in zip(reversed(guess_species.lineage), reversed(self.target.lineage)):
                if target_clade.scientific_name == guess_clade.scientific_name:
                    self.text_edit.append(taxon_to_message(guess_clade))
                    self.last_correct = guess_clade
                    self.last_ind = ind
                    if not self.last_correct == self.target:
                        self.next_correct = list(reversed(self.target.lineage))[ind + 1]
                else:
                    break
                ind += 1
            accuracy_message = f"{str(len(self.last_correct.lineage))}/{str(len(self.target.lineage))}"
            self.try_list.append([str(self.tries), taxon_to_message(guess_species), taxon_to_message(self.last_correct), accuracy_message, str_with_plus(ind - self.last_accuracy)])
            if ind > self.last_accuracy:
                self.last_accuracy = ind
            try:
                self.text_edit.append(self.last_correct.description)
            except:
                pass

            new_tree_item = QTreeWidgetItem([self.last_correct.scientific_name])
            self.tree_items[-1].addChild(new_tree_item)
            self.tree_items.append(new_tree_item)

            self.text_edit.append(f"accuracy: {accuracy_message} {str(self.last_correct.rank)[5:]}")

            if self.target == self.last_correct:
                self.text_edit.append("CONGRATS, YOU DID IT!! (moron)")
                self.text_edit.append("It took you " + str(self.tries) + " tries")
                self.dialog = WinDialog(self.try_list, self.target)
                self.dialog.exec()
        else:
            self.text_edit.append("not found. Please write a capitalized, scientific genus name")

    def on_giveup(self):
        self.text_edit.append("---------------------")
        self.text_edit.append(f"genus-code: {str(self.target.tax_id ** 2)}")
        self.text_edit.append("You failed, it was:")
        for taxon in reversed(self.target.lineage):
            try:
                self.text_edit.append(str(taxon.rank)[5:] + ": " + taxon.scientific_name + " (" + taxon.common_name + ")")
            except:
                self.text_edit.append(str(taxon.rank)[5:] + ": " + taxon.scientific_name)
        self.dialog = WinDialog(self.try_list, self.target)
        self.dialog.exec()
    def open_wiki(self):
        try:
            webbrowser.open(wikipedia.page(self.last_correct.scientific_name, auto_suggest=False).url)
        except:
            try:
                webbrowser.open(self.last_correct.wikidata_url)
            except:
                self.text_edit.append("Sry, no Wiki article available")
    def give_hint(self):
        for correct in list(reversed(self.target.lineage))[self.last_ind+1:]:
            image_url = get_image_hint(correct)
            if image_url:
                break
        if image_url:
            self.text_edit.append("---------------------")
            self.text_edit.append("Try " + str(self.tries) + ": image hint")
            self.tries += 1
            self.try_list.append([str(self.tries), "image hint", "", "", ""])
            self.dialog = HintDialog(self.last_correct.scientific_name, str(self.next_correct.rank)[5:], image_url)
            self.dialog.exec()
        else:
            self.text_edit.append("sry, no images available")

app = QApplication(sys.argv)
widget = MyWidget()
widget.show()
sys.exit(app.exec_())