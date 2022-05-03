# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 09:29:46 2022

@author: luol2

machine learning tagging

"""


import time
import io
from model_ner import HUGFACE_NER
from processing_data import ml_intext_fn,out_BIO_BERT_softmax_score_fn
import tensorflow as tf
gpu = tf.config.list_physical_devices('GPU')
print("Num GPUs Available: ", len(gpu))
if len(gpu) > 0:
    tf.config.experimental.set_memory_growth(gpu[0], True)
#tf.compat.v1.disable_eager_execution()

REL_ENT={'arg1':'Species',
         'arg2':'Gene'}

entity_tag={'arg1':['arg1s','arg1e'],
            'gene':['gene1s','gene1e'],
            'species':['species1s','species1e']
    }

def input_preprocess_notoken(doc_text):
    final_input=[]
    final_id=[]
    
    lines=doc_text.split('\n')
    token_text=lines[0]
    pmid=lines[1].split('\t')[0]
    entity_arg1={} #{species_id:[[spe_sid1,sep_eid1],[...]]}
    entity_all=[]
    for i in range(1,len(lines)):
        seg=lines[i].split('\t')
        if seg[5]==REL_ENT['arg1']:
            if seg[-1] in entity_arg1.keys():
                entity_arg1[seg[-1]].append([seg[2],seg[3]])
            else:
                entity_arg1[seg[-1]]=[[seg[2],seg[3]]]
        entity_all.append(seg)
    
    #print(token_text)
    #print(entity_chemical)
    #generate input instance
    for cur_ele in entity_arg1:
        
        #2. ner label text
        ner_text=''
        text_sid=0
        #print('nonest:',entity_nonest)
        for ele_nonest in entity_all:
            ent_id=[ele_nonest[2],ele_nonest[3]]
            ent_spe_id=ele_nonest[-1]
            ent_sid=int(ele_nonest[2])
            ent_eid=int(ele_nonest[3])
            # print('sid,eid:',ent_sid,ent_eid)
            ent_text=ele_nonest[4]
            ent_type=ele_nonest[5]
            if ent_sid>=text_sid:
                # if token_text[ent_sid:ent_eid]!=ent_text:
                #     print('error!index_text,entext:',token_text[ent_sid:ent_eid],ent_text)
                if ent_id in entity_arg1[cur_ele]: #is species    
                    ner_text+=token_text[text_sid:ent_sid]+' '+ent_spe_id+'|'+entity_tag['arg1'][0]+' '+ent_text+' '+entity_tag['arg1'][1]+' '
                else:
                    ner_text+=token_text[text_sid:ent_sid]+' '+str(ent_sid)+'-'+str(ent_eid)+'|'+entity_tag[ent_type.lower()][0]+' '+ent_text+' '+entity_tag[ent_type.lower()][1]+' '
                text_sid=ent_eid                                      
        ner_text+=token_text[text_sid:]
        sen_tokens=ner_text.split()
        #print('\nner_text:',ner_text)
        
        #3. produce input
        temp_input=[]
        temp_id={'species':'','gene':[]}
        for sen_token in sen_tokens:
            if sen_token.find(entity_tag['arg1'][0])>=0:
                en_id=sen_token.split('|')[0]
                temp_id['species']=en_id
                temp_input.append(entity_tag['arg1'][0]+'\tO')
            elif sen_token.find(entity_tag['gene'][0])>=0:
                en_id=sen_token.split('|')[0]
                temp_id['gene'].append(en_id)
                temp_input.append(entity_tag['gene'][0]+'\tO')
            elif sen_token.find(entity_tag['species'][0])>=0:
                en_id=sen_token.split('|')[0]
                # temp_id.append(en_id)
                temp_input.append(entity_tag['species'][0]+'\tO')
            else:
                if sen_token=='':
                    # print('token is none!error!')
                    pass
                else:
                    temp_input.append(sen_token+'\tO')
        final_input.append('\n'.join(temp_input))
        final_id.append(temp_id)

        # print(entity_nonest)
    return final_input,final_id,entity_all,pmid


def ml_tagging(ml_input,nn_model):

    test_set,test_label = ml_intext_fn(ml_input)
    test_x,test_y, test_bert_text_label=nn_model.rep.load_data_hugface(test_set,test_label,word_max_len=nn_model.maxlen,label_type='softmax')
    test_pre = nn_model.model.predict(test_x)
    ml_out=out_BIO_BERT_softmax_score_fn(test_pre,test_bert_text_label,nn_model.rep.index_2_label)
    return ml_out

def output_rel(ml_output,entity_map,pmid):
    fin=io.StringIO(ml_output)
    alltexts=fin.read().strip().split('\n\n')
    fin.close()
    final_out={} #{'sid-eid':[spechies id]}
    for sen_id,sentence in enumerate(alltexts):
        tokens=sentence.split('\n')
        gene_entity_id=0
        token_id=0
        arg1=''
        arg2_list=[] #[[ID, score],[id,score]]
        while (token_id<len(tokens)):
            seg=tokens[token_id].split('\t')
            if seg[0]==entity_tag['arg1'][0]:
                arg1=entity_map[sen_id]['species']
                token_id+=1
                if token_id >=len(tokens):
                    break
                seg=tokens[token_id].split('\t')
                while seg[0]!=entity_tag['arg1'][1]:
                    token_id+=1
                    if token_id >=len(tokens):
                        break
                    seg=tokens[token_id].split('\t')
            elif seg[0]==entity_tag[REL_ENT['arg2'].lower()][0]:
                temp_rel=seg[-2]
                temp_score=seg[-1]
                arg2_id=entity_map[sen_id]['gene'][gene_entity_id]
                gene_entity_id+=1
                token_id+=1
                if token_id >=len(tokens):
                    break
                seg=tokens[token_id].split('\t')
                while seg[0]!=entity_tag[REL_ENT['arg2'].lower()][1]:
                    token_id+=1
                    if token_id >=len(tokens):
                        break
                    seg=tokens[token_id].split('\t')
                    if seg[-2].find('ARG2')>=0 and temp_rel.find('ARG2')<0:
                        temp_rel=seg[-2]
                        temp_score=seg[-1]
                if temp_rel.find('ARG2')>=0:
                    arg2_list.append([arg2_id,temp_score])
            elif seg[0]==entity_tag[REL_ENT['arg1'].lower()][0]:
                token_id+=1
                if token_id >=len(tokens):
                    break
                seg=tokens[token_id].split('\t')
                while seg[0]!=entity_tag[REL_ENT['arg1'].lower()][1]:
                    token_id+=1
                    if token_id >=len(tokens):
                        break
                    seg=tokens[token_id].split('\t')

            else:
                pass
            token_id+=1
        #print(arg1,arg2_list)
        if arg2_list!=[]:
            for arg2_ele in arg2_list:
                if arg2_ele[0] not in final_out.keys():
                    final_out[arg2_ele[0]]=[arg1+'|'+arg2_ele[1]]
                else:
                    final_out[arg2_ele[0]].append(arg1+'|'+arg2_ele[1])
    return(final_out)

def NER_Tag(doc_in,nn_model,outfile,fout_conll):
    
    #1. preprocess input, input_text:conll格式, input_entity：相应的实体列表
    #print(doc_in)
    input_text,entity_index,entity_all,pmid=input_preprocess_notoken(doc_in)
    # print('pmid:',pmid)
    # print('\entity_index:',entity_index)

   
    #2. ml tagging
    if input_text!=[]:
        ml_pre=ml_tagging(input_text,nn_model)
        #print('\noutput:')
        #print(ml_pre)
        fout_conll.write(ml_pre)
        #3.generate output
        final_output=output_rel(ml_pre,entity_index,pmid)
    else:
        final_output={}
    return final_output,entity_all
    
def gene_species_entity(doc_text):
    lines=doc_text.split('\n')
    species_set=set() 
    gene_set=set()
    entity_all=[]
    for i in range(1,len(lines)):
        seg=lines[i].split('\t')
        if seg[5]==REL_ENT['arg1']:
            species_set.add(seg[-1])
        else:
            gene_set.add(seg[-1])
        entity_all.append(seg)
    return species_set,gene_set,entity_all
    
def ml_tag_main(infile,model_type,outfile,modelfile,fout_conll):
    
    print('loading models........')    
    
     
    if model_type=='bioformer':
        
        vocabfiles={'labelfile':'../vocab/SpeAss_IO_label.vocab',
                    'checkpoint_path':'../speass_trained_models/bioformer-cased-v1.0/',
                    'lowercase':False,
                    }
    else:
        vocabfiles={'labelfile':'../vocab/SpeAss_IO_label.vocab',
                    'checkpoint_path':'../speass_trained_models/BiomedNLP-PubMedBERT-base-uncased-abstract/',
                    'lowercase':True,
                    }
        
    start_time=time.time()
    nn_model=HUGFACE_NER(vocabfiles)
    nn_model.build_encoder()
    nn_model.build_softmax_decoder()
    nn_model.load_model(modelfile)
    print('model done:',time.time()-start_time)
   
    #tagging text
    print("begin tagging........")
    start_time=time.time()
    
    fin=open(infile,'r',encoding='utf-8')
    all_in=fin.read().strip().split('\n\n')
    fin.close()
    N=len(all_in)
    with open(outfile, 'w',encoding='utf-8') as fout:
        i=0
        for doc in all_in:
            i+=1
            print("Processing:{0}%".format(round(i * 100 / N)), end="\r")
            species_set,gene_set,entity_all=gene_species_entity(doc)
            # print(gene_set,species_set,entity_all)
            if len(gene_set)==0: #no gene
                for ele in entity_all:
                    fout.write('\t'.join(ele)+'\t-\n')
            elif len(species_set)==0 and len(gene_set)>0:# no species, assign human species (*9606)
                for ele in entity_all:
                    if ele[5]=='Gene':
                        fout.write('\t'.join(ele)+'\t*9606|1.0'+'\n')
                    else:
                        fout.write('\t'.join(ele)+'\t-\n')
            elif len(species_set)==1 and len(gene_set)>0: #only one speices, assign the species id 
                for ele in entity_all:
                    if ele[5]=='Gene':
                        fout.write('\t'.join(ele)+'\t'+list(species_set)[0]+'|1.0'+'\n')
                    else:
                        fout.write('\t'.join(ele)+'\t-\n')
            elif len(species_set)>1 and len(gene_set)>0: #multiple species, machine learning tagging
                
                pre_result,entity_all=NER_Tag(doc, nn_model,outfile,fout_conll)
                for ele in entity_all:
                    ent_id=ele[2]+'-'+ele[3]
                    if ent_id in pre_result.keys():
                        fout.write('\t'.join(ele)+'\t'+','.join(pre_result[ent_id])+'\n')
                    else:
                        fout.write('\t'.join(ele)+'\t-\n')
            fout.write('\n')
    
    print('tag done:',time.time()-start_time)


if __name__=="__main__":
    
    model_type='bioformer'
    infile='../data/combine/token/combine_dev_token_nonest.tsv'
    modelfile='../models/tuned_model/PubmedBERT/PubmedBERT-BC2-ES.h5'
    outfile='../results/combine_PubmedBERT_BC2ES_score.tsv'
    fout_conll=open('../results/dev_Bioformer-softmax_pre.conll','w',encoding='utf-8')
    ml_tag_main(infile,model_type,outfile,modelfile,fout_conll)
    fout_conll.close() 
    
    














