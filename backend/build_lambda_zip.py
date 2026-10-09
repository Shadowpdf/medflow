import os
import zipfile

source = "/workspace/lambda-build-new"
destination = "/workspace/medflow-lambda-analytics.zip"

with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
    for root, dirs, files in os.walk(source):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, source)
            archive.write(full_path, relative_path)

print("Lambda ZIP created successfully.")
