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
        super(TypecheckException, self).__init__(f"{line}:{column}: {message}")
        self.lineno = line
        self.offset = column

class WrongArgumentCountException(TypecheckException):
    """Exception that will be raised when a function is called with the wrong number of arguments.
    """
    def __init__(self, fun_name, expected, actual, line, column):
        super(WrongArgumentCountException, self).__init__(
            f"Wrong number of arguments for function {fun_name}. Expected {expected}, got {actual}.",
            line, column
        )

class FeatureNotSupportedError(TypecheckException):
    """Exception that will be raised when a feature is not supported by a typecheck layer.

    For example, certain layers might not support assignments as they would complicate the typechecking.
    """
    def __init__(self, msg, line, column):
        super(FeatureNotSupportedError, self).__init__(
            msg, line, column
        )