from random import randint
import clipboard
import sys
from math import sqrt
from time import sleep
from tabulate import tabulate
import urllib
from collections import Counter

import taxoniq
import pyinaturalist
import wikipedia
import webbrowser

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

def lowest_commonality(taxon1, taxon2):
    ind = 0
    for tax1, tax2 in zip(reversed(taxon1.lineage), reversed(taxon2.lineage)):
        if not tax1 == tax2:
            break
        ind += 1
    correct = list(reversed(taxon1.lineage))[:ind]
    wrong = list(reversed(taxon1.lineage))[ind:]
    return (correct, wrong)
def taxon_to_message(taxon):
    try:
        guess_message = f"{str(taxon.rank)[5:]}: {taxon.scientific_name} ({taxon.common_name})"
    except:
        guess_message = f"{str(taxon.rank)[5:]}: {taxon.scientific_name}"
    return guess_message
def good_lineage(taxon):
    dictionary = {}
    for clade in taxon.lineage:
        dictionary[clade.rank.name] = clade
    return dictionary
def get_random_taxon(parent=taxoniq.Taxon(1)):
    done = False
    while not done:
        try:
            taxon = taxoniq.Taxon(randint(0, 100000000))
            if taxon.rank == taxoniq.Rank.genus and good_lineage(taxon)[parent.rank.name] == parent:
                done = True
        except:
            done = False
    return taxon
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
    if observations:
        image_url = observations[randint(0, len(observations)-1)]["taxon"]["default_photo"]["medium_url"]
        return image_url
def tx(item):
    text = item.text(0)
    without_rank = text.split(": ")[-1]
    without_common = without_rank.split(" (")[0]
    try:
        return taxoniq.Taxon(scientific_name=without_common)
    except:
        return taxoniq.Taxon(tax_id=sqrt(int(without_common)))
def iterate(guess_item, compare_item):
    correct, wrong = lowest_commonality(tx(guess_item), tx(compare_item))
    if correct[-1] == tx(compare_item):
        if compare_item.childCount():
            for i in range(compare_item.childCount()):
                print()
                inbetween = iterate(guess_item, compare_item.child(i))
                if inbetween:
                    if isinstance(inbetween, QTreeWidgetItem):
                        return inbetween
                    else:
                        if not inbetween == tx(compare_item):
                            new_item = QTreeWidgetItem([taxon_to_message(inbetween)])
                            new_item.addChild(guess_item)
                            new_item.addChild(compare_item.takeChild(i))
                            compare_item.addChild(new_item)
                            new_item.setExpanded(True)
                            compare_item.setExpanded(True)
                            return new_item
            compare_item.addChild(guess_item)
            compare_item.setExpanded(True)
        else:
            compare_item.addChild(guess_item)
            compare_item.setExpanded(True)
    elif correct[-1] == tx(guess_item):
        compare_item.parent().addChild(guess_item)
        compare_item.parent().removeChild(compare_item)
        guess_item.addChild(compare_item)
        guess_item.parent().setExpanded(True)
        guess_item.setExpanded(True)
    else:
        return correct[-1]

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
        self.target = get_random_taxon()
        self.close()

