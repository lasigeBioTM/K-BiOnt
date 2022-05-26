from spacy.lang.en import English
import os
import itertools


def divided_by_sentences(abstract):
    """Divides abstracts by sentences
    :param abstract:
    :return: list of sentences of the abstract
    """

    nlp_l = English()
    nlp_l.add_pipe(nlp_l.create_pipe('sentencizer'))
    doc = nlp_l(abstract)
    sentences = [sent.string.strip() for sent in doc.sents]

    return sentences


def get_new_offsets_sentences(input_file):
    """
    :param input_file:
    :return:
    """

    entities = {}

    input = open(input_file, 'r')
    input_blocks = input.read().split('\n\n')
    input.close()

    for block in input_blocks:

        if len(block.split('\n')) > 3:
            block_id = block.split('|')[0]
            title = [block.split('\n')[0].split('|')[2]]
            abstract = block.split('\n')[1].split('|')[2]
            list_sentences = title + divided_by_sentences(abstract)

            annotation_lines = block.split('\n')[2:]

            limit_1 = 0
            limit_2 = 0
            sentence_id = 0

            for sentence in list_sentences:
                entity_id = 0
                limit_2 += len(sentence) + 1

                for annotation in annotation_lines:
                    if 'CID' not in annotation and annotation != '':

                        offset_1 = annotation.split('\t')[1]
                        offset_2 = annotation.split('\t')[2]

                        if limit_1 <= int(offset_1) <= limit_2 and limit_1 <= int(offset_2) <= limit_2:
                            entities['a' + block_id + '.s' + str(sentence_id) + '.e' + str(entity_id)] = annotation.split('\t')[5].split('|')[0]
                            entity_id += 1

                sentence_id += 1
                limit_1 += len(sentence) + 1

    return entities


def get_new_offsets_sentences_entities(block):
    """
    :param block:
    :return:
    """

    entities_per_sentence = {}

    block_id = block.split('|')[0]
    title = [block.split('\n')[0].split('|')[2]]
    abstract = block.split('\n')[1].split('|')[2]
    list_sentences = title + divided_by_sentences(abstract)

    annotation_lines = block.split('\n')[2:]

    limit_1 = 0
    limit_2 = 0
    sentence_id = 0

    for sentence in list_sentences:

        entity_id = 0

        limit_2 += len(sentence) + 1
        entities_per_sentence[('a' + block_id + '.s' + str(sentence_id), sentence)] = []

        for annotation in annotation_lines:

            if 'CID' not in annotation and annotation != '':

                offset_1 = annotation.split('\t')[1]
                offset_2 = annotation.split('\t')[2]

                if limit_1 <= int(offset_1) <= limit_2 and limit_1 <= int(offset_2) <= limit_2:

                    updated_offset_1 = int(offset_1) - limit_1
                    updated_offset_2 = int(offset_2) - limit_1 - 1

                    entities_per_sentence[('a' + block_id + '.s' + str(sentence_id), sentence)].append((entity_id,
                                           updated_offset_1, updated_offset_2, annotation.split('\t')[3],
                                           annotation.split('\t')[4], annotation.split('\t')[5].split('|')[0]))

                    entity_id += 1

        sentence_id += 1
        limit_1 += len(sentence) + 1

    return entities_per_sentence


