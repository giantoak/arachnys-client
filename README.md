Arachnys API documentation
--------------------------

### Background

Arachnys supplies:

*   A library of sources organised into categories
*   The ability to query those sources and retrieve results

#### Searches

##### Index types

When you execute a search on Arachnys, you are actually running one or several
queries against the following **index types**:

*   Basic index (`basic_index`). These sources only support queries of moderate
complexity, do not support date ordering, and are limited to 100 results.
*   Advanced index (`advanced_index`) - sources are being transitioned from
`basic_index` to `advanced_index`, which supports dirty word searches, wildcards
and other complex search features.
*   Timeline search (`timeline_index`) - news results supporting advanced_index
query features and publication date ordering
*   User simulator (`user_simulator`) - real-time querying of external resources.
These are essentially macros which navigate a preprogrammed path on external
resources. This allows Arachnys to integrate with third-party resources that
do not themselves supply an API.

Currently we are in the process of migrating our indexes from `basic_index`
to `advanced_index` or `timeline_index` backends.

###### Things to be aware of

*   It is not possible to merge results of queries of different index types
together - API clients are responsible for getting results and merging them.
*   `user_simulator` queries take a significantly longer time to execute than
queries against other index types.

Because of restrictions on merging results from different query types, it is
necessary when conducting a search to gather results from each sub-search (we
call these `searchworker`s) separately.

### Making requests

#### URL patterns

    https://api.arachnys.com/api/v1/<resource>/?<querystring>

#### Specifying a version of the API

This documentation relates to v1 of the API.

To make sure your code does not break when we release backward-incompatible
API versions, you should make sure that you specify `v1` in the URL path.

#### Request format

Currently we only support JSON as both a request and response format.

#### List requests and responses

If not stated otherwise, all list requests accept the following querystring parameters:

*   `page_size <int>` - max number of objects to show on page (default: `10`)
*   `start <int>` - 0-based index of first result to show in results page
(default: `0`)

#### Constants

##### category

All sources are assigned to a `category`, which can take one of the following
string values:

*   `"Corporate registry"` - corporate records
*   `"Corporate data"` - government gazettes, stock exchanges and business directories
*   `"News"` - newspapers, magazines and TV channels relating to a specific country
or a small group of countries in a geographical region
*   `"Litigation"` - court proceedings
*   `"Government"` - governmental bodies and information published by them
*   `"Social media"` - blogs, microblogging and social networking sites
*   `"Regional news"` - newspapers, magazines or online news sources that cover several
countries in a region or worldwide
*   `"Sanctions list"` - official lists of sanctioned individuals or companies and/or
individuals wanted by authorities in connection with crimes
*   `"Directories"` - other sources of corporate or personal information
*   `"Leaks"` - high-impact leak sites such as WikiLeaks and OffshoreLeaks

##### index_type

One of `"basic_index"`, `"advanced_index"`, `"timeline_index"` or `"user_simulator"`

See above for further information on these.

### Parsing responses

#### Format

All responses are formatted as JSON.

#### Response status codes

Responses will return HTTP status codes indicating whether the request was
successful or returned an error.

##### Errors and human-readable messages

If the response indicates that there was an error, the API will try to
provide some information on what the error was. This will be passed in the
`error_message` attribute of the response.

#### meta attributes

List responses include a convenience `meta` attribute which helps you handle
pagination:

    $ curl -XGET --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/countries/

    {
      ...
      "meta":
      {
        "next_page_link": "/api/v1/countries/?start=10&page_size=10",
        "page_size": 10,
        "start": 0,
        "total": 216
      },
      ...
    }

*   `start` - index of the first item in the list retrieved
*   `page_size` - size of page retrieved
*   `total` - total number of items available
*   `next_page_link` gives you the path that you need to request the next page in
    the sequence

It is important to note that for some types of searches it is only possible
to retrieve the first 100 results. This is a restriction that we are working
hard to lift.

## Handlers

### List countries

`GET /countries/`

#### Parameters

Required:

None

Optional:

*   `name_filter` - string to filter against (case-insensitive). Will also match
    against any configured aliases.

#### Response

*   `countries <list of objects>`
    *   `iso_code` - 2 letter iso code of country
    *   `name` - English name of country

#### Example

    $ curl -XGET --user "<app_id>:<api_key" https://api.arachnys.com/api/v1/countries/

    {
      "countries":
      [
        {"iso_code": "af", "name": "Afghanistan"},
        {"iso_code": "al", "name": "Albania"},
        ...,
        {"iso_code": "aw", "name": "Aruba"}
      ],
      "meta":
      {
        "next_page_link": "/api/v1/countries/?start=10&page_size=10",
        "page_size": 10,
        "start": 0,
        "total": 216
      },
      "status": "ok"
    }

