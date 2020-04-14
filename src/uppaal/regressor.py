class Regressor:
    def __init__(self, state_var_values: [], trans_val_pairs: []) -> None:
        self.state_var_values = state_var_values
        # Tuples of (transition, value)
        self.trans_val_pairs = trans_val_pairs
        super().__init__()

    def get_lowest_val_trans(self):
        lowest = None
        for pair in self.trans_val_pairs:
            if lowest is None:
                lowest = pair
            elif lowest[1] > pair[1]:
                lowest = pair
        return lowest

    def get_highest_val_trans(self):
        highest = None
        for pair in self.trans_val_pairs:
            if highest is None:
                highest = pair
            elif highest[1] < pair[1]:
                highest = pair
        return highest

    def __repr__(self) -> str:
        return "(State_var_values: {0}, trans_val_pairs {1})".format(self.state_var_values, self.trans_val_pairs)

    def __str__(self) -> str:
        return "(State_var_values: {0}, trans_val_pairs {1})".format(self.state_var_values, self.trans_val_pairs)