def get_sentence_entities(base_dir):
    """

    :param base_dir:
    :return:
    """

    all_entities = {}  # (sentence_id, entity_1_id, entity_2_id):False

    input_blocks = []
    for infile in os.listdir(base_dir):
        input_file = open(base_dir + '/' + infile, 'r')
        input_blocks.extend(input_file.read().split('\n\n'))
        input_file.close()


    for block in input_blocks:
        if len(block.split('\n')) > 3:

            all_pairs = []
            for line in block.split('\n')[2:]:
                if 'CID' in line:
                    all_pairs.append((line.split('\t')[2], line.split('\t')[3]))

            entities_per_sentence = get_new_offsets_sentences_entities(block)

            if all_pairs:
                for sentence, entities_sentence in entities_per_sentence.items():

                    entities = {}
                    for pair in all_pairs:
                        pair_entities = []
                        save_entity_1 = []
                        save_entity_2 = []
                        for entity in entities_sentence:
                            if entity[5] in pair[0]:
                                save_entity_1.append([sentence[0] + '.e' + str(entity[0]), entity[5], entity[3]])
                            elif entity[5] in pair[1]:
                                save_entity_2.append([sentence[0] + '.e' + str(entity[0]), entity[5], entity[3]])

                        if save_entity_1 and save_entity_2:
                            for element_1 in save_entity_1:
                                for element_2 in save_entity_2:
                                    pair_entities.append((element_1, element_2))

                        for pair_id in pair_entities:
                            if sentence[0] not in entities:
                                entities[sentence[0]] = [pair_id]
                            else:
                                entities[sentence[0]].append(pair_id)

                    save_entities_list_chemicals = []
                    save_entities_list_diseases = []
                    check_if_possible_cid = []
                    for entity in entities_sentence:
                        if entity[4] == 'Chemical':
                            save_entities_list_chemicals.append([sentence[0] + '.e' + str(entity[0]), entity[5], entity[3]])
                        elif entity[4] == 'Disease':
                            save_entities_list_diseases.append([sentence[0] + '.e' + str(entity[0]), entity[5], entity[3]])
                        check_if_possible_cid.append(entity[4])

                    if len(set(check_if_possible_cid)) == 2:
                        all_possible_pairs = [(x, y) for x in save_entities_list_chemicals for y in save_entities_list_diseases]

                        for all_possible_pair in all_possible_pairs:
                            if sentence[0] in entities:
                                if all_possible_pair in entities[sentence[0]] or (all_possible_pair[1], all_possible_pair[0]) in entities[sentence[0]]:
                                    all_entities[str((sentence[0], all_possible_pair[0], all_possible_pair[1]))] = 'True'
                                else:
                                    all_entities[str((sentence[0], all_possible_pair[0], all_possible_pair[1]))] = 'False'
                            else:
                                all_entities[str((sentence[0], all_possible_pair[0], all_possible_pair[1]))] = 'False'

    return all_entities


def get_sentence_information_entities(base_dir):
    """

    :param base_dir:
    :return:
    """

    all_entities = {}  # (sentence_id, entity_1_id, entity_2_id):False

    input_blocks = []
    for infile in os.listdir(base_dir):
        input_file = open(base_dir + '/' + infile, 'r')
        input_blocks.extend(input_file.read().split('\n\n'))
        input_file.close()

    for block in input_blocks:
        if len(block.split('\n')) > 3:

            all_pairs = []
            for line in block.split('\n')[2:]:
                if 'CID' in line:
                    all_pairs.append((line.split('\t')[2], line.split('\t')[3]))

            entities_per_sentence = get_new_offsets_sentences_entities(block)

            if all_pairs:
                for sentence, entities_sentence in entities_per_sentence.items():

                    entities = {}
                    for pair in all_pairs:
                        pair_entities = []
                        save_entity_1 = []
                        save_entity_2 = []
                        for entity in entities_sentence:
                            if entity[5] in pair[0]:
                                save_entity_1.append([entity[5], entity[3]])
                            elif entity[5] in pair[1]:
                                save_entity_2.append([entity[5], entity[3]])

                        if save_entity_1 and save_entity_2:
                            for element_1 in save_entity_1:
                                for element_2 in save_entity_2:
                                    pair_entities.append((element_1, element_2))

                        for pair_id in pair_entities:
                            if sentence[0] not in entities:
                                entities[sentence[0]] = [pair_id]
                            else:
                                entities[sentence[0]].append(pair_id)
                    save_entities_list_chemicals = []
                    save_entities_list_diseases = []
                    check_if_possible_cid = []
                    for entity in entities_sentence:
                        if entity[4] == 'Chemical':
                            save_entities_list_chemicals.append([entity[5], entity[3]])
                        elif entity[4] == 'Disease':
                            save_entities_list_diseases.append([entity[5], entity[3]])
                        check_if_possible_cid.append(entity[4])

                    if len(set(check_if_possible_cid)) == 2:
                        all_possible_pairs = [(x, y) for x in save_entities_list_chemicals for y in save_entities_list_diseases]

                        for all_possible_pair in all_possible_pairs:
                            if sentence[0] in entities:
                                if all_possible_pair in entities[sentence[0]] or (all_possible_pair[1], all_possible_pair[0]) in entities[sentence[0]]:
                                    all_entities[str((sentence[0], all_possible_pair[0], all_possible_pair[1]))] = 'True'
                                else:
                                    all_entities[str((sentence[0], all_possible_pair[0], all_possible_pair[1]))] = 'False'
                            else:
                                all_entities[str((sentence[0], all_possible_pair[0], all_possible_pair[1]))] = 'False'

    return all_entities