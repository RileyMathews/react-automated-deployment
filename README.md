# Automated react deployment to s3 with python

In this readme are step by step instructions on how to deploy a static react app to s3 using the code in this repos python file as an example.
Pre requisites
1. You must have a react app somewhere on your local machine
1. You must have an aws s3 bucket created and ready for deployment
1. You must have the awscli and boto3 python packages installed on your system and accessible by your python file (either globally or from an envnironment). If you have none of these installed run the following commands from your terminal
```
pip install awscli
pip install boto3
aws configure
```

## setup your react app
First we are going to create a json file in your react app that allows us to store the name of the s3 bucket the project should be deployed to. 

In the root directory of your react app run `touch deployment.json`

Add the following code to that file, substituting the name of your own s3 bucket
```
{
    "bucket_name": "name-of-your-aws-bucket"
}
```

## create the python file
Anywhere on your system create a python file that you can access the directory of for later in this guide. For example I created mine in a directory of 
```
~/python-scripts/react-deployment/deploy-react-to-s3.py
````


## python code
Now lets walk through exactly what will be in this file

```
import boto3
import os
import json
import subprocess
import mimetypes
import shutil
```

This will import the nessesary packages for our script. 
1. boto3 is the aws python package for interacting with its various resources
1. os will let us work with our computers directory system
1. json will let us parse the json file we created earlier
1. subprocess will let us run terminal commands from the python script
1. mimetypes will give us some handy functionality to process file content types for use when we upload are build products to s3
1. shutil allows us to delete the entire build folder that is already there before we run a new one

```
def get_content_type(file):
    print(file)
    content_type = mimetypes.guess_type(file, strict=True)[0]
    if content_type == None:
        return 'binary/octet-stream'
    else:
        return content_type
```
This method will be used later when we loop through each file we need to upload. If we don't specifify the correct content types for each file. AWS will just upload raw data that the browsers that try to load your website will not recognize as html/javascript etc...

```
# initialize s3
s3 = boto3.resource('s3')

# get working directory of folder
working_directory = os.path.abspath(os.path.curdir)
deployment_json = f'{working_directory}/deployment.json'
build_folder = f'{working_directory}/build'
print(working_directory)

# read json file and get bucket name
with open(deployment_json) as file:
    data = json.load(file)

    bucket_name = data['bucket_name']

# init bucket object
bucket = s3.Bucket(bucket_name)

print(bucket_name)
print(data)
```
This code simply gets all the variables in order we will need to finish the process. We first create an s3 instance that allows us to access s3 buckets, Then we get the filepath the file was called from. THIS IS IMPORTANT, you will need to always run this file from the root directory of your react app. We then load the name of the bucket from the json file and use it to hook into that bucket for use in the rest of the file. The print statements are just for you to debug if anything goes wrong. 


Now we are going to build our react app
```
# delete current local build folder
if os.path.exists(build_folder):
    shutil.rmtree(build_folder)

# run app build
subprocess.check_call('npm run build', shell=True)
print('app built')
```
This code will delete the current build folder and call npm run build to make a new one. 

```
# remove old files from s3
bucket.objects.all().delete()
```
This part isn't strictly nessesary since the build folder will generate unique file names each time its run and link its html file to those. But if you want to save on cloud storage space you could manually delete your current local build folder before uploading and this command will clear out the s3 bucket before uploading the new files. 


```
# push new files to s3
# loop through folders in build folder
for subdir, dirs, files in os.walk(build_folder):
    # loop through the files in each
    for file in files:
        # get the path of that file
        full_path = os.path.join(subdir, file)
        # open that file
        with open(full_path, 'rb') as data:
            # generate a key based on file path
            key = full_path[len(build_folder)+1:]
            # generate a similar file object to debug errors
            file_obj = {
                "Key": key,
                "Body": data,
                "ACL": 'public-read',
                "content-type": get_content_type(key)
            }
            print(file_obj)
            bucket.put_object(
                Key=full_path[len(build_folder)+1:],
                Body=data,
                ACL='public-read',
                ContentType=get_content_type(key)
            )
```
This is the code that actually loops through our build folder and pushes it to s3. Notice that the get content type method is called for each file making sure the content type is attached to it. The lines that create the file_obj dictionary and print it aren't nesseary. But if you run into issues with the files once they are uploaded you can use that dictionary to see exactly what data is getting attached to each file. 

## calling this file
Again remember. You need to call this file while you are in the root directory of your react project. An easy way to simplify this is once you have the directory of this python script. You can make a shell script alias that is easier to remember. So for example if your python script is living under the directory of...
`~/python-scripts/deployment/deploy-react-to-s3.py`
You could make a bash alias like so
`alias reactlive="python ~/python-scripts/deployment/deploy-react-to-s3.py`
Then from the root directory of your react project you simply call
`reactlive`
And the script will be called using that directory

## setting up multiple react projects
If you have multiple react projects you want deployed to s3 buckets. You simply need to create a new json file for each of them that contains the bucket name under the same key. Make sure the key is the same for each file or the python script will break.