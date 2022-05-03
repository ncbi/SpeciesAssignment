# Species Assignment
***
This repo contains the source code and dataset for Species Assignment.

Species assignment is the task of recognizing the corresponding species of the gene mentions, which is a very important step for Gene name normalization. While the existing methods of the corresponding species recognition are still heavily relying on the heuristic rules based on the co-occurrence of the gene and the species in the context. We therefore developed a high-accuracy method using a novel deep learning-based framework.


## Content
- [Dependency package](#package)
- [Introduction of folders](#intro)
- [Download trained models](#model)
- [Species Assignment with trained models](#tagging)
- [Training a new model](#training)


## Dependency package
<a name="package"></a>
The codes have been tested using Python3.8 on CentOS and uses the following main dependencies on a CPU and GPU:
- [TensorFlow 2.3.0](https://www.tensorflow.org/)
- [Transformer 4.18.0](https://huggingface.co/docs/transformers/installation)
- [stanza 1.4.0](stanfordnlp.github.io/stanza/)


To install all dependencies automatically using the command:

    $ pip install -r requirements.txt

## Introduction of folders
<a name="intro"></a>

- data: the data set for species assignment (training and test sets with PubTator and Conll formats)
- example: input example files, including PubTator and BioC formats
- src: the codes for species assignment
- vocab: label files for machine learning models


## Download trained models
<a name="model"></a>
To run this code, you need to first download [the model file ( it includes two trained models, i.e., PubMedBERT and Bioformer)](https://ftp.ncbi.nlm.nih.gov/pub/lu/BC7DrugProt/speass_trained_models.zip), then unzip and put the model folder into the SpeciesAssignment folder.


## Species Assignment with trained models
<a name="tagging"></a>
You can use our trained models (i.e., PubmedBERT/Bioformer) for species assignment by the  /src/*Species_Assignment.py* file.

The file has 3 parameters:

- --input, -i, help="input file"
- --modelfile, -m, help="trained deep learning model file"
- --outpath, -o, help="output folder to save the tagged results"

The input file format can be in [BioC(xml)](bioc.sourceforge.net) or [PubTator(tab-delimited text file)](ncbi.nlm.nih.gov/research/pubtator/). You can find some input examples in the /example/ folder.

Run Example:

    $ python Species_Assignment.py -i ../example/Example_input.PubTator -m ../pretrained_models/SpeAss-Bioformer-SG.h5 -o ../results/



## Training a new model
<a name="training"></a>
Train a new species assigment model using the /src/*Model_Training.py* file.

The file has 4 parameters:

- --trainfile, -t, help="the training set file"
- --devfile, -d, help="the development set file (optional)"
- --modeltype, -m, help="deep learning model (bioformer or pubmedbert?)"
- --outpath, -o, help="the model output folder"

Note that --devfile is an optional parameter. When the development set is provided, the model training will early stop by the performance on the development. If no, the model training will early stop by the loss of training set. 

Run Example:

    $ python Model_Training.py -t ../data/SpeAss_Train_token_nonest.conll -m bioformer -o ../models/

After the training is finished, the trained model (e.g., *SpeAss-Bioformer-SG-ES-new.h5*) will be generated in the output folder. If the development set is provided, two trained models (*SpeAss-Bioformer-SG-ES-new.h5* for early stopping by the loss of training set; *SpeAss-Bioformer-SG-BEST-new.h5* for early stopping by the performance on the dev set) will be generated in the output folder.


## Acknowledgments
This research was supported by the Intramural Research Program of the National Library of Medicine (NLM), National Institutes of Health.