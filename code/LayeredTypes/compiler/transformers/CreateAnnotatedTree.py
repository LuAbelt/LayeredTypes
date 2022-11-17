from typing import Optional

import lark
from lark.tree import Meta


class AnnotatedTree(lark.Tree):
    def __init__(self, data: str, children: 'List[Branch[_Leaf_T]]', meta: Optional[Meta]=None):
        super().__init__(data, children)
        self._meta = meta
        self.annotations = dict()

class CreateAnnotatedTree(lark.Transformer):
    def __default__(self, data, children, meta):
        return AnnotatedTree(data, children, meta)