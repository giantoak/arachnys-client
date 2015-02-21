from urlparse import urljoin
import datetime
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
        if api_key is None:
            api_key = os.environ.get('ARACHNYS_API_KEY')
            if not api_key:
                raise ConfigException('You need an api key')
        self.debug = debug
        self.session = requests.session()
        self.session.auth = (app_id, api_key)
        self.session.headers['Accept'] = 'application/json'

    def make_request(self, endpoint, method='get', resource_id=None, params=None):
        """
        Takes an endpoint and makes the request, returning a Response object Params
        will be urlencoded if making a GET request, and otherwise will be sent as a
        JSON object.
        :param endpoint:
        :param method:
        :param resource_id:
        :param params:
        :return dict:
        """
        url = urljoin(self.API_BASE, endpoint)
        if not url.endswith('/'):
            url += '/'
        if resource_id is not None:
            url += str(resource_id) + '/'
        method = method.upper()
        data = None
        headers = None
        if method in ('POST', 'PUT', 'DELETE'):
            if params:
                data = json.dumps(params)
            params = None
            headers = {'Content-Type': 'application/json'}
        if self.debug:
            debug_url = url
            if params:
                debug_url = '%s?%s' % (url, urllib.urlencode(params))
            print 'Sending %s request to %s' % (method, debug_url)
            print 'Body: %s' % data
        resp = self.session.request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
        )
        if self.debug:
            print "Got response from API: %s" % resp.content
        if not resp.ok:
            try:
                error = resp.json()['error_message']
            except (ValueError, KeyError):
                error = resp.content
            raise ResponseException('Got error from Arachnys API: [%s] %s' %
                                    (resp.status_code, error))
        return resp.json()

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

    def get_collection(self, collection_id):
        return self.make_request('collection', 'get', collection_id)

    def create_collection(self, name=None, description=None, sources=()):
        return self.make_request('collection', 'post', params={
            'name': name,
            'description': description,
            'sources': sources,
        })

    def modify_collection(self, collection_id, name=None, description=None, sources=()):
        params = {}
        if name is not None:
            params['name'] = name
        if description is not None:
            params['description'] = description
        if sources:
            params['sources'] = sources
        if not params:
            raise Exception('No data supplied to modify resource')
        return self.make_request('collection', 'put', collection_id, params=params)

    def delete_collection(self, collection_id):
        return self.make_request('collection', 'delete', collection_id)

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

    # News Search

    def do_news_search(self, query,
                       countries=None, exclude_countries=None,
                       sources=None, exclude_sources=None,
                       categories=None, exclude_categories=None,
                       from_date=None, to_date=None):
        payload = {
            'query': query,
            'countries': countries,
            'exclude_countries': exclude_countries,
            'sources': sources,
            'exclude_sources': exclude_sources,
            'categories': categories,
            'exclude_categories': exclude_categories,
            'from_date': from_date,
            'to_date': to_date,
        }
        return self.make_request('news', 'post', params=payload)

    def get_news_search(self, uid, start=None):
        params = {'start': start} if start else {}
        return self.make_request('news/' + str(uid), 'get', params=params)

    # SearchWorker / results

    def get_searchworker(self, sw_id, start=0, page_size=10):
        return self.make_request('searchworker', 'get', sw_id, {
            'start': start,
            'page_size': page_size,
            })

    def get_worker_results(self, sw_id, max_results=-1, start=0, timeout=120, sleep_time=2):
        """
        Get 'searchresults' fields for a particular searchworker up to a given count.
        :param sw_id: searchworker for which to fetch results
        :param int max_results: maximum number of results to return. If less than 1, return all results
        :param int start: first result to return
        :param int timeout:
        :param int sleep_time:
        :return list: the max_results entries for the 'searchresults' field, unpaginated
        """
        started = time.time()
        sw = None
        while sw is None and time.time() - started < timeout:
            try:
                sw = self.get_searchworker(sw_id, start)
            except ResponseException:
                time.sleep(sleep_time)

        if sw is None:
            return []

        results = sw['searchresults']
        if max_results < 1:
            max_results = sw['meta']['total']
        else:
            max_results += start

        cur_start = start + sw['meta']['page_size']
        while cur_start < max_results and time.time() - started < timeout:
            try:
                sw = self.get_searchworker(sw_id, cur_start)
                results += sw['searchresults']
                cur_start += sw['meta']['page_size']
            except ResponseException:
                time.sleep(sleep_time)

        return results[:max_results]

    def poll_searchworkers_fast(self, ids, start=0, page_size=10):
        """
        Just does a one-time pass through searchworkers, polling them for values.
        Done as a workaround for when poll_searchworkers crashes because it hits
        a ResponseException
        :param ids:
        :param int start:
        :param int page_size:
        :return tuple: succeeded, failed, other, error_ids
        """
        if not isinstance(ids, list):
            ids = [ids]
        id_set = set(ids)

        succeeded = []
        succeeded_ids = set()
        failed = []
        failed_ids = set()
        error_ids = set()
        other = []
        other_ids = set()

        for sw_id in id_set:
            try:
                worker = self.get_searchworker(sw_id, start, page_size)
                status = worker['searchworker']['status']
                if status == 'failed':
                    failed.append(worker)
                    failed_ids.add(sw_id)
                elif status == 'succeeded':
                    succeeded.append(worker)
                    succeeded_ids.add(sw_id)
                else:
                    other.append(worker)
                    other_ids.add(sw_id)
            except ResponseException:
                error_ids.add(sw_id)

        return succeeded, failed, other, error_ids

    def poll_searchworkers(self, ids,
                           timeout=120, sleep_time=2,
                           start=0, page_size=10):
        """
        Polls a searchworker or a list of searchworkers for a result. Will time out
        after `timeout` seconds.
        This method will block until either
        a) all workers have completed, or
        b) timeout is reached
        Implementing a non-blocking version is left as an exercise to the reader.
        :param ids:
        :param int|float timeout:
        :param int|float sleep_time:
        :param int start:
        :param int page_size:
        :return:
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
            for sw_id in id_set:
                try:
                    worker = self.get_searchworker(sw_id, start, page_size)
                    status = worker['searchworker']['status']
                    if status == 'failed':
                        failed.append(worker)
                        failed_ids.add(sw_id)
                    elif status == 'succeeded':
                        succeeded.append(worker)
                        succeeded_ids.add(sw_id)
                except ResponseException:
                    # Retrieving the worker failed
                    pass
                id_set = id_set - (failed_ids | succeeded_ids)
            if not id_set:  # We're finished, none left
                break
            if time.time() - started > timeout:
                # Mark unfinished as failed
                for sw_id in id_set:
                    failed.append(self.get_searchworker(sw_id))
                    failed_ids.add(sw_id)
                break
            time.sleep(sleep_time)
        return succeeded, failed

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

    # Alerts

    def get_alerts(self):
        return self.make_request('alerts', 'get')

    def get_alert_updates(self, alert_id, updates_since=None):
        if updates_since:
            if not isinstance(updates_since, datetime.date):
                raise ValueError("'updates_since' must be a datetime.date instance")
            params = {'updates_since': updates_since.isoformat()[:19]}
        else:
            params = None
        return self.make_request('alert', 'get', alert_id, params)

    def register_alert(self, query, country=None):
        return self.make_request('alert', 'post', params={
            'query': query,
            'country': country,
        })

    def update_alert(self, alert_id, **kwargs):
        if not kwargs:
            raise ValueError('Specify at least one parameter to update')
        return self.make_request('alert', 'put', alert_id, kwargs)

    def delete_alert(self, alert_id):
        return self.make_request('alert', 'delete', alert_id)


class ConfigException(Exception):
    pass


class ResponseException(Exception):
    pass
