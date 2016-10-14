# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import requests
import zipfile
import io
from .. import base
from .parser import parse_record
logger = logging.getLogger(__name__)


def collect(conf, conn, date_from=None, date_to=None):
    file_count = 0
    base.helpers.start(conf, 'cochrane', {})

    content = requests.get(conf['COCHRANE_ARCHIVE_URL']).content
    word_filters = ['published', 'for publication']
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for filename in archive.namelist():
            if any(word in filename.lower() for word in word_filters):
                with archive.open(filename, 'rU') as review_file:
                    file_count += 1
                    db_records = parse_record(conf['COCHRANE_ARCHIVE_URL'], review_file)
                    for rec in db_records:
                        query = {'file_name': rec['file_name'], 'study_id': rec['study_id']}
                        if rec.table in conn['warehouse'].tables:
                            existing = conn['warehouse'][rec.table].find_one(**query)
                            if existing:
                                rec['id'] = existing['id']
                        rec.write(conf, conn)

    logger.info("Collected %s review files.", file_count)
    base.helpers.stop(conf, 'cochrane', {'collected': file_count})
