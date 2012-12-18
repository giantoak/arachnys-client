from urlparse import urljoin
import json
import os
import time
import urllib

import requests


API_BASE = 'https://api.arachnys.com/api/v1/'


class ArachnysClient(object):
    def __init__(self, app_id=None, api_key=None, host=None, debug=False):
        """
        Expects to either get passed `app_id` and `api_key`, or to find them in the
        environment.
        """
        if not host:
            self.API_BASE = API_BASE
        else:
            self.API_BASE = host
        if app_id is None:
            app_id = os.environ.get('ARACHNYS_APP_ID')
            if not app_id:
                raise ConfigException('You need an app id')
        self.app_id = app_id
        if api_key is None:
            api_key = os.environ.get('ARACHNYS_API_KEY')
            if not api_key:
                raise ConfigException('You need an api key')
        self.api_key = api_key
        self.debug = debug

    def make_request(self, endpoint, method='get', resource_id=None, params={}):
        """
        Takes an endpoint and makes the request, returning a Response object Params
        will be urlencoded if making a GET request, and otherwise will be sent as a
        JSON object.
        """
        url = urljoin(self.API_BASE, endpoint)
        if not url.endswith('/'):
            url += '/'
        if resource_id is not None:
            url += str(resource_id) + '/'
        try:
            if method == 'get':
                data = {}
                params = params
            elif method in ('post', 'put', 'delete'):
                data = json.dumps(params)
                params = {}
            if self.debug:
                debug_url = url
                if params:
                    debug_url = '%s?%s' % (url, urllib.urlencode(params))
                print 'Sending request to %s' % debug_url
                print 'Body: %s' % data
            resp = getattr(requests, method)(
                url,
                auth=(self.app_id, self.api_key),
                params=params,
                data=data,
                headers={
                    'accept': 'application/json',
                    'content-type': 'application/json'
                }
            )
        except requests.exceptions.RequestException, e:
            raise e
        if self.debug:
            print "Got response from API: %s" % resp.json
        if not resp.ok:
            if resp.json:
                error_message = resp.json['error_message']
            else:
                error_message = str(resp.status_code)
            raise ResponseException('Got error from Arachnys API: %s' % error_message)
        return resp.json

    # Translation

    def _make_translate_payload(self, text, language_from, language_to):
        return {
            'to': language_to,
            'from': language_from,
            'text': text,
        }

    def translate_text(self, text, language_from='', language_to='en'):
        params = self._make_translate_payload(text, language_from, language_to)
        return self.make_request('translate', 'post', params=params)

    def translate_query(self, text, language_from='', language_to='en'):
        params = self._make_translate_payload(text, language_from, language_to)
        params['is_query'] = True
        return self.make_request('translate', 'post', params=params)

    # Collections

    def get_collections(self, filter=None):
        params = {}
        if filter is not None:
            params['filter'] = filter
        return self.make_request('collections', 'get', params=params)

    def get_collection(self, id):
        return self.make_request('collection', 'get', id)

    def create_collection(self, name=None, description=None, sources=()):
        return self.make_request('collection', 'post', params={
            'name': name,
            'description': description,
            'sources': sources,
        })

    def modify_collection(self, id, name=None, description=None, sources=()):
        params = {}
        if name is not None:
            params['name'] = name
        if description is not None:
            params['description'] = description
        if sources:
            params['sources'] = sources
        if not params:
            raise Exception('No data supplied to modify resource')
        return self.make_request('collection', 'put', id, params=params)

    def delete_collection(self, id):
        return self.make_request('collection', 'delete', id)

    # Countries

    def get_countries(self, filter=None):
        params = {}
        if filter is not None:
            params['name_filter'] = filter
        return self.make_request('countries', 'get', params=params)

    def get_country(self, iso_code):
        return self.make_request('country', 'get', iso_code)

    # Search

    def do_search(self, query, country_iso_code=None, category=None,
                  index_type=None, source_ids=(), collection_id=None):
        payload = {
            'query': query,
            'country_iso_code': country_iso_code,
            'category': category,
            'index_type': index_type,
            'source_ids': source_ids,
            'collection_id': collection_id
        }
        return self.make_request('search', 'post', params=payload)

    def get_search(self, uid):
        return self.make_request('search', 'get', uid)

    # SearchWorker / results

    def get_searchworker(self, id, start=0, page_size=10):
        return self.make_request('searchworker', 'get', id, {
            'start': start,
            'page_size': page_size,
        })

    def poll_searchworkers(self, ids, timeout=120):
        """
        Polls a searchworker or a list of searchworkers for a result. Will time out
        after `timeout` seconds.

        This method will block until either
        a) all workers have completed, or
        b) timeout is reached

        Implementing a non-blocking version is left as an exercise to the reader.
        """
        started = time.time()
        if not isinstance(ids, list):
            ids = [ids]
        succeeded = []
        succeeded_ids = set([])
        failed = []
        failed_ids = set([])
        id_set = set(ids)
        # Don't even bother doing concurrent stuff
        while True:
            for id in id_set:
                worker = self.get_searchworker(id)
                status = worker['searchworker']['status']
                if status == 'failed':
                    failed.append(worker)
                    failed_ids.add(id)
                elif status == 'succeeded':
                    succeeded.append(worker)
                    succeeded_ids.add(id)
            id_set = id_set - (failed_ids | succeeded_ids)
            if not id_set:  # We're finished, none left
                break
            if time.time() - started > timeout:
                # Mark unfinished as failed
                for id in id_set:
                    failed.append(self.get_searchworker(id))
                    failed_ids.add(id)
                break
            time.sleep(2)
        return (succeeded, failed)

    # Sources

    def get_sources(self, country_iso_code=None, country_name=None,
                    category=None, country_region_name=None,
                    regional_coverage=None, query=None):
        params = {
            'country_iso_code': country_iso_code,
            'country_name': country_name,
            'category': category,
            'country_region_name': country_region_name,
            'regional_coverage': regional_coverage,
            'query': query,
        }
        return self.make_request('sources', 'get', params=params)


class ConfigException(Exception):
    pass


class ResponseException(Exception):
    pass
