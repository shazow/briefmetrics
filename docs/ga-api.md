

* Get account ID:
  `GET /analytics/v3/management/accounts HTTP/1.1`

    {
        "kind": "analytics#accounts",
        "username": "shazow@gmail.com",
        "totalResults": 8,
        "startIndex": 1,
        "itemsPerPage": 1000,
        "items": [{
            "id": "407051",
            "kind": "analytics#account",
            "selfLink": "https://www.googleapis.com/analytics/v3/management/accounts/407051",
            "name": "shazow.net",
            "created": "2006-06-11T05:04:23.000Z",
            "updated": "2012-06-06T20:35:21.541Z",
            "childLink": {
                "type": "analytics#webproperties",
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/407051/webproperties"
            }
        }]
    }

* Get property ID:
  `GET /analytics/v3/management/accounts/407051/webproperties HTTP/1.1`

    {
        "kind": "analytics#webproperties",
        "username": "shazow@gmail.com",
        "totalResults": 15,
        "startIndex": 1,
        "itemsPerPage": 1000,
        "items": [{
            "id": "UA-407051-1",
            "kind": "analytics#webproperty",
            "selfLink": "https://www.googleapis.com/analytics/v3/management/accounts/407051/webproperties/UA-407051-1",
            "accountId": "407051",
            "internalWebPropertyId": "666631",
            "name": "http://shazow.net",
            "websiteUrl": "http://shazow.net",
            "level": "STANDARD",
            "profileCount": 3,
            "industryVertical": "COMPUTERS_AND_ELECTRONICS",
            "created": "2006-06-11T05:04:23.000Z",
            "updated": "2012-12-12T22:56:19.030Z",
            "parentLink": {
                "type": "analytics#account",
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/407051"
            },
            "childLink": {
                "type": "analytics#profiles",
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/407051/webproperties/UA-407051-1/profiles"
            }
        }]
    }

* `GET /analytics/v3/management/accounts/407051/webproperties/UA-407051-1/profiles HTTP/1.1`

    {
        "kind": "analytics#profiles",
        "username": "shazow@gmail.com",
        "totalResults": 3,
        "startIndex": 1,
        "itemsPerPage": 1000,
        "items": [{
            "id": "640819",
            "kind": "analytics#profile",
            "selfLink": "https://www.googleapis.com/analytics/v3/management/accounts/407051/webproperties/UA-407051-1/profiles/640819",
            "accountId": "407051",
            "webPropertyId": "UA-407051-1",
            "internalWebPropertyId": "666631",
            "name": "shazow.net",
            "currency": "USD",
            "timezone": "America/Toronto",
            "websiteUrl": "shazow.net",
            "type": "WEB",
            "created": "2006-06-11T05:04:23.000Z",
            "updated": "2011-09-29T20:00:34.864Z",
            "eCommerceTracking": false,
            "parentLink": {
                "type": "analytics#webproperty",
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/407051/webproperties/UA-407051-1"
            },
            "childLink": {
                "type": "analytics#goals",
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/407051/webproperties/UA-407051-1/profiles/640819/goals"
            }
        }]
    }

