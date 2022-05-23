import os
import sys
import numpy as np

from data_interactions import process_interactions_cd, process_interactions_dd  # initial processing script
import parse_cid_entities  # chemical-disease interactions
import parse_dd_entities   # drug-drug interactions
import parse_gp_entities   # gene-phenotype interactions
import statistics


# PROCESS USERS FILE

def get_user_map(users_file):
    """

      :param users_file:
      :return: {entity_identifier: user_identifier, '40279': '2190', '4639': '2191', etc.}
      """

    users = open(users_file, 'r', encoding='utf-8')
    list_users = users.readlines()
    users.close()

    dict_users = {}
    for line in list_users:
        dict_users[line.split('\t')[-1][:-1]] = line.split('\t')[0]

    return dict_users


# PROCESS ITEMS FILE

def get_item_map(items_file, pair_type=None):
    """

    :param items_file:
    :param pair_type:
    :return: {entity_identifier: item_identifier, '02550': '2158', '4639': '2159'. etc.}
    """

    items = open(items_file, 'r', encoding='utf-8')
    list_items = items.readlines()
    items.close()

    dict_items = {}
    for line in list_items:
        if pair_type == 'DRUG-DRUG':
            dict_items[line.split('\t')[-1][:-1]] = line.split('\t')[0]
        elif pair_type == 'DRUG-DISEASE':
            dict_items[line.split('\t')[-1][:-1]] = line.split('\t')[0]
        else:
            dict_items['HP_' + line.split('\t')[-1][:-1]] = line.split('\t')[0]

    return dict_items


# PROCESS ITEM RECOMMENDATION LAYER FILE

def process_item_recommendation(item_recommendation_file, starting_line=62):  # tup
    """

    :param item_recommendation_file:
    :param starting_line:
    :return:
    """

    item_recommendation = open(item_recommendation_file, 'r', encoding='utf-8')
    list_item_recommendation = item_recommendation.readlines()
    item_recommendation.close()

    dict_item_recommendations = {}

    for i, line in enumerate(list_item_recommendation):
        if starting_line <= i:
            user_id = line.split('user:')[1].split('\t')[0]
            top_list = line.split('top:')[1][:-1].split(',')
            dict_item_recommendations[user_id] = top_list

    return dict_item_recommendations


# PROCESS BIONT MODEL FILE

def process_model(model_results_file, pair_type):  # biont
    """

    :param model_results_file:
    :param pair_type:
    :return:
    """

    model = open(model_results_file, 'r', encoding='utf-8')
    model.readline()  # skip header
    list_model = model.readlines()
    model.close()

    dict_model = {}
    counter = 0
    for line in list_model:
        if pair_type == 'GENE-PHENOTYPE':
            if line.split('\t')[-1][:-1] == 'effect':
                dict_model[str((line.split('\t')[0].split('.')[0].split('s')[-1], line.split('\t')[0], line.split('\t')[1]))] = True
            else:
                dict_model[str((line.split('\t')[0].split('.')[0].split('s')[-1], line.split('\t')[0], line.split('\t')[1]))] = False
        elif pair_type == 'DRUG-DISEASE':
            if line.split('\t')[-1][:-1] == 'effect':
                dict_model[str((line.split('\t')[0].split('.e')[0], line.split('\t')[0], line.split('\t')[1]))] = True
            else:
                dict_model[str((line.split('\t')[0].split('.e')[0], line.split('\t')[0], line.split('\t')[1]))] = False
        elif pair_type == 'DRUG-DRUG':
            if line.split('\t')[-1][:-1] == 'effect':
                dict_model[str((line.split('\t')[0].split('.e')[0], line.split('\t')[0], line.split('\t')[1]))] = True

            else:
                dict_model[str((line.split('\t')[0].split('.e')[0], line.split('\t')[0], line.split('\t')[1]))] = False

    return dict_model


# CREATE MAJORITY VOTING FILE COMPILING ALL OUTPUTS

