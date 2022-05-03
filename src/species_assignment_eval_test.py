# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 16:23:35 2022
input: pubtator file
output: species assignment

@author: luol2
"""
import os
import sys
import stanza
import time
from ML_Tagging_score import ml_tag_main

nlp = stanza.Pipeline(lang='en', processors={'tokenize': 'spacy'},package='None') #package='craft'


def ssplit_token(infile,outfile,errorfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    fout_error=open(errorfile,'w',encoding='utf-8')
    all_in=fin.read().strip().split('\n\n')
    fin.close()
    ori_text_newentity={} #{line[0]+line[1]:[all entity]}
    token_text_new={}#{pmid:token_text}
    for doc_text in all_in:
        lines=doc_text.split('\n')
        ori_text=lines[0].split('|t|')[1]+' '+lines[1].split('|a|')[1]
        pmid=lines[0].split('|t|')[0]
        #print(pmid)
        entity_all=[]   #[[seg0,seg1,...,],[]]
        entity_num=0
        entity_type=set()
        for i in range(2,len(lines)):
            seg=lines[i].split('\t')
            entity_type.add(seg[4])
            entity_all.append([seg[0],'M'+str(entity_num),seg[1],seg[2],seg[3],seg[4],seg[5]])
            entity_num+=1
        ori_text_newentity[lines[0]+'\n'+lines[1]]=entity_all
        # sys.exit()

        #ssplit token
        doc_stanza = nlp(ori_text)
        token_text=''
        sentence_index=[] #[text_offset]
        for sent in doc_stanza.sentences:
            for word in sent.words:
                if word.text==' ':
                    print('token is blank!')
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
        new_ents=index_map[int(entity_all[entity_i][2])]
        new_ente=index_map[int(entity_all[entity_i][3])-1]+1
        new_ent=token_text[new_ents:new_ente]
        old_ent=entity_all[entity_i][4]
        while True:
            while new_ents>=cur_sents and new_ente< cur_sente:

                if new_ent.replace(' ','') !=old_ent.replace(' ',''):
                    print('entity error:',pmid,old_ent,new_ent,entity_all[entity_i][2],entity_all[entity_i][3])
                    fout_error.write(token_text+'\n'+pmid+'\t'+old_ent+'\t'+new_ent+'\t'+entity_all[entity_i][2]+'\t'+entity_all[entity_i][3]+'\n')

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
    #print(entity_type)
    fout.close()
    fout_error.close()
    return ori_text_newentity,token_text_new

def filter_nest(infile, outfile): #sort and nonest

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
            doc_result={}
            for i in range(1,len(lines)):
                segs=lines[i].split('\t')
                doc_result[lines[i]]=[int(segs[2]),int(segs[3])]
            doc_result=sorted(doc_result.items(), key=lambda kv:(kv[1]), reverse=False)
            doc_result_sort=[]
            for ele in doc_result:
                doc_result_sort.append(ele[0])
            
            first_entity=doc_result_sort[0].split('\t')
            nest_list=[first_entity]
            max_eid=int(first_entity[3])
            total_entity+=len(lines)-2
            for i in range(1,len(doc_result_sort)):
                segs=doc_result_sort[i].split('\t')
                if int(segs[2])> max_eid:
                    if len(nest_list)==1:
                        entity_list.append(nest_list[0])
                        nest_list=[]
                        nest_list.append(segs)
                        if int(segs[3])>max_eid:
                            max_eid=int(segs[3])
                    else:
                        #print(nest_list)
                        nest_entity+=len(nest_list)-1
                        tem=find_max_entity(nest_list)#find max entity
                        #if len(tem)>1:
                        #    print('max nest >1:',tem)
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
                    #if len(tem)>1:
                    #    print('max nest >1:',tem)
                    entity_list.extend(tem)
        fout.write(context+'\n')
        for ele in entity_list:
            fout.write('\t'.join(ele)+'\n')
        fout.write('\n')
    #print(total_entity,over_entity, nest_entity)
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

def post_ori(ori_context,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0-0':[[id,score],[id,score]]}}
    for line in fin:
        seg=line.strip().split('\t')
        if len(seg)>1:
            if seg[0] not in pred_results.keys():
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                pred_results[seg[0]]={seg[1].split('-')[0]:_temp_id_score}
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                pred_results[seg[0]][seg[1].split('-')[0]]=_temp_id_score
    #print(pred_results)
    for pmid_text in ori_context.keys():
        fout.write(pmid_text+'\n')
        for ele in ori_context[pmid_text]:
            if ele[1] in pred_results[ele[0]].keys():
                temp_preds=pred_results[ele[0]][ele[1]]
                final_preds=[]
                for _ele_temp in temp_preds:
                    final_preds.append(_ele_temp[0])
                    
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\n')
        fout.write('\n')
    fout.close()
#char nearest species
def post_rule1(ori_context,token_text,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0':{'sent':'','score':[[id,score],[id,score]]}}}
    species_index={} #{pmid:{sentid:(species id1,species id2)}}
    gene_num=0
    gene_none=0
    for line in fin:
        seg=line.strip().split('\t')
        if len(seg)>1:
            if seg[5]=='Species':
                if seg[0] not in species_index.keys():
                    _sent_id=seg[1].split('-')[1]
                    species_index[seg[0]]={_sent_id:set(seg[-2])}
                else:
                    _sent_id=seg[1].split('-')[1]
                    if _sent_id in species_index[seg[0]].keys():
                        species_index[seg[0]][_sent_id].add(seg[-2])
                    else:
                        species_index[seg[0]][_sent_id]=set(seg[-2])
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[] #[[spe_id,score]]
                _sent_id=seg[1].split('-')[1]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                if seg[0] not in pred_results.keys():                   
                    pred_results[seg[0]]={seg[1].split('-')[0]:{'sent':_sent_id,'score':_temp_id_score}}
                else:
                    pred_results[seg[0]][seg[1].split('-')[0]]={'sent':_sent_id,'score':_temp_id_score}
    #print(pred_results)
    for pmid_text in ori_context.keys():
        #print(pmid_text)
        fout.write(pmid_text+'\n')
        before_species=[] #nearest
        after_species=[] #nearest
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)

            if ele[5]=='Gene':
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
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            final_preds.add(max_id)
                    else: #'-' nearst rule
                        gene_none+=1
                        # print(ele)
                        for j in range(i+1,len(ori_context[pmid_text])):
                            temp_seg=ori_context[pmid_text][j]
                            if temp_seg[5]=='Species':
                                after_species=[int(temp_seg[2]),temp_seg[6]]
                                break
                        # print(before_species,after_species)
                        # print(seg)
                        if before_species!=[] and after_species!=[]:
                            if (int(ele[2])-before_species[0]) > (after_species[0]-int(ele[3])):
                                final_preds.add(after_species[1])
                            else:
                                final_preds.add(before_species[1])
                        elif before_species==[]:
                            final_preds.add(after_species[1])
                        elif after_species==[]:
                            final_preds.add(before_species[1])
                                                    
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
                        if (int(ele[2])-before_species[0]) > (after_species[0]-int(ele[3])):
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
#marjor species
def post_rule2(ori_context,token_text,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0':{'sent':'','score':[[id,score],[id,score]]}}}
    species_index={} #{pmid:{sentid:(species id1,species id2)}}
    species_count={}#{pmid:{speid:num}}
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
                    species_index[seg[0]]={_sent_id:set(seg[-2])}
                else:
                    _sent_id=seg[1].split('-')[1]
                    if _sent_id in species_index[seg[0]].keys():
                        species_index[seg[0]][_sent_id].add(seg[-2])
                    else:
                        species_index[seg[0]][_sent_id]=set(seg[-2])
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[] #[[spe_id,score]]
                _sent_id=seg[1].split('-')[1]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                if seg[0] not in pred_results.keys():                   
                    pred_results[seg[0]]={seg[1].split('-')[0]:{'sent':_sent_id,'score':_temp_id_score}}
                else:
                    pred_results[seg[0]][seg[1].split('-')[0]]={'sent':_sent_id,'score':_temp_id_score}
    #print(pred_results)
    for pmid_text in ori_context.keys():
        #print(pmid_text)
        fout.write(pmid_text+'\n')
        pmid=pmid_text.split('|t|')[0]
        #print(species_count[pmid])
        marjor_species = max(zip(species_count[pmid].values(), species_count[pmid].keys()))
        #print(marjor_species)
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)

            if ele[5]=='Gene':
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
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            final_preds.add(max_id)

                    else: #'marjor species
                        final_preds.add(marjor_species[1])
                                                    
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
                else:
                    final_preds.add(marjor_species[1])
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\n')
        fout.write('\n')
    fout.close()

#marjor species, title *2
def post_rule2_2(ori_context,token_text,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0':{'sent':'','score':[[id,score],[id,score]]}}}
    species_index={} #{pmid:{sentid:(species id1,species id2)}}
    species_count={}#{pmid:{speid:num}}
    for line in fin:
        seg=line.strip().split('\t')
        if len(seg)>1:
            if seg[5]=='Species':
                if seg[0] not in species_count.keys():
                    if seg[1].find('-0'):
                        print('1111')
                        species_count[seg[0]]={seg[-2]:2}
                    else:
                        species_count[seg[0]]={seg[-2]:1}
                else:
                    if seg[-2] not in species_count[seg[0]].keys():
                        if seg[1].find('-0'):
                            print('111')
                            species_count[seg[0]][seg[-2]]=2
                        else:
                            species_count[seg[0]][seg[-2]]=1
                    else:
                        if seg[1].find('-0'):
                            print('1111')
                            species_count[seg[0]][seg[-2]]+=2
                        else:
                            species_count[seg[0]][seg[-2]]+=1
                
                if seg[0] not in species_index.keys():
                    _sent_id=seg[1].split('-')[1]
                    species_index[seg[0]]={_sent_id:set(seg[-2])}
                else:
                    _sent_id=seg[1].split('-')[1]
                    if _sent_id in species_index[seg[0]].keys():
                        species_index[seg[0]][_sent_id].add(seg[-2])
                    else:
                        species_index[seg[0]][_sent_id]=set(seg[-2])
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[] #[[spe_id,score]]
                _sent_id=seg[1].split('-')[1]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                if seg[0] not in pred_results.keys():                   
                    pred_results[seg[0]]={seg[1].split('-')[0]:{'sent':_sent_id,'score':_temp_id_score}}
                else:
                    pred_results[seg[0]][seg[1].split('-')[0]]={'sent':_sent_id,'score':_temp_id_score}
    #print(pred_results)
    for pmid_text in ori_context.keys():
        #print(pmid_text)
        fout.write(pmid_text+'\n')
        pmid=pmid_text.split('|t|')[0]
        print(species_count[pmid])
        marjor_species = max(zip(species_count[pmid].values(), species_count[pmid].keys()))
        print(marjor_species)
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)

            if ele[5]=='Gene':
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
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            final_preds.add(max_id)

                    else: #'marjor species
                        final_preds.add(marjor_species[1])
                                                    
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
                else:
                    final_preds.add(marjor_species[1])
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\n')
        fout.write('\n')
    fout.close()


# details nearest rule
def post_rule3(ori_context,token_text,infile,outfile):
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
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)
            
            if ele[5]=='Gene':
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
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            final_preds.add(max_id) 
                            # final_preds.add(multi_id)
                    else: #'-' nearst rule
                        gene_none+=1
                        # print(mem_sent[ele[0]])
                        _sent_id_gene=mem_sent[ele[0]][ele[1]]
                        """
                        #the species in the same sentence
                        if _sent_id_gene in species_index[ele[0]].keys():

                            max_len=-1
                            max_id=''
                            _gene_sid=pred_results[ele[0]][ele[1]]['offset'][0]
                            _gene_eid=pred_results[ele[0]][ele[1]]['offset'][1]
                            for _spe_seg in species_index[ele[0]][_sent_id_gene]:
            
                                if int(_gene_eid)<int(_spe_seg[2]): #gene before species
                                    
                                    _temp_len=len(token_text[ele[0]][int(_gene_eid):int(_spe_seg[2])].split())
                                    if _temp_len>max_len:
                                        max_id=_spe_seg[-2]
                                        max_len=_temp_len
                                elif int(_gene_sid)> int(_spe_seg[3]): #gene after species
                                    _temp_len=len(token_text[ele[0]][int(_spe_seg[3]):int(_gene_sid)].split())
                                    if _temp_len>max_len:
                                        max_id=_spe_seg[-2]
                                        max_len=_temp_len
                                else:
                                    max_id=_spe_seg[-2]
                                    break
                            # if max_id=='':
                            #     print('1',species_index[ele[0]][_sent_id_gene])
                            #     print('2',ele)
                            #     print(debug_flag)
                            
                            final_preds.add(max_id)
                        else: #not in same setence
                        """
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

# details nearest+and
def post_rule4(ori_context,token_text,infile,outfile):
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
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)
            
            if ele[5]=='Gene':
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
                        """
                        #the species in the same sentence
                        if _sent_id_gene in species_index[ele[0]].keys():

                            max_len=-1
                            max_id=''
                            _gene_sid=pred_results[ele[0]][ele[1]]['offset'][0]
                            _gene_eid=pred_results[ele[0]][ele[1]]['offset'][1]
                            for _spe_seg in species_index[ele[0]][_sent_id_gene]:
            
                                if int(_gene_eid)<int(_spe_seg[2]): #gene before species
                                    
                                    _temp_len=len(token_text[ele[0]][int(_gene_eid):int(_spe_seg[2])].split())
                                    if _temp_len>max_len:
                                        max_id=_spe_seg[-2]
                                        max_len=_temp_len
                                elif int(_gene_sid)> int(_spe_seg[3]): #gene after species
                                    _temp_len=len(token_text[ele[0]][int(_spe_seg[3]):int(_gene_sid)].split())
                                    if _temp_len>max_len:
                                        max_id=_spe_seg[-2]
                                        max_len=_temp_len
                                else:
                                    max_id=_spe_seg[-2]
                                    break
                            # if max_id=='':
                            #     print('1',species_index[ele[0]][_sent_id_gene])
                            #     print('2',ele)
                            #     print(debug_flag)
                            
                            final_preds.add(max_id)
                        else: #not in same setence
                        """
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

def post_rule4_debug(ori_context,token_text,infile,outfile):
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
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)
            miss_flag='0'
            if ele[5]=='Gene':
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
                        miss_flag='1'
                        # print(mem_sent[ele[0]])
                        _sent_id_gene=mem_sent[ele[0]][ele[1]]
                        """
                        #the species in the same sentence
                        if _sent_id_gene in species_index[ele[0]].keys():

                            max_len=-1
                            max_id=''
                            _gene_sid=pred_results[ele[0]][ele[1]]['offset'][0]
                            _gene_eid=pred_results[ele[0]][ele[1]]['offset'][1]
                            for _spe_seg in species_index[ele[0]][_sent_id_gene]:
            
                                if int(_gene_eid)<int(_spe_seg[2]): #gene before species
                                    
                                    _temp_len=len(token_text[ele[0]][int(_gene_eid):int(_spe_seg[2])].split())
                                    if _temp_len>max_len:
                                        max_id=_spe_seg[-2]
                                        max_len=_temp_len
                                elif int(_gene_sid)> int(_spe_seg[3]): #gene after species
                                    _temp_len=len(token_text[ele[0]][int(_spe_seg[3]):int(_gene_sid)].split())
                                    if _temp_len>max_len:
                                        max_id=_spe_seg[-2]
                                        max_len=_temp_len
                                else:
                                    max_id=_spe_seg[-2]
                                    break
                            # if max_id=='':
                            #     print('1',species_index[ele[0]][_sent_id_gene])
                            #     print('2',ele)
                            #     print(debug_flag)
                            
                            final_preds.add(max_id)
                        else: #not in same setence
                        """
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
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\t'+miss_flag+'\n')
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
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\t'+miss_flag+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\t0\n')
                before_species=[int(ele[3]),ele[6]]
        fout.write('\n')
    print('gene, none:',gene_num,gene_none)
    fout.close()
    
# major+and
def post_rule5(ori_context,token_text,infile,outfile):
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
        marjor_species = max(zip(species_count[pmid].values(), species_count[pmid].keys()))
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
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)
            
            if ele[5]=='Gene':
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
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
                else:
                    final_preds.add(marjor_species[1])
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\n')
        fout.write('\n')
    print('gene, none:',gene_num,gene_none)
    fout.close()
    
#nearest gene
def post_rule6(ori_context,token_text,infile,outfile):
    fin=open(infile,'r',encoding='utf-8')
    fout=open(outfile,'w',encoding='utf-8')
    pred_results={} #{pmid:{'M0':{'sent':'','score':[[id,score],[id,score]]}}}
    species_index={} #{pmid:{sentid:(species id1,species id2)}}
    for line in fin:
        seg=line.strip().split('\t')
        if len(seg)>1:
            if seg[5]=='Species':
                if seg[0] not in species_index.keys():
                    _sent_id=seg[1].split('-')[1]
                    species_index[seg[0]]={_sent_id:set(seg[-2])}
                else:
                    _sent_id=seg[1].split('-')[1]
                    if _sent_id in species_index[seg[0]].keys():
                        species_index[seg[0]][_sent_id].add(seg[-2])
                    else:
                        species_index[seg[0]][_sent_id]=set(seg[-2])
            else:
                _pred_ids=seg[-1].split(',')
                _temp_id_score=[] #[[spe_id,score]]
                _sent_id=seg[1].split('-')[1]
                for _pred_id in _pred_ids:
                    _temp_id_score.append(_pred_id.split('|'))
                if seg[0] not in pred_results.keys():                   
                    pred_results[seg[0]]={seg[1].split('-')[0]:{'sent':_sent_id,'score':_temp_id_score}}
                else:
                    pred_results[seg[0]][seg[1].split('-')[0]]={'sent':_sent_id,'score':_temp_id_score}
    #print(pred_results)
    for pmid_text in ori_context.keys():
        #print(pmid_text)
        fout.write(pmid_text+'\n')
        before_species=[] #nearest
        after_species=[] #nearest
        nearest_gene=''
        existing_gene={}
        for i,ele in enumerate(ori_context[pmid_text]):
            #print(ele)

            if ele[5]=='Gene':
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
                                if _score>max_score:
                                    max_id=_id_ass
                                    max_score=_score
                            final_preds.add(max_id)
                            nearest_gene=max_id
                            existing_gene[ele[4].lower()]=max_id
                    else: #'-' nearst rule
                        """
                        for j in range(i+1,len(ori_context[pmid_text])):
                            temp_seg=ori_context[pmid_text][j]
                            if temp_seg[5]=='Species':
                                after_species=[int(temp_seg[2]),temp_seg[6]]
                                break
                        # print(before_species,after_species)
                        # print(seg)
                        if before_species!=[] and after_species!=[]:
                            if (int(ele[2])-before_species[0]) > (after_species[0]-int(ele[3])):
                                final_preds.add(after_species[1])
                            else:
                                final_preds.add(before_species[1])
                        elif before_species==[]:
                            final_preds.add(after_species[1])
                        elif after_species==[]:
                            final_preds.add(before_species[1])
                        """
                        if ele[4].lower() in existing_gene.keys():
                            final_preds.add(existing_gene[ele[4].lower()])
                        else:
                            final_preds.add(nearest_gene)
                                                    
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
                else:
                    """
                    for j in range(i+1,len(ori_context[pmid_text])):
                        temp_seg=ori_context[pmid_text][j]
                        if temp_seg[5]=='Species':
                            after_species=[int(temp_seg[2]),temp_seg[6]]
                            break
                    # print(before_species,after_species)
                    # print(seg)
                    if before_species!=[] and after_species!=[]:
                        if (int(ele[2])-before_species[0]) > (after_species[0]-int(ele[3])):
                            final_preds.add(after_species[1])
                        else:
                            final_preds.add(before_species[1])
                    elif before_species==[]:
                        final_preds.add(after_species[1])
                    elif after_species==[]:
                        final_preds.add(before_species[1])
                    """
                    if ele[4].lower() in existing_gene.keys():
                        final_preds.add(existing_gene[ele[4].lower()])
                    else:
                        final_preds.add(nearest_gene)
                    fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t'+','.join(final_preds)+'\n')
            else:
                fout.write(ele[0]+'\t'+'\t'.join(ele[2:])+'\t-\n')
                before_species=[int(ele[3]),ele[6]]
        fout.write('\n')
    fout.close()

if __name__=='__main__':
    # path='../'
    start_time=time.time()
    path='../../'
    tmp=path+'results/tmp/'
    if not os.path.exists(tmp):
        os.makedirs(tmp)
    #infile=path+'data/combine/combine_test_match.PubTator'
    infile=path+'data/SpeAss/SpeAss_Test.PubTator'
    #1. sentence split and token
    ori_text_newentity,token_text=ssplit_token(infile,tmp+'token.tmp',tmp+'token_error.tmp')
    #print('1 done:',time.time()-start_time)
    
    #2. filter nest entity
    #start_time=time.time()
    filter_nest(tmp+'token.tmp', tmp+'token_nonest.tmp')
    #print('2 done:',time.time()-start_time)
    
    #3.ml tag
    #start_time=time.time()
    #modelfile='../models/tuned_model/PubmedBERT/SpeAss-PubmedBERT-SG-ES3.h5'
    modelfile='../../pretrained_models/SpeAss-Bioformer-SG.h5'
    #modelfile='../models/tuned_model/Bioformer/SpeAss-Bioformer-SG-ES2.h5'
    fout_conll=open(tmp+'ml_tag.conll','w',encoding='utf-8')
    ml_tag_main(tmp+'token_nonest.tmp',"bioformer",tmp+'ml_score.tsv',modelfile,fout_conll)
    #print('3 done:',time.time()-start_time)
    
    #4. post processing
    #start_time=time.time()
    post_rule5(ori_text_newentity,token_text,tmp+'ml_score.tsv',tmp+'SpeAss_test_Bioformer_SG.SA.PubTator')
    print('tag done:',time.time()-start_time)