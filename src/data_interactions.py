import os
import sys
import xml.etree.ElementTree as element_tree
import random

import pronto
import obonet
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import parse_cid_entities


def process_ratings(relations_file_path, i2kg_file_path, pair_type):
    """

    :param relations_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :return:
    """

    if pair_type == 'DRUG-DISEASE':
        dict_ids_match_items, dict_ids_match_users, dict_gold_standard, dict_interactions, entities_dict = process_interactions_cd(relations_file_path, i2kg_file_path, pair_type)
    elif pair_type == 'GENE-PHENOTYPE':
        dict_ids_match_items, dict_ids_match_users, dict_interactions, entities_dict = process_interactions_gp(relations_file_path)
    elif pair_type == 'DRUG-DRUG':
        dict_ids_match_items, dict_ids_match_users, dict_gold_standard, dict_interactions, entities_dict = process_interactions_dd(relations_file_path, i2kg_file_path, pair_type)
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
        ontology = pronto.Ontology('http://purl.obolibrary.org/obo/doid.obo')
        for term in ontology.terms():
            i2kg_file.write(term.id[5:] + '\t' + term.name.lower() + '\t' + 'http://purl.obolibrary.org/obo/'
                            + term.id.replace(':', '_') + '\n')
            ontology_dict[term.name.lower()] = term.id.split(':')[1]

    elif pair_type == 'GENE-PHENOTYPE':
        ontology = pronto.Ontology('http://purl.obolibrary.org/obo/hp.obo')
        for term in ontology.terms():
            i2kg_file.write(term.id[3:] + '\t' + term.name + '\t' + 'http://purl.obolibrary.org/obo/'
                            + term.id.replace(':', '_') + '\n')

    elif pair_type == 'DRUG-DRUG':
        import obonet
        ontology = obonet.read_obo('http://purl.obolibrary.org/obo/chebi.obo')
        for id_, data in ontology.nodes(data=True):
            try:
                if data.get('synonym'):
                    for synonym in data.get('synonym'):
                        i2kg_file.write(id_.split(':')[1] + '\t' + synonym.split('" ')[0][1:].lower() + '\t' + 'http://purl.obolibrary.org/obo/' + id_.replace(':', '_') + '\n')
                        ontology_dict[synonym.split('" ')[0][1:].lower()] = id_.split(':')[1]

                i2kg_file.write(id_.split(':')[1] + '\t' + data.get('name').lower() + '\t' + 'http://purl.obolibrary.org/obo/' + id_.replace(':', '_') + '\n')
                ontology_dict[data.get('name').lower()] = id_.split(':')[1]

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


def write_training_data(relations_train_file_path, relations_test_file_path, item_map_file_path, user_map_file_path, i2kg_file_path, pair_type, dataset_path, train=True):
    """

    :param relations_train_file_path:
    :param relations_test_file_path:
    :param item_map_file_path:
    :param user_map_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :param dataset_path:
    :param train:
    :return:
    """

    dict_item_map = write_i_map(relations_train_file_path, relations_test_file_path, i2kg_file_path, pair_type, item_map_file_path)
    dict_user_map, dict_interactions_train, dict_interactions_test = write_u_map(relations_train_file_path, relations_test_file_path, i2kg_file_path, pair_type, user_map_file_path)

    if train:
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
        doid = pronto.Ontology('http://purl.obolibrary.org/obo/doid.obo')

        internal_identifier = 0
        for term in doid.terms():
            register = True

            if register or term.id == 'DOID:4':
                entity_map_file.write(str(internal_identifier) + '\t' + 'http://purl.obolibrary.org/obo/' + term.id + '\n')
                dict_entity_map[term.id.replace(':', '_')] = str(internal_identifier)
                internal_identifier += 1

            if not register:
                other_branches.append(term.id)

    elif pair_type == 'GENE-PHENOTYPE':
        hp = pronto.Ontology('http://purl.obolibrary.org/obo/hp.obo')

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
                entity_map_file.write(str(internal_identifier) + '\t' + 'http://purl.obolibrary.org/obo/' + term.id + '\n')
                dict_entity_map[term.id.replace(':', '_')] = str(internal_identifier)
                internal_identifier += 1

            if not register:
                other_branches.append(term.id)

    elif pair_type == 'DRUG-DRUG':
        ontology = obonet.read_obo('http://purl.obolibrary.org/obo/chebi.obo')

        internal_identifier = 0
        for id_, data in ontology.nodes(data=True):
            try:
                entity_map_file.write(str(internal_identifier) + '\t' + 'http://purl.obolibrary.org/obo/' + id_ + '\n')
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
        ontology = obonet.read_obo('http://purl.obolibrary.org/obo/doid.obo')

        for id_, element in ontology.nodes(data=True):
            try:
                if id_.startswith('CHEBI') and id_.replace('_', ':') not in other_branches:
                    connection_list = []
                    is_a = element['is_a']

                    for is_a_element in is_a:
                        if is_a_element.name.startswith('DOID'):
                            connection_list = [dict_entity_map[is_a_element.name], dict_entity_map[element.name], dict_relation_map['https://www.w3.org/2000/01/rdf-schema#subClassOf']]

                        if len(connection_list) >= 1:
                            connections_lists[str(connection_list_identifier)] = connection_list
                            connection_list_identifier += 1

            except AttributeError:  # doid.owl bad formatting workaround
                continue

    elif pair_type == 'GENE-PHENOTYPE':
        ontology = obonet.read_obo('http://purl.obolibrary.org/obo/hp.obo')

        for id_, element in ontology.nodes(data=True):
            if id_.startswith('HP') and id_.replace('_', ':') not in other_branches:
                connection_list = []
                try:
                    is_a = element['is_a']

                    for is_a_element in is_a:
                        try:
                            if is_a_element.name.startswith('HP'):
                                connection_list = [dict_entity_map[is_a_element.name], dict_entity_map[element.name], dict_relation_map['https://www.w3.org/2000/01/rdf-schema#subClassOf']]

                            if len(connection_list) >= 1:
                                connections_lists[str(connection_list_identifier)] = connection_list
                                connection_list_identifier += 1
                        except AttributeError:
                            pass
                except KeyError:
                    pass

    elif pair_type == 'DRUG-DRUG':
        ontology = obonet.read_obo('http://purl.obolibrary.org/obo/chebi.obo')

        for id_, element in ontology.nodes(data=True):
            if id_.startswith('CHEBI') and id_.replace('_', ':') not in other_branches:
                connection_list = []
                try:
                    is_a = element['is_a']

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
                except KeyError:
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


