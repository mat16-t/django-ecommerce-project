import typesense

typesense_client = typesense.Client({
    'nodes': [{
        'host': 'localhost',
        'port': '8108',
        'protocol': 'http'
    }],
    'api_key': 'NJU1ovgpuxrf440jV7WdTSBVvB2YaycR',
    'connection_timeout_seconds': 2
})