def process_answers(item_recommendation_file, users_file, items_file, gold_standard_file, i2kg_file_path, original_file, model_results_file, validation_file,
                    starting_line=62, pair_type=None, test=False):
    """

    :param item_recommendation_file:
    :param users_file:
    :param items_file:
    :param gold_standard_file:
    :param i2kg_file_path:
    :param original_file:
    :param model_results_file:
    :param validation_file:
    :param starting_line:
    :param pair_type:
    :param test:
    :return:
    """

    # Generate general dictionaries
    dict_gold_standard = {}
    dict_item_recommendation = process_item_recommendation(item_recommendation_file, starting_line)
    dict_users = get_user_map(users_file)
    dict_items = get_item_map(items_file, pair_type)

    # Adapting to specific datasets
    if pair_type == 'DRUG-DISEASE':
        dict_model = process_model(model_results_file, pair_type)
        dict_gold_standard = parse_cid_entities.get_sentence_entities(original_file)
        dict_ids_match_items, dict_ids_match_users, dict_ui_gs, count_interactions, entities_dict = process_interactions_cd(gold_standard_file, i2kg_file_path, pair_type)

        dict_entities = {}
        for entity_id, entity_name in entities_dict.items():
            try:
                dict_entities[entity_id] = dict_ids_match_users[entity_name]
            except KeyError:
                try:
                    dict_entities[entity_id] = dict_ids_match_items[entity_name]
                except KeyError:
                    pass

    elif pair_type == 'DRUG-DRUG':
        dict_model = process_model(model_results_file, pair_type)
        dict_gold_standard = parse_dd_entities.get_sentence_entities(gold_standard_file)
        dict_ids_match_users, dict_ids_match_items, dict_ui_gs, count_interactions, entities_dict = process_interactions_dd(gold_standard_file, i2kg_file_path, pair_type)

        dict_entities = {}
        for entity_id, entity_name in entities_dict.items():
            try:
                dict_entities[entity_id] = dict_ids_match_users[entity_name]
            except KeyError:
                try:
                    dict_entities[entity_id] = dict_ids_match_items[entity_name]
                except KeyError:
                    pass

    else:
        assert pair_type == 'GENE-PHENOTYPE'
        dict_model = process_model(model_results_file, pair_type)
        dict_gold_standard = get_gold_standard_gp(gold_standard_file)

    # Creating validation file
    validation = open(validation_file, 'w', encoding='utf-8')
    if test:
        validation.write(
            'relation_identifier' + '\t' + 'user' + '\t' + 'item' + '\t' + 'model' + '\t' + 'in_top_3' + '\t'
            + 'in_top_5' + '\t' + 'in_top_10' + '\t' + 'final_attribution' + '\n')
    else:
        validation.write('relation_identifier' + '\t' + 'user' + '\t' + 'item' + '\t' + 'model' + '\t' + 'in_top_3' + '\t'
                     + 'in_top_5' + '\t' + 'in_top_10' + '\t' + 'gold_standard' + '\t' + 'answer' + '\n')

    identifier = 0
    list_lines = []
    entity_1_user = ''
    entity_2_item = ''

    for key, item in dict_gold_standard.items():
        if 'disease' in pair_type.lower():
            key = eval(key)
        #print(dict_model)
        try:
            entity_1_user = dict_users[dict_entities[key[1]]]
            entity_2_item = dict_items[dict_entities[key[2]]]

        except KeyError:  # -1
            continue

        gold_standard = item
        model_key_1 = (key[0], key[1], key[2])
        model_key_2 = (key[0], key[2], key[1])

        try:
            if str(model_key_1) in dict_model:
                model = dict_model[str(model_key_1)]
            else:
                model = dict_model[str(model_key_2)]

        except KeyError:
            # print('This pair is not present in the model file results:', model_key_1, model_key_2)
            continue

        if entity_1_user in dict_item_recommendation:
            if entity_2_item in dict_item_recommendation[entity_1_user]:
                if entity_2_item in dict_item_recommendation[entity_1_user][:3]:
                    in_top_3 = in_top_5 = in_top_10 = True

                elif entity_2_item in dict_item_recommendation[entity_1_user][:5]:
                    in_top_3 = False
                    in_top_5 = in_top_10 = True

                else:
                    in_top_3 = in_top_5 = False
                    in_top_10 = True

            else:
                in_top_3 = in_top_5 = in_top_10 = False

        else:
            in_top_3 = in_top_5 = in_top_10 = False

        if test:
            line = [str(identifier), key[1], key[2], str(model), str(in_top_3), str(in_top_5), str(in_top_10)]
        else:
            line = [str(identifier), entity_1_user, entity_2_item, str(model), str(in_top_3), str(in_top_5), str(in_top_10), str(gold_standard)]
        identifier += 1
        list_lines.append(line)

    for line in list_lines:
        if test:
            if line[3] == 'True' or line[4] == 'True' or line[5] == 'True' or line[6] == 'True':
                answer = 'True'
            else:
                answer = 'False'
            validation.write('\t'.join(line) + '\t' + answer + '\n')
        else:
            model = line[3]
            in_top_3 = line[4]
            in_top_5 = line[5]
            in_top_10 = line[6]
            gold_standard = line[7]

            # 0 = fully disagree
            # 1 = model correct, RS wrong
            # 2 = RS correct in top 10, model wrong
            # 3 = RS correct in top 5, model wrong
            # 4 = RS correct in top 3, model wrong
            # 5 = RS correct in top 10, model correct
            # 6 = RS correct in top 5, model correct
            # 7 = fully agree

            if model == in_top_3 == in_top_5 == in_top_10 == gold_standard:
                answer = 7
            elif model == gold_standard and model == in_top_5:
                answer = 6
            elif model == gold_standard and model == in_top_10:
                answer = 5
            elif model == gold_standard and model != in_top_10:
                answer = 1
            elif model != gold_standard:
                if in_top_3 == gold_standard:
                    answer = 4
                elif in_top_5 == gold_standard:
                    answer = 3
                elif in_top_10 == gold_standard:
                    answer = 2
                else:
                    answer = 0
            else:
                print(line)
                raise Exception('Something is wrong with the protocol.')

            validation.write('\t'.join(line) + '\t' + str(answer) + '\n')

    validation.close()
    return


