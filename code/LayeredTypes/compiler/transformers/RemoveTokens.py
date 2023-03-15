import lark


class RemoveTokens(lark.Transformer):
    def __init__(self, tokens):
        super().__init__()
        self.tokens = tokens

    def __default__(self, data, children, meta):
        if data in self.tokens:
            return lark.Discard
        else:
            return lark.Tree(data, children, meta)