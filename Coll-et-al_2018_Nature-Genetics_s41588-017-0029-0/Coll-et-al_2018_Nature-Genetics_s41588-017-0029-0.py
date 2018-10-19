#!/usr/bin/env python
import csv
import re
import requests
import sys

sys.path.insert(0,'./')
from utils.tables import write_table

details={
    "antb":["AMIKACIN","CAPREOMYCIN","CIPROFLOXACIN","CYCLOSERINE","ETHAMBUTOL","ETHIOMIDE","ISONIAZID","KANAMYCIN","MOXIFLOXACIN","OFLOXACIN","PARA-AMINOSALISYLIC_ACID","PYRAZINAMIDE","RIFAMPICIN","STREPTOMYCIN"],
    "def_res_class":{"0":"S","1":"R"},
    "fields":["xref", "tags", "antb", "exp_type", "conc", "conc_units", "mic_summary", "mic_conc_tested", "res_class", "method", "media", "device", "doi", "who_compliant", "crit_conc"]
}

def getNCBIIdType(my_id):
    #bioproject
    re_bp=re.compile("^PRJ")
    if(len(re_bp.findall(my_id))!=0):
        return "bioproject"
    #biosample
    re_bs=re.compile("^SAM")
    if(len(re_bs.findall(my_id))!=0):
        return "biosample"
    #run
    re_r=re.compile("^ERR")
    re_r2=re.compile("^SRR")
    if((len(re_r.findall(my_id))!=0) or (len(re_r2.findall(my_id))!=0)):
        return "sra"
    return "unknown"

def trace_request(**kw):
    request = "http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db={db}&rettype=runinfo&term={term}".format(**kw)
    response = requests.get(url=request,stream=True)
    response.encoding = 'utf-8'
    return response

def build_table(table_strains,data):
    data_avail={}
    data_to_write=[]
    counter=0
    inp = csv.DictReader(open(table_strains,"r"),delimiter="\t")
    for i in inp:
        counter+=1
        # I get the biosample
        print("\r{} ({})\t\t\t".format(i["Accession"],counter),end="")
        r = trace_request(db=getNCBIIdType(i["Accession"]), term=i["Accession"])
        reader=csv.DictReader(r.iter_lines(decode_unicode=True))
        biosamples=[]
        for entry in reader:
            try:
                biosamples.append(entry["BioSample"])
                if(len(set(biosamples))>1):
                    print("[ERROR] More than one biosample for {}. Skipping this NCBI ID".format(ncbi_id))
                    continue
            except:
                print("[ERROR] I  cannot find a biosample for {}".format(ncbi_id))
                #print(r.text)
                continue
        for j in details["antb"]:
        #entry: <xref> <tags> <antb> <exp_type> <conc> <conc_units> <mic_summary> <mic_conc_tested> <res_class> <method> <media> <device> <doi> <who_compliant> <crit_conc>
            entry=[""]*14
            entry[0] = next(iter(set(biosamples)))
            # I define the antibiotic
            #I correct a mistake: ETHIOMIDE → ETHIONAMIDE
            if j=="ETHIOMIDE":
                entry[2]="ETHIONAMIDE"
            elif j=="PARA-AMINOSALISYLIC_ACID":
                entry[2]="PARA-AMINOSALICYLIC_ACID"
            else:
                entry[2]=j
            entry[1]="Coll_NatGen_2018"
            # The paper says that "Drug susceptibility data were obtained from WHO-recognized testing protocols"
            entry[3]="UNKNOWN"
            res_class=i[j]
            if res_class == "":
                continue
            entry[8]=details["def_res_class"][res_class]
            entry[-2]="10.1038/s41588-017-0029-0"
            data_to_write.append(entry)
    return(data_to_write)

def parse_rows_take_decisions(list_rows_table, file_out):
    """Takes the list of lists generated by build table and generates a tsv file with the following fields: <biosample> <antibiotic> <res_class> <tags>"""
    with open(file_out,"w") as outf:
        for row in list_rows_table:
            outf.write("{}\t{}\t{}\t{}\n".format(row[0],row[2],row[8],row[1]))


rows=build_table("./sources/resistance_data/Coll-et-al_2018_Nature-Genetics_s41588-017-0029-0.csv",details)
write_table(rows,"./Coll-et-al_2018_Nature-Genetics_s41588-017-0029-0/Coll-et-al_2018_Nature-Genetics_s41588-017-0029-0.tsv",details["fields"])
parse_rows_take_decisions(rows, "./Coll-et-al_2018_Nature-Genetics_s41588-017-0029-0/Coll-et-al_2018_Nature-Genetics_s41588-017-0029-0.res")

