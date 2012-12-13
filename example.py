#!/usr/bin/env python

import argparse
from arachnys import ArachnysClient


def search_country_news(parsed):
    client = ArachnysClient(parsed.app_id, parsed.api_key, parsed.host, debug=parsed.debug)
    print 'Using app_id %s and api_key %s' % (client.app_id, client.api_key)
    query = raw_input('Enter query: ')
    translate_to = raw_input('Enter iso code of target language (blank for no translation): ').strip()
    if translate_to:
        print 'Translating query...'
        query = client.translate_query(query, '', translate_to)['translated_text']
        print 'Got translated query [%s]' % query

    iso_code = raw_input('Enter iso code of country to search: ').strip()
    if len(iso_code) != 2:
        raise Exception('Invalid iso code')
    print 'Getting country information...'
    country_info = client.get_country(iso_code)['country']
    print 'Got country info for', country_info['name']
    print 'Number of sources:'
    for k, v in country_info['num_sources'].iteritems():
        print '%s: %s' % (k[0].upper() + k[1:].lower(), v)

    confirm = raw_input('Do you want to continue (Y/n)? ')
    if confirm.strip().lower() == 'n':
        exit(0)

    search = client.do_search(query, country_iso_code=iso_code)['search']
    worker_ids = [w['id'] for w in search['searchworkers']]
    (succeeded, failed) = client.poll_searchworkers(worker_ids)
    print '%d searchworkers succeeded, %d failed' % (len(succeeded), len(failed))
    if succeeded:
        print 'Success:'
        i = 1
        for worker in succeeded:
            print '[%s] Results for %s (%s results available)' % (i, worker['searchworker']['name'],
                                                                  worker['searchworker']['results_available'])
            i += 1
            print_results(worker)
    if failed:
        print '%s searchworkers failed: %s' % (len(failed), ', '.join([f['searchworker']['name'] for f in failed]))
    if succeeded:
        to_paginate = raw_input('Enter number of search to paginate (Enter for none): ').strip()
        if not to_paginate:
            print 'Exiting'
            return
        try:
            to_paginate = int(to_paginate)
        except TypeError:
            print 'Not a valid choice, exiting'
        if to_paginate > i:
            print 'Not a valid choice, exiting'
        worker = client.get_searchworker(worker['searchworker']['id'], start=10)
        print_results(worker)


def print_results(worker):
    i = 1
    for result in worker['searchresults']:
        print '%d. %s' % (i, result['title'])
        i += 1
    print ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Do a simple Arachnys search from the command line')
    parser.add_argument('--app_id', type=str, dest='app_id', default=None)
    parser.add_argument('--api_key', type=str, dest='api_key', default=None)
    parser.add_argument('--query', type=str, dest='query', default=None)
    parser.add_argument('--country', type=str, dest='iso_code', default=None)
    parser.add_argument('--host', type=str, dest='host', default='https://api.arachnys.com/api/v1/')
    parser.add_argument('--debug', action='store_true', default=False)
    parsed = parser.parse_args()
    search_country_news(parsed)