class WinDialog(QDialog):
    def __init__(self, try_list, solution):
        super().__init__()
        self.setWindowTitle("Taxonomia")
        self.vert_layout = QVBoxLayout()
        self.setLayout(self.vert_layout)

        self.try_list = try_list
        self.tries = self.try_list[-1][0]
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
                    <p align="center">Genus-code: {self.solution.tax_id**2} \nYou needed {self.tries} tries.</p>
                      <tr>
                        <th style="border: 1px solid black; padding: 8px;">Try Nr.</th>
                        <th style="border: 1px solid black; padding: 8px;">Tried Name</th>
                        <th style="border: 1px solid black; padding: 8px;">Commonality</th>
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
        table = tabulate(self.try_list, headers=["Try Nr.", "Tried Name", "Commonality", "Progress"])
        genus_code = str(self.solution.tax_id**2)
        message = f"""I won Taxonomia!!! 
genus-code: **{genus_code}**
It took me **{self.tries} tries**. can you beat me?
Download [Taxonomia on Github](https://github.com/Hexogrammer/Taxonomia)

Guess history:
||`{table}`||"""
        clipboard.copy(message)
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
        self.vert_layout.addWidget(QLabel(f"Random species of the correct {next_correct_rank} (after {last_correct_name}).\nNO REVERSE IMAGE SEARCH!!!"))

        data = urllib.request.urlopen(image_url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.vert_layout.addWidget(self.image_label)

class PieChartWidget(QWidget):
    def __init__(self, data):
        super().__init__()

        self.figure = plt.figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.plot_pie_chart(data)
    def plot_pie_chart(self, data):
        self.figure.clear()
        self.figure.set_constrained_layout(True)
        ax = self.figure.add_subplot(111)
        ax.set_aspect('equal')
        ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=90)

