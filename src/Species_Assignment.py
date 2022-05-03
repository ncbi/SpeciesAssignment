# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 16:23:35 2022
input: pubtator or xml file 
output: species assignment
more general
@author: luol2
"""
import os
import argparse
import stanza
import sys
import re
import bioc
from ML_Tagging_score import ml_tag_main

nlp = stanza.Pipeline(lang='en', processors={'tokenize': 'spacy'},package='None') #package='craft'


def ssplit_token(infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    all_in=fin.read().strip().split('\n\n')
    fin.close()
    ori_text_newentity={} #{line[0]+line[1]:[all entity]}
    entity_type=set()
    token_text_new={}#{pmid:token_text}
    for doc_text in all_in:
        lines=doc_text.split('\n')
        ori_text=lines[0].split('|t|')[1]+' '+lines[1].split('|a|')[1]
        pmid=lines[0].split('|t|')[0]
        # print(pmid)
        entity_all=[]   #[[seg0,seg1,...,],[]]
        entity_all_ori=[]
        entity_num=0
        
        #first sort
        doc_result={}
        for i in range(2,len(lines)):
            segs=lines[i].split('\t')
            doc_result[lines[i]]=[int(segs[1]),int(segs[2])]
        doc_result=sorted(doc_result.items(), key=lambda kv:(kv[1]), reverse=False)
        doc_result_sort=[]
        for ele in doc_result:
            doc_result_sort.append(ele[0])
        
        for i in range(0,len(doc_result_sort)):
            seg=doc_result_sort[i].strip().split('\t')
            entity_type.add(seg[4])
            # print(seg)
            if len(seg)<=5:#Gene
                entity_all_ori.append([seg[0],'M'+str(entity_num),seg[1],seg[2],seg[3],seg[4],'-'])
                entity_all.append([seg[0],'M'+str(entity_num),seg[1],seg[2],seg[3],'Gene','-'])
                entity_num+=1
            else:# Species
                entity_all_ori.append([seg[0],'M'+str(entity_num),seg[1],seg[2],seg[3],seg[4],seg[5]])
                entity_all.append([seg[0],'M'+str(entity_num),seg[1],seg[2],seg[3],'Species',seg[5]])
                entity_num+=1
        ori_text_newentity[lines[0]+'\n'+lines[1]]=entity_all_ori
        # sys.exit()

        #ssplit token
        doc_stanza = nlp(ori_text)
        token_text=''
        sentence_index=[] #[text_offset]
        for sent in doc_stanza.sentences:
            for word in sent.words:
                if word.text==' ':
                    # print('token is blank!')
                    pass
                token_text+=word.text+' '
            token_text=token_text+''  #sentence split 
            sentence_index.append(len(token_text))
        
        #ori_index map token_index
        index_map=[-1]*len(ori_text)
        j=0
        space_list=[' ',chr(160),chr(8201),chr(8194),chr(8197),chr(8202)] #空格有好几种，第一个是常用32,第二个shi 160,8201,8194,8197
        for i in range(0,len(ori_text)):
            if ori_text[i] in space_list:
                pass
            elif ori_text[i]==token_text[j]:
                index_map[i]=j
                j+=1
            else:
                j+=1
                temp_log=j
                try:
                    while(ori_text[i]!=token_text[j]):
                        j+=1
                except:
                    print('doc',doc_text)
                    print('token_text:',token_text)
                    print('error:',ori_text[i-10:i+10],'i:',ori_text[i],'j:',token_text[temp_log],',',token_text[temp_log-10:temp_log+10])
                    print(ord(ori_text[i]),ord(' '))
                    sys.exit()
                index_map[i]=j
                j+=1
        # token_text=token_text.replace('     ','<EOS>')
        # print(token_text)
        fout.write(token_text+'\n')
        token_text_new[pmid]=token_text
        entity_i=0
        cur_sent_i=0
        new_ente=0
        cur_sents=0
        cur_sente=sentence_index[0]
        if entity_all!=[]:
            new_ents=index_map[int(entity_all[entity_i][2])]
            new_ente=index_map[int(entity_all[entity_i][3])-1]+1
            new_ent=token_text[new_ents:new_ente]
            old_ent=entity_all[entity_i][4]
            while True:
                while new_ents>=cur_sents and new_ente< cur_sente:
    
                    if new_ent.replace(' ','') !=old_ent.replace(' ',''):
                        # print('entity error:',pmid,old_ent,new_ent,entity_all[entity_i][2],entity_all[entity_i][3])
                        pass
                    fout.write(entity_all[entity_i][0]+'\t'+entity_all[entity_i][1]+'-'+str(cur_sent_i)+'\t'+str(new_ents)+'\t'+str(new_ente)+'\t'+new_ent+'\t'+entity_all[entity_i][5]+'\t'+entity_all[entity_i][6]+'\n')
                    entity_i+=1
                    if entity_i>=len(entity_all):
                        break
                    new_ents=index_map[int(entity_all[entity_i][2])]
                    new_ente=index_map[int(entity_all[entity_i][3])-1]+1
                    new_ent=token_text[new_ents:new_ente]
                    old_ent=entity_all[entity_i][4]
                cur_sent_i+=1
                if cur_sent_i >= len(sentence_index):
                    break
                cur_sents=sentence_index[cur_sent_i-1]
                cur_sente=sentence_index[cur_sent_i]
        fout.write('\n')
    # print(entity_type)
    fout.close()
    return ori_text_newentity,token_text_new

def filter_nest(infile, outfile): #nonest

    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    
    documents=fin.read().strip().split('\n\n')
    fin.close()
    total_entity=0
    over_entity=0
    nest_entity=0
    for doc in documents:
        lines=doc.split('\n')
        context=lines[0]
        entity_list=[]
        if len(lines)>1:
            first_entity=lines[1].split('\t')
            nest_list=[first_entity]
            max_eid=int(first_entity[3])
            total_entity+=len(lines)-2
            for i in range(2,len(lines)):
                segs=lines[i].split('\t')
                if int(segs[2])> max_eid:
                    if len(nest_list)==1:
                        entity_list.append(nest_list[0])
                        nest_list=[]
                        nest_list.append(segs)
                        if int(segs[3])>max_eid:
                            max_eid=int(segs[3])
                    else:
                        # print(nest_list)
                        nest_entity+=len(nest_list)-1
                        tem=find_max_entity(nest_list)#find max entity
                        # if len(tem)>1:
                        #     print('max nest >1:',tem)
                        entity_list.extend(tem)
                        nest_list=[]
                        nest_list.append(segs)
                        if int(segs[3])>max_eid:
                            max_eid=int(segs[3])
                        
                else:
                    nest_list.append(segs)
                    if int(segs[3])>max_eid:
                        max_eid=int(segs[3])
            if nest_list!=[]:
                if len(nest_list)==1:
                    entity_list.append(nest_list[0])

                else:
                    tem=find_max_entity(nest_list)#find max entity
                    # if len(tem)>1:
                    #     print('max nest >1:',tem)
                    entity_list.extend(tem)
        fout.write(context+'\n')
        for ele in entity_list:
            fout.write('\t'.join(ele)+'\n')
        fout.write('\n')
    # print(total_entity,over_entity, nest_entity)
def find_max_entity(nest_list):
    max_len=0
    final_tem=[]
    max_index=0
    for i in range(0, len(nest_list)):
        cur_len=int(nest_list[i][3])-int(nest_list[i][2])
        if cur_len>max_len:
            max_len=cur_len
            max_index=i
        elif cur_len==max_len:
            if nest_list[i][5] =='Gene':
                max_index=i
        # elif nest_list[i][5] =='Species':
        #     final_tem.append(nest_list[i])

    final_tem.append(nest_list[max_index])
    return final_tem



# details nearest+and
def post_rule1(ori_context,token_text,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0':{'sent':'','offset':[sid,eid],'score':[[id,score],[id,score]]}}} #gene
    species_index={} #{pmid:{sentid:[[spe_seg1],[spe_seg]]}}
    mem_sent={} #{pmid:{'M0':sentid}}
    gene_num=0
    gene_none=0
    for line in fin:
        seg=line.strip().split('\t')
        if len(seg)>1:
            if seg[0] not in mem_sent.keys():
                _term_seg=seg[1].split('-')
                mem_sent[seg[0]]={_term_seg[0]:_term_seg[1]}
            else:
                _term_seg=seg[1].split('-')
                mem_sent[seg[0]][_term_seg[0]]=_term_seg[1]
            if seg[5]=='Species':   
                if seg[0] not in species_index.keys():
                    _sent_id=seg[1].split('-')[1]
                    species_index[seg[0]]={_sent_id:[seg]}
                else:
                    _sent_id=seg[1].split('-')[1]
                    if _sent_id in species_index[seg[0]].keys():
                        species_index[seg[0]][_sent_id].append(seg)
                    else:
                        species_index[seg[0]][_sent_id]=[seg]
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[] #[[spe_id,score]]
                _sent_id=seg[1].split('-')[1]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                if seg[0] not in pred_results.keys():                   
                    pred_results[seg[0]]={seg[1].split('-')[0]:{'sent':_sent_id,'offset':[seg[2],seg[3]],'score':_temp_id_score}}
                else:
                    pred_results[seg[0]][seg[1].split('-')[0]]={'sent':_sent_id,'offset':[seg[2],seg[3]],'score':_temp_id_score}
    #print(pred_results)
    for pmid_text in ori_context.keys():
        #print(pmid_text)
        lines=pmid_text.split('\n')
        ori_text=lines[0].split('|t|')[1]+' '+lines[1].split('|a|')[1]
        # print(ori_text)
        fout.write(pmid_text+'\n')
        pmid=lines[0].split('|t|')[0]
        before_species=[] #nearest [eid,spe_id]
        after_species=[] #nearest  [sid,spe_id]
        doc_specs=species_index[pmid]
        #mul and spe
        mul_and_spe=[]
        for spe_sent in doc_specs.keys():
            last_id=''
            new_diff_spe=[]
            _temp_speid=set()
            for ele in doc_specs[spe_sent]:
                if ele[-2] !=last_id:
                    new_diff_spe.append(ele)
                    last_id =ele[-2]
                    _temp_speid.add(ele[-2])
                else:
                    
                    new_diff_spe.pop()
                    new_diff_spe.append(ele)
                    _temp_speid.add(ele[-2])
                    last_id =ele[-2]
            if len(new_diff_spe)==2:
                spe_and_text=new_diff_spe[0][4]+' and '+new_diff_spe[1][4]
                if ori_text.find(spe_and_text)>=0:
                    # print('old:',doc_specs[spe_sent])
                    # print('new:',new_diff_spe)
                    # print('\n')
                    mul_and_spe=list(_temp_speid)
                    # print(mul_and_spe)
            elif len(new_diff_spe)>2:
                spe_and_text=''
                for i in range(0,len(new_diff_spe)-1):
                    spe_and_text+=new_diff_spe[i][4]+', '
                spe_and_text1=spe_and_text[0:-2]+' and '+new_diff_spe[-1][4]
                spe_and_text2=spe_and_text+'and '+new_diff_spe[-1][4]
                if ori_text.find(spe_and_text1)>=0 or ori_text.find(spe_and_text2)>=0:
                    # print('old:',doc_specs[spe_sent])
                    # print('new:',new_diff_spe)
                    mul_and_spe=list(_temp_speid)
                    # print(mul_and_spe)
        Gene_type_list=['Gene','FamilyName','DomainMotif']
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)
            
            if ele[5] in Gene_type_list:
                gene_num+=1
                final_preds=set()
                if ele[1] in pred_results[ele[0]].keys():
                    temp_preds=pred_results[ele[0]][ele[1]]['score']
                    
                    if temp_preds!=[['-']]:
                        if len(temp_preds)==1:
                            final_preds.add(temp_preds[0][0])
                        else:
                            max_id=''
                            max_score=0
                            for _temp_pred in temp_preds:
                                _score=float(_temp_pred[1])
                                _id_ass=_temp_pred[0]
                                if len(mul_and_spe)>1:
                                    if _score>0.5 and (_id_ass in mul_and_spe):
                                        # print(_score)
                                        final_preds.add(_id_ass)
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            if len(final_preds)==0:
                                final_preds.add(max_id) 
                            # final_preds.add(multi_id)
                    else: #'-' nearst rule
                        gene_none+=1
                        # print(mem_sent[ele[0]])
                        _sent_id_gene=mem_sent[ele[0]][ele[1]]
                     
                        for j in range(i+1,len(ori_context[pmid_text])):
                            temp_seg=ori_context[pmid_text][j]
                            if temp_seg[5]=='Species':
                                after_species=[int(temp_seg[2]),temp_seg[6]]
                                break
                        # print(before_species,after_species)
                        # print(seg)
                        if before_species!=[] and after_species!=[]:
                            if len(ori_text[before_species[0]:int(ele[2])].split()) > len(ori_text[int(ele[3]):after_species[0]].split()):
                                final_preds.add(after_species[1])
                            else:
                                final_preds.add(before_species[1])
                        elif before_species==[]:
                            final_preds.add(after_species[1])
                        elif after_species==[]:
                            final_preds.add(before_species[1])
                    if len(final_preds)==0:
                        print('none pred!!!')                             
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
                else:
                    # gene_none+=1
                    # print(ele)
                    for j in range(i+1,len(ori_context[pmid_text])):
                        temp_seg=ori_context[pmid_text][j]
                        if temp_seg[5]=='Species':
                            after_species=[int(temp_seg[2]),temp_seg[6]]
                            break
                    # print(before_species,after_species)
                    # print(seg)
                    if before_species!=[] and after_species!=[]:
                        if len(ori_text[before_species[0]:int(ele[2])].split()) > len(ori_text[int(ele[3]):after_species[0]].split()):
                            final_preds.add(after_species[1])
                        else:
                            final_preds.add(before_species[1])
                    elif before_species==[]:
                        final_preds.add(after_species[1])
                    elif after_species==[]:
                        final_preds.add(before_species[1])
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\n')
                before_species=[int(ele[3]),ele[6]]
        fout.write('\n')
    print('gene, none:',gene_num,gene_none)
    fout.close()
    
# major+and
def post_rule2(ori_context,token_text,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0':{'sent':'','offset':[sid,eid],'score':[[id,score],[id,score]]}}} #gene
    species_index={} #{pmid:{sentid:[[spe_seg1],[spe_seg]]}}
    species_count={}#{pmid:{speid:num}}
    gene_num=0
    gene_none=0
    for line in fin:
        seg=line.strip().split('\t')
        if len(seg)>1:
            if seg[5]=='Species':
                if seg[0] not in species_count.keys():
                    species_count[seg[0]]={seg[-2]:1}
                else:
                    if seg[-2] not in species_count[seg[0]].keys():
                        species_count[seg[0]][seg[-2]]=1
                    else:
                        species_count[seg[0]][seg[-2]]+=1
                        
                if seg[0] not in species_index.keys():
                    _sent_id=seg[1].split('-')[1]
                    species_index[seg[0]]={_sent_id:[seg]}
                else:
                    _sent_id=seg[1].split('-')[1]
                    if _sent_id in species_index[seg[0]].keys():
                        species_index[seg[0]][_sent_id].append(seg)
                    else:
                        species_index[seg[0]][_sent_id]=[seg]
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[] #[[spe_id,score]]
                _sent_id=seg[1].split('-')[1]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                if seg[0] not in pred_results.keys():                   
                    pred_results[seg[0]]={seg[1].split('-')[0]:{'sent':_sent_id,'offset':[seg[2],seg[3]],'score':_temp_id_score}}
                else:
                    pred_results[seg[0]][seg[1].split('-')[0]]={'sent':_sent_id,'offset':[seg[2],seg[3]],'score':_temp_id_score}
    #print(pred_results)
    for pmid_text in ori_context.keys():
        #print(pmid_text)
        lines=pmid_text.split('\n')
        ori_text=lines[0].split('|t|')[1]+' '+lines[1].split('|a|')[1]
        # print(ori_text)
        fout.write(pmid_text+'\n')
        pmid=lines[0].split('|t|')[0]
        if pmid in species_count.keys():
            marjor_species = max(zip(species_count[pmid].values(), species_count[pmid].keys()))
        else:
            marjor_species = (1000,'*9606')
        
        if pmid in species_index.keys():
            doc_specs=species_index[pmid]
            #mul and spe
            mul_and_spe=[]
            for spe_sent in doc_specs.keys():
                last_id=''
                new_diff_spe=[]
                _temp_speid=set()
                for ele in doc_specs[spe_sent]:
                    if ele[-2] !=last_id:
                        new_diff_spe.append(ele)
                        last_id =ele[-2]
                        _temp_speid.add(ele[-2])
                    else:
                        
                        new_diff_spe.pop()
                        new_diff_spe.append(ele)
                        _temp_speid.add(ele[-2])
                        last_id =ele[-2]
                if len(new_diff_spe)==2:
                    spe_and_text=new_diff_spe[0][4]+' and '+new_diff_spe[1][4]
                    if ori_text.find(spe_and_text)>=0:
                        # print('old:',doc_specs[spe_sent])
                        # print('new:',new_diff_spe)
                        # print('\n')
                        mul_and_spe=list(_temp_speid)
                        # print(mul_and_spe)
                elif len(new_diff_spe)>2:
                    spe_and_text=''
                    for i in range(0,len(new_diff_spe)-1):
                        spe_and_text+=new_diff_spe[i][4]+', '
                    spe_and_text1=spe_and_text[0:-2]+' and '+new_diff_spe[-1][4]
                    spe_and_text2=spe_and_text+'and '+new_diff_spe[-1][4]
                    if ori_text.find(spe_and_text1)>=0 or ori_text.find(spe_and_text2)>=0:
                        # print('old:',doc_specs[spe_sent])
                        # print('new:',new_diff_spe)
                        mul_and_spe=list(_temp_speid)
                        # print(mul_and_spe)
        else:
            mul_and_spe=[]
            
        Gene_type_list=['Gene','FamilyName','DomainMotif']
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)
            
            if ele[5] in Gene_type_list:
                gene_num+=1
                final_preds=set()
                if ele[1] in pred_results[ele[0]].keys():
                    temp_preds=pred_results[ele[0]][ele[1]]['score']
                    
                    if temp_preds!=[['-']]:
                        if len(temp_preds)==1:
                            final_preds.add(temp_preds[0][0])
                        else:
                            max_id=''
                            max_score=0
                            for _temp_pred in temp_preds:
                                _score=float(_temp_pred[1])
                                _id_ass=_temp_pred[0]
                                if len(mul_and_spe)>1:
                                    if _score>0.5 and (_id_ass in mul_and_spe):
                                        # print(_score)
                                        final_preds.add(_id_ass)
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            if len(final_preds)==0:
                                final_preds.add(max_id) 
                            # final_preds.add(multi_id)
                    else: #'-' major species
                        gene_none+=1
                        # print(mem_sent[ele[0]])
                        final_preds.add(marjor_species[1])
                    if len(final_preds)==0:
                        print('none pred!!!')                             
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:-1])+'\tTax:'+','.join(final_preds).replace('*','')+'\n')
                else:
                    final_preds.add(marjor_species[1])
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:-1])+'\tTax:'+','.join(final_preds).replace('*','')+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\n')
        fout.write('\n')
    # print('gene, none:',gene_num,gene_none)
    fout.close()


def PubTator_Converter(infile,outpath,modelfile,model_type):
    #1. sentence split and token
    print('.......senten split, tokenizer.........')
    ori_text_newentity,token_text=ssplit_token(infile,outpath+'tmp/token.tmp')
    
    #2. filter nest entity
    filter_nest(outpath+'tmp/token.tmp', outpath+'tmp/token_nonest.tmp')
    
    #3.ml tag
    print('.......machine learning-based tagging.........')
    fout_conll=open(outpath+'tmp/ml_tag.conll','w',encoding='utf-8')
    ml_tag_main(outpath+'tmp/token_nonest.tmp',model_type,outpath+'tmp/ml_score.tsv',modelfile,fout_conll)
    
    #4. post processing
    print('.......post processing.........')
    post_rule2(ori_text_newentity,token_text,outpath+'tmp/ml_score.tsv',outpath+'Species_Assignment_results.PubTator')

    print('........species assignment done, the resuls can be found in '+outpath+'Species_Assignment_results.PubTator')

def BioC_Converter(infile,outpath,modelfile,model_type):

    #BioC xml to pubtator
    fin = open(infile, 'r',encoding='utf-8')
    fout_pubtator=open(outpath+'tmp/input_xml.pubtator','w', encoding='utf-8')
    collection = bioc.load(fin)
    fin.close()
    ori_ann_index={}  #{'pmid':{'id':'ent_s-ent_e'}}
    for document in collection.documents:
        doc_pmid=document.id
        doc_title=''
        doc_abstract=''
        doc_annotation=[]
        _ann_index={}
        for passage in document.passages:
            passage_offset=passage.offset
            #print(passage_offset,type(passage_offset))
            if passage.infons['type']=='title':
                doc_title=passage.text
                for temp_annotation in passage.annotations:
                    ent_start=temp_annotation.locations[0].offset-passage_offset
                    ent_end=ent_start+temp_annotation.locations[0].length
                    #print(ent_start,ent_end)
                    _ann_index[temp_annotation.id]=str(ent_start)+'-'+str(ent_end)
                    # print(temp_annotation.infons)
                    if 'Identifier' in temp_annotation.infons.keys():
                        # print(temp_annotation.infons.keys['Identifier'])
                        doc_annotation.append(doc_pmid+'\t'+str(ent_start)+'\t'+str(ent_end)+'\t'+temp_annotation.text+'\t'+temp_annotation.infons['type']+'\t'+temp_annotation.infons['Identifier'])
                    else:
                        doc_annotation.append(doc_pmid+'\t'+str(ent_start)+'\t'+str(ent_end)+'\t'+temp_annotation.text+'\t'+temp_annotation.infons['type'])

                    
            elif passage.infons['type']=='abstract':
                doc_abstract=passage.text
                for temp_annotation in passage.annotations:
                    ent_start=len(doc_title)+1+temp_annotation.locations[0].offset-passage_offset
                    ent_end=ent_start+temp_annotation.locations[0].length
                    #print(ent_start,ent_end)
                    _ann_index[temp_annotation.id]=str(ent_start)+'-'+str(ent_end)
                    if 'Identifier' in temp_annotation.infons.keys():
                        # print(temp_annotation.infons.keys['Identifier'])
                        doc_annotation.append(doc_pmid+'\t'+str(ent_start)+'\t'+str(ent_end)+'\t'+temp_annotation.text+'\t'+temp_annotation.infons['type']+'\t'+temp_annotation.infons['Identifier'])
                    else:
                        doc_annotation.append(doc_pmid+'\t'+str(ent_start)+'\t'+str(ent_end)+'\t'+temp_annotation.text+'\t'+temp_annotation.infons['type'])
        fout_pubtator.write(doc_pmid+'|t|'+doc_title+'\n')
        fout_pubtator.write(doc_pmid+'|a|'+doc_abstract+'\n')
        for ele in doc_annotation:
            fout_pubtator.write(ele+'\n')
        fout_pubtator.write('\n')
        ori_ann_index[doc_pmid]=_ann_index
    # print(ori_ann_index)
    fout_pubtator.close()
    
    #pubtator tagging
    print('.......senten split, tokenizer.........')
    ori_text_newentity,token_text=ssplit_token(outpath+'tmp/input_xml.pubtator',outpath+'tmp/token.tmp')
    #2. filter nest entity
    filter_nest(outpath+'tmp/token.tmp', outpath+'tmp/token_nonest.tmp')
    #3.ml tag
    print('.......machine learning-based tagging.........')
    fout_conll=open(outpath+'tmp/ml_tag.conll','w',encoding='utf-8')
    ml_tag_main(outpath+'tmp/token_nonest.tmp',model_type,outpath+'tmp/ml_score.tsv',modelfile,fout_conll)
    #4. post processing
    print('.......post processing.........')
    post_rule2(ori_text_newentity,token_text,outpath+'tmp/ml_score.tsv',outpath+'tmp/temp_results.PubTator')

    fin_result=open(outpath+'tmp/temp_results.PubTator','r',encoding='utf-8')
    all_in=fin_result.read().strip().split('\n\n')
    fin_result.close()
    all_results={} #{'pmid':{'ent_s-ent_e':assgn_id}}
    for doc in all_in:
        lines=doc.split('\n')
        pmid=lines[0].split('|t|')[0]
        annotation_results={}
        for i in range(2,len(lines)):
            segs=lines[i].split('\t')
            annotation_results[segs[1]+'-'+segs[2]]=segs[-1]
        all_results[pmid]=annotation_results
    
    fin = open(infile, 'r',encoding='utf-8')
    fout_xml=open(outpath+'Species_Assignment_results.xml','w', encoding='utf8')
    collection = bioc.load(fin)
    for document in collection.documents:
        doc_pmid=document.id
        for passage in document.passages:
            for temp_annotation in passage.annotations:
                if 'Identifier' not in temp_annotation.infons.keys():
                    map_index=ori_ann_index[doc_pmid][temp_annotation.id]
                    if map_index in all_results[doc_pmid].keys():
                        temp_annotation.infons['Identifier']=all_results[doc_pmid][map_index]
                
    bioc.dump(collection, fout_xml, pretty_print=True)
    print('........species assignment done, the resuls can be found in '+outpath+'Species_Assignment_results.xml')


if __name__=='__main__':
    
    parser = argparse.ArgumentParser(description='runing species assignment, python Species_Assignment.py -i infile -m modelfile -o outpath')
    parser.add_argument('--infile', '-i', help="input file",default='../example/Example_input.PubTator')
    parser.add_argument('--modelfile', '-m', help="trained deep learning model file (name includes bioformer or pubmedbert to select model type)",default='../speass_trained_models/SpeAss-Bioformer-SG.h5')
    parser.add_argument('--outpath', '-o', help="output folder to save the tagged results",default='../results/')
    args = parser.parse_args()
    
    if not os.path.exists(args.outpath+'tmp/'):
        os.makedirs(args.outpath+'tmp/')
    if args.modelfile.lower().find('bioformer')>=0:
        model_type='bioformer'
    else:
        model_type='pubmedbert'
    
    fin=open(args.infile, 'r',encoding='utf-8')
    file_format=""
    for line in fin:
        pattern_bioc = re.compile('.*<collection>.*')
        pattern_pubtator = re.compile('^([^\|]+)\|[^\|]+\|(.*)')
        if pattern_pubtator.search(line):
            file_format="PubTator"
            break
        elif pattern_bioc.search(line):
            file_format="BioC"
            break
    fin.close()
    if(file_format == "PubTator"):
        PubTator_Converter(args.infile,args.outpath,args.modelfile,model_type)
    elif(file_format == "BioC"):
        BioC_Converter(args.infile,args.outpath,args.modelfile,model_type)

    