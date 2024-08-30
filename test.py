import os
import zipfile


def zip_files_exclude_email(path):
    with zipfile.ZipFile(f"{path}/events.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file != "email.json":
                    file_path = f"{path}/{file}"
                    print(file)
                    zipf.write(file_path, arcname=file)
    #for filename in os.listdir(path):
    #    file_path = os.path.join(path, filename)
    #    if os.path.isfile(file_path) and filename not in ['events.zip', 'email.json']:
    #        os.remove(file_path)


zip_files_exclude_email('results/20240830_104815/154')