* Get visitor data. Use `start-index` and `max-results` to paginate.
  (See https://developers.google.com/analytics/devguides/reporting/core/v3/reference)
  `https://www.googleapis.com/analytics/v3/data/ga?ids=ga:640819&start-date=2012-01-01&end-date=2012-03-29&metrics=ga:visits&dimensions=day&start-index=1`

    {
        "kind": "analytics#gaData",
        "id": "https://www.googleapis.com/analytics/v3/data/ga?ids=ga:640819&dimensions=ga:day&metrics=ga:visits&start-date=2012-01-01&end-date=2012-03-29",
        "query": {
            "start-date": "2012-01-01",
            "end-date": "2012-03-29",
            "ids": "ga:640819",
            "dimensions": "ga:day",
            "metrics": ["ga:visits"],
            "start-index": 1,
            "max-results": 1000
        },
        "itemsPerPage": 1000,
        "totalResults": 31,
        "selfLink": "https://www.googleapis.com/analytics/v3/data/ga?ids=ga:640819&dimensions=ga:day&metrics=ga:visits&start-date=2012-01-01&end-date=2012-03-29",
        "profileInfo": {
            "profileId": "640819",
            "accountId": "407051",
            "webPropertyId": "UA-407051-1",
            "internalWebPropertyId": "666631",
            "profileName": "shazow.net",
            "tableId": "ga:640819"
        },
        "containsSampledData": false,
        "columnHeaders": [{
            "name": "ga:day",
            "columnType": "DIMENSION",
            "dataType": "STRING"
        }, {
            "name": "ga:visits",
            "columnType": "METRIC",
            "dataType": "INTEGER"
        }],
        "totalsForAllResults": {
            "ga:visits": "2931"
        },
        "rows": [
            ["01", "94"],
            ["02", "96"],
            ["03", "118"],
            ["04", "93"],
            ["05", "109"],
            ["06", "115"],
            ["07", "111"],
            ["08", "112"],
            ["09", "129"],
            ["10", "110"],
            ["11", "91"],
            ["12", "98"],
            ["13", "118"],
            ["14", "99"],
            ["15", "98"],
            ["16", "119"],
            ["17", "91"],
            ["18", "84"],
            ["19", "104"],
            ["20", "100"],
            ["21", "78"],
            ["22", "74"],
            ["23", "108"],
            ["24", "79"],
            ["25", "91"],
            ["26", "80"],
            ["27", "79"],
            ["28", "92"],
            ["29", "80"],
            ["30", "45"],
            ["31", "36"]
        ]
    }

* Get 30 referrers by visits:
  `GET /analytics/v3/data/ga?ids=ga:640819&start-date=2012-01-01&end-date=2013-01-01&metrics=ga:visits&dimensions=ga:fullReferrer,ga:source,ga:medium&sort=-ga:visits&max-results=30 HTTP/1.1`


    {
        "kind": "analytics#gaData",
        "id": "https://www.googleapis.com/analytics/v3/data/ga?ids=ga:640819&dimensions=ga:fullReferrer,ga:source,ga:medium&metrics=ga:visits&sort=-ga:visits&start-date=2012-01-01&end-date=2013-01-01&max-results=30",
        "query": {
            "start-date": "2012-01-01",
            "end-date": "2013-01-01",
            "ids": "ga:640819",
            "dimensions": "ga:fullReferrer,ga:source,ga:medium",
            "metrics": ["ga:visits"],
            "sort": ["-ga:visits"],
            "start-index": 1,
            "max-results": 30
        },
        "itemsPerPage": 30,
        "totalResults": 183,
        "selfLink": "https://www.googleapis.com/analytics/v3/data/ga?ids=ga:640819&dimensions=ga:fullReferrer,ga:source,ga:medium&metrics=ga:visits&sort=-ga:visits&start-date=2012-01-01&end-date=2013-01-01&max-results=30",
        "nextLink": "https://www.googleapis.com/analytics/v3/data/ga?ids=ga:640819&dimensions=ga:fullReferrer,ga:source,ga:medium&metrics=ga:visits&sort=-ga:visits&start-date=2012-01-01&end-date=2013-01-01&start-index=31&max-results=30",
        "profileInfo": {
            "profileId": "640819",
            "accountId": "407051",
            "webPropertyId": "UA-407051-1",
            "internalWebPropertyId": "666631",
            "profileName": "shazow.net",
            "tableId": "ga:640819"
        },
        "containsSampledData": false,
        "columnHeaders": [{
            "name": "ga:fullReferrer",
            "columnType": "DIMENSION",
            "dataType": "STRING"
        }, {
            "name": "ga:source",
            "columnType": "DIMENSION",
            "dataType": "STRING"
        }, {
            "name": "ga:medium",
            "columnType": "DIMENSION",
            "dataType": "STRING"
        }, {
            "name": "ga:visits",
            "columnType": "METRIC",
            "dataType": "INTEGER"
        }],
        "totalsForAllResults": {
            "ga:visits": "9978"
        },
        "rows": [
            ["(direct)", "(direct)", "(none)", "7476"],
            ["google", "google", "organic", "1147"],
            ["newtab/", "newtab", "referral", "374"],
            ["html5today.it/esempi/linerage-gioco-html5-ispirato-tron-pi-curve-pi-divertimento", "html5today.it", "referral", "160"],
            ["chanian.com/2010/08/01/tutorial-moving-from-canada-to-america-as-a-software-developer/", "chanian.com", "referral", "138"],
            ["stackoverflow.com/users/187878/shazow", "stackoverflow.com", "referral", "86"],
            ["plus.url.google.com/url", "plus.url.google.com", "referral", "46"],
            ["twitter.com/", "twitter.com", "referral", "34"],
            ["html5game.ru/index.php", "html5game.ru", "referral", "29"],
            ["twitter.com/shazow", "twitter.com", "referral", "28"],
            ["chanian.com/", "chanian.com", "referral", "20"],
            ["news.ycombinator.com/item", "news.ycombinator.com", "referral", "16"],
            ["homescreen.gaiamobile.org/", "homescreen.gaiamobile.org", "referral", "13"],
            ["chip.de/bildergalerie/Die-coolsten-Mini-Spiele-von-Mozilla-Labs-Gaming-Galerie_46710585.html", "chip.de", "referral", "11"],
            ["mobile.twitter.com/shazow", "mobile.twitter.com", "referral", "11"],
            ["msn.com/", "msn.com", "referral", "10"],
            ["webiur.tk/", "webiur.tk", "referral", "10"],
            ["linkedin.com/in/andreypetrov", "linkedin.com", "referral", "9"],
            ["youtube.com/", "youtube.com", "referral", "9"],
            ["google.com/", "google.com", "referral", "8"],
            ["google.dk/", "google.dk", "referral", "8"],
            ["jsperf.com/position-object-3", "jsperf.com", "referral", "8"],
            ["system.gaiamobile.org/", "system.gaiamobile.org", "referral", "8"],
            ["system.openwebdevice.com/", "system.openwebdevice.com", "referral", "8"],
            ["www.tinyurl.com/BuyFacebookShares/", "www.tinyurl.com/BuyFacebookShares", "referral", "8"],
            ["coolmath-games.com/0-run-2/index.html", "coolmath-games.com", "referral", "7"],
            ["www.rock.to/VeryProfitForex/", "www.rock.to/VeryProfitForex", "referral", "7"],
            ["google.com/reader/view/", "google.com", "referral", "6"],
            ["icomnow.com/angry-birds-rio-v1-0/", "icomnow.com", "referral", "6"],
            ["kirupa.com/lab/kville/main_old.htm", "kirupa.com", "referral", "6"]
        ]
    }

