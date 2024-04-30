import taxoniq
from random import randint

import wikipedia
import webbrowser

import sys
from math import sqrt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence

class DialogWindow(QDialog):
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

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taxonomia")

        self.tries = 0

        self.main_layout = QHBoxLayout()

        self.vert_layout = QVBoxLayout()
        self.main_layout.addLayout(self.vert_layout)

        self.horizontal_layout = QHBoxLayout()

        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_text_update)
        self.horizontal_layout.addWidget(self.line_edit)

        self.button = QPushButton('Enter')
        self.button.setShortcut(QKeySequence(Qt.Key_Return))
        self.button.setDisabled(True)
        self.button.clicked.connect(self.on_enter)
        self.horizontal_layout.addWidget(self.button)

        self.vert_layout.addLayout(self.horizontal_layout)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.vert_layout.addWidget(self.text_edit)

        self.giveup_button = QPushButton('Give up (looser)')
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

        self.dialog = DialogWindow()
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
            self.button.setDisabled(False)
        except:
            self.button.setDisabled(True)
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
                ind += 1
                if target_clade.scientific_name == guess_clade.scientific_name:
                    try:
                        self.text_edit.append(str(guess_clade.rank)[5:] + ": " + guess_clade.scientific_name + " " + "(" + guess_clade.common_name + ")")
                    except:
                        self.text_edit.append(str(guess_clade.rank)[5:] + ": " + guess_clade.scientific_name)
                    self.last_correct = guess_clade
                else:
                    break
            try:
                self.text_edit.append(self.last_correct.description)
            except:
                pass

            new_tree_item = QTreeWidgetItem([self.last_correct.scientific_name])
            self.tree_items[-1].addChild(new_tree_item)
            self.tree_items.append(new_tree_item)

            self.text_edit.append("accuracy: " + str(ind) + "/" + str(len(self.target.lineage)) + " " + str(self.last_correct.rank)[5:])

            if self.target == guess_species:
                self.text_edit.append("CONGRATS, YOU DID IT!! (moron)")
                self.text_edit.append("It took you " + str(self.tries) + " tries")
        else:
            self.text_edit.append("not found. Please write a capitalized, scientific genus name")

    def on_giveup(self):
        self.text_edit.append("---------------------")
        self.text_edit.append("You failed, it was:")
        for taxon in reversed(self.target.lineage):
            try:
                self.text_edit.append(str(taxon.rank)[5:] + ": " + taxon.scientific_name + " (" + taxon.common_name + ")")
            except:
                self.text_edit.append(str(taxon.rank)[5:] + ": " + taxon.scientific_name)
    def open_wiki(self):
        try:
            webbrowser.open(wikipedia.page(self.last_correct.scientific_name, auto_suggest=False).url)
        except:
            webbrowser.open(self.last_correct.wikidata_url)

app = QApplication(sys.argv)
widget = MyWidget()
widget.show()
sys.exit(app.exec_())