class AnalyzeDialog(QDialog):
    def __init__(self, selection):
        super().__init__()
        self.setWindowTitle("Analyze")
        self.setWindowModality(Qt.NonModal)
        self.vert_layout = QVBoxLayout()
        self.setLayout(self.vert_layout)
        self.ranks = [taxoniq.Rank(value=i).name for i in range(1, 46)]
        self.selection = selection

        self.hori_layout1 = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_text_update)
        self.line_edit_label = QLabel("Level")
        self.hori_layout1.addWidget(self.line_edit_label)
        self.hori_layout1.addWidget(self.line_edit)
        self.vert_layout.addLayout(self.hori_layout1)
        self.hori_layout2 = QHBoxLayout()
        self.spin_box = QSpinBox()
        self.spin_box.setMaximum(10000)
        self.spin_box.setValue(100)
        self.spin_box_label = QLabel("Sample size")
        self.hori_layout2.addWidget(self.spin_box_label)
        self.hori_layout2.addWidget(self.spin_box)
        self.vert_layout.addLayout(self.hori_layout2)
        self.button = QPushButton("Analyze")
        self.button.pressed.connect(self.start_analysis)
        self.button.setDisabled(True)
        self.vert_layout.addWidget(self.button)
        self.progress_bar = QProgressBar()
        self.vert_layout.addWidget(self.progress_bar)
    def start_analysis(self):
        self.button.setDisabled(True)
        self.level = self.line_edit.text()
        self.sample_size = self.spin_box.value()
        self.progress_bar.setMaximum(self.sample_size)
        self.samples = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.add_sample)
        self.timer.start(1)
    def add_sample(self):
        print(len(self.samples))
        lin = good_lineage(get_random_taxon(self.selection))
        self.progress_bar.setValue(len(self.samples))
        if self.level in lin:
            self.samples.append(taxon_to_message(lin[self.level]))
        else:
            self.samples.append(f"No {self.level}")
        if len(self.samples) >= self.sample_size:
            self.timer.stop()
            self.finish_analysis()
    def finish_analysis(self):
        data = dict(sorted(Counter(self.samples).items(), key=lambda x: x[1], reverse=True))
        # fig = plt.figure()
        # pie_chart = plt.pie(data.values(), labels=data.keys())
        # plt.gcf().canvas.manager.set_window_title(f"{self.level} distributions of {taxon_to_message(self.selection)}")
        # plt.show(block=False)
        dialog = QDialog()
        dialog.setWindowTitle(f"{self.level} distributions of {taxon_to_message(self.selection)}")
        dialog.setWindowModality(Qt.NonModal)

        pie_chart_widget = PieChartWidget(data)
        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(pie_chart_widget)
        dialog.setLayout(dialog_layout)
        dialog.exec_()
    def on_text_update(self):
        if self.line_edit.text() in self.ranks:
            self.button.setDisabled(False)
        else:
            self.button.setDisabled(True)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taxonomia")
        self.setGeometry(400, 200, 900, 700)

        self.tries = 0
        self.try_list = []
        self.next_correct = None
        self.last_correct = None
        self.last_ind = 0
        self.last_accuracy = 0

        self.main_layout = QHBoxLayout()
        self.vert_layout = QVBoxLayout()
        self.vert_layout2 = QVBoxLayout()
        self.main_layout.addLayout(self.vert_layout)
        self.main_layout.addLayout(self.vert_layout2)

        self.horizontal_layout = QHBoxLayout()

        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_text_update)
        self.horizontal_layout.addWidget(self.line_edit)

        self.enter_button = QPushButton("Enter")
        self.enter_button.setShortcut(QKeySequence(Qt.Key_Return))
        self.enter_button.setDisabled(True)
        self.enter_button.clicked.connect(self.on_enter)
        self.horizontal_layout.addWidget(self.enter_button)

        self.hint_button = QPushButton("Hint (3 guesses)")
        self.hint_button.clicked.connect(self.give_hint)
        self.horizontal_layout.addWidget(self.hint_button)

        self.console = QLabel()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.console)
        self.scroll_area.setAlignment(Qt.AlignBottom)
        self.vert_layout.addWidget(self.scroll_area)
        self.console.adjustSize()

        self.vert_layout.addLayout(self.horizontal_layout)

        self.description_box = QTextEdit()
        self.description_box.setReadOnly(True)

        # self.giveup_button = QPushButton("Give up (looser)")
        # self.giveup_button.clicked.connect(self.on_giveup)
        # self.vert_layout.addWidget(self.giveup_button)

        self.setLayout(self.main_layout)

        self.dialog = OpeningDialog()
        self.dialog.exec()
        if self.dialog.target:
            self.target = self.dialog.target
        else:
            self.close()
            exit()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Tree view")
        self.tree.itemSelectionChanged.connect(self.on_select)
        self.vert_layout.addWidget(self.tree)
        self.vert_layout2.addWidget(self.description_box)

        self.wiki_button = QPushButton("Open on Wikipedia")
        self.wiki_button.clicked.connect(self.open_wiki)
        self.wiki_button.setDisabled(True)
        self.vert_layout2.addWidget(self.wiki_button)

        self.iNat_button = QPushButton("Open on iNaturalist")
        self.iNat_button.clicked.connect(self.open_iNat)
        self.iNat_button.setDisabled(True)
        self.vert_layout2.addWidget(self.iNat_button)

        self.analyze_button = QPushButton("Analyze (1 guess)")
        self.analyze_button.clicked.connect(self.analyze)
        self.analyze_button.setDisabled(True)
        self.vert_layout2.addWidget(self.analyze_button)

        self.root = QTreeWidgetItem(["root"])
        self.root.addChild(QTreeWidgetItem([str(self.target.tax_id**2)]))
        self.tree.insertTopLevelItems(0, [self.root])
        self.tree.itemCollapsed.connect(self.on_item_collapsed)
        self.tree.setCurrentItem(self.root.child(0))

        self.line_edit.setFocus()
    def on_item_collapsed(item):
        item.setExpanded(True)
    def on_select(self):
        self.selection = tx(self.tree.selectedItems()[-1])
        if self.selection == self.target:
            self.selection = None
            self.description_box.setText("<b>Unknown</b>\nGuess scientific Genus names to find out what hides behind this code")
            self.wiki_button.setDisabled(True)
            self.iNat_button.setDisabled(True)
            self.analyze_button.setDisabled(True)

        else:
            self.description_box.setText("\n".join([taxon_to_message(i) for i in reversed(self.selection.lineage)]))
            self.wiki_button.setDisabled(False)
            self.iNat_button.setDisabled(False)
            self.analyze_button.setDisabled(False)
            try:
                self.description_box.append(self.selection.description)
            except:
                pass
    def on_text_update(self):
        guess_text = self.line_edit.text()
        guess_species = None
        try:
            guess_species = taxoniq.Taxon(scientific_name=guess_text)
            self.enter_button.setDisabled(False)
        except:
            self.enter_button.setDisabled(True)
    def on_enter(self):
        guess = taxoniq.Taxon(scientific_name=self.line_edit.text())
        self.line_edit.clear()
        self.tries += 1

        correct, wrong = lowest_commonality(self.target, guess)
        self.last_correct = correct[-1]
        if wrong:
            self.next_correct = wrong[0]
        self.last_ind = len(correct)-1
        progress = self.last_ind - self.last_accuracy

        guess_item = QTreeWidgetItem([taxon_to_message(guess)])
        new_item = iterate(guess_item, self.root)
        if new_item and progress > 0:
            self.tree.setCurrentItem(new_item)

        accuracy_message = f"{str(len(self.last_correct.lineage))}/{str(len(self.target.lineage))}"
        self.console.setText(self.console.text() + f"\nTry {self.tries}: {taxon_to_message(guess)} {str_with_plus(progress)}")
        self.console.adjustSize()
        self.try_list.append([str(self.tries), taxon_to_message(guess), taxon_to_message(self.last_correct), str_with_plus(progress)])
        if self.last_ind > self.last_accuracy:
            self.last_accuracy = self.last_ind


        if self.target == self.last_correct:
            self.console.setText(self.console.text() + f"\nYou Win, it took you {self.tries} tries")
            self.console.adjustSize()
            self.dialog = WinDialog(self.try_list, self.target)
            self.dialog.exec()
    def on_giveup(self):
        self.console.setText(self.console.text() + "\n---------------------")
        self.console.setText(self.console.text() + f"\ngenus-code: {str(self.target.tax_id ** 2)}")
        self.console.setText(self.console.text() + "\nYou failed, it was:")
        self.console.adjustSize()
        for taxon in reversed(self.target.lineage):
            self.console.setText(self.console.text() + f"\n{taxon_to_message(taxon)}")
        self.console.adjustSize()
        self.dialog = WinDialog(self.try_list, self.target)
        self.dialog.exec()
    def open_wiki(self):
        if self.selection:
            try:
                webbrowser.open(wikipedia.page(self.selection.scientific_name, auto_suggest=False).url)
            except:
                try:
                    webbrowser.open(self.selection.wikidata_url)
                except:
                    self.console.setText(self.console.text() + "\nNo wiki article available")
        self.console.adjustSize()
    def open_iNat(self):
        if self.selection:
            search = pyinaturalist.get_taxa(q=self.selection.scientific_name)["results"]
            if search:
                id = search[0]["id"]
                try:
                    webbrowser.open(f"https://www.inaturalist.org/observations?place_id=any&taxon_id={id}&view=species")
                except:
                    pass
            else:
                self.console.setText(self.console.text() + "\nNot available on iNaturalist")
        self.console.adjustSize()
    def give_hint(self):
        for correct in list(reversed(self.target.lineage))[self.last_ind+1:]:
            image_url = get_image_hint(correct)
            if image_url:
                break
        if image_url:
            self.tries += 1
            self.console.setText(self.console.text() + f"\nTry {str(self.tries)}-{str(self.tries + 2)}: image hint")
            self.try_list.append([f"{str(self.tries)}-{str(self.tries + 2)}", "image hint", taxon_to_message(self.last_correct), "0"])
            self.tries += 2
            self.dialog = HintDialog(self.last_correct.scientific_name, str(self.next_correct.rank)[5:], image_url)
            self.dialog.setWindowModality(Qt.NonModal)
            self.dialog.show()
        else:
            self.console.setText(self.console.text() + "\nNo images available")
        self.console.adjustSize()
    def analyze(self):
        self.dialog = AnalyzeDialog(self.selection)
        self.dialog.setWindowModality(Qt.NonModal)
        self.dialog.show()
        self.tries += 1
        self.console.setText(self.console.text() + f"\nTry {self.tries}: {taxon_to_message(self.selection)} analysis")
        self.try_list.append([f"{self.tries}", f"{taxon_to_message(self.selection)} analysis", taxon_to_message(self.last_correct), "0"])
        self.console.adjustSize()

app = QApplication(sys.argv)
widget = MainWindow()
widget.show()
sys.exit(app.exec_())