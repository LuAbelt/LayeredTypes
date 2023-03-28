import graphlib
import os.path
from enum import Enum
from warnings import warn

import lark
from pathlib import Path
from termcolor import colored

from compiler.Exceptions import LayerException
from compiler.transformers.RemoveTokens import RemoveTokens
from layers.Layer import Layer
from layers.LayerImplWrapper import LayerImplWrapper

from compiler.transformers.CollectLayers import CollectLayers
from compiler.interpreters.CheckCF import CheckCF
from compiler.transformers.CreateAnnotatedTree import CreateAnnotatedTree as AnnotateTree
from compiler.Interpreters import SimpleInterpreter


class LayerVerificationState(Enum):
    UNPROCESSED = 0 # Layer has not been processed yet
    VERIFYING = 1   # Unused at the moment. Used for parallel verification
    SUCCESS = 2     # Layer has been successfully verified
    FAILURE = 3     # Layer has failed verification
    BLOCKED = 4     # Layer has been blocked by a layer that failed verification
    CYCLE = 5       # Layer is part of a cycle
    CYCLE_BLOCKED = 6   # Layer is blocked by a layer that is part of a cycle

class LayeredCompiler:
    def __init__(self, layer_base_dir, implementations_file=None):

        self.layer_states = dict()
        self.layer_errors = dict()
        self.layer_base_dir = Path(layer_base_dir)
        self.cycle = set()

        if implementations_file is None:
            self.implementations_file = None
        else:
            self.implementations_file = Path(implementations_file)
            if not self.implementations_file.is_file():
                raise FileNotFoundError(f"Could not find implementations file at {self.implementations_file}")

        if not self.layer_base_dir.is_dir():
            raise FileNotFoundError(f"Could not find layer base directory at {self.layer_base_dir}")

        # Build path for grammar file
        grammar_file = os.path.dirname(os.path.realpath(__file__)) + "/grammar_file.lark"
        self.parser = lark.Lark.open(grammar_file
                                     , parser= "lalr"
                                     , debug=True
                                     , propagate_positions=True
                                     , transformer=RemoveTokens(["newline"]))
        self.layers = dict()
        self.interpreter = SimpleInterpreter(self.implementations_file)

    def typecheck(self, input_file, check_cf=True, verbose=False, raise_on_error=True):
        tree = self.parse(input_file)

        self.__typecheck(tree, check_cf, raise_on_error)

        if verbose:
            self.print_summary()

        return True

    def __typecheck(self, tree, check_cf=True, raise_on_error=True):
        tree = AnnotateTree().transform(tree)

        if check_cf:
            cf_check = CheckCF(self.interpreter.external_functions_names)
            cf_check.visit(tree)

        layer_graph = self.build_layer_graph(tree)

        self.layer_states = {layer_id: LayerVerificationState.UNPROCESSED for layer_id in layer_graph}
        # Store the processing states for all layers
        for layer_id in layer_graph:
            self.layer_states.update({layer_id: LayerVerificationState.UNPROCESSED for layer_id in layer_graph[layer_id]})

        # We use graphlib to process layers in topological order
        # Currently this is not yet parallelized, but in the future we might want to do that

        topological_sorter = graphlib.TopologicalSorter(layer_graph)

        try:
            topological_sorter.prepare()
        except graphlib.CycleError as e:
            if raise_on_error:
                raise graphlib.CycleError(f"Cycle in layer dependencies: {e.args[0]}")

            self.cycle = set(e.args[1])

            for layer_id in e.args[1]:
                self.layer_states[layer_id] = LayerVerificationState.CYCLE

        while topological_sorter.is_active():
            processed_one = False
            for node in topological_sorter.get_ready():
                processed_one = True
                assert self.layer_states[node] == LayerVerificationState.UNPROCESSED
                layer_handle = self.layers[node]
                try:
                    tree = layer_handle.typecheck(tree)
                    topological_sorter.done(node)
                    self.layer_states[node] = LayerVerificationState.SUCCESS
                except Exception as e:
                    if raise_on_error:
                        raise LayerException(node,e)
                    self.layer_states[node] = LayerVerificationState.FAILURE
                    self.layer_errors[node] = LayerException(node,e)

            # We do not want to process nodes that depend on a failed node
            # This is done by marking the node as done, so it is not returned by get_ready()
            # We do this until there are no more nodes to process
            if not processed_one:
                break

        # There might be unparsed layers, which are blocked due to failed dependencies
        for layer_id in self.layer_states:
            if self.layer_states[layer_id] == LayerVerificationState.FAILURE:
                # We mark the node as done, so we can mark all nodes that depend on it as blocked
                topological_sorter.done(layer_id)
                while topological_sorter.is_active():
                    processed_one = False
                    for node in topological_sorter.get_ready():
                        processed_one = True
                        self.layer_states[node] = LayerVerificationState.BLOCKED
                        topological_sorter.done(node)

                    if not processed_one:
                        break

        # All layers that are still unprocessed are blocked because they depend on a layer that is part of a cycle
        for layer_id in self.layer_states:
            if self.layer_states[layer_id] == LayerVerificationState.UNPROCESSED:
                self.layer_states[layer_id] = LayerVerificationState.CYCLE_BLOCKED

        # Return true iff all layers are successfully verified
        return all([self.layer_states[layer_id] == LayerVerificationState.SUCCESS for layer_id in self.layer_states])

    def build_layer_graph(self, tree):
        lv = CollectLayers()
        lv.transform(tree)

        layer_graph = {}
        self.layers = {}
        implicit_layers = set()

        for layer_id in lv.layers:
            self.layers[layer_id] = LayerImplWrapper(self.layer_base_dir, lv.layers[layer_id])

            required_layers = self.layers[layer_id].depends_on()
            layer_graph[layer_id] = required_layers
            implicit_layers.update(required_layers - set(lv.layers.keys()))

            required_layers = self.layers[layer_id].run_before()
            for layer in required_layers:
                layer_graph[layer].add(layer_id)

            implicit_layers.update(required_layers - set(lv.layers.keys()))

            implied_layers = self.layers[layer_id].run_before()
            implicit_layers.update(implied_layers - set(lv.layers.keys()))
            for implied_layer in implied_layers:
                if implied_layer not in layer_graph:
                    layer_graph[implied_layer] = set()
                layer_graph[implied_layer].add(layer_id)

        while len(implicit_layers) > 0:
            layer_id = implicit_layers.pop()
            if not layer_id in self.layers:
                warn(
                    f"Layer {layer_id} was not loaded during CollectLayers, but is required by at least one other layer. Loading it now.")
                self.layers[layer_id] = LayerImplWrapper(self.layer_base_dir, Layer(layer_id))
                required_layers = self.layers[layer_id].depends_on()
                layer_graph[layer_id] = required_layers
                implicit_layers.update(required_layers - set(self.layers.keys()))

                required_layers = self.layers[layer_id].run_before()
                for layer in required_layers:
                    layer_graph[layer].add(layer_id)
                implicit_layers.update(required_layers - set(lv.layers.keys()))
        return layer_graph

    def parse(self, input_file):
        # Reset layer errors and states since these belong to the last typecheck
        self.layer_errors = dict()
        self.layer_states = dict()
        self.cycle = set()

        with open(os.path.abspath(input_file)) as f:
            tree = self.parser.parse(f.read())

        Remover = RemoveTokens(["newline"])
        tree = Remover.transform(tree)

        return tree

    def compile(self, program):
        tree = self.parse(program)

        if not self.__typecheck(tree, raise_on_error=False):
            self.print_summary()
            exit(1)

        return tree
    def run(self, program):
        tree = self.compile(program)

        return self.interpreter.run(tree)

    def print_layer_states(self):
        print("The following layers were processed:")
        for layer_id in self.layer_states:
            state = self.layer_states[layer_id]
            # Print layer name and state
            # Color of state depends on state:
            #   - Success: Green
            #   - Failure: Red
            #   - Blocked: Yellow
            #   - Unprocessed: White
            #   - Cycle: Magenta
            colors = {
                LayerVerificationState.SUCCESS: "green",
                LayerVerificationState.FAILURE: "red",
                LayerVerificationState.BLOCKED: "yellow",
                LayerVerificationState.UNPROCESSED: "white",
                LayerVerificationState.CYCLE: "magenta",
                LayerVerificationState.CYCLE_BLOCKED: "cyan"
            }

            print(colored(f"\t{layer_id}: {state.name}", colors[state]))

        print("\n")

    def print_layer_errors(self):
        # Print here all errors that occurred during typechecking
        if len(self.layer_errors) > 0:
            print("The following layers failed during typechecking:")
            for layer_id in self.layer_errors:
                print(f"\t{layer_id}:\n\t {self.layer_errors[layer_id]}")

    def print_summary(self):
        if len(self.layer_errors) == 0 and len(self.cycle) == 0:
            print("All layers were successfully verified.")
        else:
            print("Not all layers could be verified.")

        if len(self.cycle) > 0:
            print("The following cycle in the layer dependency graph was detected:")

            for layer_id in self.cycle:
                print(f"\t{layer_id}")

        self.print_layer_states()
        self.print_layer_errors()




