import re
import os

import torch
from torchtext.data import Field, TabularDataset
from torchtext.data.iterator import BucketIterator
from torchtext.vocab import Vectors


def clean_string(string):
    """
    Performs tokenization and string cleaning for the Reuters dataset
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'`]", " ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.lower().strip().split()


def clean_string_fl(string):
    """
    Returns only the title and first line (excluding the title) for every Reuters article, then calls clean_string
    """
    split_string = string.split('.')
    if len(split_string) > 1:
            return clean_string(split_string[0] + ". " + split_string[1])
    else:
        return clean_string(string)


def process_labels(string):
    """
    Returns the label string as a list of integers
    :param string:
    :return:
    """
    return [float(x) for x in string]


class Reuters(TabularDataset):
    NAME = 'Reuters'
    NUM_CLASSES = 90

    TEXT_FIELD = Field(batch_first=True, tokenize=clean_string)
    LABEL_FIELD = Field(sequential=False, use_vocab=False, batch_first=True, preprocessing=process_labels)

    @staticmethod
    def sort_key(ex):
        return len(ex.text)

    @classmethod
    def splits(cls, path, train=os.path.join('Reuters-21578', 'data', 'reuters_train.tsv'),
               validation=os.path.join('Reuters-21578', 'data', 'reuters_validation.tsv'),
               test=os.path.join('Reuters-21578', 'data','reuters_test.tsv'), **kwargs):
        return super(Reuters, cls).splits(
            path, train=train, validation=validation, test=test,
            format='tsv', fields=[('label', cls.LABEL_FIELD), ('text', cls.TEXT_FIELD)]
        )

    @classmethod
    def iters(cls, path, vectors_name, vectors_cache, batch_size=64, shuffle=True, device=0, vectors=None,
              unk_init=torch.Tensor.zero_):
        """
        :param path: directory containing train, test, dev files
        :param vectors_name: name of word vectors file
        :param vectors_cache: path to directory containing word vectors file
        :param batch_size: batch size
        :param device: GPU device
        :param vectors: custom vectors - either predefined torchtext vectors or your own custom Vector classes
        :param unk_init: function used to generate vector for OOV words
        :return:
        """
        if vectors is None:
            vectors = Vectors(name=vectors_name, cache=vectors_cache, unk_init=unk_init)

        train, val, test = cls.splits(path)
        cls.TEXT_FIELD.build_vocab(train, val, test, vectors=vectors)
        return BucketIterator.splits((train, val, test), batch_size=batch_size, repeat=False, shuffle=shuffle,
                                     sort_within_batch=True, device=device)