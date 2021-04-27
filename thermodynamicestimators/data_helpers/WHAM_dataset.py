import math
import torch
import thermodynamicestimators.data_helpers.dataset as dataset


''' The dataset to use with WHAM. Samples are returned in the shape of unnormalized histograms specifying bin counts for 
each thermodynamic state.'''
class WHAM_dataset(dataset.dataset):
    def __init__(self, potential, biases, histogram_range, sampled_positions=None, bias_coefficients=None):
        super().__init__(potential, biases)

        sampled_positions = torch.tensor(sampled_positions, dtype=torch.long)
        super().add_data(sampled_positions)

        self._histogram_range = histogram_range
        self._bias_coefficients = bias_coefficients

        if bias_coefficients is None and biases is not None:
            bias_coefficients_shape = tuple([len(biases)] + [d_range[1]- d_range[0]for d_range in self._histogram_range])

            self._bias_coefficients = torch.zeros(bias_coefficients_shape)

            # fill an array with all indices of the bias coefficients.
            indices = (self._bias_coefficients == 0).nonzero()

            # iterate over the indices to fill the bias coefficients array.
            # The array is filled in this way because we don't know the shape of the histogram beforehand and there is
            # no equivalent of numpy.ndenumerate in pytorch.
            for idx in indices:
                self._bias_coefficients[tuple(idx)] = math.exp(-biases[idx[0]](idx[1:]+ histogram_range[:, 0]))


    ''' The bias coefficient matrix for a discrete estimator (WHAM) '''
    @property
    def bias_coefficients(self):
        return self._bias_coefficients


    ''' The histogram range over each dimensional axis.
    eg. for a two-dimensional histogram: [[min_x, max_x], [min_y, max_y]]'''
    @property
    def histogram_range(self):
        return self._histogram_range


    ''' The shape of the histogram in which to bin the data. Calculated from self.histogram_range. 
    All bins are assumed to be of size 1.'''
    @property
    def histogram_shape(self):
        return tuple([dimension_range[1]-dimension_range[0] for dimension_range in self.histogram_range])


    def __len__(self):
        return len(self._sampled_positions[0])


    ''' One sample consists of one sampled position for each thermodynamic state, returned in the shape of M histograms,
    where M is the number of states. The selected samples are binned in a separate histogram belonging to their state.
    The histogram tensor is of shape (M, d1, d2,...) with M the number of thermodynamic states and d1, d2,... the sizes 
    of the dimensions. 
    This method is written to be used with a data loader so that one item is indexed at a time. If a range index is used,
    the method loops over the samples to construct a histogram, which is slow. '''
    def __getitem__(self, item):
        sample = self._sampled_positions[:, item]

        #TODO: test n-dimensional histogram
        hist = torch.zeros(tuple([self.n_states]) + self.histogram_shape)

        # if multiple items were sampled we iterate over all samples and add 1 to the histogram for all sampled indices.
        if len(sample.squeeze(-1).shape) > len(self.histogram_shape):
            for i in range(sample.shape[1]):
                idx = torch.cat((torch.tensor(range(self.n_states)).unsqueeze(1), sample[:,i] - self.histogram_range[:, 0]),
                                axis=1)
                hist[list(idx.T)] += 1
        else:
            # The sample has one coordinate for each thermodynamic state. The bias coordinate is added to the sampled
            # coordinates to obtain the histogram coordinates the histogram range is substracted since the histogram
            # indices start at 0, but the coordinate space might not. The histogram element at the resulting indices
            # is set to 1.
            idx = torch.cat((torch.tensor(range(self.n_states)).unsqueeze(1), sample - self.histogram_range[:,0]),
                            axis=1)
            hist[list(idx.T)]  = 1

        return torch.tensor(hist)