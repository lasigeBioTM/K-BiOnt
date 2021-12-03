import os
import xml.etree.ElementTree as element_tree
import random

import pronto
from owlready2 import *


# ITEM RECOMMENDATION FILE PREPARATION CHEMICAL|DRUG-DISEASE ####

def process_interactions_cd(txt_file_path, i2kg_file_path, pair_type):
    """

    :param txt_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :return: dict with the relations, tagged with 0 if false and with 1 if true, of type
             {identifier1: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), 1],
             identifier2: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), -1], ...}
    """

    ontology_dict = write_i2kg(i2kg_file_path, pair_type)
    count_interactions_draft = {}
    entities_dict = {}
    entity_identifier = 0
    entities_unique_identifier = {}
    used_entities = []

    relations_file = open(txt_file_path, 'r', encoding='utf-8')
    relations_file.readline()  # skip header
    relations = relations_file.readlines()

    count_interactions = {}
    identifier = 0
    for relation in relations:
        elements = relation.split('\t')
        if elements[-1][:-1] == 'true':
            tag = 1
        else:
            tag = -1

        if elements[2] != '-1' and elements[6] != '-1':  # wrong ids in original data
            count_interactions[identifier] = [(elements[2], elements[3]), (elements[6], elements[7]), tag]
            entities_dict[elements[2]] = elements[3]
            entities_dict[elements[6]] = elements[7]

            if elements[3] not in used_entities:
                entities_unique_identifier[elements[3]] = '0' + str(entity_identifier)
                entity_identifier += 1
                used_entities.append(elements[3])
            if elements[7] not in used_entities:
                entities_unique_identifier[elements[7]] = '0' + str(entity_identifier)
                entity_identifier += 1
                used_entities.append(elements[7])

            if elements[2].startswith('D'):  # diseases second (item)
                count_interactions_draft[identifier] = [elements[6], elements[2], tag]

            elif elements[6].startswith('D'):
                count_interactions_draft[identifier] = [elements[2], elements[6], tag]

            identifier += 1

    dict_ids_match_items = {}
    dict_ids_match_users = {}
    dict_gold_standard = {}
    count_interactions = {}
    for items in count_interactions_draft.items():
        entity_2_name = entities_dict[items[1][1]]

        try:
            ontology_entity_2 = ontology_dict[entity_2_name]
        except KeyError:
            # print(entity_2_name, 'not in DOID ontology!')
            ontology_entity_2 = entities_unique_identifier[entities_dict[items[1][1]]]

        count_interactions[items[0]] = [
            (entities_unique_identifier[entities_dict[items[1][0]]], entities_dict[items[1][0]]),
            (ontology_entity_2, entity_2_name), items[1][2]]

        dict_ids_match_users[entities_dict[items[1][0]]] = entities_unique_identifier[entities_dict[items[1][0]]]
        dict_ids_match_items[entity_2_name] = ontology_entity_2
        dict_gold_standard[str((entities_unique_identifier[entities_dict[items[1][0]]], ontology_entity_2))] = items[1][2]

    return dict_ids_match_items, dict_ids_match_users, dict_gold_standard, count_interactions


# ITEM RECOMMENDATION FILE PREPARATION GENE-PHENOTYPE ####

def process_interactions_gp(xml_file_path):
    """

    :param xml_file_path:
    :return: dict with the relations, tagged with 0 if false and with 1 if true, of type
             {identifier1: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), 1],
             identifier2: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), -1], ...}
    """

    tree = element_tree.parse(xml_file_path)
    root = tree.getroot()

    count_interactions = {}
    identifier = 0

    for sentence in root:
        entities_list = []

        for elements in sentence:
            if elements.tag == 'entity':
                entities_list.append((elements.attrib['ontology_id'].replace('_', ':'), elements.attrib['text']))
            elif elements.tag == 'pair':
                if elements.attrib['relation'] == 'true':
                    entities_list.append(1)
                elif elements.attrib['relation'] == 'false':
                    entities_list.append(-1)

        count_interactions[identifier] = entities_list
        identifier += 1

    return count_interactions


# ITEM RECOMMENDATION FILE PREPARATION DRUG-DRUG ####

