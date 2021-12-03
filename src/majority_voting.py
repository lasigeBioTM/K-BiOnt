import os
import xml.etree.ElementTree as ET

from data_interactions import process_interactions_dd

def process_item_recommendation(item_recommendation_file, starting_line=62, end_line=1102):
    """

    :param item_recommendation_file:
    :param starting_line:
    :param end_line:
    :return:
    """

    item_recommendation = open(item_recommendation_file, 'r', encoding='utf-8')
    list_item_recommendation = item_recommendation.readlines()
    item_recommendation.close()

    dict_item_recommendations = {}

    for i, line in enumerate(list_item_recommendation):
        if starting_line <= i < end_line:
            user_id = line.split('user:')[1].split('\t')[0]
            top_list = line.split('top:')[1][:-1].split(',')
            dict_item_recommendations[user_id] = top_list

    return dict_item_recommendations

#print(process_item_recommendation('results/jkr_results/results_item_recommendation.txt'))
#print(process_item_recommendation('results/jkr_results/results_knowledgable_recommendation.txt', starting_line=68, end_line=1108))

def get_user_map(users_file):
    """

      :param users_file:
      :return:
      """

    users = open(users_file, 'r', encoding='utf-8')
    list_users = users.readlines()
    users.close()

    dict_users = {}
    for line in list_users:
        dict_users[line.split('\t')[-1][:-1]] = line.split('\t')[0]

    return dict_users

#print(get_user_map('corpora/ml1m/u_map.dat'))

def get_item_map(items_file, pair_type=None):
    """

    :param items_file:
    :param pair_type:
    :return:
    """

    items = open(items_file, 'r', encoding='utf-8')
    list_items = items.readlines()
    items.close()

    dict_items = {}
    for line in list_items:
        if pair_type == 'DRUG-DRUG':
            dict_items[line.split('\t')[-1][:-1]] = line.split('\t')[0]
        else:
            dict_items['HP_' + line.split('\t')[-1][:-1]] = line.split('\t')[0]


    return dict_items

#print(get_item_map('corpora/ml1m/i_map.dat'))

def process_model(users_file, items_file, model_results_file, pair_type=None):
    """

    :param users_file:
    :param items_file:
    :param model_results_file:
    :param pair_type:
    :return:
    """


    dict_users = get_user_map(users_file)
    if pair_type == 'DRUG-DRUG':
        dict_items = get_item_map(items_file, pair_type='DRUG-DRUG')
    else:
        dict_items = get_item_map(items_file)

    model = open(model_results_file, 'r', encoding='utf-8')
    model.readline()  # skip header
    list_model = model.readlines()
    model.close()

    dict_model = {}

    for line in list_model:
        if pair_type == 'DRUG-DRUG':
            if line.split('\t')[0] == 'ERROR':
                user = 'ERROR'
                item = 'ERROR'
            else:
                user = dict_users[line.split('\t')[0]]
                item = dict_items[line.split('\t')[1]]
        else:
            user = dict_users[line.split('\t')[1]]
            item = dict_items[line.split('\t')[0]]
        classification = line.split('\t')[-1][:-1]

        if str((user, item)) in dict_model:
            if classification == dict_model[str((user, item))]:
                continue
            elif classification != dict_model[str((user, item))]:
                if classification == 'effect':
                    dict_model[str((user, item))] = classification
        else:
            dict_model[str((user, item))] = classification

    for items in dict_model.items():
        if items[1] == 'effect':
            dict_model[items[0]] = True
        else:
            dict_model[items[0]] = False

    return dict_model

#print(process_model('corpora/ml1m/u_map.dat', 'corpora/ml1m/i_map.dat', 'results/biont_results/gene_phenotype_relations_identifiers.tsv'))

