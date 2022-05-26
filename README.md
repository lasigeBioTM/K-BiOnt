# K-BiOnt: Biomedical Relation Extraction with Knowledge Graph-based Recommendations

The K-BiOnt system integrates KGs into biomedical RE through a recommendation model to further improve their range of action. This system adopts a baseline state-of-the-art deep biomedical RE system ([BiOnt](https://github.com/lasigeBioTM/BiOnt)) with an existing KG-based recommendation state-of-the-art system ([TUP](https://github.com/TaoMiner/joint-kg-recommender)) to perform biomedical RE for different entities, such as genes, phenotypes, diseases, and chemical compounds.

Our academic paper which describes K-BiOnt in detail can be found [here](https://doi.org/10.1109/JBHI.2022.3173558).

## Downloading Pre-Trained Weights

Available versions of pre-trained models are as follows:

* [DRUG-DRUG](https://drive.google.com/file/d/1NC13Q2NYRWxDRUff2CfrU0_QpBo4gzhf/view?usp=sharing)
* [DRUG-DISEASE](https://drive.google.com/file/d/1kn9c2DGIr7dDLDjUK2WU2GRO8h9E9sNf/view?usp=sharing)
* [GENE-PHENOTYPE](https://drive.google.com/file/d/17KfDXGxe8mm6e4dBWQT8du2ZIWHkHvgO/view?usp=sharing)

The training details are described in our academic paper.



## Getting Started

Our project includes code adaption of the TUP model available [here](https://github.com/TaoMiner/joint-kg-recommender), which is not an open-source project. To produce the models described above, one must implement both TUP and [BiOnt](https://github.com/lasigeBioTM/BiOnt). 

However, to make inferences on the models produced or access the processed datasets/knowledge graphs, you can check the following sections, use the [K-BiOnt Image](https://hub.docker.com/r/dpavot/kbiont) available at Docker Hub, and git clone the [TUP](https://github.com/TaoMiner/joint-kg-recommender) repository into the docker container to setup the rest of the experimental environment.

### Preprocessed Datasets

* **PGR-crowd** ([original](https://github.com/lasigeBioTM/PGR-crowd) and [preprocessed](/corpora/gene_phenotype/))
* **DDI Corpus** ([original](https://github.com/isegura/DDICorpus) and [preprocessed](/corpora/drug_drug/)) 
* **BC5CDR** ([original](https://github.com/JHnlp/BioCreative-V-CDR-Corpus) and [preprocessed](/corpora/drug_disease/))

### Preprocessed Knowledge Graphs/Ontologies

* **HPO** ([original](http://purl.obolibrary.org/obo/hp.obo) and [preprocessed](/corpora/gene_phenotype/kg/))
* **ChEBI** ([original](http://purl.obolibrary.org/obo/chebi.obo) and [preprocessed](/corpora/drug_drug/kg/))
* **DO** ([original](http://purl.obolibrary.org/obo/doid.obo) and [preprocessed](/corpora/drug_disease/kg/))


## Predict New Data

We need to preprocess our original data to make predictions based on the existing models. We can do this using the initial preprocessing step of the [BiOnt](https://github.com/lasigeBioTM/BiOnt) model. Afterwards, we can get the predictions based on [BiOnt](https://github.com/lasigeBioTM/BiOnt) and [TUP](https://github.com/TaoMiner/joint-kg-recommender). Using our preprocessed models, our system only supports three different types of relations **DRUG/CHEMICAL-DRUG/CHEMICAL**, **HUMAN PHENOTYPE-GENE** AND **CHEMICAL-DISEASE**. Check *data/* to see a sample of the supported data formats for each pair type. 

If your testing data is a small dataset with less than ten different entities, you should consider, when interpreting the final output, that TUP predictions will be skewed to search for the correct answer in the TOP@10. 


* $2: pair_type
* $3: data_to_test
* $4: biont_model_name
* $5: tup_model_name

#### Example:

````
 python3 src/predict.py DRUG-DRUG data/drug_drug/sample drug_drug_model_ontologies drug_drug-transup
````

For more options check **predict.sh**.

## Reference

- Diana Sousa and Francisco M. Couto. 2022. Biomedical Relation Extraction with Knowledge Graph-based Recommendations. IEEE Journal of Biomedical and Health Informatics.