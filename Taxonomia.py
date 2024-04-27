import taxoniq
from random import randint

import wikipedia
import webbrowser

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence

done = False
fail_count = 0
while not done:
    fail_count += 1
    try:
        target_species = taxoniq.Taxon(randint(0, 100000000))
        if target_species.rank == taxoniq.Rank.genus:
            sci = target_species.scientific_name
            com = target_species.common_name
            done = True
    except:
        done = False

# print(fail_count, "tries")
# print(sci, "(" + com + ")")



class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taxonomia")

        self.tries = 0

        self.layout = QVBoxLayout()

        self.horizontal_layout = QHBoxLayout()

        self.line_edit = QLineEdit()
        self.horizontal_layout.addWidget(self.line_edit)

        self.button = QPushButton('Enter')
        self.button.setShortcut(QKeySequence(Qt.Key_Return))
        self.button.clicked.connect(self.on_enter)
        self.horizontal_layout.addWidget(self.button)

        self.layout.addLayout(self.horizontal_layout)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        self.giveup_button = QPushButton('Give up (looser)')
        self.giveup_button.clicked.connect(self.on_giveup)
        self.layout.addWidget(self.giveup_button)

        self.wiki_button = QPushButton("Open on Wikipedia")
        self.wiki_button.clicked.connect(self.open_wiki)
        self.layout.addWidget(self.wiki_button)

        self.setLayout(self.layout)
        self.setGeometry(600, 200, 700, 700)

    def on_enter(self):
        self.text_edit.append("---------------------")
        guess_text = self.line_edit.text()
        guess_species = None
        try:
            guess_species = taxoniq.Taxon(scientific_name=guess_text)
        except:
            pass
        if guess_species:
            self.tries += 1
            self.text_edit.append("Try " + str(self.tries) + ": " + guess_text)
            ind = 0
            for target_clade, guess_clade in zip(reversed(guess_species.lineage), reversed(target_species.lineage)):
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
            self.text_edit.append("accuracy: " + str(ind) + "/" + str(len(target_species.lineage)) + " " + str(self.last_correct.rank)[5:])

            if target_species == guess_species:
                self.text_edit.append("CONGRATS, YOU DID IT!! (moron)")
                self.text_edit.append("It took you " + str(self.tries) + " tries")
        else:
            self.text_edit.append("SRY, NOT FOUND")

    def on_giveup(self):
        self.text_edit.append("---------------------")
        self.text_edit.append("You failed, it was:")
        for taxon in reversed(target_species.lineage):
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