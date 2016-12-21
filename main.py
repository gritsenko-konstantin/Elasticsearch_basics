from elasticsearch import Elasticsearch
import json
from pprint import pprint as pp


class Tweet:
    def __init__(self, author_id, author, text, timestamp, **kwargs):
        self.id = author_id
        self.author = author
        self.text = text
        self.timestamp = timestamp
        for key, value in kwargs.items():
            setattr(self, key, value)


class BaseElasticSearchRepository(object):
    def __init__(self, elastic_search):
        self._elastic_search = elastic_search
        self._index = None
        self._doc_type = None
        # Fields can be extended

    def get_all_query(self):
        return self._elastic_search.search(index=self._index)

    def clear_indexes(self):
        self._elastic_search.indices.delete(index=self._index, ignore=[400, 404])

    def create_index(self, body):
        self._elastic_search.index(index=self._index, doc_type=self._doc_type, body=body, pretty=True)

    def delete_by_id(self, id):
        self.es.delete(self.index, self.doc_type, id)

    def get_sources(self, elasticsearch_request):
        pass


class ElasticSearchRepository(BaseElasticSearchRepository):
    def __init__(self, elastic_search, index, doc_type):
        self._index = index
        self._doc_type = doc_type
        self._elastic_search = elastic_search

    def get_all(self):
        # source = self._elastic_search.get(index=self._index)
        tweets_response = self._elastic_search.search(index=self._index)
        tweets = []
        for tweet in tweets_response['hits']['hits']:
            source = tweet['_source']
            tweets.append(Tweet(tweet['_id'], **source))
        return tweets

    def search(self, query_string, fields=['content']):
        list_dict_fields = []
        for i in fields:
            list_dict_fields.append({i: {}})
        query = {
            "query": {
                "multi_match": {
                    "query": query_string,
                    "fields": fields,
                    "operator": "and"
                }
            },
            "highlight": {
                "fields": list_dict_fields,
                "require_field_match": 'false'
            }
        }

        response = self._elastic_search.search(self._index, body=query)

        tweets = []
        for response_item in response['hits']['hits']:
            source = response_item['_source']
            highlights = response_item['highlight']
            tweet = Tweet(response_item['_id'], **source)
            [setattr(tweet, key, str(value[0])) for key, value in highlights.items()]
            tweets.append(tweet)

        pp(response, indent=4)

        return tweets


class FileManager:
    def load_objects_from_json_file(self, path):
        documents = []
        with open(path) as o:
            documents = json.load(o)
        return documents


if __name__ == "__main__":
    elastic_search_repository = ElasticSearchRepository(Elasticsearch(), 'messages', 'tweets')
    elastic_search_repository.clear_indexes()
    file_manager = FileManager()
    json_files = file_manager.load_objects_from_json_file("./indexes.json")
    [elastic_search_repository.create_index(json) for json in json_files]

    tweets_found = elastic_search_repository.search('Ok.', ['author', 'text'])
    for tweet in tweets_found:
        pp(tweet.__dict__, indent=4)

    print('-' * 20)

    # json.dumps(dict)
    all_index_data = elastic_search_repository.get_all()
    for item in all_index_data:
        pp(item.__dict__, indent=4)