def process_interactions_dd(xml_file_path, i2kg_file_path, pair_type):
    """

    :param xml_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :return: dict with the relations, tagged with 0 if false and with 1 if true, of type
             {identifier1: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), 1],
             identifier2: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), -1], ...}
    """

    ontology_dict = write_i2kg(i2kg_file_path, pair_type)
    count_interactions_draft = {}
    entities_dict = {}
    identifier = 0
    entity_identifier = 0
    entities_unique_identifier = {}
    used_entities = []

    for filename in os.listdir(xml_file_path):
        tree = element_tree.parse(xml_file_path + filename)
        root = tree.getroot()

        for sentence in root:
            for elements in sentence:
                if elements.tag == 'entity':
                    entities_dict[elements.attrib['id']] = elements.attrib['text']

                    if elements.attrib['text'] not in used_entities:
                        entities_unique_identifier[elements.attrib['text']] = '0' + str(entity_identifier)
                        entity_identifier += 1
                        used_entities.append(elements.attrib['text'])

                elif elements.tag == 'pair':
                    if elements.attrib['ddi'] == 'true':
                        relation = 1
                    else:
                        relation = -1
                    pairs_list = [elements.attrib['e1'], elements.attrib['e2'], relation]
                    count_interactions_draft[identifier] = pairs_list
                    identifier += 1

    dict_ids_match_items = {}
    dict_ids_match_users = {}
    dict_gold_standard = {}
    count_interactions = {}
    for items in count_interactions_draft.items():
        entity_2_name = entities_dict[items[1][1]]

        try:
            ontology_entity_2 = ontology_dict[entity_2_name]
        except KeyError:
            # print(entity_2_name, 'not in ChEBI ontology!')
            ontology_entity_2 = entities_unique_identifier[entities_dict[items[1][1]]]

        count_interactions[items[0]] = [(entities_unique_identifier[entities_dict[items[1][0]]], entities_dict[items[1][0]]),
                                        (ontology_entity_2, entity_2_name), items[1][2]]

        dict_ids_match_users[entities_dict[items[1][0]]] = entities_unique_identifier[entities_dict[items[1][0]]]
        dict_ids_match_items[entity_2_name] = ontology_entity_2
        dict_gold_standard[str((entities_unique_identifier[entities_dict[items[1][0]]], ontology_entity_2))] = items[1][2]

    return dict_ids_match_items, dict_ids_match_users, dict_gold_standard, count_interactions


def process_ratings(relations_file_path, i2kg_file_path, pair_type):
    """

    :param relations_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :return:
    """

    if pair_type == 'DRUG-DISEASE':
        dict_ids_match_items, dict_ids_match_users, dict_gold_standard, dict_interactions = process_interactions_cd(relations_file_path, i2kg_file_path, pair_type)
    elif pair_type == 'GENE-PHENOTYPE':
        dict_interactions = process_interactions_gp(relations_file_path)
    elif pair_type == 'DRUG-DRUG':
        dict_ids_match_items, dict_ids_match_users, dict_gold_standard, dict_interactions = process_interactions_dd(relations_file_path, i2kg_file_path, pair_type)
    else:
        raise Exception('Pair type is ill defined!')

    value_counts = {}

    for interaction in dict_interactions.items():
        first_element = interaction[1][0]
        second_element = interaction[1][1]
        value_element = interaction[1][2]

        if pair_type == 'GENE-PHENOTYPE':
            if str([first_element[0], second_element[0]]) in value_counts:
                new_value = value_counts[str([first_element[0], second_element[0]])] + value_element
                value_counts[str([first_element[0], second_element[0]])] = new_value

            elif str([second_element[0], first_element[0]]) in value_counts:
                new_value = value_counts[str([second_element[0], first_element[0]])] + value_element
                value_counts[str([second_element[0], first_element[0]])] = new_value

            else:
                if first_element[0].startswith('HP'):
                    value_counts[str([second_element[0], first_element[0]])] = value_element
                elif second_element[0].startswith('HP'):
                    value_counts[str([first_element[0], second_element[0]])] = value_element

        elif pair_type == 'DRUG-DISEASE' or pair_type == 'DRUG-DRUG':
            if str([first_element[0], second_element[0]]) in value_counts:
                new_value = value_counts[str([first_element[0], second_element[0]])] + value_element
                value_counts[str([first_element[0], second_element[0]])] = new_value

            else:
                value_counts[str([first_element[0], second_element[0]])] = value_element

    num_preferences = []
    new_identifier = 0
    dict_interactions_counts = {}
    for interaction in value_counts.items():

        value_element = interaction[1]
        first_element = eval(interaction[0])[0]
        second_element = eval(interaction[0])[1]

        dict_interactions_counts[new_identifier] = [first_element, second_element, value_element]
        new_identifier += 1

        if value_element not in num_preferences:
            num_preferences.append(value_element)

    return dict_interactions_counts


