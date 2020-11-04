#!/usr/bin/python3

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-bucket-policies.html

import boto3
from botocore.exceptions import ClientError
import json
import argparse
import os
from string import Template

import logging

logging.basicConfig(filename='example.log', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)

s3 = boto3.client('s3')

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

# buckets = ['wel-science-codedeploy-dev', 'wel-tst']
buckets = []
try:
    buckets = s3.list_buckets()["Buckets"]
except Exception as e:
    log.exception(e)


def appendPolicy(newFragment, orig):
    ''' load the original, insert the new fragment '''
    temp = json.loads(orig['Policy'])
    newJSONencoded = json.loads(newFragment)
    temp['Statement'].append(newJSONencoded)
    return temp


def newPolicy(newFragment):
    ''' just create the entire policy '''
    newFullPolicy = newPolicyTemplate.safe_substitute(statement=newFragment)
    return json.loads(newFullPolicy)


def storeResultACL(account, filename, contents):
    try:
        os.mkdir(account)
    except Exception as e:
        log.exception(e)
        pass

    try:
        with open(os.path.join('acl', filename)) as f:
            f.write(contents)
            f.close()
    except Exception as e:
        log.exception(e)


def processSharing(shareID):
    '''not working'''

    """
    template = Template('''Grantee': {'DisplayName': '$accountName', 'ID': '$accountID', 'Type': 'CanonicalUser'}, 'Permission': 'READ'}}]''')
    accountName = "aws.digital.wpl-wrk-cds-np"
    accountID = "77b879c68a62663e697b77d7254d84f78ede2189764ffb8026f48b8db1c83827"

    for currentBucket in buckets:
        bucketName = currentBucket["Name"]
        result = ''
        newFragment = template.safe_substitute(accountName=accountName,
                                               accountID=accountID)
        try:
            result = s3.get_bucket_acl(Bucket=bucketName)
            storeResultACL(shareID, bucketName, result)
            if accountID in str(result['Grants']):
                '''already there'''
                log.info('dont add - alread there')
            else:
                log.info('add - NOT alread there')
                newJson = json.loads(json.dumps(result))
                newJson['Grants'].append(newFragment)
                result = newJson
                s3.put_bucket_acl(Bucket=)
        except ClientError as e:
            log.error(e)
        log.info("{} : {}".format(bucketName, result))
    """


def processBuckets(destAccountNum):

    for currentBucket in buckets:
        bucketName = currentBucket["Name"]
        if not bucketName.startswith('wel-') and not bucketName.startswith('pcs-'):
            continue

        orig_bucket_policy = ''
        newStatementSting = newStatementTemplate.safe_substitute(bucket=bucketName, accountnum=destAccountNum)

        try:
            orig_bucket_policy = s3.get_bucket_policy(Bucket=bucketName)
        except ClientError as e:
            # no policy
            log.info(e)
        except Exception as e:
            log.exception(e)
            break

        # backup existing or 'no-policy'
        try:
            if not os.path.exists(destAccountNum):
                os.mkdir(destAccountNum)
            with open(os.path.join(destAccountNum, bucketName), 'w') as f:
                if orig_bucket_policy == '':
                    f.write("no-policy")
                else:
                    f.write(json.dumps(orig_bucket_policy['Policy']))
                f.close()
        except IOError as e:
            log.exception(e)

        # update the policy
        if orig_bucket_policy == '':
            '''create the policy'''
            log.info("new policy: {}".format(bucketName))
            log.info(json.dumps(newPolicy(newStatementSting)))
            s3.put_bucket_policy(Bucket=bucketName,
                                 Policy=json.dumps(newPolicy(newStatementSting)))

        else:
            '''append the policy'''

            '''check if already run....'''
            if destAccountNum in str(orig_bucket_policy):
                log.info('already in there - do not append')
            else:
                log.info("append policy : {}".format(bucketName))
                log.info(json.dumps(
                    appendPolicy(newStatementSting, orig_bucket_policy)))
                s3.put_bucket_policy(Bucket=bucketName,
                                     Policy=json.dumps(
                                        appendPolicy(newStatementSting,
                                                     orig_bucket_policy)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add Permissions to ALL your S3 buckets')
    parser.add_argument('-d', '--destAccount',
                        help='Account to grant permisssion to')
    parser.add_argument('-s', '--crossAccountShare',
                        help='fullID to enable cross account share')

    args = parser.parse_args()

    # if args.crossAccountShare:
    #    processSharing(args.crossAccountShare)
    if args.destAccount:
        processBuckets(args.destAccount)


def test_newPolicy():
    pass


def test_existingPolicy():
    pass
