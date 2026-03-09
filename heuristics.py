import heapq

class VSIDS:
    def __init__(self, num_vars, decay_factor=0.95):
        self.scores = {i: 0.0 for i in range(1, num_vars + 1)}
        self.phases = {i: 1 for i in range(1, num_vars + 1)} 
        self.decay_factor = decay_factor
        self.step = 1.0
        self.heap = [(-0.0, i) for i in range(1, num_vars + 1)]
        heapq.heapify(self.heap)

    def bump_variable(self, var, val=None):
        self.scores[var] += self.step
        if val is not None:
            self.phases[var] = 1 if val > 0 else -1
        heapq.heappush(self.heap, (-self.scores[var], var))

    def decay_scores(self):
        self.step /= self.decay_factor

    def pick_variable(self, assignment):
        while self.heap:
            score, var = heapq.heappop(self.heap)
            if assignment[var] == 0 and -score == self.scores[var]:
                return var, self.phases[var]
        return None, None