def write_i2kg(i2kg_file_path, pair_type):
    """

    :param i2kg_file_path:
    :param pair_type:
    :return:
    """

    i2kg_file = open(i2kg_file_path, 'w', encoding='utf-8')
    ontology_dict = {}

    if pair_type == 'DRUG-DISEASE':
        ontology = pronto.Ontology('https://purl.obolibrary.org/obo/doid.obo')
        for term in ontology.terms():
            i2kg_file.write(term.id[5:] + '\t' + term.name + '\t' + 'https://purl.obolibrary.org/obo/'
                            + term.id.replace(':', '_') + '\n')

    elif pair_type == 'GENE-PHENOTYPE':
        ontology = pronto.Ontology('https://purl.obolibrary.org/obo/hp.obo')
        for term in ontology.terms():
            i2kg_file.write(term.id[3:] + '\t' + term.name + '\t' + 'https://purl.obolibrary.org/obo/'
                            + term.id.replace(':', '_') + '\n')

    elif pair_type == 'DRUG-DRUG':
        import obonet
        ontology = obonet.read_obo('https://purl.obolibrary.org/obo/chebi.obo')
        for id_, data in ontology.nodes(data=True):
            try:
                i2kg_file.write(id_.split(':')[1] + '\t' + data.get('name') + '\t' + 'https://purl.obolibrary.org/obo/'
                                + id_.replace(':', '_') + '\n')
                ontology_dict[data.get('name')] = id_.split(':')[1]
            except TypeError:
                pass

    else:
        raise Exception('Pair type is ill defined!')

    i2kg_file.close()

    return ontology_dict


def write_i_map(relations_train_file_path, relations_test_file_path, i2kg_file_path, pair_type, item_map_file_path):
    """

    :param relations_train_file_path:
    :param relations_test_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :param item_map_file_path:
    :return:
    """

    dict_interactions_train = process_ratings(relations_train_file_path, i2kg_file_path, pair_type)
    dict_interactions_test = process_ratings(relations_test_file_path, i2kg_file_path, pair_type)

    dict_interactions = {}
    refactored_identifier = 0

    for identifier, elements_list in dict_interactions_train.items():
        dict_interactions[refactored_identifier] = elements_list
        refactored_identifier += 1

    for identifier, elements_list in dict_interactions_test.items():
        dict_interactions[refactored_identifier] = elements_list
        refactored_identifier += 1

    item_map_file = open(item_map_file_path, 'w', encoding='utf-8')

    item_map = []

    for identifier, elements_list in dict_interactions.items():
        item_map.append(elements_list[1])

    counter = 0
    dict_item_map = {}
    for element in set(item_map):
        item_map_file.write(str(counter) + '\t' + element.split('_')[-1] + '\n')
        dict_item_map[element] = str(counter)
        counter += 1

    item_map_file.close()

    return dict_item_map


def write_u_map(relations_train_file_path, relations_test_file_path, i2kg_file_path, pair_type, user_map_file_path):
    """

    :param relations_train_file_path:
    :param relations_test_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :param user_map_file_path:
    :return:
    """

    dict_interactions_train = process_ratings(relations_train_file_path, i2kg_file_path, pair_type)
    dict_interactions_test = process_ratings(relations_test_file_path, i2kg_file_path, pair_type)

    dict_interactions = {}
    refactored_identifier = 0

    for identifier, elements_list in dict_interactions_train.items():
        dict_interactions[refactored_identifier] = elements_list
        refactored_identifier += 1

    for identifier, elements_list in dict_interactions_test.items():
        dict_interactions[refactored_identifier] = elements_list
        refactored_identifier += 1

    user_map_file = open(user_map_file_path, 'w', encoding='utf-8')

    user_map = []

    for identifier, elements_list in dict_interactions.items():
        user_map.append(elements_list[0])

    counter = 0
    dict_user_map = {}
    for element in set(user_map):
        user_map_file.write(str(counter) + '\t' + element + '\n')
        dict_user_map[element] = str(counter)
        counter += 1

    user_map_file.close()

    return dict_user_map, dict_interactions_train, dict_interactions_test


