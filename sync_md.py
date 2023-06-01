import argparse
import csv
import datetime
import logging
import os
import random
import re
import shutil
import sys

from enum import IntEnum, unique

LOG_DIR = f"{os.getcwd()}/log"
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

# LOGGING_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
LOGGING_FORMAT = "%(message)s"
logging.basicConfig(level=logging.DEBUG,
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler(f"{LOG_DIR}/sync_md.log", "w", "utf-8")
                    ],
                    format=LOGGING_FORMAT)

MD_INDEX_FIELD_NAMES = ["FileName", "MdUrl", "ModifiedDate", "IsSynced"]
IMG_INDEX_FIELD_NAMES = ["MdFileName", "IsDownloaded", "ImageUrl", "ImageName"]
FIELD_MODIFIED_DATE_FORMAT = "%Y/%m/%d %H:%M:%S.%f %z"


class DataPrintable:
    def __str__(self):
        return f"<{self.__class__.__name__}\n" \
               f"    {str(self.__dict__)}\n" \
               f">"


@unique
class MdIndexIsSynced(IntEnum):
    N_FIRST = -1
    N = 0
    Y = 1


class MdIndexRecord(DataPrintable):
    def __init__(self, filename, md_url, is_synced: MdIndexIsSynced, modified_date: datetime.datetime):
        self.filename = filename
        self.md_url = md_url
        self.is_synced = is_synced
        self.modified_date = modified_date


def md_index_raw_record_to_md_index_record(raw) -> MdIndexRecord:
    record = MdIndexRecord(raw["FileName"],
                           raw["MdUrl"],
                           MdIndexIsSynced(int(raw["IsSynced"])),
                           datetime.datetime.strptime(raw["ModifiedDate"], FIELD_MODIFIED_DATE_FORMAT))
    return record


class ImgIndexRecord(DataPrintable):
    def __init__(self, md_filename, is_downloaded: bool, img_url, img_name):
        self.md_filename = md_filename
        self.is_downloaded = is_downloaded
        self.img_url = img_url
        self.img_name = img_name


def img_index_raw_record_to_img_index_record(raw) -> ImgIndexRecord:
    record = ImgIndexRecord(raw["MdFileName"],
                            bool(int(raw["IsDownloaded"])),
                            raw["ImageUrl"],
                            raw["ImageName"])
    return record