# ITEM RECOMMENDATION FILE PREPARATION DRUG-DRUG ####

def exception_item_to_kg(output_path, pair_type):
    """

    :param output_path:
    :param pair_type:
    :return:
    """

    try:
        ontology_dict = np.load('bin/i2kg_map_cd.npy', allow_pickle=True)
        #print('Loaded item to knowledge graph identifier dictionary from file bin/i2kg_map_cd.npy!')
    except FileNotFoundError:
        ontology_dict = write_i2kg(output_path, pair_type)
        np.save('bin/i2kg_map_cd.npy', ontology_dict)
        ontology_dict = np.load('bin/i2kg_map_cd.npy', allow_pickle=True)
        #print('Created item to knowledge graph identifier dictionary to file bin/i2kg_map_cd.npy!')

    return ontology_dict


def exception_levenshtein(support_dict, entities_dict, ontology_dict):
    """

    :param support_dict:
    :param entities_dict:
    :param ontology_dict:
    :return:
    """

    try:
        levenshtein_distances = np.load('bin/levenshtein_distances_cd.npy', allow_pickle=True)
        #print('Loaded levenshtein dictionary from file bin/levenshtein_distances_cd.npy!')

    except FileNotFoundError:
        levenshtein_distances = {}
        for items in support_dict.items():
            entity_1_name = entities_dict[items[1][0]].lower()
            entity_2_name = entities_dict[items[1][1]].lower()
            for ontology_term in ontology_dict.item():
                if (entity_2_name, ontology_term) not in levenshtein_distances:
                    distance = fuzz.token_sort_ratio(entity_2_name, ontology_term)
                    if distance >= 90:
                        levenshtein_distances[(entity_2_name, ontology_term)] = distance
                if (entity_1_name, ontology_term) not in levenshtein_distances:
                    distance = fuzz.token_sort_ratio(entity_1_name, ontology_term)
                    if distance >= 90:
                        levenshtein_distances[(entity_1_name, ontology_term)] = distance

        np.save('bin/levenshtein_distances_cd.npy', levenshtein_distances)
        levenshtein_distances = np.load('bin/levenshtein_distances_cd.npy', allow_pickle=True)
        #print('Created levenshtein dictionary to file bin/levenshtein_distances_cd.npy!')

    return levenshtein_distances