### Get country info

`GET /country/<iso_code>/`

#### Parameters

None

#### Response

*   `country <object>`
    *   `iso_code <string>`
    *   `name <string>`
    *   `num_sources <object>`
        *   `corporate registry <int>` - number of corporate registry sources available for country
        *   `news <int>` - number of news sources available for country
        *   etc

It should be noted that some sources relate to more than one country.

#### Example

    $ curl -XGET --user "<app_id>:<api_key" https://api.arachnys.com/api/v1/country/kz/

    {
      u'status': u'ok',
      u'country':
      {
        u'num_sources':
        {
          u'social media': 1,
          u'government': 5,
          u'patent': 1,
          u'regional': 11,
          u'news': 61,
          u'corporate': 2
        },
      u'iso_code': u'kz',
      u'name': u'Kazakhstan'
      }
    }

### Get sources

`GET /sources/`

#### Parameters

Required:

At **least** one of:

*   `country_iso_code <string>` - two letter iso code of the country
*   `category <string>` - one of the values for category (see elsewhere in this document)
*   `query` - case-insensitive *contains* match against following source attributes:
    *   `name`
    *   `country` `name`
    *   `description`
    *   `language`

#### Response

*   `sources <list of objects>`
    *   `id <int>` - unique id of source
    *   `name <string>` - name of the source
    *   `description <string>` - description of source
    *   `countries <list of objects>`
        *   `iso_code` - two-letter iso code of associated country
    *   `category` - which category the source belongs to
    *   `index_type` - one of `basic_index`, `advanced_index`, etc

#### Example

    $ curl -XGET --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/sources/?country_iso_code=cn&category=news

    {
      "meta": ...,
      "sources":
      [
        {
          "category": "News",
          "countries": [{"iso_code": "cn"}],
          "description": "163.com is a popular social networking platform and news portal founded in 1997 ...",
          "id": 6676,
          "index_type": "basic_index",
          "name": "163 (news)"
        },
        ...,
        ...
      ],
      "status": "ok"
    }

### Source collections

#### Limitations

Currently it is only possible to add a maximum of 100 sources to a source
collection.

### List collections

`GET /collections/`

#### Params

Required

None

Optional

*   `filter` - filter collections on `name` and `description`

#### Response

*   `collections <list of objects>`
    *   `id` - unique id of collection
    *   `name` - name of collection
    *   `description` - description
    *   `sources_num` - number of sources in collection

#### Example

    $ curl -XGET --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/collections/

    {
      "collections":
      [
        {"description": "Human readable description",
        "id": 7,
        "is_global": false,
        "name": "New collection",
        "num_sources": 2,
        "user_id": 265}
      ],
      "meta":
      {
        "next_page_link": null,
        "page_size": 10,
        "start": 0,
        "total": 1
      },
      "status": "ok"
    }

### Create collection

`POST /collection/`

#### Params

Required

*   `name`

Optional

*   `description <string>` - description of the collection
*   `sources <list of source ids>` - numeric ids of sources to add to the collection

#### Response

*   `id` - id of new collection

#### Example

    $ curl -XPOST --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/collection/ -d '
    {
      "name": "New collection",
      "description": "Human readable description",
      "sources": [45, 53]
    }'

    {
      "id": 7,
      "status": "ok"
    }

### Alter collection

`PUT /collection/<collection_id>/`

#### Parameters

All optional

*   `name`
*   `description`
*   `sources` - list given will **replace** any sources already set

#### Example

    $ curl -XPUT --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/collection/7/ -d '
    {
      "name": "New collection",
      "description": "New description",
      "sources": [10999]
    }'

    {
      "status": "ok"
    }

### Delete collection

`DELETE /collection/<collection_id>/`

#### Parameters

None

#### Response

None

#### Example

    $ curl -XDELETE --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/collection/7/

    {
      "status": "ok"
    }

### Searching

#### Overview

Because some queries can take a significant amount of time to execute,
all searches are asynchronous.

What that means is that you:

*   Create a search and set it going by `POST`ing to `/search/`. This gives
you one or more search ids.
*   Retrieve the results by `GET`ting from `/searchworker/<searchworker_id>/`

### Start search

`POST /search/`

#### Parameters

Required

*   `query <string>` - query in Arachnys syntax (see Syntax Guide)

Plus ONE OR MORE of the following filters on the sources that will be searched:

EITHER

*   One or both of:
    *   `country_iso_code`
    *   `category`

OR

*   `source_ids <list>` - max of 100 source ids to search

OR

*   `collection_id` - id of a source collection

#### Response

*   `uid <string>` - `search`es do not have `id`s but `uid`s. You should use the
    `uid` to access information about the search status.
*   `query <string>` - query searched
*   `searchworkers <list of objects>
    *   `id`
    *   `grouped_by_type <bool>`
    *   `sources <list of objects>`
        *   `id` - id of source
        *   `name` - name of source

#### Examples of permissible source groupings

*   All news sources
*   All corporate sources
*   All litigation sources
*   All sources in Guyana
*   All news sources in Guatemala
*   Collection of <= 100 arbitrary sources

#### Example

    # Search for Abramovich in Albania
    $ curl -XPOST --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/search/ -d '
    {
      "category": null,
      "group_types": true,
      "country_iso_code": "al",
      "source_ids": [],
      "index_type": null,
      "collection_id": null,
      "query": "abramovich"
    }'

    {
      "status": "ok",
      "search":
      {
        "query": "abramovich",
        "searchworkers":
        [
          {
            "category": "Corporate registry",
            "name": "All Albania corporate",
            "results_retrieved": 0,
            "index_type": "basic_index",
            "sources_searched": [],
            "failed": false,
            "running": false,
            "grouped_by_type": false,
            "id": 23863,
            "running_time": 0.0
          },
          {
            ...,
            "category": "Government"
          }
        ]
      }
    }

### Get search results

`GET /searchworker/<searchworker_id>/`

#### Parameters

None

#### Response

*   `searchresults <list of objects>` - list of search results
    *   `id` - id of result
    *   `title` - title of result document
    *   `snippet` - snippet of result
    *   `public_extra` - flat key -> value mapping of extra result data
    *   `url` - url of result
    *   `norman_url` - url to a normalized copy of the result page
    *   `language` - detected language of result (two letter code)
    *   `published_date` - date of publication of result, if available
*   `searchworker`
    *   `id`
    *   `name` - name of worker
    *   `results_available` - number of results matching query (NB it may not be possible to access all results)
    *   `status` - status of individual searchworker - one of `succeeded`, `error`
    *   `search` - uid of `search` that created this `searchworker`

#### Example

    $ curl -XGET --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/searchworker/23863/?start=0&page_size=10

    {
      "meta": { [...] },
      "searchresults":
      [
        {
          "extra": null,
          "id": 34420,
          "language": "sq",
          "published_date": null,
          "snippet": "27 Maj 2012 ... Sipas tabloidit britanik \"Daily Express\" Abramovich [truncated]...",
          "title": "Albeu.com - Nuk dor\u00ebzohet Abramovich, 17 milion euro p\u00ebr ...",
          "url": "http://www.albeu.com/sport/nuk-dorezohet-abramovich-17-milion-euro-per-guardiolen/76310/"
        },
        { [...] }
      ],
      "searchworker":
      {
        "id": 23862,
        "name": "All Albania news",
        "results_available": 2150000,
        "search": "6apCKDCUS5a3objmMg2Qb3",
        "status": "succeeded"
      },
      "status": "ok"
    }

### News search (beta)

#### Overview

Queries over our date ordered news index are fast and synchronous.

What that means to you is that:

*   Creating a search will return the results immediately.
*   Further pages of results can be retrieved by `GET`ting from `/news/<news_uid>/?start=N`

### Start a news search

`POST /news/`

#### Parameters

Required:

*   `query <string>` - query in Arachnys syntax (see Syntax Guide)

Plus ZERO OR MORE of the following filters:

*   `sources` or `exclude_sources <list of integers>`
*   `countries` or `exclude_countries <list of iso code strings>`
*   `categories` or `exclude_categories <list of strings>`
*   `from_date <string in form YYYY-MM-DD>`
*   `to_date <string in form YYYY-MM-DD>`

The only categories returned by and accepted as arguments are:

*   `"News"`
*   `"Regional news"`

Does not accept

*   `page_size`

#### Response

*   `uid <string>` - `search`es do not have `id`s but `uid`s. You should use the
    `uid` to reference the search.
*   `query <string>` - query searched
*   `results <list of objects>`
    +  `title <string>`
    +  `original_url <string>`
    +  `cached_page <string>`
    +  `translated_page <string>`
    +  `snippet <string>`
    +  `published_date <string>`
    +  `sources <list of integers>`
*   `meta <object>`
    +   `next_page_link <string>`
    +   `page_size <integer>`
    +   `start <integer>` - 0 based offset of results retrieved
    +   `total <integer>` - total number of results found


#### Example

    # Search for Abramovich in Albania
    $ curl -XPOST --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/news/ -d '
    {
      "query": "abramovich",
      "countries": ["al"]
    }'

    {
      'uid': '5CUWrznMBDHfC55iu2L',
      'query': 'abramovich',
      'results': [
        {
          'cached_page': 'https://norman.arachnys.com/?url=https%3A% ... mbrojtesi%2F',
          'original_url': 'http://botasot.info/sporti/234711/barcelona-ne-kerkim-te-nje-mbrojtesi/',
          'published_date': '2013-08-01T00:00:00+00:00',
          'snippet': '<span>. Nj\u00eb tjetu ... 20 milion\u00eb Euro. \n\n</span>',
          'sources': [4401],
          'title': 'Barcelona n\u00eb k\u00ebrkim t\u00eb nj\u00eb mbrojt\u00ebsi - Sporti - Bota Sot',
          'translated_page': 'https://norman.arachnys.com/?url=https%3A%2F%2 ... %2Fbarcelona-ne-kerkim-te-nje-mbrojtesi%2F&translate=en'
        },
        ...
      ],
      'status': 'ok',
      'meta': {
        'next_page_link': '/api/v1/news/5CUWrznMBDHfC55iu2L/?start=10',
        'page_size': 10,
        'start': 0,
        'total': 226
      }
    }

### Paginate news search results

`GET /news/<search_uid>/?start=10`

#### Parameters

Required:

*   `search_uid` - uid of the search

Optional:

*   `start <integer - 0 based result offset, default is 0>`

`page_size` is set at 10.

#### Response

Same as from creating a news search


### Translation

`GET` or `POST /translate/`

NB use of the POST verb is preferred because it reduces the scope for encoding
problems.

#### Parameters

Required:

*   `to <string>`: language to translate to as a two letter code
*   `text <string>`: text to translate

Optional:

*   `from <string>`: two letter code of the language that the input text is in (defaults to
    `""`, meaning "autodetect")
*   `is_query <bool>`: whether or not `text` should be parsed before translation as a query in
    Arachnys syntax. If so, keywords `AND`, `OR`, `NOT`, `NEARx` will not be translated
    Defaults to `false`

#### Example

    $ curl -XPOST --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/translate/ -d '
    {
      "to": "ru",
      "from": "",
      "text": "abramovich"
    }'

    {
      "status": "ok",
      "translated_text": "\u0410\u0431\u0440\u0430\u043c\u043e\u0432\u0438\u0447"
    }
    # абрамович

    $ curl -XPOST --user "<app_id>:<api_key>" https://api.arachnys.com/api/v1/translate/ -d '
    {
      "to": "ru",
      "from": "",
      "text": "abramovich near5 putin",
      "is_query": true
    }'

    {
      "status": "ok",
      "translated_text": "\u0410\u0431\u0440\u0430\u043c\u043e\u0432\u0438\u0447 NEAR5 \u041f\u0443\u0442\u0438\u043d"
    } # абрамович NEAR5 путин - i.e. "abramovich in Cyrillic within 5 words of putin in Cyrillic"

### List alerts

`GET /alerts/`

#### Params

None

### Get alert updates

`GET /alert/<alert_id>/`

#### Params

*   `updates_since`: iso-formatted date. Limit the updates returned to those
    following the given date. Defaults to 1 day ago

#### Response

*   `updates <list of objects>` - list of alert updates
    *   `id` - id of update
    *   `start_date` - lower bound of search results published date interval.
    *   `end_date` - upper bound of search results published date interval,
                     usually it's the date in which the update is run.
    *   `query` - search term results have been searched against
    *   `total_results` - total number of results
    *   `results` <list of objects> - list of search results
        *   `title` - title of the search result
        *   `norman_url` - url to a normalized copy of the result page
        *   `published_date` - publication date of the search result
        *   `original_url` - original url of the document


### Register new alert

`POST /alert/`

#### Params

*   `query`: search terms
*   `country`: country iso code

### Update existing alert

`PUT /alert/<alert_id>/`

#### Params (specify at least one)

*   `query`: search terms
*   `country`: country iso code

### Delete alert

`DELETE /alert/<alert_id>/`

#### Params

None

API client
==========

The API client library is designed as a reference implementation.

It is written in Python but the principles can be easily applied in any language.

We're in the process of documenting it properly, but for the most part it maps
one-to-one onto API calls.

See `arachnys.py` for details.
