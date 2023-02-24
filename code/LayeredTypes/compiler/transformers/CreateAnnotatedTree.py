from copy import copy
from typing import Optional

import lark
from lark.tree import Meta


class AnnotatedTree(lark.Tree):
    def __init__(self, data: str, children: 'List[Branch[_Leaf_T]]', meta: Optional[Meta] = None):
        super().__init__(data, children, meta)
        self.__annotations = dict()

    def update_layer_annotations(self, layer_identifier: str, identifier: str, values: dict):
        if layer_identifier not in self.__annotations:
            self.__annotations[layer_identifier] = dict()
        if identifier not in self.__annotations:
            self.__annotations[layer_identifier][identifier] = dict()
        self.__annotations[layer_identifier][identifier].update(copy(values))

    def add_layer_annotation(self, layer_identifier: str, identifier: str, key: str, value):
        if layer_identifier not in self.__annotations:
            self.__annotations[layer_identifier] = dict()
        if identifier not in self.__annotations[layer_identifier]:
            self.__annotations[layer_identifier][identifier] = dict()

        self.__annotations[layer_identifier][identifier][key] = copy(value)

    def get_all_layer_annotations(self, layer_id: str, identifier: str):
        if layer_id not in self.__annotations:
            return {}

        return self.__annotations[layer_id][identifier]

    def get_layer_annotation(self, layer_id: str, identifier: str, key: str):
        if layer_id not in self.__annotations:
            return None

        if identifier not in self.__annotations[layer_id]:
            return None

        if key not in self.__annotations[layer_id][identifier]:
            return None

        return self.__annotations[layer_id][identifier][key]


class CreateAnnotatedTree(lark.Transformer):
    def __default__(self, data, children, meta):
        return AnnotatedTree(data, children, meta)

def make_annotated_tree(tree):
    transformer = CreateAnnotatedTree()
    return transformer.transform(tree)