def get_gold_standard(users_file, items_file, gold_standard_file):
    """

    :param users_file:
    :param items_file:
    :param gold_standard_file:
    :return:
    """

    dict_users = get_user_map(users_file)
    dict_items = get_item_map(items_file)

    dict_gold_standard = {}

    tree = ET.parse(gold_standard_file)
    root = tree.getroot()

    for sentence in root:
        pair = ()
        relation = None
        for e in sentence.findall('entity'):
            e_ontology_id = e.get('ontology_id')
            pair = pair + (e_ontology_id,)

        for p in sentence.findall('pair'):
            relation = p.get('relation')

        if str(pair) in dict_gold_standard:
            if relation == dict_gold_standard[str(pair)]:
                continue
            elif relation != dict_gold_standard[str(pair)]:
                if relation == 'true':
                    dict_gold_standard[str(pair)] = relation
        elif str((pair[1], pair[0])) in dict_gold_standard:
            if relation == dict_gold_standard[str((pair[1], pair[0]))]:
                continue
            elif relation != dict_gold_standard[str((pair[1], pair[0]))]:
                if relation == 'true':
                    dict_gold_standard[str((pair[1], pair[0]))] = relation
        else:
            dict_gold_standard[str(pair)] = relation

    dict_gs_organized = {}
    for items in dict_gold_standard.items():
        entity_1, entity_2 = eval(items[0])
        if entity_1.startswith('HP'):
            item = dict_items[entity_1]
            user = dict_users[entity_2]
        else:
            user = dict_users[entity_1]
            item = dict_items[entity_2]

        if items[1] == 'true':
            relation = True
        else:
            relation = False

        dict_gs_organized[str((user, item))] = relation

    return dict_gs_organized


def get_gold_standard_dd(users_file, items_file, gold_standard, i2kg_file_path, pair_type):
    """

    :param users_file:
    :param items_file:
    :param gold_standard:
    :param i2kg_file_path:
    :param pair_type:
    :return:
    """

    dict_users = get_user_map(users_file)
    dict_items = get_item_map(items_file, pair_type='DRUG-DRUG')

    dict_ids_match_users, dict_ids_match_items, dict_gold_standard, dict_interactions = process_interactions_dd(gold_standard, i2kg_file_path, pair_type)

    dict_gs_organized = {}
    for items in dict_gold_standard.items():
        entity_1, entity_2 = eval(items[0])

        user = dict_users[entity_1]
        item = dict_items[entity_2]

        if items[1] == 1:
            relation = True
        else:
            relation = False

        dict_gs_organized[str((user, item))] = relation

    return dict_gs_organized


#print(get_gold_standard('corpora/ml1m/u_map.dat', 'corpora/ml1m/i_map.dat', 'data/data_test_xml/expert_gene.xml'))

def process_answers(item_recommendation_file, users_file, items_file, gold_standard_file, model_results_file, validation_file,
                    starting_line=62, end_line=1102, pair_type=None):
    """

    :param item_recommendation_file:
    :param users_file:
    :param items_file:
    :param gold_standard_file:
    :param model_results_file:
    :param validation_file:
    :param starting_line:
    :param end_line:
    :param pair_type:
    :return:
    """

    dict_item_recommendation = process_item_recommendation(item_recommendation_file, starting_line, end_line)

    if pair_type == 'DRUG-DRUG':
        dict_gold_standard = get_gold_standard_dd(users_file, items_file, gold_standard_file, 'corpora/drug_drug/ml1m/i2kg_map.tsv', pair_type)
        dict_model = process_model(users_file, items_file, model_results_file, pair_type)
    else:
        dict_gold_standard = get_gold_standard(users_file, items_file, gold_standard_file)
        dict_model = process_model(users_file, items_file, model_results_file)

    validation = open(validation_file, 'w', encoding='utf-8')
    validation.write('relation_identifier' + '\t' + 'user' + '\t' + 'item' + '\t' + 'model' + '\t' + 'in_top_3' + '\t'
                     + 'in_top_5' + '\t' + 'in_top_10' + '\t' + 'gold_standard' + '\t' + 'answer' + '\n')

    identifier = 0
    list_lines = []

    for items in dict_gold_standard.items():
        entity_1_user = eval(items[0])[0]
        entity_2_item = eval(items[0])[1]

        gold_standard = items[1]

        try:
            model = dict_model[items[0]]

        except KeyError:
            print('This pair is not present in the model file results:', items[0])
            continue

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

        line = [str(identifier), entity_1_user, entity_2_item, str(model), str(in_top_3), str(in_top_5), str(in_top_10), str(gold_standard)]
        identifier += 1
        list_lines.append(line)

    for line in list_lines:
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

