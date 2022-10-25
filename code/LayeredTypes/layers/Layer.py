class Layer:
    def __init__(self,
                 layer_ident : str):
        self.name = layer_ident
        self.refinements = dict()

    def add_refinement(self,
                       identifier,
                       refinement_str):
        if not identifier in self.refinements.keys():
            self.refinements[identifier] = []
        self.refinements[identifier].append(refinement_str)

    def __str__(self):

        res = "{}:\n".format(self.name)
        for ident in self.refinements:
            refinements = self.refinements[ident]
            res += "\t{}\n".format(ident)

            for refinement in refinements:
                res += "\t\t{}\n".format(refinement)

        return res