def write_training_data(relations_train_file_path, relations_test_file_path, item_map_file_path, user_map_file_path, i2kg_file_path, pair_type, dataset_path):
    """

    :param relations_train_file_path:
    :param relations_test_file_path:
    :param item_map_file_path:
    :param user_map_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :param dataset_path:
    :return:
    """

    dict_item_map = write_i_map(relations_train_file_path, relations_test_file_path, i2kg_file_path, pair_type, item_map_file_path)
    dict_user_map, dict_interactions_train, dict_interactions_test = write_u_map(relations_train_file_path, relations_test_file_path, i2kg_file_path, pair_type, user_map_file_path)

    interactions_lists = {}
    interaction_number = 0

    for interaction_identifier, interaction_elements in dict_interactions_train.items():

        interaction_list = [dict_user_map[interaction_elements[0]], dict_item_map[interaction_elements[1]], interaction_elements[2]]
        interactions_lists[interaction_number] = interaction_list
        interaction_number += 1

    train_dataset = open(dataset_path + 'train.dat', 'w', encoding='utf-8')
    valid_dataset = open(dataset_path + 'valid.dat', 'w', encoding='utf-8')

    train_length = int(len(interactions_lists)*0.9)

    train_dataset_list = []
    while train_length > 0:
        value = random.choice(list(interactions_lists.items()))
        train_dataset_list.append(value[1])
        del interactions_lists[value[0]]
        train_length -= 1

    train_dataset_list.sort(key=lambda x: int(x[0]))
    for element in train_dataset_list:
        train_dataset.write(element[0] + '\t' + element[1] + '\t' + str(element[2]) + '\n')

    valid_dataset_list = list(interactions_lists.values())

    valid_dataset_list.sort(key=lambda x: int(x[0]))
    for element in valid_dataset_list:
        valid_dataset.write(element[0] + '\t' + element[1] + '\t' + str(element[2]) + '\n')

    train_dataset.close()
    valid_dataset.close()

    interactions_lists = {}
    interaction_number = 0

    for interaction_identifier, interaction_elements in dict_interactions_test.items():

        interaction_list = [dict_user_map[interaction_elements[0]], dict_item_map[interaction_elements[1]], interaction_elements[2]]
        interactions_lists[interaction_number] = interaction_list
        interaction_number += 1

    test_dataset = open(dataset_path + 'test.dat', 'w', encoding='utf-8')

    test_dataset_list = []
    for interaction_number, interaction_list in interactions_lists.items():
        test_dataset_list.append(interaction_list)

    test_dataset_list.sort(key=lambda x: int(x[0]))
    for element in test_dataset_list:
        test_dataset.write(element[0] + '\t' + element[1] + '\t' + str(element[2]) + '\n')

    test_dataset.close()
    
    return


# KNOWLEDGE GRAPH REPRESENTATION FILE PREPARATION ####

