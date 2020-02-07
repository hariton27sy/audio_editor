# PEP8 Checked
import requests
import gzip
import shutil
import tarfile
import os
import sys


def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def __file_name(file_path):
    index_of_dot = os.path.basename(file_path).index('.')
    file_name = os.path.basename(file_path)[:index_of_dot]
    return file_name


def untar(fname, output_dir):
    tar = tarfile.open(fname)
    tar.extractall(path=output_dir)
    tar.close()
    print("Extracted in" + output_dir)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def main():
    file_id = '1EYhTrw_ZonheK7XSQk3DePtbJ_zo4teT'
    destination = 'archive.tar.gz'
    download_file_from_google_drive(file_id, destination)

    with gzip.open('archive.tar.gz', 'rb') as f_in:
        with open('archive.tar', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    untar("archive.tar", "./")

    os.remove("archive.tar.gz")
    os.remove("archive.tar")


def get_directory(dir_path):
    file_id = '1EYhTrw_ZonheK7XSQk3DePtbJ_zo4teT'
    destination = os.path.join(dir_path, 'archive.tar.gz')
    download_file_from_google_drive(file_id, destination)
    with gzip.open(destination, 'rb') as f_in:
        with open(os.path.join(dir_path, 'archive.tar'), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    untar(os.path.join(dir_path, 'archive.tar'), dir_path)

    os.remove(os.path.join(dir_path, 'archive.tar'))
    os.remove(os.path.join(dir_path, 'archive.tar.gz'))


if __name__ == "__main__":
    main()