def statistics(validation_file):
    """

    :param validation_file:
    :return:
    """

    validation = open(validation_file, 'r', encoding='utf-8')
    validation.readline()
    list_validation = validation.readlines()
    validation.close()

    count_rs = 0
    count_model = 0
    count_both_wrong = 0
    count_both_right = 0
    count_both_agree_10 = 0
    count_both_agree_5 = 0

    for line in list_validation:
        line = line.split('\t')
        model = line[3]
        in_top_3 = line[4]
        in_top_5 = line[5]
        in_top_10 = line[6]
        gold_standard = line[7]
        answer = int(line[8][:-1])

        if answer == 2 or answer == 3 or answer == 4:
            count_rs += 1
            print(line)

        elif answer == 1:
            count_model += 1

        elif answer == 0:
            count_both_wrong += 1

        elif answer == 7:
            count_both_right += 1

        elif answer == 5:
            count_both_agree_10 += 1

        elif answer == 6:
            count_both_agree_5 += 1

    total = sum([count_rs, count_model, count_both_agree_5, count_both_agree_10, count_both_right, count_both_wrong])

    return count_rs, count_model, count_both_agree_5, count_both_agree_10, count_both_right, count_both_wrong, total

def metrics(validation_file):
    """

    :param validation_file:
    :return:
    """

    validation = open(validation_file, 'r', encoding='utf-8')
    validation.readline()
    list_validation = validation.readlines()

    true_positive = 0
    false_positive = 0
    false_negative = 0

    for line in list_validation:
        line = line.split('\t')
        model = line[3]
        in_top_3 = line[4]
        in_top_5 = line[5]
        in_top_10 = line[6]
        gold_standard = line[7]
        answer = int(line[8][:-1])

        if model == 'True' and gold_standard == 'True':
            true_positive += 1

        #elif in_top_10 == 'True' and gold_standard == 'True':
        #elif in_top_5 == 'True' and gold_standard == 'True':
        #elif in_top_3 == 'True' and gold_standard == 'True':
        #    true_positive += 1

        elif model == 'False' and gold_standard == 'True':
            false_negative += 1

        elif model == 'True' and gold_standard == 'False':
            false_positive +=  1

        #elif in_top_10 == 'True' and gold_standard == 'False':
        #elif in_top_5 == 'True' and gold_standard == 'False':
        #elif in_top_3 == 'True' and gold_standard == 'False':
         #   false_positive += 1

    print(true_positive, false_positive, false_negative)
    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (false_negative + true_positive)
    f_score = 2 * ((precision * recall) / (precision + recall))

    return precision, recall, f_score

#### RUN ####

def main():
    """Generates a validation file
    """

    ### GENE-PHENOTYPE

    # process_answers('results/jkr_results/gene_phenotype/results_item_recommendation.txt', 'corpora/gene_phenotype/ml1m/u_map.dat',
    #                  'corpora/gene_phenotype/ml1m/i_map.dat', 'data/data_test_gene_phenotype_xml/expert_gene.xml',
    #                  'results/biont_results/gene_phenotype/gene_phenotype_relations_identifiers.tsv', 'results/validation_items_gp.tsv',
    #                 starting_line=64, end_line=1103)

    # process_answers('results/jkr_results/gene_phenotype/results_knowledgable_recommendation.txt', 'corpora/gene_phenotype/ml1m/u_map.dat',
    #                   'corpora/gene_phenotype/ml1m/i_map.dat', 'data/data_test_gene_phenotype_xml/expert_gene.xml',
    #                   'results/biont_results/gene_phenotype/gene_phenotype_relations_identifiers.tsv', 'results/validation_gp.tsv',
    #                 starting_line=71, end_line=1110)
    #
    #print(statistics('results/validation_items_gp.tsv'))

    #print(metrics('results/validation_gp.tsv'))

    ### DRUG-DRUG

    # process_answers('results/jkr_results/drug_drug/results_item_recommendation.txt', 'corpora/drug_drug/ml1m/u_map.dat',
    #                  'corpora/drug_drug/ml1m/i_map.dat', 'data/data_test_drug_drug_xml/',
    #                  'results/biont_results/drug_drug/drug_drug_relations_identifiers.tsv', 'results/validation_items_dd.tsv',
    #                 starting_line=63, end_line=1083, pair_type='DRUG-DRUG')

    # process_answers('results/jkr_results/drug_drug/results_knowledgable_recommendation.txt', 'corpora/drug_drug/ml1m/u_map.dat',
    #                   'corpora/drug_drug/ml1m/i_map.dat', 'data/data_test_drug_drug_xml/',
    #                   'results/biont_results/drug_drug/drug_drug_relations_identifiers.tsv', 'results/validation_dd.tsv',
    #                 starting_line=71, end_line=1091, pair_type='DRUG-DRUG')
    #
    #print(statistics('results/validation_items_dd.tsv'))

    print(metrics('results/validation_dd.tsv'))

    return


# python3 src/process_results.py
if __name__ == "__main__":
    main()