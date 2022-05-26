import os
import xml.etree.ElementTree as element_tree


def get_gold_standard_gp(gold_standard_file):
    """

    :param gold_standard_file:
    :return:
    """

    dict_gold_standard = {}

    for infile in os.listdir(gold_standard_file):
        tree = element_tree.parse(gold_standard_file + '/' + infile)
        root = tree.getroot()

        for sentence in root:
            sentence_id = sentence.get('id')
            entities = []

            for e in sentence.findall('entity'):
                e_id = e.get('ontology_id')
                entities.append(e_id)

            for p in sentence.findall('pair'):
                relation = p.get('relation')
                if entities[0].startswith('HP'):
                    dict_gold_standard[str((sentence_id, entities[1].replace('_', ':'), entities[0].replace('_', ':')))] = relation.capitalize()
                else:
                    dict_gold_standard[str((sentence_id, entities[0].replace('_', ':'), entities[1].replace('_', ':')))] = relation.capitalize()

    return dict_gold_standard