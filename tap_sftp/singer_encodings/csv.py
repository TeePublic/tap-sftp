import codecs
import csv
import os

from tap_sftp.singer_encodings import compression
from tap_sftp import decrypt

SDC_EXTRA_COLUMN = "_sdc_extra"

# TODO: dont make decrypt default true
def get_row_iterators(iterable, options={}, infer_compression=False, gpg_decrypt=True):
    """Accepts an interable, options and a flag to infer compression and yields
    csv.DictReader objects which can be used to yield CSV rows."""
    file_name = options.get('file_name')
    if gpg_decrypt:
        # decrypt and remove extension
        iterable = decrypt.gpg_decrypt(iterable, file_name)
        file_name = ''
    if infer_compression:
        compressed_iterables = compression.infer(iterable, file_name)
    for item in compressed_iterables:
        yield get_row_iterator(item, options=options)

def get_row_iterator(iterable, options=None):
    """Accepts an interable, options and returns a csv.DictReader object
    which can be used to yield CSV rows."""
    options = options or {}

    file_stream = codecs.iterdecode(iterable, encoding='utf-8')

    # Replace any NULL bytes in the line given to the DictReader
    reader = csv.DictReader((line.replace('\0', '') for line in file_stream), fieldnames=None, restkey=SDC_EXTRA_COLUMN, delimiter=options.get('delimiter', ','))

    headers = set(reader.fieldnames)
    if options.get('key_properties'):
        key_properties = set(options['key_properties'])
        if not key_properties.issubset(headers):
            raise Exception('CSV file missing required headers: {}'
                            .format(key_properties - headers))

    if options.get('date_overrides'):
        date_overrides = set(options['date_overrides'])
        if not date_overrides.issubset(headers):
            raise Exception('CSV file missing date_overrides headers: {}'
                            .format(date_overrides - headers))
    return reader
