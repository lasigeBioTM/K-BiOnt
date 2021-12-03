#python3 run_item_recommendation.py -model_type transup -dataset drug_disease -data_path ../../corpora/ -log_path log/ -rec_test_files valid.dat:test.dat -num_preferences 2 -use_st_gumbel -nohas_visualization
python3 run_item_recommendation.py -model_type transup -dataset drug_disease -data_path ../../corpora/ -log_path log/ -topn 10 -eval_only_mode -load_experiment_name drug_disease-transup-1638541964 -rec_test_files test.dat -use_st_gumbel -nohas_visualization -is_report