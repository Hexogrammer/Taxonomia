import taxoniq
from random import randint
from math import sqrt
from matplotlib import pyplot as plt
from collections import Counter
from multiprocess import Process, Manager, Pool
def taxon_to_message(taxon):
    try:
        guess_message = f"{taxon.rank.name}: {taxon.scientific_name} ({taxon.common_name})"
    except:
        guess_message = f"{taxon.rank.name}: {taxon.scientific_name}"
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
            taxon = taxoniq.Taxon(randint(0, 1000000))
            if taxon.rank == taxoniq.Rank.genus and good_lineage(taxon)[parent.rank.name] == parent:
                done = True
        except:
            done = False
    return taxon

def analyze(mode, level, sample_size=100, parent=None, sample_list=[]):
    # sample_list = [taxoniq.Taxon(tax_id=sqrt(i)) for i in [721835689, 1824314944, 106912650625, 148165715929, 101290700644]]
    samples = []
    for i in range(0, sample_size):
        if mode == "random":
            lin = good_lineage(get_random_taxon(taxoniq.Taxon(0)))
        elif mode == "list":
            lin = good_lineage(sample_list[i])  # get_random_taxon())
        elif mode == "children":
            lin = good_lineage(get_random_taxon(parent))
        if level in lin:
            print(taxon_to_message(lin[level]))
            samples.append(taxon_to_message(lin[level]))
    data = dict(sorted(Counter(samples).items(), key=lambda x: x[1], reverse=True))

    fig = plt.figure()
    pie_chart = plt.pie(data.values(), labels=data.keys())
    if mode == "random":
        plt.gcf().canvas.set_window_title(f"random {level} distribution")
    elif mode == "list":
        plt.gcf().canvas.set_window_title(f"{level} distributions of inserted taxons")
    elif mode == "children":
        plt.gcf().canvas.set_window_title(f"{level} distributions of {taxon_to_message(parent)}")
    plt.show()

def get_info_density(taxon, accuracy=500):
    info_density = 0
    for n in range(1, accuracy):
        for level in taxon.lineage:
            new_genus = get_random_taxon()
            if level in new_genus.lineage:
                info_density += 1
        #print(round(info_density / n, 2))
    return round(info_density / accuracy, 1)
genera = {}
record_density = 10.4
record_genus = ""

def process_code():
    global record_genus
    global record_density
    global genera
    print("Starting process_code")
    for i in range(100):
        genus = get_random_taxon()
        info_density = get_info_density(genus)
        genera[taxon_to_message(genus)] = info_density
        if info_density > record_density:
            record_density = info_density
            record_genus = taxon_to_message(genus)
            print(f"{record_density} - {record_genus}")

if __name__ == '__main__':
    with Manager() as manager:
        processes = [Process(target=process_code) for i in range(15)]
        for p in processes:
            p.start()

while True:
    if input('type "end" to end') == "end":
        break
    print(dict(sorted(genera.items(), key=lambda item: item[1])))
# print(get_info_density(taxoniq.Taxon(scientific_name="Heliothis"), 1000))