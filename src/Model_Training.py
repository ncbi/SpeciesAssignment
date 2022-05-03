# -*- coding: utf-8 -*-
"""
Created on Tue May 18 10:49:23 2021

@author: luol2
training species assignment model (from species to gene)
"""

import os
import argparse
from model_ner import HUGFACE_NER
from processing_data import ml_intext,out_BIO_BERT_softmax
from Evaluation import Rel_Evaluation_Hugface_fn
from tensorflow.keras import callbacks
import tensorflow as tf

gpu = tf.config.list_physical_devices('GPU')
print("Num GPUs Available: ", len(gpu))
if len(gpu) > 0:
    tf.config.experimental.set_memory_growth(gpu[0], True)



class BC7Callback_PLM(callbacks.Callback):
    def __init__(self, temp_files):
        super(BC7Callback_PLM, self).__init__()
        self.tempout = temp_files['infiles']
        self.index_2_label=temp_files['index_2_label']
        self.model_out=temp_files['model_out']
        self.dev_set=temp_files['dev_set']

        
    def on_train_begin(self, logs=None):
        self.max_dev=[0.0,0.0,0.0]
        self.max_dev_epoch=0

        self.max_train=0.0
        self.max_train_epoch=0
        self.patein_es=0
        
    def on_epoch_end(self, epoch, logs=None):
        #_lr=0
        _lr = self.model.optimizer._decayed_lr(tf.float32).numpy()
        current_acc = logs.get("accuracy")
        if self.dev_set!=[]: # if there is a dev set, will save the best performance model on dev set
            print('\n......dev performance:')
            _dev_predict = self.model.predict(self.dev_set[0])
            out_BIO_BERT_softmax(self.tempout['devtemp'],_dev_predict,self.dev_set[1],self.index_2_label)
            _dev_pre,_dev_metrics=Rel_Evaluation_Hugface_fn(self.tempout['devtemp'],ARG2_label='gene1s')
    
            if _dev_pre[-1]>self.max_dev[-1]:
                self.max_dev=_dev_pre
                #self.max_dev_test=_test_pre
                self.max_dev_epoch=epoch
                self.model.save_weights(self.model_out['BEST'])
        
        if current_acc >self.max_train:
            self.max_train = current_acc
            self.max_train_epoch = epoch+1
            self.model.save_weights(self.model_out['ES'])
            self.patein_es=0
        if self.patein_es>6:
            self.model.stop_training = True
            print('\nearly stop!')
        self.patein_es+=1
        if self.dev_set!=[]:
            print('\nmax_train_acc=%f in epoch %d, max_dev_f1=%f in epoch=%d, now_epoch=%d, lr=%f\n' %(self.max_train, self.max_train_epoch, self.max_dev[-1], self.max_dev_epoch+1, epoch+1, _lr))
        else:
            print('\nmax_train_acc=%f in epoch %d,  now_epoch=%d, lr=%f\n' %(self.max_train, self.max_train_epoch, epoch+1, _lr))
        
   
    

def Hugface_training(infiles,vocabfiles,model_out):
    

    #build model
    plm_model=HUGFACE_NER(vocabfiles)
    plm_model.build_encoder() 
    plm_model.build_softmax_decoder()

    #load dataset
    print('loading dataset......')  
    trainfile=infiles['trainfile']
    train,train_label = ml_intext(trainfile)
    train_x, train_y,train_bert_text_label = plm_model.rep.load_data_hugface(train,train_label,word_max_len=plm_model.maxlen,label_type='softmax')

    
    if infiles['devfile']!='':
        devfile=infiles['devfile']
        dev,dev_label = ml_intext(devfile)
        dev_x, dev_y,dev_bert_text_label = plm_model.rep.load_data_hugface(dev,dev_label,word_max_len=plm_model.maxlen,label_type='softmax')

        temp_files={'infiles':infiles,
                    'index_2_label':plm_model.rep.index_2_label,
                    'model_out':model_out,
                    'dev_set':[dev_x,dev_bert_text_label],
                    }
    else:
        temp_files={'infiles':infiles,
                    'index_2_label':plm_model.rep.index_2_label,
                    'model_out':model_out,
                    'dev_set':[],
                    }
    #train model
    plm_model.model.fit(train_x,train_y, batch_size=16, epochs=100,verbose=1,callbacks=[BC7Callback_PLM(temp_files)])
            
if __name__=="__main__":
    
    parser = argparse.ArgumentParser(description='train species assignment model, python Model_Training.py -t trainfile -d devfile -m modeltype -o outpath')
    parser.add_argument('--trainfile', '-t', help="the training set file",default='../data/SpeAss_Train_token_nonest.conll')
    parser.add_argument('--devfile', '-d', help="the development set file",default='')
    parser.add_argument('--modeltype', '-m', help="deep learning model (bioformer or pubmedbert?)",default='bioformer')
    parser.add_argument('--outpath', '-o', help="the model output folder",default='../models/')
    args = parser.parse_args()
    
    if not os.path.exists(args.outpath):
        os.makedirs(args.outpath)
    

    infiles={'trainfile':args.trainfile,
             'devfile':args.devfile,
             'devtemp':args.outpath+'dev_temp_pre.conll',
               }# drugprot_dev_all_token
    
    if args.modeltype=='bioformer':
        vocabfiles={'labelfile':'../vocab/SpeAss_IO_label.vocab',
                    'checkpoint_path':'../speass_trained_models/bioformer-cased-v1.0/', 
                    'lowercase':False,
                    }
        
        model_out={'BEST':args.outpath+'SpeAss-Bioformer-SG-BEST-new.h5',
                   'ES':args.outpath+'SpeAss-Bioformer-SG-ES-new.h5'} 
        
    else:
        vocabfiles={'labelfile':'../vocab/SpeAss_IO_label.vocab',
                    'checkpoint_path':'../speass_trained_models/BiomedNLP-PubMedBERT-base-uncased-abstract/',
                    'lowercase':True,
                    }
        
        model_out={'BEST':args.outpath+'SpeAss-PubmedBERT-SG-BEST-new.h5',
                   'ES':args.outpath+'SpeAss-PubmedBERT-SG-ES-new.h5'}  
      
       
    Hugface_training(infiles,vocabfiles,model_out)
                             
