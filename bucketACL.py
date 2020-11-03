#!/usr/bin/python3

#https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-bucket-policies.html

import boto3
import json
import pickle
from string import Template

import logging

logging.basicConfig(filename='example.log', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)

s3 = boto3.client('s3')


#This is the account you want to alow.
destAccountNum = "109804077997"

#buckets = ['wel-science-codedeploy-dev', 'wel-tst']
buckets = s3.list_buckets()["Buckets"]
newPolicyTemplate = Template('''
{
    "Version": "2012-10-17",
    "Statement": [$statement]
}
''')

newStatementTemplate = Template('''
{
    "Sid": "crossAccountCopy-ctz-np",
    "Effect": "Allow",
    "Principal": {
        "AWS": "arn:aws:iam::$accountnum:root"
    },
    "Action": [
        "s3:Get*",
        "s3:List*"
    ],
    "Resource": [
        "arn:aws:s3:::$bucket",
        "arn:aws:s3:::$bucket/*"]
}
''')

def appendPolicy(bucketName, orig):
    ''' load the original, insert the new fragment '''
    temp = json.loads(orig['Policy'])
    newJSONencoded = json.loads(newStatementTemplate.safe_substitute(bucket=bucketName, accountnum=destAccountNum))
    temp['Statement'].append(newJSONencoded)
    return temp

def newPolicy(bucketName):
    newStatementSting = newStatementTemplate.safe_substitute(bucket=bucketName, accountnum=destAccountNum)
    newFullPolicy = newPolicyTemplate.safe_substitute(statement=newStatementSting)
    return json.loads(newFullPolicy)



if __name__ == "__main__":
    for currentBucket in buckets:
        bucketName = currentBucket["Name"]
        orig_bucket_policy = ''

        try: 
            orig_bucket_policy = s3.get_bucket_policy(Bucket=bucketName)
            try:
                with open(bucketName, 'w') as f:
                    f.write(json.dumps(orig_bucket_policy['Policy']))
                    f.close()
            except IOError as e:
                log.exception(e)
            log.info("append policy : {}".format(bucketName))
            log.info(json.dumps(appendPolicy(bucketName,orig_bucket_policy)))
            #s3.put_bucket_policy(Bucket=bucketName, Policy=json.dumps(appendPolicy(bucketName,orig_bucket_policy)))


        except Exception as e:

            try:
                with open(bucketName, 'w') as f:
                    f.write("no-policy")
                    f.close()
            except IOError as e:
                log.exception(e)
            log.info("new policy: {}".format(bucketName))
            log.info(json.dumps(newPolicy(bucketName)))
            #s3.put_bucket_policy(Bucket=bucketName, Policy=json.dumps(newPolicy(bucketName)))

        finally:
            pass



def test_newPolicy():
    pass

def test_existingPolicy():
    pass