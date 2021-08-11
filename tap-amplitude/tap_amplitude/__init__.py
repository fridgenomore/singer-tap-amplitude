#!/usr/bin/env python3
import os
import json
import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema

from io import BytesIO
from zipfile import ZipFile
from urllib import request
import base64
import gzip

from singer.transform import Transformer

REQUIRED_CONFIG_KEYS = ["start_date", "username", "password"]
LOGGER = singer.get_logger()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        # TODO: populate any metadata and stream's key properties here..
        stream_metadata = []
        key_properties = []
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )
    return Catalog(streams)


def load_events():
    url = 'https://amplitude.com/api/2/export?start=20210701T5&end=20210702T20'
    auth_user = 'xxx'
    auth_passwd = 'xxx'
    base64string = base64.b64encode(('%s:%s' % (auth_user, auth_passwd)).encode('utf-8')).decode('utf-8').replace('\n', '')

    hdr = {
        "Authorization": f'Basic {base64string}'
    }
    req = request.Request(url, headers=hdr)

    resp = request.urlopen(req)
    zipfile = ZipFile(BytesIO(resp.read()))
    for file_name in zipfile.namelist():
        with zipfile.open(file_name) as gz_file:
            gz_content = gz_file.read()
            str_content = gzip.decompress(gz_content).decode("utf-8")
            lines = str_content.split("\n")
            for line in lines:
                if "" == line.strip():
                    continue
                yield json.loads(line)

def sync(config, state, catalog):
    """ Sync data from tap source """
    # Loop over selected streams in catalog
    stream = catalog.get_stream("event")
    LOGGER.info("Syncing stream:" + stream.tap_stream_id)

    bookmark_column = stream.replication_key
    is_sorted = True  # TODO: indicate whether data is sorted ascending on bookmark value

    singer.write_schema(
        stream_name=stream.tap_stream_id,
        schema=stream.schema.to_dict(),
        key_properties=stream.key_properties,
    )

    tap_data = load_events

    max_bookmark = None
    with Transformer() as transformer:
        for row in tap_data():
            print(row)
            rec = transformer.transform(row, stream.schema.to_dict())
            singer.write_records(stream.tap_stream_id, [rec])
            if bookmark_column:
                if is_sorted:
                    # update bookmark to latest value
                    singer.write_state({stream.tap_stream_id: rec[bookmark_column]})
                else:
                    # if data unsorted, save max value until end of writes
                    max_bookmark = max(max_bookmark, rec[bookmark_column])

    if bookmark_column and not is_sorted:
        singer.write_state({stream.tap_stream_id: max_bookmark})
    return


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()
        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
