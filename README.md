# Assigning Species Information to Corresponding Genes by a Sequence-Labeling Framework
***
This repository contains the source code and dataset for Species Assignment.

Species assignment is the task of identifying the corresponding species of the gene mentions, which is one of the most important steps of gene name normalization. The task of recognizing the corresponding species from various candidates for gene mentions is more relevant to information-retrieval or relation-extraction tasks, but we rephrased the problem into a sequence-labeling task, which is normally applied to a named-entity recognition task. The new method raised the performance accuracy of the species assignment (from 65.8% to 81.3%) within an acceptable process speed for large-scale data processing.


## Content
- [Dependency package](#package)
- [Introduction of folders](#intro)
- [Download trained models](#model)
- [Species Assignment with trained models](#tagging)
- [Training a new model](#training)


## Dependency package
<a name="package"></a>
The codes have been tested by Python3.8 on CentOS. We used the following main dependencies on GPU (and CPU):
- [TensorFlow 2.3.0](https://www.tensorflow.org/)
- [Transformer 4.18.0](https://huggingface.co/docs/transformers/installation)
- [stanza 1.4.0](stanfordnlp.github.io/stanza/)


To install all dependencies automatically, please use the following command:

    $ pip install -r requirements.txt

## Introduction of folders
<a name="intro"></a>

- data: the data set for species assignment (training and test sets with PubTator and Conll formats)
- example: input example files, including PubTator and BioC formats
- src: the codes for species assignment
- vocab: label files for machine learning models


## Where to download the trained models
<a name="model"></a>
To setup the tool on you computer, please download [the model file ( it includes two trained models, i.e., PubMedBERT and Bioformer)](https://ftp.ncbi.nlm.nih.gov/pub/lu/BC7DrugProt/speass_trained_models.zip), then uncompress the file, and put the model folder into the SpeciesAssignment folder.


## Species Assignment with trained models
<a name="tagging"></a>
Please use our pre-trained models (i.e., PubmedBERT/Bioformer) for species assignment by /src/*Species_Assignment.py*.

Species_Assignment.py has 3 parameters:

- --input, -i, help="input file"
- --modelfile, -m, help="trained deep learning model file"
- --outpath, -o, help="output folder to save the tagged results"

The input file format should be either [BioC(xml)](bioc.sourceforge.net) or [PubTator(tab-delimited text file)](ncbi.nlm.nih.gov/research/pubtator/). Few examples are provided in the /example/ folder.

Run Example:

    $ python Species_Assignment.py -i ../example/Example_input.PubTator -m ../pretrained_models/SpeAss-Bioformer-SG.h5 -o ../results/



## Training a new model
<a name="training"></a>
User allows to re-train a new model for species assigment. please use /src/*Model_Training.py*.

Model_Training.py has 4 parameters:

- --trainfile, -t, help="the training set file"
- --devfile, -d, help="the development set file (optional)"
- --modeltype, -m, help="deep learning model (bioformer or pubmedbert?)"
- --outpath, -o, help="the model output folder"

Note that --devfile is an optional parameter. Once the development set is provided, the process can monitor the performance on the development set to determine the timing to stop. If no, the stop time would be determined by the loss of training set. 

Run Example:

    $ python Model_Training.py -t ../data/SpeAss_Train_token_nonest.conll -m bioformer -o ../models/

Once the training step is finished, the trained model (e.g., *SpeAss-Bioformer-SG-ES-new.h5*) will be automatically generated in the output folder. If the development set is provided, two individual trained models (*SpeAss-Bioformer-SG-ES-new.h5*: stopped by the loss of training set; *SpeAss-Bioformer-SG-BEST-new.h5*:stopped by the performance on the dev set) will be generated in the output folder.

## Species recognition

We also generated a dictionary-based species tagger that can better handle the enormous size of the species lexicon, based on the hierarchical structure of the taxonomy system. More specifically, our species tagger was implemented by adopting a prefix tree to reorganize the species names within a highly efficient structure for a string search. The species recognition agorithm has been embedded in [GNormPlus](https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmTools/download/GNormPlus/GNormPlusJava.zip). Users can follow the instruction to recognize the species entities by the species recognition module. 

## Acknowledgments
This research was supported by the Intramural Research Program of the National Library of Medicine (NLM), National Institutes of Health.

## Disclaimer
This tool shows the results of research conducted in the Computational Biology Branch, NCBI. The information produced on this website is not intended for direct diagnostic use or medical decision-making without review and oversight by a clinical professional. Individuals should not change their health behavior solely on the basis of information produced on this website. NIH does not independently verify the validity or utility of the information produced by this tool. If you have questions about the information produced on this website, please see a health care professional. More information about NCBI's disclaimer policy is available.
