# Copyright (C) 2016 Deloitte Argentina.
# This file is part of CodexGigas - https://github.com/codexgigassys/
# See the file 'LICENSE' for copying permission.
import os
import math
import traceback
from pymongo import MongoClient
from secrets import env
#from IPython import embed
from datetime import datetime

# Saves and reads metadata to/from the db.
class MetaController():

    def __init__(self,db_collection=None):
        if db_collection is None:
            db_collection = env["db_metadata_collection"]
        client=MongoClient(env["metadata"]["host"],env["metadata"]["port"])
        db=client[env["db_metadata_name"]]
        self.collection=db[db_collection]
        self.import_coll=db.imports_tree
        self.av_coll=db.av_analysis

    def __delete__(self):
        pass

    def read(self,file_id):
        f=self.collection.find_one({"file_id":file_id})
        if(f==None): return None

        # Antivirus stuff is in another collection
        av_analysis=self.search_av_analysis(file_id)
        if(av_analysis!=None):
            # we don't want all VT metadata to get displayed.
            f["av_analysis"] = { your_key: av_analysis.get(your_key) for your_key in ["scans","positives","total","scan_date"] }
            #f["av_analysis"]=av_analysis

        return f

    def write(self,file_id,data_dic):
        command={"$set":data_dic}
        #print(command)
        try:
            self.collection.update_one({"file_id":file_id},command,upsert=True)
        except:
            print("**** Error File: %s ****"%(file_id,))
            print(command)
            err=str(traceback.format_exc())
            print(err)
            return -1
        return 0

    def writeImportsTree(self,imports):
        command={"$inc":{"count":1}}
        bulk=self.import_coll.initialize_unordered_bulk_op()
        execute_bool=False
        for i in imports:
            dll_name=i["lib"]
            funcs=i["functions"]
            for imp_name in funcs:
                execute_bool=True
                bulk.find({"function_name":imp_name.lower(),"dll_name":dll_name.lower()}).upsert().update(command)
                #print("**** Error Imports Tree ****")
                #err=str(traceback.format_exc())
                #print(err)
                #return -1
        try:
            if(execute_bool):bulk.execute({'w':0})
        except:
            print("**** Error Imports Tree ****")
            err=str(traceback.format_exc())
            print(err)
            return -1
        return 0

    def searchImportByName(self,import_name):
        r=self.import_coll.find_one({"function_name":import_name})
        return r

    def searchDllByName(self,dll_name):
        r=self.import_coll.find_one({"dll_name":dll_name})
        return r

    def searchExactImport(self,import_name,dll_name):
        r=self.import_coll.find_one({"function_name":import_name,"dll_name":dll_name})
        return r

    def count_section_used(self,section_sha1):
        f=self.collection.find({"particular_header.sections.sha1":section_sha1}).count()
        return f

    def count_resources_used(self,resources_sha1):
        f=self.collection.find({"particular_header.res_entries.sha1":resources_sha1}).count()
        return f

    def search_av_analysis(self,file_id):
        f=self.av_coll.find_one({"sha1":file_id})
        return f

    def save_first_seen(self,file_id,vt_date):
        if vt_date is None:
            return None
        try:
            date=datetime.strptime(vt_date,"%Y-%m-%d %H:%M:%S")
        except ValueError:
            print "MetaController()->save_first_seen: invalid date recieved by VT:"+str(vt_date)
            return
        self.write(file_id,{"date": date})


    def save_av_analysis(self,file_id,analysis_result):
        command={"$set":analysis_result}
        #print(command)
        try:
            self.av_coll.update_one({"sha1":file_id},command,upsert=True)
        except:
            print("**** Error File: %s ****"%(file_id,))
            print(command)
            err=str(traceback.format_exc())
            print(err)
            return -1
        self.save_first_seen(file_id,analysis_result.get('first_seen'))
        return 0

#****************TEST_CODE******************
def testCode():
    pass


#****************TEST_EXECUTE******************
from Utils.test import test
test("-test_MetaController",testCode)
