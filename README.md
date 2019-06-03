# GSAM
GSAM: Geospatial Semantic Address Model Based on Deep Neural Network Language Modeling and Geospatial-Semantic feature fusion clustering
## Setup
* TensorFlow, version 1.11.0 or later
* If you run training/evaluation on your local machine, using a GPU like a Titan X or GTX 1080. Else you can also train on a Google Cloud TPU
## Code Description
* `Clustering_part.ipynb`: Concat geospatial and semantic features and cluster the merged features.
* `create_pretraining_data.py`: Create TFRecord from raw text.
* `extract_features.py`: Extract pre-computed feature vectors from ALM.
* `feature pooling.ipynb`: Obtain fixed vectors of addresses.
* `generateVocab.py`: Generate Vocab for address corpus.
* `modelingMRC.py`: The main BERT model and related functions.
* `optimization2.py`: Functions and classes related to optimization.
* `run_classifier.py`: ALM finetuning runner for generating GSAM.
* `run_coorprediction.py`: GSAM-based address coordinates prediction task runner.
* `run_pretraining.py`: Pretrain the ALM.
* `run_word2vec_coorprediction.py`: Word2vec-based address coordinates prediction task runner.
* `tokenization.py`: Tokenization classes.
## Dataset
* Because of data confidentiality, the full dataset are not provided herein, but I provide a small dataset (5000 addresses) in the `sampleData.txt` for test.
## Contact
* Feel free to email xlczju@zju.edu.cn for any pertinent questions/bugs regarding the code.
