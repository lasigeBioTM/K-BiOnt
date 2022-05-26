import os
import sys


def main():
	"""

	usage example:
	python3 src/predict.py DRUG-DRUG data/drug_drug/sample drug_drug_model_ontologies drug_drug-transup
	"""

	pair_type = sys.argv[1]  # DRUG-DRUG
	data_to_test_location = sys.argv[2]  # data/drug_drug/sample
	biont_model_name = sys.argv[3]
	tup_model_name = sys.argv[4]

	# Preprocess data for BiOnt
	os.system('cp -rf ' + data_to_test_location + '/* ../BiOnt/corpora/' + pair_type.lower().replace('-', '_') + '/')
	os.chdir('../BiOnt/')
	os.system('python3 src/ontologies_embeddings.py preprocess ' + pair_type + ' test corpora/' + pair_type.lower().replace('-', '_') + '/')
	os.chdir('../K-BiOnt/')

	# Preprocess data for TUP
	os.system('python3 src/data_interactions.py ' + pair_type + ' test ' + data_to_test_location)

	# Run BiOnt
	os.system('cp -rf models/biont_models/' + biont_model_name + '* ../BiOnt/models/' + pair_type.lower().replace('-', '_') + '/')
	os.chdir('../BiOnt/')
	os.system('rm results/' + pair_type.lower().replace('-', '_') + '/* | true')
	os.system('python3 src/ontologies_embeddings.py test ' + pair_type + ' ' + biont_model_name +
	' corpora/' + pair_type.lower().replace('-', '_') + '/ words wordnet concatenation_ancestors common_ancestors')
	os.chdir('../K-BiOnt/')

	# Run TUP
	os.system('cp -rf models/tup_models/' + tup_model_name + '* ../joint-kg-recommender/log/')
	os.system('touch corpora/to_test/train.dat | true')
	os.system('mv corpora/to_test/ corpora/ml1m')
	os.chdir('../joint-kg-recommender/')
	os.system('rm log/* | true')
	os.system('python3 run_item_recommendation.py -model_type transup -dataset ml1m -data_path ../K-BiOnt/corpora/ \
	-log_path log/ -topn 10 -eval_only_mode -load_experiment_name ' + tup_model_name + ' -rec_test_files \
	test.dat -use_st_gumbel -nohas_visualization -is_report')
	os.chdir('../K-BiOnt/')
	os.system('mv corpora/ml1m/ corpora/to_test/')

	# Final Joined Predictions
	os.system('cp ../joint-kg-recommender/log/ml1m-*.log results/ | true')
	os.system('mv results/ml1m-*.log results/test_transup.log | true')
	os.system('rm ../joint-kg-recommender/log/ml1m-*.log | true')
	os.system('cp ../BiOnt/results/' + pair_type.lower().replace('-', '_') + '/*_results.txt results/ | true')
	os.system('mv results/*_results.txt results/test_biont.txt | true')
	os.system('rm ../BiOnt/results/' + pair_type.lower().replace('-', '_') + '/*_results.txt | true')
	os.system('python3 src/majority_voting.py ' + pair_type + ' test ' + data_to_test_location)

	print('\nYou can find your final test predictions for the files in ' + data_to_test_location + ' on the results/ directory under the name results.tsv.\n')


if __name__ == "__main__":
	main()
