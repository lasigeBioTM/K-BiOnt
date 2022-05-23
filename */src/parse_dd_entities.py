import os
import xml.etree.ElementTree as et


def get_sentence_entities(base_dir):
    """
    :param base_dir:
    :return:
    """

    all_entities = {}          # (sentence_id, id_1, id_2): relation

    for f in os.listdir(base_dir):

        tree = et.parse(base_dir + '/' + f)
        root = tree.getroot()

        for sentence in root:
            sentence_id = sentence.get('id')
            all_pairs = sentence.findall('pair')

            for pair in all_pairs:
                if pair.get('ddi') == 'true':
                    all_entities[(sentence_id, pair.get('e1'), pair.get('e2'))] = True
                else:
                    all_entities[(sentence_id, pair.get('e1'), pair.get('e2'))] = False

    return all_entities