# RUN ####

def main():
    """Generates a validation file
    """

    pair_type = sys.argv[1]  # DRUG-DRUG, GENE-PHENOTYPE, GENE-DRUG, etc.
    to_test = sys.argv[2]

    # GENE-PHENOTYPE
    if pair_type == 'GENE-PHENOTYPE':
        pass
        # process_answers('bin/joint-kg-recommender/log/gene_phenotype/results_item_recommendation.txt', 'corpora/gene_phenotype/u_map.dat',
        #                 'corpora/gene_phenotype/i_map.dat', 'data/gene_phenotype/test/expert_gene.xml',
        #                 'bin/biont/gene_phenotype/results/model_ontologies_gene_phenotype_results.txt', 'results/validation_items_gp.tsv',
        #                 starting_line=64, end_line=1103, pair_type='GENE-PHENOTYPE')

        # process_answers('results/jkr_results/gene_phenotype/results_knowledgable_recommendation.txt', 'corpora/gene_phenotype/ml1m/u_map.dat',
        #                   'corpora/gene_phenotype/ml1m/i_map.dat', 'data/data_test_gene_phenotype_xml/expert_gene.xml',
        #                   'results/biont_results/gene_phenotype/gene_phenotype_relations_identifiers.tsv', 'results/validation_gp.tsv',
        #                 starting_line=71, end_line=1110)
        #
        # print(statistics('results/validation_items_gp.tsv'))
        # print(metrics('results/validation_items_gp.tsv'))

    # DRUG-DISEASE
    elif pair_type == 'DRUG-DISEASE':

        # process_answers('bin/joint-kg-recommender/log/drug_disease_subset/results_item_recommendation.txt',
        #                 'corpora/drug_disease/u_map.dat',
        #                 'corpora/drug_disease/i_map.dat', 'data/drug_disease/test_bc5cdr_corpus_all_information.tsv',
        #                 'data/drug_disease/i2kg_map.tsv',
        #                 'data/drug_disease/original_data/test_corpus.txt',
        #                 'bin/biont/drug_disease/results/model_ontologies_drug_disease_results.txt',
        #                 'results/validation_items_cd.tsv', starting_line=55, end_line=300, pair_type='DRUG-DISEASE')
        #
        # process_answers('bin/joint-kg-recommender/log/drug_disease/results_item_recommendation.txt',
        #                 'corpora/drug_disease/u_map.dat',
        #                 'corpora/drug_disease/i_map.dat', 'data/drug_disease/test_bc5cdr_corpus_all_information.tsv',
        #                 'data/drug_disease/i2kg_map.tsv',
        #                 'data/drug_disease/original_data/test_corpus.txt',
        #                 'bin/biont/drug_disease/results/model_ontologies_drug_disease_results.txt',
        #                 'results/validation_items_cd.tsv', starting_line=55, end_line=300, pair_type='DRUG-DISEASE')

        if to_test == 'test':
            data_to_test_location = sys.argv[3]
            process_answers('results/test_transup.log',
                            'corpora/to_test/u_map.dat',
                            'corpora/to_test/i_map.dat', data_to_test_location + '/',
                            'corpora/to_test/i2kg_map.tsv',
                            data_to_test_location + '/',
                            'results/test_biont.txt',
                            'results/results.tsv', starting_line=55, pair_type='DRUG-DISEASE', test=True)

        #print(statistics.statistics('results/validation_items_cd.tsv'))
        #print(statistics.metrics('results/validation_items_cd.tsv'))

    # DRUG-DRUG
    elif pair_type == 'DRUG-DRUG':

        # process_answers('bin/joint-kg-recommender/log/drug_drug/results_item_recommendation.txt',
        #                 'corpora/drug_drug/u_map.dat',
        #                 'corpora/drug_drug/i_map.dat', 'data/drug_drug/test/',
        #                 'data/drug_drug/i2kg_map.tsv',
        #                 'data/drug_drug/test/',
        #                 'bin/biont/drug_drug/results/model_ontologies_drug_drug_results.txt',
        #                 'results/validation_items_dd.tsv', starting_line=55, end_line=856, pair_type='DRUG-DRUG')

        if to_test == 'test':
            data_to_test_location = sys.argv[3]
            process_answers('results/test_transup.log',
                            'corpora/to_test/u_map.dat',
                            'corpora/to_test/i_map.dat', data_to_test_location + '/',
                            'corpora/to_test/i2kg_map.tsv',
                            data_to_test_location + '/',
                            'results/test_biont.txt',
                            'results/results.tsv', starting_line=55, pair_type='DRUG-DRUG', test=True)

        # Results
        # count_rs, count_model, count_both_agree_5, count_both_agree_10, count_both_right, count_both_wrong, total = statistics.statistics('results/validation_items_dd.tsv')
        # print('\nRecommendations correct, model wrong:', count_rs, '\nModel correct, recommendations wrong:', count_model,
        #       '\nSame answer at Top@5:', count_both_agree_5, '\nSame answer at Top@10:', count_both_agree_10,
        #       '\nSame correct answer all around:', count_both_right,
        #       '\nSame incorrect answer:', count_both_wrong, '\nTotal number of evaluations:', total)
        # print(statistics.metrics('results/validation_items_dd.tsv'))

    return


# python3 src/majority_voting.py DRUG-DRUG
if __name__ == "__main__":
    main()