def exception_entity(ontology_dict, entities_dict, levenshtein_distances, entities_unique_identifier, items, entity_name, entity=None):
    """

    :param ontology_dict:
    :param entities_dict:
    :param levenshtein_distances:
    :param entities_unique_identifier:
    :param items:
    :param entity_name:
    :param entity:
    :return:
    """

    ontology_entity = ''
    try:
        ontology_entity = ontology_dict.item()[entity_name]
    except KeyError:
        matched = False
        for ontology_term in ontology_dict.item():
            if (entity_name, ontology_term) in levenshtein_distances.item():
                ontology_entity = ontology_dict.item()[ontology_term]
                matched = True
                break

        if not matched:
            # print(entity_name, 'not in ChEBI ontology!')
            if entity == 1:
                ontology_entity = entities_unique_identifier[entities_dict[items[1][0]]]
            else:
                ontology_entity = entities_unique_identifier[entities_dict[items[1][1]]]

    return ontology_entity


def process_interactions_dd(xml_file_path, i2kg_file_path, pair_type):
    """

    :param xml_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :return: dict with the relations, tagged with 0 if false and with 1 if true, of type
             {identifier1: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), 1],
             identifier2: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), -1], ...}
    """

    ontology_dict = exception_item_to_kg(i2kg_file_path, pair_type)

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
                        used_entities.append(elements.attrib['text'])
                        entity_identifier += 1

                elif elements.tag == 'pair':
                    if elements.attrib['ddi'] == 'true':
                        relation = 1
                    else:
                        relation = -1
                    count_interactions_draft[identifier] = [elements.attrib['e1'], elements.attrib['e2'], relation]
                    identifier += 1

    dict_ids_match_items = {}
    dict_ids_match_users = {}
    dict_gold_standard = {}
    count_interactions = {}

    # for full dataset
    levenshtein_distances = exception_levenshtein(count_interactions_draft, entities_dict, ontology_dict)

    for items in count_interactions_draft.items():
        entity_1_name = entities_dict[items[1][0]].lower()
        entity_2_name = entities_dict[items[1][1]].lower()

        ontology_entity_1 = exception_entity(ontology_dict, entities_dict, levenshtein_distances, entities_unique_identifier, items, entity_1_name, entity=1)
        ontology_entity_2 = exception_entity(ontology_dict, entities_dict, levenshtein_distances, entities_unique_identifier, items, entity_2_name, entity=2)

        count_interactions[items[0]] = [(ontology_entity_1, entity_1_name), (ontology_entity_2, entity_2_name), items[1][2]]
        dict_ids_match_users[entity_1_name] = ontology_entity_1
        dict_ids_match_items[entity_2_name] = ontology_entity_2
        # dict_gold_standard[(ontology_entity_1, ontology_entity_2)] = items[1][2]
        dict_gold_standard[ontology_entity_1] = entities_unique_identifier[entities_dict[items[1][0]]]
        dict_gold_standard[ontology_entity_2] = entities_unique_identifier[entities_dict[items[1][1]]]

        # for sub-set
        # try:
        #     ontology_entity_2 = ontology_dict[entity_2_name]
        #     count_interactions[items[0]] = [
        #         (entities_unique_identifier[entities_dict[items[1][0]]], entities_dict[items[1][0]]),
        #         (ontology_entity_2, entity_2_name), items[1][2]]
        #
        #     dict_ids_match_users[entities_dict[items[1][0]]] = entities_unique_identifier[entities_dict[items[1][0]]]
        #     dict_ids_match_items[entity_2_name] = ontology_entity_2
        #     dict_gold_standard[str((entities_unique_identifier[entities_dict[items[1][0]]], ontology_entity_2))] = \
        #     items[1][2]
        #
        # except KeyError:
        #     continue

    return dict_ids_match_items, dict_ids_match_users, dict_gold_standard, count_interactions, entities_dict


# ITEM RECOMMENDATION FILE PREPARATION CHEMICAL|DRUG-DISEASE ####

wrong_diseases_list = ['mutism', 'noma']


