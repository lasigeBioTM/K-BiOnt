import os
import xml.etree.ElementTree as ET

from data_interactions import process_interactions_dd

def process_entities(corpus_path, i2kg_file_path=None, pair_type=None):
    """

    :param corpus_path:
    :param i2kg_file_path:
    :param pair_type:
    :return:
    """

    if pair_type == 'DRUG-DRUG':
        dict_ids_match_items, dict_ids_match_users, dict_gold_standard, dict_interactions = process_interactions_dd(corpus_path, i2kg_file_path, pair_type)

    e_dict_name = {}
    e_dict_id = {}
    e_dict_id_user = {}
    e_dict_id_item = {}

    for filename in os.listdir(corpus_path):

        tree = ET.parse(corpus_path + '/' + filename)
        root = tree.getroot()

        for sentence in root:
            if pair_type == 'DRUG-DRUG':
                for e in sentence.findall('entity'):
                    e_id = e.get('id')
                    e_name = e.get('text')
                    e_dict_name[e_id] = e_name

                for p in sentence.findall('pair'):
                    e1_id = p.get('e1')
                    e2_id = p.get('e2')
                    e_dict_id_user[e1_id] = dict_ids_match_users[e_dict_name[e1_id]]
                    e_dict_id_item[e2_id] = dict_ids_match_items[e_dict_name[e2_id]]
            else:
                for e in sentence.findall('entity'):
                    e_id = e.get('id')
                    e_name = e.get('text')
                    e_dict_name[e_id] = e_name
                    e_dict_id[e_id] = e_ontology_id
                e_dict_id = e_dict_id_user = e_dict_id_item

    return e_dict_name, e_dict_id_user, e_dict_id_item

def process_results_individual(corpus_path, results_file, destination_file_names, destination_file_identifiers, i2kg_file_path=None, pair_type=None):
    """

    :param corpus_path:
    :param results_file:
    :param destination_file_names:
    :param destination_file_identifiers:
    :param i2kg_file_path:
    :param pair_type:
    :return:
    """

    if pair_type == 'DRUG-DRUG':
        e_dict_name, e_dict_id_user, e_dict_id_item = process_entities(corpus_path, i2kg_file_path, pair_type)

    else:
        e_dict_name, e_dict_id_user, e_dict_id_item = process_entities(corpus_path)
        e_dict_id = e_dict_id_user

    results_names = open(destination_file_names, 'w')
    results_identifiers = open(destination_file_identifiers, 'w')

    results = open(results_file, 'r')
    header = results.readline()  # skip header
    results_names.write(header)
    results_identifiers.write(header)
    results_lines = results.readlines()
    results.close()

    for result in results_lines:
        entity_1_result_id = result.split('\t')[0]
        entity_2_result_id = result.split('\t')[1]

        results_names.write(e_dict_name[entity_1_result_id] + '\t' + e_dict_name[entity_2_result_id] + '\t' + result.split('\t')[2])
        if pair_type == 'DRUG-DRUG':
            try:
                results_identifiers.write(e_dict_id_user[entity_1_result_id] + '\t' + e_dict_id_item[entity_2_result_id] + '\t' + result.split('\t')[2])
            except KeyError:
                results_identifiers.write('ERROR'+ '\t' + 'ERROR' + '\t' + result.split('\t')[2])
        else:
            results_identifiers.write(e_dict_id[entity_1_result_id] + '\t' + e_dict_id[entity_2_result_id] + '\t' + result.split('\t')[2])

    results_names.close()
    results_identifiers.close()

    return

def join_results(results_path, destination_file):
    """

    :param results_path:
    :param destination_file:
    :return:
    """

    joint_names = open(results_path + '/' + destination_file + '_names.tsv', 'w')
    joint_names.write('Entity_1\tEntity_2\tPredicted_class' + '\n')
    joint_identifiers = open(results_path + '/' + destination_file + '_identifiers.tsv', 'w')
    joint_identifiers.write('Entity_1\tEntity_2\tPredicted_class' + '\n')

    for filename in os.listdir(results_path):
        if filename.endswith('names.tsv'):
            results_file = open(results_path + '/' + filename, 'r')
            results_file.readline()
            results_file_lines = results_file.readlines()
            for line in results_file_lines:
                joint_names.write(line)
            results_file.close()

        elif filename.endswith('identifiers.tsv'):
            results_file = open(results_path + '/' + filename, 'r')
            results_file.readline()
            results_file_lines = results_file.readlines()
            for line in results_file_lines:
                joint_identifiers.write(line)
            results_file.close()

    joint_names.close()
    joint_identifiers.close()

    return


#### RUN ####

def main():
    """Generates a results file with the entities names
    """

    #process_results_individual('corpora/go_phenotype_xml_100/', 'results/model_ontologies_go_phenotype_results_100.txt',
    #                           'results/go_phenotype_100_relations_names.tsv', 'results/go_phenotype_100_relations_identifiers.tsv')
    #process_results_individual('corpora/drug_disease_xml_100/', 'results/model_ontologies_drug_disease_results_100.txt',
    #                           'results/drug_disease_100_relations_names.tsv',
    #                           'results/drug_disease_100_relations_identifiers.tsv')
    #process_results_individual('corpora/drug_disease_xml/', 'results/model_ontologies_drug_disease_results.txt',
    #                            'results/drug_disease_relations_names.tsv',
    #                            'results/drug_disease_relations_identifiers.tsv')
    #process_results_individual('data/data_test_xml/', 'results/biont_results/model_ontologies_gene_phenotype_results.txt',
    #                           'results/biont_results/gene_phenotype_relations_names.tsv',
    #                           'results/biont_results/gene_phenotype_relations_identifiers.tsv')
    process_results_individual('data/data_test_drug_drug_xml/', 'results/biont_results/drug_drug/model_ontologies_drug_drug_results.txt',
                              'results/biont_results/drug_drug/drug_drug_relations_names.tsv',
                              'results/biont_results/drug_drug/drug_drug_relations_identifiers.tsv', 'corpora/drug_drug/i2kg_map.tsv', 'DRUG-DRUG')
    #join_results('results', 'joint_results')

    return


# python3 src/process_results.py
if __name__ == "__main__":
    main()