def write_e_map(entity_map_file_path, pair_type):
    """

    :param entity_map_file_path:
    :param pair_type:
    :return:
    """

    dict_entity_map = {}
    other_branches = []
    entity_map_file = open(entity_map_file_path, 'w', encoding='utf-8')

    if pair_type == 'DRUG-DISEASE':
        doid = pronto.Ontology('https://purl.obolibrary.org/obo/doid.obo')

        internal_identifier = 0
        for term in doid.terms():
            register = True

            if register or term.id == 'DOID:4':
                entity_map_file.write(str(internal_identifier) + '\t' + 'https://purl.obolibrary.org/obo/'
                                      + term.id + '\n')
                dict_entity_map[term.id.replace(':', '_')] = str(internal_identifier)
                internal_identifier += 1

            if not register:
                other_branches.append(term.id)

    elif pair_type == 'GENE-PHENOTYPE':
        hp = pronto.Ontology('https://purl.obolibrary.org/obo/hp.obo')

        internal_identifier = 0
        for term in hp.terms():

            register = True

            # uncomment if only want the phenotypic abnormality branch for KG Representation
            # superclass = iter(term.superclasses())
            # try:
            #     moment = next(superclass)
            #     while moment.id != 'HP:0000118':  # we just want the phenotypic abnormality branch
            #         moment = next(superclass)
            # except StopIteration:
            #     register = False
            # end

            if register or term.id == 'HP:0000001':
                entity_map_file.write(str(internal_identifier) + '\t' + 'https://purl.obolibrary.org/obo/'
                                      + term.id + '\n')
                dict_entity_map[term.id.replace(':', '_')] = str(internal_identifier)
                internal_identifier += 1

            if not register:
                other_branches.append(term.id)

    elif pair_type == 'DRUG-DRUG':
        import obonet
        ontology = obonet.read_obo('https://purl.obolibrary.org/obo/chebi.obo')

        internal_identifier = 0
        for id_, data in ontology.nodes(data=True):
            try:
                entity_map_file.write(str(internal_identifier) + '\t' + 'https://purl.obolibrary.org/obo/'
                                      + id_ + '\n')
                dict_entity_map[id_.replace(':', '_')] = str(internal_identifier)
                internal_identifier += 1
            except TypeError:
                pass

    entity_map_file.close()

    return dict_entity_map, other_branches


def write_r_map(relation_map_file_path):
    """

    :param relation_map_file_path:
    :return:
    """

    dict_relation_map = {}
    relation_map_file = open(relation_map_file_path, 'w', encoding='utf-8')
    relation_map_file.write(str(0) + '\t' + 'https://www.w3.org/2000/01/rdf-schema#subClassOf' + '\n')
    dict_relation_map['https://www.w3.org/2000/01/rdf-schema#subClassOf'] = str(0)

    relation_map_file.close()

    return dict_relation_map


def write_connections_items(entity_map_file_path, relation_map_file_path, dataset_path, pair_type):
    """

    :param entity_map_file_path:
    :param relation_map_file_path:
    :param dataset_path:
    :param pair_type:
    :return:
    """

    dict_entity_map, other_branches = write_e_map(entity_map_file_path, pair_type)
    dict_relation_map = write_r_map(relation_map_file_path)

    connections_lists = {}
    connection_list_identifier = 0

    if pair_type == 'DRUG-DISEASE':
        onto = get_ontology("https://purl.obolibrary.org/obo/doid/doid-merged.owl").load()

        for element in onto.classes():
            try:
                if element.name.startswith('DOID') and element.name.replace('_', ':') not in other_branches:
                    connection_list = []
                    is_a = element.is_a

                    for is_a_element in is_a:
                        if is_a_element.name.startswith('DOID'):
                            connection_list = [dict_entity_map[is_a_element.name], dict_entity_map[element.name], dict_relation_map['https://www.w3.org/2000/01/rdf-schema#subClassOf']]

                        if len(connection_list) >= 1:
                            connections_lists[str(connection_list_identifier)] = connection_list
                            connection_list_identifier += 1
            except AttributeError:  # doid.owl bad formatting workaround
                continue

    elif pair_type == 'GENE-PHENOTYPE':
        onto = get_ontology("https://purl.obolibrary.org/obo/hp.owl").load()

        for element in onto.classes():
            if element.name.startswith('HP') and element.name.replace('_', ':') not in other_branches:
                connection_list = []
                is_a = element.is_a

                for is_a_element in is_a:
                    if is_a_element.name.startswith('HP'):
                        connection_list = [dict_entity_map[is_a_element.name], dict_entity_map[element.name], dict_relation_map['https://www.w3.org/2000/01/rdf-schema#subClassOf']]

                    if len(connection_list) >= 1:
                        connections_lists[str(connection_list_identifier)] = connection_list
                        connection_list_identifier += 1

    elif pair_type == 'DRUG-DRUG':
        onto = get_ontology("https://purl.obolibrary.org/obo/chebi.owl").load()

        for element in onto.classes():
            if element.name.startswith('CHEBI') and element.name.replace('_', ':') not in other_branches:
                connection_list = []
                is_a = element.is_a

                for is_a_element in is_a:
                    try:
                        if is_a_element.name.startswith('CHEBI'):
                            connection_list = [dict_entity_map[is_a_element.name], dict_entity_map[element.name],
                                               dict_relation_map['https://www.w3.org/2000/01/rdf-schema#subClassOf']]

                        if len(connection_list) >= 1:
                            connections_lists[str(connection_list_identifier)] = connection_list
                            connection_list_identifier += 1

                    except AttributeError:
                        pass

    train_dataset = open(dataset_path + 'train.dat', 'w', encoding='utf-8')
    test_dataset = open(dataset_path + 'test.dat', 'w', encoding='utf-8')
    valid_dataset = open(dataset_path + 'valid.dat', 'w', encoding='utf-8')

    train_length = int(len(connections_lists) * 0.6)
    test_length = int(len(connections_lists) * 0.3)

    train_dataset_list = []
    while train_length > 0:
        value = random.choice(list(connections_lists.items()))
        train_dataset_list.append(value[1])
        del connections_lists[value[0]]
        train_length -= 1

    train_dataset_list.sort(key=lambda x: int(x[0]))
    for element in train_dataset_list:
        train_dataset.write(element[0] + '\t' + element[1] + '\t' + str(element[2]) + '\n')

    test_dataset_list = []
    while test_length > 0:
        value = random.choice(list(connections_lists.items()))
        test_dataset_list.append(value[1])
        del connections_lists[value[0]]
        test_length -= 1

    test_dataset_list.sort(key=lambda x: int(x[0]))
    for element in test_dataset_list:
        test_dataset.write(element[0] + '\t' + element[1] + '\t' + str(element[2]) + '\n')

    valid_dataset_list = list(connections_lists.values())

    valid_dataset_list.sort(key=lambda x: int(x[0]))
    for element in valid_dataset_list:
        valid_dataset.write(element[0] + '\t' + element[1] + '\t' + str(element[2]) + '\n')

    train_dataset.close()
    test_dataset.close()
    valid_dataset.close()
    
    return