def process_interactions_cd(txt_file_path, i2kg_file_path, pair_type):
    """

    :param txt_file_path:
    :param i2kg_file_path:
    :param pair_type:
    :return: dict with the relations, tagged with 0 if false and with 1 if true, of type
             {identifier1: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), 1],
             identifier2: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), -1], ...}
    """

    ontology_dict = exception_item_to_kg(i2kg_file_path, pair_type)

    count_interactions_draft = {}
    entities_dict = {}
    entity_identifier = 0
    entities_unique_identifier = {}
    used_entities = []

    relations = parse_cid_entities.get_sentence_information_entities(txt_file_path)

    identifier = 0
    for relation, value in relations.items():
        relation = eval(relation)
        if value == 'True':
            tag = 1
        else:
            tag = -1

        if relation[1][0] != '-1' and relation[2][0] != '-1':  # wrong ids in original data
            entities_dict[relation[1][0]] = relation[1][1]
            entities_dict[relation[2][0]] = relation[2][1]

            if relation[1][1] not in used_entities:
                entities_unique_identifier[relation[1][1]] = 'D' + str(entity_identifier)
                entity_identifier += 1
                used_entities.append(relation[1][1])

            if relation[2][1] not in used_entities:
                entities_unique_identifier[relation[2][1]] = 'C' + str(entity_identifier)
                entity_identifier += 1
                used_entities.append(relation[2][1])

            count_interactions_draft[identifier] = [relation[1][0], relation[2][0], tag]

            identifier += 1

    dict_ids_match_items = {}
    dict_ids_match_users = {}
    dict_gold_standard = {}
    count_interactions = {}

    # for full dataset
    levenshtein_distances = exception_levenshtein(count_interactions_draft, entities_dict, ontology_dict)

    for items in count_interactions_draft.items():
        entity_1_name = entities_dict[items[1][0]].lower()
        entity_2_name = entities_dict[items[1][1]].lower()

        ontology_entity_1 = exception_entity(ontology_dict, entities_dict, levenshtein_distances, entities_unique_identifier, items, entity_1_name, entity=1)
        ontology_entity_2 = exception_entity(ontology_dict, entities_dict, levenshtein_distances, entities_unique_identifier, items, entity_2_name, entity=2)

        count_interactions[items[0]] = [(ontology_entity_1, entity_1_name), (ontology_entity_2, entity_2_name),
                                        items[1][2]]
        dict_ids_match_users[entity_1_name] = ontology_entity_1
        dict_ids_match_items[entity_2_name] = ontology_entity_2
        # dict_gold_standard[(ontology_entity_1, ontology_entity_2)] = items[1][2]
        dict_gold_standard[ontology_entity_1] = entities_unique_identifier[entities_dict[items[1][0]]]
        dict_gold_standard[ontology_entity_2] = entities_unique_identifier[entities_dict[items[1][1]]]

        # for sub-set
        # try:
        #     ontology_entity_2 = ontology_dict[entity_2_name]
        #
        #     count_interactions[items[0]] = [(entities_unique_identifier[entities_dict[items[1][0]]],
        #                                      entities_dict[items[1][0]]),
        #                                     (ontology_entity_2, entity_2_name),
        #                                     items[1][2]]
        #
        #     dict_ids_match_users[entities_dict[items[1][0]]] = entities_unique_identifier[entities_dict[items[1][0]]]
        #     dict_ids_match_items[entity_2_name] = ontology_entity_2
        #
        # except KeyError:
        #     continue

    return dict_ids_match_items, dict_ids_match_users, dict_gold_standard, count_interactions, entities_dict


# ITEM RECOMMENDATION FILE PREPARATION GENE-PHENOTYPE ####

def process_interactions_gp(xml_file_path):
    """

    :param xml_file_path:
    :return: dict with the relations, tagged with 0 if false and with 1 if true, of type
             {identifier1: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), 1],
             identifier2: [(id_entity_1, name_entity_1), (id_entity_2, name_entity_2), -1], ...}
    """

    count_interactions = {}
    entities_dict = {}
    identifier = 0

    for infile in os.listdir(xml_file_path):
        tree = element_tree.parse(xml_file_path + '/' + infile)
        root = tree.getroot()

        for sentence in root:
            entities_list = []

            for elements in sentence:
                if elements.tag == 'entity':
                    entities_list.append((elements.attrib['ontology_id'].replace('_', ':'), elements.attrib['text']))
                    entities_dict[elements.attrib['ontology_id'].replace('_', ':')] = elements.attrib['text']
                elif elements.tag == 'pair':
                    if elements.attrib['relation'] == 'true':
                        entities_list.append(1)
                    elif elements.attrib['relation'] == 'false':
                        entities_list.append(-1)

            if entities_list[0][0].startswith('HP'):
                entities_list[0], entities_list[1] = entities_list[1], entities_list[0]
            count_interactions[identifier] = entities_list
            identifier += 1

    dict_ids_match_items = {}
    dict_ids_match_users = {}

    for items in count_interactions.items():
        entity_1_name = entities_dict[items[1][0][0]].lower()
        entity_2_name = entities_dict[items[1][1][0]].lower()
        dict_ids_match_users[entity_1_name] = items[1][0][0]
        dict_ids_match_items[entity_2_name] = items[1][1][0]

    return dict_ids_match_items, dict_ids_match_users, count_interactions, entities_dict


# RUN ####