class MdIndexWriter:

    def __init__(self, filepath):
        self.filepath = filepath

    def __enter__(self):
        logging.debug(f"open: {self.filepath}")
        self._file = open(self.filepath, mode="w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=MD_INDEX_FIELD_NAMES, quoting=csv.QUOTE_ALL)
        self._writer.writeheader()
        return self

    def __exit__(self, e_type, e_value, traceback):
        if not e_type:
            logging.debug(f"close: {self.filepath}")
            self._file.close()
        else:
            logging.error(f"\nException type: {e_type}"
                          f"\nException value: {e_value}"
                          f"\nTraceback: {traceback}\n")

    def create(self, record: MdIndexRecord):
        self._writer.writerow(
            {"FileName": record.filename,
             "MdUrl": record.md_url,
             "ModifiedDate": record.modified_date.strftime(FIELD_MODIFIED_DATE_FORMAT),
             "IsSynced": record.is_synced.value})

    def create_by_raw_record(self, record):
        filename = record["FileName"]
        md_url = record["MdUrl"]
        modified_date = record["ModifiedDate"]
        is_synced = record["IsSynced"]

        self._writer.writerow(
            {"FileName": filename, "MdUrl": md_url, "ModifiedDate": modified_date, "IsSynced": is_synced})


class MdIndexReader:
    def __init__(self, filepath):
        self.filepath = filepath
        self._filenames = []

    def __enter__(self):
        logging.debug(f"open: {self.filepath}")
        self._file = open(self.filepath, newline="", encoding="utf-8")
        self._reader = csv.DictReader(self._file, quoting=csv.QUOTE_ALL)
        self._filenames = self._list_filename()
        return self

    def __exit__(self, e_type, e_value, traceback):
        if not e_type:
            logging.debug(f"close: {self.filepath}")
            self._file.close()
        else:
            logging.error(f"\nException type: {e_type}"
                          f"\nException value: {e_value}"
                          f"\nTraceback: {traceback}\n")

    def _get_reader(self):
        # logging.debug(f"before {self._reader.line_num}, {self._reader.reader.line_num}")
        if self._reader.line_num > 0:
            self._file.seek(0)
            next(self._reader)  # skip header
            # logging.debug(f"after {self._reader.line_num}, {self._reader.reader.line_num}")
        return self._reader

    def _list_filename(self):
        filenames = []
        for row in self._get_reader():
            filenames.append(row["FileName"])

        return filenames

    def list_filename(self):
        return self._filenames

    def has_filename(self, filename):
        is_existed = False
        filenames = self.list_filename()

        if filename in filenames:
            is_existed = True

        return is_existed

    def get_raw_record_by_filename(self, filename):
        filenames = self.list_filename()
        record_i = filenames.index(filename)

        record = None
        for idx, row in enumerate(self._get_reader()):
            if idx == record_i:
                record = row
                break

        # logging.debug(f"raw record= {record}")
        return record

    def get_record_by_filename(self, filename):
        record = self.get_raw_record_by_filename(filename)
        record = md_index_raw_record_to_md_index_record(record)

        return record

    def list_record(self):
        for row in self._get_reader():
            record = md_index_raw_record_to_md_index_record(row)
            yield record


class ImgIndexWriter:

    def __init__(self, filepath):
        self.filepath = filepath

    def __enter__(self):
        logging.debug(f"open: {self.filepath}")
        self._file = open(self.filepath, mode="w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=IMG_INDEX_FIELD_NAMES, quoting=csv.QUOTE_ALL)
        self._writer.writeheader()
        return self

    def __exit__(self, e_type, e_value, traceback):
        if not e_type:
            logging.debug(f"close: {self.filepath}")
            self._file.close()
        else:
            logging.error(f"\nException type: {e_type}"
                          f"\nException value: {e_value}"
                          f"\nTraceback: {traceback}\n")

    def create(self, record: ImgIndexRecord):
        self._writer.writerow(
            {"MdFileName": record.md_filename,
             "IsDownloaded": int(record.is_downloaded),
             "ImageUrl": record.img_url,
             "ImageName": record.img_name})

    def create_by_raw_records(self, raw_records):
        for r in raw_records:
            record = {}
            for field_name in IMG_INDEX_FIELD_NAMES:
                record[field_name] = r.get(field_name)

            self._writer.writerow(record)


class ImgIndexReader:

    def __init__(self, filepath):
        self.filepath = filepath

    def __enter__(self):
        logging.debug(f"open: {self.filepath}")
        self._file = open(self.filepath, newline="", encoding="utf-8")
        self._reader = csv.DictReader(self._file, quoting=csv.QUOTE_ALL)
        self._record_index_by_md_filename = self._index_records_by_md_filename()
        return self

    def __exit__(self, e_type, e_value, traceback):
        if not e_type:
            logging.debug(f"close: {self.filepath}")
            self._file.close()
        else:
            logging.error(f"\nException type: {e_type}"
                          f"\nException value: {e_value}"
                          f"\nTraceback: {traceback}\n")

    def _get_reader(self):
        # logging.debug(f"before {self._reader.line_num}, {self._reader.reader.line_num}")
        if self._reader.line_num > 0:
            self._file.seek(0)
            next(self._reader)  # skip header
            # logging.debug(f"after {self._reader.line_num}, {self._reader.reader.line_num}")
        return self._reader

    def _index_records_by_md_filename(self):
        record_index = {}
        for idx, row in enumerate(self._get_reader()):
            record = img_index_raw_record_to_img_index_record(row)
            index_list = record_index.get(record.md_filename)
            if index_list is None:
                record_index[record.md_filename] = index_list = []

            index_list.append(idx)

        return record_index

    def get_raw_records_by_md_filename(self, md_filename):
        records = []
        index_list = self._record_index_by_md_filename.get(md_filename)
        if not index_list:
            return records

        for idx, row in enumerate(self._get_reader()):
            if idx in index_list:
                records.append(row)

        return records

    def get_records_by_md_filename(self, md_filename):
        records = []
        index_list = self._record_index_by_md_filename.get(md_filename)
        if not index_list:
            return records

        for idx, row in enumerate(self._get_reader()):
            if idx in index_list:
                record = img_index_raw_record_to_img_index_record(row)
                records.append(record)

        return records


def merge_md_filenames(md_dir_path, old_md_index_path):
    filenames = set((fn for fn in os.listdir(md_dir_path) if os.path.isfile(f"{md_dir_path}/{fn}")))

    with MdIndexReader(old_md_index_path) as old_md_index:
        existed_filenames = old_md_index.list_filename()

    logging.debug(f"existed_filenames= {existed_filenames}")
    filenames.update(existed_filenames)
    filenames = list(filenames)
    filenames.sort()

    logging.debug(f"\n=== All MD {len(filenames)} ==============================================")
    # for i in range(len(filenames)):
    #     logging.debug(f"file #{i + 1}= {filenames[i]}")
    logging.debug("=========================================================\n")

    return filenames


def get_md_url_mapping(md_url_index_path):
    md_url_mapping = {}

    if md_url_index_path in (None, ""):
        return md_url_mapping

    with open(md_url_index_path, newline="", encoding="utf-8") as md_url_index:
        for row in md_url_index:
            line = row.strip()

            # markdown link ex: `[Page A.md](https://hackmd.io/aaa)`
            # https://regexr.com/7el7e
            pattern = r'\[(.+)\]\((https*:\/\/.+)\)'
            result = re.search(pattern, line)
            if result is not None:
                groups = result.groups()
                # logging.debug(f"md_url match groups= {groups}")
                title, link = groups
                md_url_mapping[title] = link

    return md_url_mapping


def generate_md_index(md_dir_path, md_url_index_path, old_md_index_path, md_index_path, tmp_md_index_path):
    md_filenames = merge_md_filenames(md_dir_path, old_md_index_path)
    md_url_mapping = get_md_url_mapping(md_url_index_path)

    with MdIndexReader(old_md_index_path) as old_md_index, \
            MdIndexWriter(md_index_path) as md_index, \
            MdIndexWriter(tmp_md_index_path) as tmp_md_index:

        for md_filename in md_filenames:
            md_path = f"{md_dir_path}/{md_filename}"  # !!! md_path may not be existed.
            md_url = md_url_mapping.get(md_filename)

            if os.path.exists(md_path):
                modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(md_path)).astimezone()

                if old_md_index.has_filename(md_filename):
                    record = old_md_index.get_record_by_filename(md_filename)
                    # logging.debug(f"old record= {record}")
                    record.md_url = md_url if md_url is not None else record.md_url

                    if modified_date > record.modified_date:
                        record.is_synced = MdIndexIsSynced.N
                        record.modified_date = modified_date

                        md_index.create(record)
                        tmp_md_index.create(record)

                    else:
                        if record.is_synced != MdIndexIsSynced.Y:
                            record.is_synced = MdIndexIsSynced.N

                            md_index.create(record)
                            tmp_md_index.create(record)

                        else:
                            md_index.create(record)

                else:
                    record = MdIndexRecord(md_filename, md_url, MdIndexIsSynced.N_FIRST, modified_date)

                    md_index.create(record)
                    tmp_md_index.create(record)

            else:
                record = old_md_index.get_record_by_filename(md_filename)
                record.md_url = md_url if md_url is not None else record.md_url

                md_index.create(record)


def mock_old_index():
    tmp_dir = f"{os.getcwd()}/tmp"
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    old_md_index_path = f"{tmp_dir}/index-markdown.csv"
    old_img_index_path = f"{tmp_dir}/index-image.csv"
    logging.debug(f"mock old_md_index= {old_md_index_path}"
                  f"\nmock old_img_index= {old_img_index_path}")

    with MdIndexWriter(old_md_index_path) as old_md_index, \
            ImgIndexWriter(old_img_index_path) as old_img_index:
        pass

    return [old_md_index_path, old_img_index_path]


def copy_md_files(md_input_dir_path, md_output_dir_path):
    logging.debug(f"\n=== copy_md_files ====================================\n"
                  f"from {md_input_dir_path}\n"
                  f"to {md_output_dir_path}\n"
                  f"=======================================================\n")

    shutil.rmtree(md_output_dir_path)
    shutil.copytree(md_input_dir_path, md_output_dir_path, dirs_exist_ok=True)


def parse_img_urls_in_md(md_path, acceptance_predicate):
    img_urls = set()

    if not os.path.exists(md_path) or os.path.isdir(md_path):
        return img_urls

    with open(md_path, newline="", encoding="utf-8") as md:
        for row in md:
            line = row.strip()

            # markdown img ex: `![img alt](https://i.imgur.com/bbb.png)`
            # https://regexr.com/7el72
            pattern = r"\!\[(.*)\]\((https*:\/\/([^\)]+))\)"
            result = re.search(pattern, line)
            if result is not None:
                groups = result.groups()
                # logging.debug(f"img_url match groups= {groups}")
                alt, link, link_without_protocol = groups
                if acceptance_predicate is None \
                        or acceptance_predicate(link):
                    img_urls.add(link)
                else:
                    logging.info(f"excluding img_url\n  {link}")

    return img_urls


def is_acceptable_img_url(img_url):
    acceptance = (
        "https://i.imgur.com/",
        "https://i.stack.imgur.com/",
    )

    if img_url.startswith(acceptance, 0, len(img_url) - 1):
        return True
    else:
        return False


def generate_img_name(img_url):
    idx = img_url.rfind("/")
    url_page = img_url[idx + 1:]
    norm_name = os.path.normcase(url_page)
    # logging.debug(f"generate_img_name from `{img_url}`\n  {url_page}\n  {norm_name}")

    num = random.randint(1, 100)  # avoid duplicate name

    img_name = f"{num}-{norm_name}"

    return img_name


def generate_img_index(md_dir_path, md_index_path,
                       old_img_index_path, img_index_path, tmp_img_index_path, delete_img_list_path):
    with MdIndexReader(md_index_path) as md_index, \
            ImgIndexReader(old_img_index_path) as old_img_index, \
            ImgIndexWriter(img_index_path) as img_index, \
            ImgIndexWriter(tmp_img_index_path) as tmp_img_index, \
            open(delete_img_list_path, mode="w", newline="", encoding="utf-8") as delete_img_list:
        md_records = md_index.list_record()
        for md_record in md_records:
            md_path = f"{md_dir_path}/{md_record.filename}"  # !!! md_path may not be existed.

            if not os.path.exists(md_path) \
                    or md_record.is_synced == MdIndexIsSynced.Y:
                old_records = old_img_index.get_raw_records_by_md_filename(md_record.filename)
                img_index.create_by_raw_records(old_records)

            elif md_record.is_synced == MdIndexIsSynced.N_FIRST:
                img_urls = parse_img_urls_in_md(md_path, is_acceptable_img_url)
                # if img_urls:
                #     logging.debug(f"image urls in `{md_record.filename}`\n  {img_urls}")

                for img_url in img_urls:
                    img_name = generate_img_name(img_url)
                    record = ImgIndexRecord(md_record.filename, False, img_url, img_name)

                    img_index.create(record)
                    tmp_img_index.create(record)

            elif md_record.is_synced == MdIndexIsSynced.N:
                img_urls = parse_img_urls_in_md(md_path, is_acceptable_img_url)
                # if img_urls:
                #     logging.debug(f"image urls in `{md_record.filename}`\n  {img_urls}")

                old_records = old_img_index.get_records_by_md_filename(md_record.filename)

                old_img_urls = set()
                old_record_index = {}
                for r in old_records:
                    old_img_urls.add(r.img_url)
                    old_record_index[r.img_url] = r

                duplicate_img_urls = img_urls & old_img_urls
                new_img_urls = img_urls - old_img_urls
                deleted_img_urls = old_img_urls - img_urls

                for img_url in duplicate_img_urls:
                    record = old_record_index[img_url]

                    img_index.create(record)
                    if not record.is_downloaded:
                        tmp_img_index.create(record)

                for img_url in new_img_urls:
                    img_name = generate_img_name(img_url)
                    record = ImgIndexRecord(md_record.filename, False, img_url, img_name)

                    img_index.create(record)
                    tmp_img_index.create(record)

                for img_url in deleted_img_urls:
                    record = old_record_index[img_url]

                    (md_filename_without_ext, sep, ext) = record.md_filename.rpartition(".")
                    if sep == "." and ext == "md":
                        img_dir_name = md_filename_without_ext
                    else:
                        img_dir_name = record.md_filename

                    img_path = f"{img_dir_name}/{record.img_name}"

                    delete_img_list.write(f"{img_path}\n")


def sync_md(md_dir_path, md_url_index_path, old_md_index_path, old_img_index_path):
    logging.debug(f"\n=== console params ====================================\n"
                  f"md_dir= {md_dir_path}\n"
                  f"md_url_index= {md_url_index_path}\n"
                  f"old_md_index= {old_md_index_path}\n"
                  f"old_img_index= {old_img_index_path}\n"
                  f"=======================================================\n")

    if old_md_index_path is None or old_img_index_path is None:
        # in create mode
        logging.debug("sync_md_in_create_mode")
        [old_md_index_path, old_img_index_path] = mock_old_index()
    else:
        # in update mode
        logging.debug("sync_md_in_update_mode")

    logging.debug(f"\n=== sync_md params ======================================\n"
                  f"md_dir= {md_dir_path}\n"
                  f"md_url_index= {md_url_index_path}\n"
                  f"old_md_index= {old_md_index_path}\n"
                  f"old_img_index= {old_img_index_path}\n"
                  f"==========================================================\n")

    output_dir = f"{os.getcwd()}/output"
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    md_index_path = f"{output_dir}/index-markdown.csv"
    tmp_md_index_path = f"{output_dir}/index-markdown-tmp.csv"
    generate_md_index(md_dir_path, md_url_index_path, old_md_index_path, md_index_path, tmp_md_index_path)

    md_output_dir_path = f"{output_dir}/SyncedMd"
    copy_md_files(md_dir_path, md_output_dir_path)

    img_index_path = f"{output_dir}/index-image.csv"
    tmp_img_index_path = f"{output_dir}/index-image-tmp.csv"
    delete_img_list_path = f"{output_dir}/deleteImgList.txt"
    generate_img_index(md_output_dir_path, md_index_path,
                       old_img_index_path, img_index_path, tmp_img_index_path, delete_img_list_path)


def main():
    ap = argparse.ArgumentParser(description="Sync HackMD markdown, output is in dir `output`")
    ap.add_argument("-d", "--md-dir", required=True, help="input absolute path of markdown directory")
    ap.add_argument("-l", "--md-url-index", required=False, metavar="index-mdurl.md",
                    help="input absolute path of `index-mdurl.md`")
    ap.add_argument("-s", "--old-index", required=False, nargs=2,
                    metavar=('index-markdown.csv', 'index-image.csv'),
                    default=[None, None],
                    help="input absolute path of `index-markdown.csv`"
                         " and absolute path of `index-image.csv`"
                         " for update mode")

    args = vars(ap.parse_args())
    sync_md(args["md_dir"], args["md_url_index"], args["old_index"][0], args["old_index"][1])


if __name__ == '__main__':
    main()