# RUN ####

def main():
    """

    usage example:
    python3 src/data_interactions.py DRUG-DISEASE
    """

    pair_type = sys.argv[1]  # DRUG-DRUG, GENE-PHENOTYPE, GENE-DRUG, etc.

    if pair_type == 'DRUG-DISEASE':
        # ITEM RECOMMENDATION
        write_training_data('data/drug_disease/train_bc5cdr_corpus_all_information.tsv', 'data/drug_disease/test_bc5cdr_corpus_all_information.tsv',
                            'corpora/drug_disease/i_map.dat', 'corpora/drug_disease/u_map.dat', 'corpora/drug_disease/i2kg_map.tsv',
                            pair_type, 'corpora/drug_disease/')

        # KNOWLEDGE GRAPH REPRESENTATION
        write_connections_items('corpora/drug_disease/kg/e_map.dat', 'corpora/drug_disease/kg/r_map.dat', 'corpora/drug_disease/kg/',
                                pair_type)

    elif pair_type == 'GENE-PHENOTYPE':

        # ITEM RECOMMENDATION
        write_i2kg('corpora/i2kg_map.tsv', pair_type)
        write_training_data('data/gene_phenotype/train/amazon_gene.xml', 'data/gene_phenotype/test/expert_test.xml',
                            'corpora/gene_phenotype/i_map.dat', 'corpora/gene_phenotype/u_map.dat', 'corpora/gene_phenotype/i2kg_map.tsv',
                            pair_type, 'corpora/gene_phenotype/')

        # KNOWLEDGE GRAPH REPRESENTATION
        write_connections_items('corpora/gene_phenotype/kg/e_map.dat', 'corpora/gene_phenotype/kg/r_map.dat', 'corpora/gene_phenotype/kg/',
                                pair_type)

    elif pair_type == 'DRUG-DRUG':

        # ITEM RECOMMENDATION
        write_training_data('data/drug_drug/train/', 'data/drug_drug/test/', 'corpora/drug_drug/i_map.dat', 'corpora/drug_drug/u_map.dat',
                            'corpora/drug_drug/i2kg_map.tsv', pair_type, 'corpora/drug_drug/')

        # KNOWLEDGE GRAPH REPRESENTATION
        write_connections_items('corpora/drug_drug/kg/e_map.dat', 'corpora/drug_drug/kg/r_map.dat', 'corpora/drug_drug/kg/',
                                pair_type)

    return


if __name__ == "__main__":
    main()