def main():
    """

    usage example:
    python3 src/data_interactions.py DRUG-DISEASE test[OPTIONAL]
    """

    pair_type = sys.argv[1]  # DRUG-DRUG, GENE-PHENOTYPE, GENE-DRUG, etc.
    test = sys.argv[2]

    if pair_type == 'DRUG-DISEASE':
        # ITEM RECOMMENDATION
        if test:
            data_to_test_location = sys.argv[3]
            os.system('rm -rf corpora/to_test/ | true')
            os.system('mkdir corpora/to_test/')
            write_i2kg('corpora/to_test/i2kg_map.tsv', pair_type)
            os.system('mkdir corpora/bin/')
            write_training_data('corpora/bin/', data_to_test_location + '/', 'corpora/to_test/i_map.dat',
                                'corpora/to_test/u_map.dat',
                                'corpora/to_test/i2kg_map.tsv', pair_type, 'corpora/to_test/', False)
            os.system('rm -rf corpora/bin/ | true')

        else:
            write_training_data('data/drug_disease/train_bc5cdr_corpus_all_information.tsv', 'data/drug_disease/test_bc5cdr_corpus_all_information.tsv',
                            'corpora/drug_disease/i_map.dat', 'corpora/drug_disease/u_map.dat', 'corpora/drug_disease/i2kg_map.tsv',
                            pair_type, 'corpora/drug_disease/')

        # KNOWLEDGE GRAPH REPRESENTATION
        write_connections_items('corpora/drug_disease/kg/e_map.dat', 'corpora/drug_disease/kg/r_map.dat', 'corpora/drug_disease/kg/',
                                pair_type)

    elif pair_type == 'GENE-PHENOTYPE':

        # ITEM RECOMMENDATION
        if test:
            data_to_test_location = sys.argv[3]
            os.system('rm -rf corpora/to_test/ | true')
            os.system('mkdir corpora/to_test/')
            write_i2kg('corpora/to_test/i2kg_map.tsv', pair_type)
            os.system('mkdir corpora/bin/')
            write_training_data('corpora/bin/', data_to_test_location + '/', 'corpora/to_test/i_map.dat',
                                'corpora/to_test/u_map.dat',
                                'corpora/to_test/i2kg_map.tsv', pair_type, 'corpora/to_test/', False)
            os.system('rm -rf corpora/bin/ | true')

        else:
            write_i2kg('corpora/i2kg_map.tsv', pair_type)
            write_training_data('data/gene_phenotype/train/amazon_gene.xml', 'data/gene_phenotype/test/expert_test.xml',
                            'corpora/gene_phenotype/i_map.dat', 'corpora/gene_phenotype/u_map.dat', 'corpora/gene_phenotype/i2kg_map.tsv',
                            pair_type, 'corpora/gene_phenotype/')

        # KNOWLEDGE GRAPH REPRESENTATION
        write_connections_items('corpora/gene_phenotype/kg/e_map.dat', 'corpora/gene_phenotype/kg/r_map.dat', 'corpora/gene_phenotype/kg/',
                                pair_type)

    elif pair_type == 'DRUG-DRUG':

        # ITEM RECOMMENDATION
        if test:
            data_to_test_location = sys.argv[3]
            os.system('rm -rf corpora/to_test/ | true')
            os.system('mkdir corpora/to_test/')
            write_i2kg('corpora/to_test/i2kg_map.tsv', pair_type)
            os.system('mkdir corpora/bin/')
            write_training_data('corpora/bin/', data_to_test_location + '/', 'corpora/to_test/i_map.dat', 'corpora/to_test/u_map.dat',
                                'corpora/to_test/i2kg_map.tsv', pair_type, 'corpora/to_test/', False)
            os.system('rm -rf corpora/bin/ | true')

        else:
            write_i2kg('corpora/i2kg_map.tsv', pair_type)
            write_training_data('data/drug_drug/train/', 'data/drug_drug/test/', 'corpora/drug_drug/i_map.dat', 'corpora/drug_drug/u_map.dat',
                                'corpora/drug_drug/i2kg_map.tsv', pair_type, 'corpora/drug_drug/')

        # KNOWLEDGE GRAPH REPRESENTATION
        if test:
            # data_to_test_location = sys.argv[3]
            os.system('rm -rf corpora/to_test/kg/ | true')
            os.system('mkdir corpora/to_test/kg/')
            write_connections_items('corpora/to_test/kg/e_map.dat', 'corpora/to_test/kg/r_map.dat',
                                    'corpora/to_test/kg/', pair_type)
        else:
            write_connections_items('corpora/drug_drug_subset/kg/e_map.dat', 'corpora/drug_drug_subset/kg/r_map.dat',
                                    'corpora/drug_drug_subset/kg/', pair_type)

    return


if __name__ == "__main__":
    main()
