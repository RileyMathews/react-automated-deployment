import boto3
import os
import json
import subprocess
import mimetypes
import shutil

# get content type method
def get_content_type(file):
    print(file)
    content_type = mimetypes.guess_type(file, strict=True)[0]
    if content_type == None:
        return "binary/octet-stream"
    else:
        return content_type


# initialize s3
s3 = boto3.resource("s3")

# get working directory of folder
working_directory = os.path.abspath(os.path.curdir)
deployment_json = f"{working_directory}/deployment.json"
build_folder = f"{working_directory}/build"
print(working_directory)

# read json file and get bucket name
with open(deployment_json) as file:
    data = json.load(file)

    bucket_name = data["bucket_name"]

# init bucket object
bucket = s3.Bucket(bucket_name)

print(bucket_name)
print(data)

# delete current local build folder
if os.path.exists(build_folder):
    shutil.rmtree(build_folder)

# run app build
subprocess.check_call("npm run build", shell=True)
print("app built")

# remove old files from s3
bucket.objects.all().delete()

# push new files to s3
# loop through folders in build folder
for subdir, dirs, files in os.walk(build_folder):
    # loop through the files in each
    for file in files:
        # get the path of that file
        full_path = os.path.join(subdir, file)
        # open that file
        with open(full_path, "rb") as data:
            # generate a key based on file path
            key = full_path[len(build_folder) + 1 :]
            # generate a similar file object to debug errors
            file_obj = {
                "Key": key,
                "Body": data,
                "ACL": "public-read",
                "content-type": get_content_type(key),
            }
            print(file_obj)
            bucket.put_object(
                Key=full_path[len(build_folder) + 1 :],
                Body=data,
                ACL="public-read",
                ContentType=get_content_type(key),
            )
