def get_gold_standard_gp(gold_standard_file):
    """

    :param gold_standard_file:
    :return:
    """

    dict_gold_standard = {}

    tree = ET.parse(gold_standard_file)
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
                dict_gold_standard[str((sentence_id, entities[1], entities[0]))] = relation.capitalize()
            else:
                dict_gold_standard[str((sentence_id, entities[0], entities[1]))] = relation.capitalize()

    return dict_gold_standard