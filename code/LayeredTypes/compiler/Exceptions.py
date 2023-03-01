class LayerException(Exception):
    """Exception that will be raised when one of the type layers encounters an error.

    It wraps the original exception and adds the layer name to the message.

    """
    def __init__(self, layer_name, original_exception):
        self.layer_name = layer_name
        self.original_exception = original_exception
        super(LayerException, self).__init__(
            "Layer '{0}' failed with error: {1}".format(
                layer_name, str(original_exception)
            )
        )

class TypecheckException(SyntaxError):
    """Base exception for all errors that occur during typechecking.
        Is a subclass of SyntaxError, so that it can contain the exact error position.
    """
    def __init__(self, message, line, column):
        super(TypecheckException, self).__init__(message)
        self.lineno = line
        self.offset = column

class LiquidSubtypeException(TypecheckException):
    """Exception that will be raised when during liquid typechecking a subtype check fails.

    Attributes:
        left_type -- the left type of the subtype check
        right_type -- the right type of the subtype check
        context -- the context in which the subtype check failed
    """
    def __init__(self, left_type, right_type, context, line, column):
        self.left_type = left_type
        self.right_type = right_type
        self.context = context
        super().__init__(f"{left_type} is not a subtype of {right_type} (Context: {context})", line, column)
        pass